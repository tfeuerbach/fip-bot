# Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    build-essential \
    gcc \
    git \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code
COPY . .

# Run the bot
CMD ["python", "bot.py"]
