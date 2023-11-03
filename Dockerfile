FROM python:3.9-slim AS builder

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .