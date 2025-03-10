# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install wget, unzip, libnss3, libxi6 and libgbm1
    RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    libnss3 \
    libgconf-2-4 \
    libxi6 \
    libgbm1 \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    file \
    && apt-get clean

# Install manually all the missing libraries
RUN apt-get update
RUN apt-get install -y gconf-service libasound2 libatk1.0-0 libcairo2 libcups2 libfontconfig1 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libxss1 fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils

# Install Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install

# Install ChromeDriver
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/134.0.6998.35/linux64/chromedriver-linux64.zip \
   && unzip chromedriver-linux64.zip \
   && mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
   && chmod +x /usr/local/bin/chromedriver \
   && rm chromedriver-linux64.zip

# Verify the architecture of ChromeDriver
RUN file /usr/local/bin/chromedriver

# Install chromedriver-binary and chromedriver-binary-auto
RUN pip install chromedriver-binary
RUN pip install chromedriver-binary-auto
RUN pip install --upgrade --force-reinstall chromedriver-binary-auto

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set environment variables for BigQuery authentication and ChromeDriver
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]