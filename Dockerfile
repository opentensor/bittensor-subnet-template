FROM python:3.9-slim

WORKDIR /blockchain-data-subnet
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN pip install --no-cache-dir .
RUN chmod +rwx scripts/*

RUN python -m unittest discover -s neurons -p '*test*.py'