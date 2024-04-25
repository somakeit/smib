# Use an official Python 3.11 runtime as a base image
FROM python:3.11-slim
smib.Dockerfile
RUN pip install poetry==1.4.2

# Set the working directory in the container to /smib
WORKDIR /smib

# Copy the entire smib package into the container at /smib
COPY smib ./smib
COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN ls -al

# Use pyproject.toml to install package dependencies
RUN poetry install --without dev