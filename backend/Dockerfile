FROM python:3.11-slim

WORKDIR /app

# Install deps first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .

# Ensure Python can import from /app
ENV PYTHONPATH=/app

# Railway provides PORT
CMD ["uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-5000}"]
