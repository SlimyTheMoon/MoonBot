FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (gcc might be needed for some python libs)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./ ./

# Run the bot
CMD ["python", "main.py"]