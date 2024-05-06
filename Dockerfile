# Use the official Python 3.10 image
FROM python:3.10

# Set the working directory
WORKDIR /blockchain-data-subnet

# Copy the requirements file into the working directory
COPY requirements.txt requirements.txt

# Update the package list and install necessary packages
RUN apt-get update && apt-get install -y \
    python3-dev \
    cmake \
    make \
    gcc \
    g++ \
    libssl-dev

# Install pymgclient directly via pip
RUN pip install pymgclient

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all remaining project files to the working directory
COPY . .

# Install the project package itself
RUN pip install --no-cache-dir .

# Make the scripts executable
RUN chmod +x scripts/*

# Set the entry point or command if required
# ENTRYPOINT ["your_entry_point"]
# CMD ["your_command"]
