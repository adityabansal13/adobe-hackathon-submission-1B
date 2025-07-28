import os
import json
import pdfplumber
from pathlib import Path
from collections import Counter
import torch
from sentence_transformers import SentenceTransformer, util
import time
import nltk
from nltk.tokenize import sent_tokenize

def extract_outline(pdf_path):
    """
    Extracts the title, a hierarchical outline of headings, and their content from a PDF file.
    This function forms the foundation of the document processing pipeline.
    """
    with pdfplumber.open(pdf_path) as pdf:
        font_sizes = Counter(char['size'] for page in pdf.pages for char in page.chars)
        if not font_sizes:
            return {"title": "", "outline": []}
        
        sorted_sizes = sorted(font_sizes.keys(), reverse=True)
        
        title = ""
        title_size = 0
        if pdf.pages:
            first_page = pdf.pages[0]
            first_page_sizes = Counter(char['size'] for char in first_page.chars)
            if first_page_sizes:
                title_size = max(first_page_sizes.keys())
                for line in first_page.extract_text_lines():
                    if line['chars'] and line['chars'][0]['size'] == title_size:
                        title = line['text'].strip()
                        break
        
        # Heuristic: The top 3 font sizes (excluding title) are likely H1, H2, H3.
        # This is a key assumption for structuring the document.
        heading_sizes = [s for s in sorted_sizes if s != title_size][:3]
        size_to_level = {size: f"H{i+1}" for i, size in enumerate(heading_sizes)}

        outline = []
        for page in pdf.pages:
            lines = page.extract_text_lines()
            current_section_info = None
            content_buffer = []

            for line in lines:
                line_text = line['text'].strip()
                if not line_text or not line['chars']:
                    continue

                line_size = line['chars'][0]['size']
                # A line is a heading if its font size is one of the heading sizes, it's not too long, and doesn't look like a sentence.
                is_heading = (line_size in size_to_level and 
                              len(line_text.split()) <= 15 and 
                              not line_text.endswith('.'))

                if is_heading:
                    # If we have a pending heading, save it with its content
                    if current_section_info:
                        current_section_info['content'] = ' '.join(content_buffer).strip()
                        outline.append(current_section_info)
                    
                    # Start a new heading and reset content buffer
                    content_buffer = []
                    current_section_info = {
                        "level": size_to_level[line_size],
                        "text": line_text,
                        "page": page.page_number,
                        "content": ""
                    }
                elif current_section_info:
                    # This is content for the current heading
                    content_buffer.append(line_text)
            
            # Add the last section from the page
            if current_section_info:
                current_section_info['content'] = ' '.join(content_buffer).strip()
                outline.append(current_section_info)

    # Combine consecutive headings of the same level into a single section
    # for better semantic analysis.
    refined_outline = []
    if outline:
        current_section = outline[0]
        for next_section in outline[1:]:
            is_same_section = (next_section['level'] == current_section['level'] and 
                               next_section['page'] == current_section['page'])
            
            if is_same_section:
                current_section['text'] += " " + next_section['text']
                if 'content' in next_section and next_section['content']:
                    # Ensure content exists before trying to access it.
                    current_content = current_section.get('content', '')
                    next_content = next_section.get('content', '')
                    current_section['content'] = (current_content + " " + next_content).strip()
            else:
                refined_outline.append(current_section)
                current_section = next_section
        refined_outline.append(current_section)
    
    return {"title": title, "outline": refined_outline}

def analyze_documents(doc_paths, persona, job_to_be_done, model):
    """
    Analyzes documents to find sections relevant to a persona's job-to-be-done.
    """
    focus_areas_str = ", ".join(persona['focus_areas'])
    query = f"{persona['role_description']} looking for {focus_areas_str} to {job_to_be_done['task']}"
    query_embedding = model.encode(query, convert_to_tensor=True)
    
    all_sections = []
    for doc_path in doc_paths:
        data = extract_outline(doc_path)
        for section in data['outline']:
            section_text = section['text']
            section_embedding = model.encode(section_text, convert_to_tensor=True)
            
            # Calculate cosine similarity between the query and the section text.
            cosine_score = util.pytorch_cos_sim(query_embedding, section_embedding).item()
            
            all_sections.append({
                "document": doc_path.name,
                "page_number": section['page'],
                "section_title": section['text'],
                "relevance_score": cosine_score,
                "content": section.get("content", "")
            })
            
    # Sort sections by relevance score in descending order and assign a rank.
    ranked_sections = sorted(all_sections, key=lambda x: x['relevance_score'], reverse=True)
    for i, section in enumerate(ranked_sections):
        section['importance_rank'] = i + 1
        
    return ranked_sections

def analyze_sub_sections(ranked_sections, query, model):
    """
    Analyzes the content of ranked sections to extract and rank relevant sub-sections (sentences).
    """
    query_embedding = model.encode(query, convert_to_tensor=True)
    sub_section_analysis = []

    # Focus on the top 5 most relevant sections for sub-section analysis to manage processing time.
    nltk.download('punkt')
    for section in ranked_sections[:5]:
        sentences = sent_tokenize(section['content'])
        if not sentences:
            continue

        sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
        similarities = util.pytorch_cos_sim(query_embedding, sentence_embeddings)[0]
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                sub_section_analysis.append({
                    "document": section['document'],
                    "original_section_title": section['section_title'],
                    "refined_text": sentence.strip(),
                    "page_number": section['page_number'],
                    "relevance_score": similarities[i].item()
                })

    # Sort all extracted sentences by relevance and return the top 10.
    return sorted(sub_section_analysis, key=lambda x: x['relevance_score'], reverse=True)[:10]

def process_submission():
    """
    Main function to run the complete Round 1B solution.
    """
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # In a real scenario, persona and job would come from a config file or API.
    # Here, we define them directly as per the Round 1B structure.
    config_path = input_dir / "persona.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
            persona_data = config["persona"]
            job_to_be_done_data = config["job_to_be_done"]
    else:
        persona_data = {
            "role_description": "Investment Analyst",
            "focus_areas": ["revenue trends", "R&D investments", "market positioning"]
        }
        job_to_be_done_data = {
            "task": "Analyze revenue trends, R&D investments, and market positioning strategies from annual reports."
        }
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in /app/input.")
        return

    # Load the pre-cached sentence transformer model.
    model = SentenceTransformer('all-MiniLM-L6-v2')

    start_time = time.time()
    extracted_sections = analyze_documents(pdf_files, persona_data, job_to_be_done_data, model)
    
    # Construct the same query for sub-section analysis
    focus_areas_str = ", ".join(persona_data['focus_areas'])
    query = f"{persona_data['role_description']} looking for {focus_areas_str} to {job_to_be_done_data['task']}"
    
    sub_section_results = analyze_sub_sections(extracted_sections, query, model)
    processing_time = time.time() - start_time

    # Clean up the `content` field from the main sections list for the final output
    for section in extracted_sections:
        del section['content']

    output_data = {
        "metadata": {
            "input_documents": [pdf.name for pdf in pdf_files],
            "persona": persona_data,
            "job_to_be_done": job_to_be_done_data,
            "processing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "processing_time_seconds": round(processing_time, 2)
        },
        "extracted_sections": extracted_sections,
        "sub_section_analysis": sub_section_results
    }

    output_file = output_dir / "analysis_output.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)
    print(f"Successfully processed {len(pdf_files)} documents. Output saved to {output_file}")

if __name__ == "__main__":
    process_submission() 