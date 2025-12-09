FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
# Create a temporary requirements file for ML service specific deps if needed
# For now, we use the main one but ideally should be separate
RUN pip install --no-cache-dir fastapi uvicorn pydantic scikit-learn numpy pandas

# Copy application code
COPY . .

# Create directory for models
RUN mkdir -p /app/models

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
