# Use an official Python 3.11 runtime as a base image
FROM python:3.13-bookworm AS builder

RUN pip install poetry==2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set the working directory in the container to /smib
WORKDIR /app

COPY src/ ./src
COPY pyproject.toml poetry.lock poetry.toml ./

RUN poetry install && rm -rf $POETRY_CACHE_DIR

# The runtime image, used to just run the code provided its virtual environment
FROM python:3.13-slim-bookworm AS runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Set timezone - can still be overridden in the docker-compose file
COPY --from=builder /etc/environment /etc/environment
COPY --from=builder /etc/localtime /etc/localtime

WORKDIR /app
COPY src/ ./src

CMD ["python", "-m", "smib"]
