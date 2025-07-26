import os
import json
import pdfplumber
from pathlib import Path
from collections import Counter
import torch
from sentence_transformers import SentenceTransformer, util
import time

def extract_outline(pdf_path):
    """
    Extracts the title and a hierarchical outline of headings from a PDF file.
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
            # Noise Filtering: Ignore lines with too many words (likely paragraphs) or ending in a period.
            # This heuristic is crucial for cleaning the output but may miss unconventionally formatted headings.
            for line in page.extract_text_lines():
                line_text = line['text'].strip()
                if not line_text or not line['chars'] or len(line_text.split()) > 15 or line_text.endswith('.'):
                    continue

                line_size = line['chars'][0]['size']
                if line_size in size_to_level:
                    outline.append({
                        "level": size_to_level[line_size],
                        "text": line_text,
                        "page": page.page_number
                    })

    # Combine consecutive headings of the same level into a single section
    # for better semantic analysis.
    refined_outline = []
    if outline:
        current_section = outline[0]
        for next_section in outline[1:]:
            if next_section['level'] == current_section['level'] and next_section['page'] == current_section['page']:
                current_section['text'] += " " + next_section['text']
            else:
                refined_outline.append(current_section)
                current_section = next_section
        refined_outline.append(current_section)
    
    return {"title": title, "outline": refined_outline}

def analyze_documents(doc_paths, persona, job_to_be_done, model):
    """
    Analyzes documents to find sections relevant to a persona's job-to-be-done.
    """
    query = f"{persona['role_description']} {job_to_be_done['task']}"
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
                "relevance_score": cosine_score
            })
            
    # Sort sections by relevance score in descending order and assign a rank.
    ranked_sections = sorted(all_sections, key=lambda x: x['relevance_score'], reverse=True)
    for i, section in enumerate(ranked_sections):
        section['importance_rank'] = i + 1
        
    return ranked_sections

def process_submission():
    """
    Main function to run the complete Round 1B solution.
    """
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # In a real scenario, persona and job would come from a config file or API.
    # Here, we define them directly as per the Round 1B structure.
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

    for pdf_file in pdf_files:
        start_time = time.time()
        extracted_sections = analyze_documents([pdf_file], persona_data, job_to_be_done_data, model)
        processing_time = time.time() - start_time

        output_data = {
            "metadata": {
                "input_documents": [pdf_file.name],
                "persona": persona_data,
                "job_to_be_done": job_to_be_done_data,
                "processing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "processing_time_seconds": round(processing_time, 2)
            },
            "extracted_sections": extracted_sections,
            "sub_section_analysis": [] 
        }

        output_file = output_dir / f"{pdf_file.stem}.json"
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=4)
    print(f"Successfully processed {len(pdf_files)} documents. Output files saved in {output_dir}")

if __name__ == "__main__":
    process_submission() 