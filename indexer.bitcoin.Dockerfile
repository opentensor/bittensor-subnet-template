# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable defaults
ENV NODE_RPC_URL=""
ENV GRAPH_DB_URL=""
ENV GRAPH_DB_USER=""
ENV GRAPH_DB_PASSWORD=""

# Run miner.py when the container launches
CMD ["python", "./neurons/miners/bitcoin/miner.py"]
