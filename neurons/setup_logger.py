import logging
import json
import time

class CustomFormatter(logging.Formatter):
    def format(self, record):
        ct = self.converter(record.created)
        s = time.strftime(self.default_time_format, ct)
        if self.default_msec_format:
            s = self.default_msec_format % (s, record.msecs)
        config = {
            'timestamp' : s,
            'level' : record.levelname,
            'message' : record.msg
        }
        if(record.__dict__.get('extra_content')): config.update(record.__dict__["extra_content"])
        return json.dumps(config)

def setup_logger(name):
    formatter = CustomFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger
def logger_extra_data(**kwargs):
    extra = {}
    for key in kwargs:
        extra[key] = kwargs[key]
    return {"extra_content" : extra}