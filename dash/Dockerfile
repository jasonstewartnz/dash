# syntax=docker/dockerfile:1
FROM python:3.9-slim

# Copy in files
WORKDIR /usr/src
COPY ./requirements.txt ./requirements.txt
COPY app ./app

# Install deps
RUN pip install --no-cache-dir -r requirements.txt --default-timeout=90

# CMD gunicorn -b 0.0.0.0:80 app.app:server
CMD python app/app.py
# docker run --rm -it --entrypoint bash
EXPOSE 8050