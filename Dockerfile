# Use an official Python 3.13 runtime as a base image
FROM python:3.13-bookworm AS builder

# Install Poetry directly via pip
RUN pip install --no-cache-dir poetry==2

# Configure Poetry for installation and caching
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Define the working directory
WORKDIR /app

# Copy Poetry configuration files (dependency caching optimization)
COPY pyproject.toml poetry.lock poetry.toml ./

# Install all dependencies without the source code first (caches dependencies)
RUN poetry install --no-root --no-directory && rm -rf $POETRY_CACHE_DIR

# Copy the source code into the container
COPY src/ ./src

# Re-run poetry install to install the `smib` module itself in editable mode
RUN poetry install --only-root

# Second stage: runtime environment
FROM python:3.13-slim-bookworm AS runtime

# Define virtual environment path and update PATH
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Copy virtual environment and dependencies from the builder image
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Set working directory and copy the application code
WORKDIR /app
COPY src/ ./src

# Default command to run the application
CMD ["python", "-m", "smib"]