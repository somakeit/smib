# Use an official Python 3.11 runtime as a base image
FROM python:3.11-buster as builder

RUN pip install poetry==1.4.2

# Install tzdata, curl, and jq.
# RUN apt-get update && apt-get install -y tzdata curl jq

# Fetch the timezone using the API, set the TZ environment variable to the fetched timezone.
#RUN TIMEZONE=$(curl -s http://worldtimeapi.org/api/ip | jq -r .timezone) && \
 #   ln -fs /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
  #  dpkg-reconfigure -f noninteractive tzdata && \
   # echo "TZ=$TIMEZONE" >> /etc/environment

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set the working directory in the container to /smib
WORKDIR /app

# Copy the entire smib package into the container at /smib
COPY smib ./smib
COPY pyproject.toml poetry.lock README.md ./

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# The runtime image, used to just run the code provided its virtual environment
FROM python:3.11-slim-buster as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Set timezone - can still be overridden in the docker-compose file
COPY --from=builder /etc/environment /etc/environment
COPY --from=builder /etc/localtime /etc/localtime

WORKDIR /app
COPY smib ./smib

RUN rm ./smib/logging.json
COPY smib/logging.json /app/config/logging.json
