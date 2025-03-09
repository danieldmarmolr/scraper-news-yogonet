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

# Install Google Chrome from the official repository
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get update && apt-get install -y google-chrome-stable

# Install the latest version of ChromeDriver
RUN LATEST_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -q "https://chromedriver.storage.googleapis.com/${LATEST_VERSION}/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip -d /usr/local/bin/ \
    && rm chromedriver_linux64.zip

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
# ENV CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]