#-*- coding:utf-8 -*-
import logging.config

IMAGE_SIZES = {
    "large": (360,150),
    "middle": (328, 185),
    "small": (113, 80)
}

IMAGE_SAVE_DIR = "/Users/jiangqiurong/Desktop"

mongodb_conn_string = "mongodb://47.88.194.127:27017/"

mysql_config = {
    "user": "zhaozhi",
    "password": "zzhao",
    "host": "47.88.194.127",
    "database": "news_test",
    "charset": "utf8"
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s [%(filename)s %(funcName)s] %(message)s'
        },
    },
    'filters': {
    },
    'handlers': {
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file':{
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename':'/tmp/sync_news.log',
            'when': 'D',
            'backupCount':7,
            'formatter': 'simple'
        }
    },
    'loggers': {
        'sync_news': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'sync_news_test': {
            'handlers': ['console', 'file'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("sync_news_test")
