# Use an official Python 3.11 runtime as a base image
FROM python:3.12.3-bullseye AS builder

RUN pip install poetry==2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set the working directory in the container to /smib
WORKDIR /app

# Copy the entire smib package into the container at /smib
COPY smib ./smib
COPY pyproject.toml poetry.lock README.md ./

RUN poetry install && rm -rf $POETRY_CACHE_DIR

# The runtime image, used to just run the code provided its virtual environment
FROM python:3.12.3-slim-bullseye AS runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Set timezone - can still be overridden in the docker-compose file
COPY --from=builder /etc/environment /etc/environment
COPY --from=builder /etc/localtime /etc/localtime

WORKDIR /app
COPY smib ./smib

# Remove logging.json from container
RUN rm ./smib/logging.json

# Copy logging.json into correct container location
COPY smib/logging.json /app/config/logging.json

# Copy .env if it exists
COPY .env* /app/config/
