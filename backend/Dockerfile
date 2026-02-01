FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directories
RUN mkdir -p uploads/frames uploads/walls uploads/models

# Expose port
EXPOSE 5000

# Run the application
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "run:app"]
