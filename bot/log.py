# log.py
import logging.config


LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s.%(module)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        'main': {
            'handlers': ['console'],
            'level': 'INFO'
        },
        'bot': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
    }
}


def configure_logger():
    logging.config.dictConfig(LOG_CONFIG)
