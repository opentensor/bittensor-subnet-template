
import os


def get_docker_image_version():
    return os.getenv('DIGEST_CHARS', 'n/a')

