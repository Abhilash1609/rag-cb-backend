# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Set environment variable so GCP SDK picks the right credentials
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/secrets/serviceaccount.json"

# Expose FastAPI port
EXPOSE 8080

# Start the FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
