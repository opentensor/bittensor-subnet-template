import socket
import docker
import bittensor as bt

def get_docker_image_version():
    try:
        container_id = socket.gethostname()
        client = docker.from_env()
        container = client.containers.get(container_id)
        image_details = container.image.tags
        image_details = [x for x in image_details if x != 'latest']
        if len(image_details) > 0:
            return image_details[0]
        else:
            bt.logging.error(f"Could not find docker container with id: {container_id}")
            return 'not found'
    except docker.errors.NotFound as e:
        bt.logging.error(f"Could not find docker container with id: {container_id}")
        return 'n/a'