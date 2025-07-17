import os
import json
import pdfplumber
from pathlib import Path
from collections import Counter

def extract_outline(pdf_path):
    """
    Extracts the title and a hierarchical outline of headings from a PDF file.
    """
    with pdfplumber.open(pdf_path) as pdf:
        # Get the font sizes of all characters in the document
        font_sizes = Counter(char['size'] for page in pdf.pages for char in page.chars)
        if not font_sizes:
            return {"title": "", "outline": []}
        
        # Identify heading sizes
        sorted_sizes = sorted(font_sizes.keys(), reverse=True)
        
        # A more robust way to find the title: largest font size on the first page
        title = ""
        if pdf.pages:
            first_page = pdf.pages[0]
            # Find the largest font size on the first page
            first_page_sizes = Counter(char['size'] for char in first_page.chars)
            if first_page_sizes:
                title_size = max(first_page_sizes.keys())
                # Find the first line with this font size
                for line in first_page.extract_text_lines():
                    if line['chars'] and line['chars'][0]['size'] == title_size:
                        title = line['text'].strip()
                        break
        
        # The top 3 font sizes (excluding the title's size) are likely H1, H2, H3
        heading_sizes = [s for s in sorted_sizes if s != title_size][:3]
        size_to_level = {size: f"H{i+1}" for i, size in enumerate(heading_sizes)}

        outline = []
        for page in pdf.pages:
            for line in page.extract_text_lines():
                line_text = line['text'].strip()
                if not line_text or not line['chars']:
                    continue
                
                # Filter out noise
                if len(line_text.split()) > 15 or line_text.endswith('.'):
                    continue

                line_size = line['chars'][0]['size']
                if line_size in size_to_level:
                    outline.append({
                        "level": size_to_level[line_size],
                        "text": line_text,
                        "page": page.page_number
                    })

    return {"title": title, "outline": outline}

def process_pdfs():
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    for pdf_file in pdf_files:
        data = extract_outline(pdf_file)
        
        output_file = output_dir / f"{pdf_file.stem}.json"
        with open(output_file, "w") as f:
            json.dump(data, f, indent=4)
        
        print(f"Processed {pdf_file.name} -> {output_file.name}")

if __name__ == "__main__":
    process_pdfs() 