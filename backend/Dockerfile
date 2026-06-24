FROM python:3.12-slim

WORKDIR /app

# Install system dependencies + GoAccess
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        goaccess \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set python path so backend modules can be resolved from /app/backend
ENV PYTHONPATH=/app

# Verify GoAccess exists during image build
RUN goaccess --version

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
