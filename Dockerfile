# Unstable DistilBERT sentiment API -> pushed as sentiment-api:unstable
FROM python:3.10-slim

WORKDIR /app

# Install CPU-only PyTorch first. The default torch==2.3.0 wheel bundles ~5GB of
# CUDA libraries that are useless on this CPU-only VM and would blow the image up
# to ~9GB. Installing the CPU build first satisfies the torch==2.3.0 pin in
# requirements.txt without modifying that provided file, keeping the image ~1.5GB.
RUN pip install --no-cache-dir torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-bake the HuggingFace model into the image so the container starts fast
# and does not need to download the model at pod startup (avoids CrashLoop).
RUN python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')"

COPY . .
RUN mkdir -p /app/logs

EXPOSE 5000
CMD ["python", "app.py"]
