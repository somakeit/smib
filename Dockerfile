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
COPY uv.lock uv.lock

# Create venv and install dependencies
RUN uv sync

COPY src/ src
RUN uv pip install -e .


## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.13-slim-bookworm AS runtime

RUN useradd --create-home --home-dir /home/smibuser smibuser
USER smibuser

WORKDIR /app

# Copy the entire source directory and virtual environment
COPY --from=builder /app/src ./src
COPY --from=builder /app/.venv ./.venv

# Set up environment variables for production
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

CMD ["python", "-m", "smib"]