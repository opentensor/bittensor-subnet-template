# Containerization Best Practices

Containerization is a powerful technique that offers several advantages for developing and deploying Bittensor subnets. This document outlines the key benefits and provides an example of a secure Python container setup.

## Advantages of Containerization

1. **Dependency Isolation**: Containers encapsulate all necessary dependencies, ensuring consistency across different environments and eliminating "it works on my machine" issues.

2. **Security**: Containers provide an additional layer of isolation, reducing the attack surface and allowing for better control over resource access.

3. **Ease of Deployment**: Containerized applications can be easily deployed across various environments, from development to production, with minimal configuration changes.

4. **Dependency Injection**: Containers allow for easy dependency injection through environment variables and volumes. This enables:
   - Mounting of wallets
   - Injection of API keys (e.g., OpenAI, Weights & Biases)
   - Configuration of runtime parameters without modifying the container image

5. **Orchestration**: Containerization lends itself well to orchestration tools and environments, such as:
   - Docker Compose: For managing multi-container applications on a single host
   - Kubernetes: For orchestrating containerized applications across multiple hosts in a cluster

These orchestration tools provide powerful capabilities for scaling, load balancing, and managing complex deployments of containerized applications.

## Example: Subnet Minder Python Container with Reduced Privileges

Here's an example Dockerfile that demonstrates how to create a Python container with reduced privileges for improved security:

```dockerfile
# Build stage
FROM python:3.9-slim-buster AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.9-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user
RUN useradd --create-home subuser

# Set working directory
WORKDIR /home/subuser/app

# Copy installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy project files
COPY . .

# Change ownership of the working directory
RUN chown -R subuser:subuser /home/subuser/app

# Switch to non-root user
USER subuser

# Run the miner nueron
CMD ["python", "neurons/miner.py"]
```

## Build Instructions

To build the Docker image, follow these steps:

1. Navigate to the directory containing the Dockerfile and your project files.
2. Run the following command:

```bash
docker build -t my-subnet-image .
```

3. Once the build is complete, you can run the container using:

```bash
docker run -it --rm my-subnet-image
```

## Mounting Wallets and Injecting API Keys

When running your containerized subnet, you can mount wallets and inject API keys using Docker's volume mounting and environment variable features. Here are some examples:

### Mounting a Wallet

To mount a wallet directory from your host machine into the container:

```bash
docker run -it --rm \
  -v /path/to/host/wallet:/home/subuser/app/wallet \
  my-subnet-image
```

This command mounts the `/path/to/host/wallet` directory from your host machine to `/home/subuser/app/wallet` inside the container.

### Injecting API Keys

To inject API keys or other sensitive information as environment variables:

```bash
docker run -it --rm \
  -e OPENAI_API_KEY=your_openai_api_key_here \
  -e WANDB_API_KEY=your_wandb_api_key_here \
  my-subnet-image
```

This command sets the `OPENAI_API_KEY` and `WANDB_API_KEY` environment variables inside the container.

### Combining Mounting and Environment Variables

You can combine both approaches:

```bash
docker run -it --rm \
  -v /path/to/host/wallet:/home/subuser/app/wallet \
  -e OPENAI_API_KEY=your_openai_api_key_here \
  -e WANDB_API_KEY=your_wandb_api_key_here \
  my-subnet-image
```

This setup mounts the wallet directory and injects API keys, providing a secure way to use sensitive information without hardcoding it into your image or source code.

Remember to update your application code to read these mounted volumes and environment variables appropriately.