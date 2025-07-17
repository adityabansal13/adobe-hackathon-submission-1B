FROM --platform=linux/amd64 python:3.10

WORKDIR /app

# Copy our solution script
COPY solution.py .

# Install our dependencies
RUN pip install pdfplumber

# Set the command to run our script
CMD ["python", "solution.py"] 