# syntax=docker/dockerfile:1
FROM python:3.9-slim

# Copy in files
WORKDIR /usr/src
COPY ./requirements.txt ./requirements.txt
COPY ./update_cache.py ./update_cache.py

# Install deps
RUN pip install --no-cache-dir -r requirements.txt --default-timeout=90

RUN pip install -r https://raw.githubusercontent.com/snowflakedb/snowflake-connector-python/v2.9.0/tested_requirements/requirements_310.reqs

CMD python update_cache.py