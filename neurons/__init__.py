import json
import sys
from loguru import logger
import bittensor as bt
import logging

mandatory_config = {}

def serialize(record):
    try:
        tmstamp = format(record['time'], "%Y-%m-%d %H:%M:%S.%03d")
        subset = {
            'timestamp': tmstamp,
            'level': record['level'].name,
            'message': record['message'],
        }
        subset.update(mandatory_config)
        subset.update(record['extra'])
        return json.dumps(subset)
    except Exception:
        return record['message']


def patching(record):
    record['message'] = serialize(record)


def custom_log_formatter(record):
    """Custom log formatter"""
    return "<level>{message}</level>\n"

logger = logger.patch(patching)
logger.remove(0)
logger.add(sys.stdout, format=custom_log_formatter)

bt.logging._logger.setLevel(logging.CRITICAL)  # disable btlogging