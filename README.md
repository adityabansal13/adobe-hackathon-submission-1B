# Round 1A: Document Outline Extractor

This is a solution for Round 1A of the "Connecting the Dots" Hackathon. It's a Python script that extracts a structured outline (title, H1, H2, H3) from a PDF file and outputs it as a JSON file.

## Approach

The core of the solution is a rule-based algorithm that analyzes the font properties of the text in the PDF to identify headings. Here's a high-level overview of the approach:

1.  **Font Analysis:** The script first analyzes the font sizes used throughout the document to get a sense of the document's typography.
2.  **Title Extraction:** The title is identified by finding the line of text with the largest font size on the first page of the document.
3.  **Heading Detection:** Headings are identified by finding lines of text with a font size that is larger than the most common font size in the document. The heading levels (H1, H2, H3) are determined by ranking the font sizes of the headings.
4.  **Noise Filtering:** The script includes a number of rules to filter out "noise" (i.e., text that looks like a heading but isn't), such as lines that are too long or that end with a period.
5.  **JSON Output:** The extracted title and outline are then formatted into a JSON file, as per the requirements of the challenge.

## Libraries Used

*   **pdfplumber:** This library was chosen for its ability to extract detailed information about the text and layout of a PDF, including character-level font information. This was essential for the font analysis part of the algorithm.
*   **pathlib:** This standard library was used for path manipulation.

## How to Build and Run

The solution is packaged as a Docker container. To build and run it, follow these steps:

1.  **Build the Docker image:**

    ```bash
    docker build -t outline-extractor .
    ```

2.  **Run the Docker container:**

    ```bash
    docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output outline-extractor
    ```

    This will process all the PDF files in the `input` directory and save the corresponding JSON files to the `output` directory. 