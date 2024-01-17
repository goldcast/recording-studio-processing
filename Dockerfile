# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.8.5-slim-buster
LABEL authors="gaurangrokad"


# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV AWS_DEFAULT_REGION us-east-1

# Install any needed packages specified in requirements.txt
RUN apt-get update && apt-get install -y \
    ffmpeg \
    awscli \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install GCP SDK
RUN apt-get update && apt-get install -y \
    curl \
    lsb-release \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy the local requirements.txt file to the container
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Set ENTRYPOINT for the script execution
ENTRYPOINT ["python", "process_recordings.py"]