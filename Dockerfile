FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ app/
COPY run.py .
COPY uploads/ uploads/

# Create directories
RUN mkdir -p uploads/icons data && chown -R appuser:appuser /app

# Create non-root user (before chown, recreate)
RUN useradd -m -u 1000 appuser 2>/dev/null || true

EXPOSE 8000

CMD ["python", "run.py"]
