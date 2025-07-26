FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
# Using a requirements.txt is a best practice for Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download and cache the sentence transformer model
# This ensures the model is available for offline execution inside the container.
# The model 'all-MiniLM-L6-v2' is small, efficient, and well-suited for CPU execution.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the rest of the application code
COPY solution.py .

# Create input/output directories as expected by the run command
RUN mkdir -p /app/input /app/output

# Set the command to run the solution
CMD ["python", "solution.py"]
