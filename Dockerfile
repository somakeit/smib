## ------------------------------- Builder Stage ------------------------------ ##
FROM ghcr.io/astral-sh/uv:0.11.27-python3.14-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/python \
    UV_PYTHON_PREFERENCE=only-managed \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# git is required to install the project in editable mode from a bind-mounted .git
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN uv python install

# Set up the UV environment path correctly
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy bare minimum for requirements install
COPY pyproject.toml README.md uv.lock ./

# Override to dummy version when installing dependencies only
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Copy entire context - so we can calculate the git revision
COPY src /app/src

# Unset version so the actual version number can be used 
ENV SETUPTOOLS_SCM_PRETEND_VERSION=
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=.git,target=/app/.git,readonly \
    uv pip install --no-deps --editable .

RUN rm -rf /root/.cache

## ------------------------------- Production Stage ------------------------------ ##
FROM gcr.io/distroless/cc-debian13 AS runtime

WORKDIR /app

# Copy the entire source directory and virtual environment
COPY --from=builder --chown=nonroot:nonroot /python /python
COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv
COPY --from=builder --chown=nonroot:nonroot /app/src /app/src
COPY --from=builder --chown=nonroot:nonroot /app/pyproject.toml /app/pyproject.toml

USER nonroot:nonroot

# Set up environment variables for production
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --chown=nonroot:nonroot docker/healthcheck.py ./healthcheck.py

HEALTHCHECK --interval=10s --timeout=10s --start-period=8s --retries=3 \
 CMD ["python", "/app/healthcheck.py"]

CMD ["python", "-m", "smib"]
