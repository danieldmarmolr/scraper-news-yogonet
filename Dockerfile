# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install wget, curl, gnupg, Chrome, and other dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    && apt-get clean

# Download and install Google Chrome from the provided URL
RUN wget -q "https://storage.googleapis.com/chrome-for-testing-public/134.0.6998.35/linux64/chrome-linux64.zip" \
    && unzip chrome-linux64.zip -d /usr/local/bin/ \
    && rm chrome-linux64.zip

# Install ChromeDriver
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/134.0.6998.35/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver-linux64.zip

# Verify the architecture of ChromeDriver
RUN file /usr/local/bin/chromedriver

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set environment variables for BigQuery authentication and ChromeDriver
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
ENV CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]