# Use the official Python 3.10 image
FROM python:3.10
WORKDIR /blockchain-data-subnet
COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install -y \
    python3-dev \
    cmake \
    make \
    gcc \
    g++ \
    libssl-dev \

RUN pip install pymgclient
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN pip install --no-cache-dir .

RUN chmod +x scripts/*
