import json

import bittensor as bt

mandatory_config = {}

def serialize(record):
    tmstamp = format(record['time'], "%Y-%m-%d %H:%M:%S.%03d")
    subset = {
        'timestamp': tmstamp,
        'level': record['level'].name,
        'message': record['message'],
    }
    subset.update(mandatory_config)
    subset.update(record['extra'])
    return json.dumps(subset)


def patching(record):
    record['message'] = serialize(record)


def custom_log_formatter(record):
    """Custom log formatter"""
    return "{message}\n"


bt.btlogging.logging.log_formatter = custom_log_formatter
bt.btlogging.logger = bt.btlogging.logger.patch(patching)
bt.btlogging.logging.debug = bt.btlogging.logger.debug
bt.btlogging.logging.info = bt.btlogging.logger.info
bt.btlogging.logging.warning = bt.btlogging.logger.warning
bt.btlogging.logging.error = bt.btlogging.logger.error
bt.btlogging.logging.success = bt.btlogging.logger.success
bt.btlogging.logging.trace = bt.btlogging.logger.trace





