# First stage: Building the application
FROM python:3.9-slim AS builder

WORKDIR /app

# Copy only the files needed for pip install
COPY requirements.txt .
COPY setup.py .
COPY README.md .
COPY insights/ insights/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir .

# Second stage: Setup the runtime environment
FROM python:3.9-slim

WORKDIR /app

# Copy the installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy the application code
COPY . .
