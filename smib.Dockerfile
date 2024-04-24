# Use an official Python 3.11 runtime as a base image
FROM python:3.11-slim

# Set the working directory in the container to /smib
WORKDIR /smib

# Copy the entire smib package into the container at /smib
COPY . .

RUN rm -rf /smib/tests

# Use pyproject.toml to install package dependencies
RUN pip install -e .