# Round 1B: Persona-Driven Document Intelligence

## 📝 Overview
This solution is designed for the Round 1B challenge of the Document Intelligence Hackathon. It extracts and ranks the most relevant sections from a set of input PDFs, based on a specific persona and job-to-be-done.

## 📦 Contents
```
.
├── Dockerfile
├── solution.py
├── requirements.txt
├── approach_explanation.md
└── models
    └── paraphrase-MiniLM-L6-v2
        ├── config.json
        ├── pytorch_model.bin
        ├── sentence_bert_config.json
        ├── special_tokens_map.json
        ├── tokenizer_config.json
        └── vocab.txt
```

## ⚙️ Requirements
- Docker
- PDFs to analyze (provide at runtime)

## 🐳 Build Docker Image
```bash
docker build -t round1b-solution .
```

## 🚀 Run Inference
1. Place your input PDFs in the current directory
2. Update `solution.py` (or mount JSON inputs)
3. Run:
```bash
docker run --rm -v $PWD:/app round1b-solution
```

## 📤 Output
- A file named `output.json` is generated
- It contains:
  - Metadata
  - Ranked extracted sections
  - Subsection analysis

## ✅ Compliance
- ✅ CPU-only inference
- ✅ Model size < 1GB
- ✅ No internet access
- ✅ ≤ 60s runtime for 3–5 PDFs

## 🧠 Model Info
Uses `paraphrase-MiniLM-L6-v2` from Sentence Transformers, saved locally in `models/`.

## 🧪 Sample Test
To test, drop a few PDFs in the directory and run the container. Sample persona/job-to-be-done can be updated in `solution.py`.

## 📩 Contact
For any issues, reach out to the team via the hackathon portal.
