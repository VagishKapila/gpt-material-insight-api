# Use an official Python image
FROM python:3.10-slim

# Install system packages including ffmpeg and git
RUN apt-get update && \
    apt-get install -y ffmpeg git gcc libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask runs on
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Start Flask server
CMD ["flask", "run"]
