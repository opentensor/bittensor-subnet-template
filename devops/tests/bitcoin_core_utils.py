import docker


def remove_container(container_name):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        container.stop()
        container.remove()
        print(f"Container {container_name} removed.")
    except docker.errors.NotFound:
        print(f"Container {container_name} not found. Skipping removal.")


def create_and_start_bitcoin_core_container(container_name):
    client = docker.from_env()
    image_name = "ruimarinho/bitcoin-core:latest"
    container_name = container_name
    command = [
        "-printtoconsole",
        "-regtest=1",
        "-rpcallowip=0.0.0.0/0",
        "-rpcbind=0.0.0.0",  # Bind RPC server to all network interfaces
        "-server=1",
        "-txindex=1",
        "-rpcuser=bitcoinrpc",
        "-rpcpassword=rpcpassword"
    ]
    ports = {"18443/tcp": 18443}  # Expose port 18443 for the host

    # Ensure the image is pulled
    client.images.pull(image_name)

    # Create and start the container
    container = client.containers.create(
        image=image_name,
        command=command,
        ports=ports,
        name=container_name
    )
    container.start()
    print(f"Container {container_name} created and started.")

def execute_bitcoin_cli_command(container_name, command, network="-regtest", rpcuser="bitcoinrpc", rpcpassword="rpcpassword"):
    """Executes a bitcoin-cli command inside a Docker container."""
    client = docker.from_env()
    container = client.containers.get(container_name)
    bitcoin_command = f"bitcoin-cli {network} -rpcuser={rpcuser} -rpcpassword={rpcpassword} {command}"
    return container.exec_run(bitcoin_command)