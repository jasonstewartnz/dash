# syntax=docker/dockerfile:1
FROM python:3.9-slim

# Copy in files
WORKDIR /usr/src
COPY ./requirements.txt ./requirements.txt
COPY app ./app

# Install deps
RUN pip install --no-cache-dir -r requirements.txt --default-timeout=900

# install dependencies for Snowflake - redundancy?
# RUN apt-get install -y libssl-dev libffi-dev
# RUN pip install --upgrade pip
RUN pip install -r https://raw.githubusercontent.com/snowflakedb/snowflake-connector-python/v2.9.0/tested_requirements/requirements_310.reqs
# RUN pip install snowflake-connector-python==2.9 

# RUN pip install pandas
# pip install jupyter-dash

# FROM python:3.9-slim
# COPY requirements.txt ./requirements.txt
# RUN pip install -r requirements.txt
# COPY . ./
# CMD gunicorn -b 0.0.0.0:80 app.app:server
CMD python app/app.py
# docker run --rm -it --entrypoint bash
EXPOSE 8050