# Approach Explanation – Round 1B

###  Goal
Given a persona and a job-to-be-done, extract and rank the most relevant sections from a collection of PDFs.

###  Step 1: PDF Parsing and Structure Extraction
We use `pdfplumber` to extract text, organized by headings. Font size heuristics are used to identify headings and classify them into levels (H1, H2, H3). Content is grouped under each heading into structured chunks.

###  Step 2: Embedding Generation
Each text chunk is embedded using `all-MiniLM-L6-v2` from Sentence Transformers — a lightweight, offline-compatible model (<100MB). The combined persona and task form a query embedding.

###  Step 3: Similarity Ranking
Cosine similarity between the query and each document chunk determines relevance. The top N most relevant sections (default 10) are selected and scored.

### � Step 4: Structured Output
Each selected chunk includes:
- Section title
- Page number
- Rank and score
- Subsection summary

The output also contains metadata like document list, persona, job, and timestamp.

###  Constraints Addressed
- Fully offline
- <1GB model
- Executes in <60s on 3–5 PDFs
- CPU-only

This approach ensures semantic relevance while staying lightweight, generalizable, and interpretable.
