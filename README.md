# Adobe Hackathon 2025 Submission – Unified Round 1A & 1B

This solution handles both Round 1A and Round 1B of Adobe's "Connecting the Dots" Hackathon challenge using a single script controlled by an environment variable.

##  Rounds Overview

- **Round 1A**: Extracts the title and hierarchical outline (H1, H2, H3) from PDFs.
- **Round 1B**: Extracts and ranks the most relevant document sections for a persona-driven task.

##  Build the Docker Image

```bash
docker build --platform linux/amd64 -t adobe-pdf-solution .
```

##  Run the Container

### Round 1A
```bash
docker run --rm   -e MODE=round1a   -v $(pwd)/input:/app/input   -v $(pwd)/output:/app/output   --network none   adobe-pdf-solution
```

### Round 1B
```bash
docker run --rm   -e MODE=round1b   -e PERSONA="PhD Researcher in Computational Biology"   -e JOB_TO_BE_DONE="Prepare a literature review on GNNs for drug discovery"   -v $(pwd)/input:/app/input   -v $(pwd)/output:/app/output   --network none   adobe-pdf-solution
```

##  File Structure

- `solution.py`: Unified script for both rounds
- `Dockerfile`: Container setup for offline execution
- `README.md`: Setup and usage documentation
- `approach_explanation.md`: Methodology explanation for Round 1B

## ⚠️ Note
Ensure `input/` contains valid `.pdf` files before running.
