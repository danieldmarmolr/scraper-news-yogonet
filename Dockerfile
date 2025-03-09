# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install wget, curl, Chrome, and other dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    && apt-get clean

# Install Google Chrome version 114
RUN wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb
RUN dpkg -i google-chrome-stable_114.0.5735.90-1_amd64.deb; apt-get -fy install

# Install ChromeDriver version 114
RUN wget -q "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip -d /usr/local/bin/ \
    && rm chromedriver_linux64.zip

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set environment variables for BigQuery authentication
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]