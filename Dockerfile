## ------------------------------- Builder Stage ------------------------------ ##
FROM python:3.13-bookworm AS builder

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Download the latest installer, install it and then remove it
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 655 /install.sh && /install.sh && rm /install.sh

# Set up the UV environment path correctly
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY uv.lock uv.lock
COPY .git .git

# Create venv and install dependencies
RUN uv sync

COPY src/ src
RUN uv pip install -e .

RUN rm -r .git


## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.13-slim-bookworm AS runtime

RUN useradd smibuser
USER smibuser

WORKDIR /app

# Copy the entire source directory and virtual environment
COPY --from=builder /app/src ./src
COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/pyproject.toml ./pyproject.toml

# Set up environment variables for production
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

HEALTHCHECK \
  CMD python -c "import os, urllib.request; exit(0) if urllib.request.urlopen(f'http://localhost:{os.environ.get(\"SMIB_WEBSERVER_PORT\", \"80\")}/openapi.json').status == 200 else exit(1)"

CMD ["python", "-m", "smib"]
