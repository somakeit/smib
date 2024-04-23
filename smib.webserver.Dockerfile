# Use an official Python 3.11 runtime as a base image
FROM python:3.11-slim

# Set the working directory in the container to /smib
WORKDIR /smib

# Copy the entire smib package into the container at /smib
COPY . .

RUN rm -rf /smib/smib/slack
RUN rm -rf /smib/tests

# Install Poetry
RUN pip install poetry

# Use Poetry to install package dependencies
RUN pip install -e .

# Run smib.webserver when the container launches
CMD ["python", "-m", "smib.webserver"]