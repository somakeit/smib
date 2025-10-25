## ------------------------------- Builder Stage ------------------------------ ##
FROM python:3.14-bookworm AS builder

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Download the latest installer, install it and then remove it
ADD https://astral.sh/uv/install.sh /install.sh
ENV UV_VERSION=0.9.5
RUN chmod -R 755 /install.sh && /install.sh && rm /install.sh

# Set up the UV environment path correctly
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy bare minimum for requirements install
COPY pyproject.toml README.md ./

# Override to dummy version when installing dependencies only
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0
RUN uv sync --no-install-project --no-install-workspace

# Copy entire context - so we can calculate the git revision
COPY . .

# Unset version so the actual version number can be used 
ENV SETUPTOOLS_SCM_PRETEND_VERSION=
RUN uv pip install -e .

## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.14-slim-bookworm AS runtime

RUN useradd smibuser
USER smibuser

WORKDIR /app

# Copy the entire source directory and virtual environment
COPY --from=builder /app/src ./src
COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/pyproject.toml ./pyproject.toml

# Set up environment variables for production
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

COPY docker/healthcheck.py ./healthcheck.py

HEALTHCHECK --interval=10s --timeout=10s --start-period=8s --retries=3 \
 CMD ["python", "/app/healthcheck.py"]

CMD ["python", "-m", "smib"]
