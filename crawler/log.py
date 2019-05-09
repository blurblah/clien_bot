# log.py
import logging.config


LOG_CONFIG = {
    'version': 1,
    'filters': {
        'request_id': {
            '()': 'crawler.request_id.RequestIdFilter'
        }
    },
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s.%(module)s.%(funcName)s:%(lineno)d - %(levelname)s - %(request_id)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['request_id'],
            'formatter': 'standard'
        }
    },
    'loggers': {
        'werkzeug': {
            'handlers': ['console'],
            'level': 'INFO'
        },
        'main': {
            'handlers': ['console'],
            'level': 'INFO'
        },
        'controller': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
        'crawler': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
        'job': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
    }
}


def configure_logger():
    logging.config.dictConfig(LOG_CONFIG)
