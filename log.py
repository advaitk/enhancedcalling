# from http.client import HTTPConnection
# HTTPConnection.debuglevel = 1
class log_config():
    common_log_config = {
            'version': 1,
            'formatters': {
                'verbose': {
                    'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose',
                },
            },
            'loggers': {
                'zeep.transports': {
                    'level': 'ERROR',
                    'propagate': True,
                    'handlers': ['console'],
                },
                'urllib3':{
                    'level' : 'ERROR',
                    'propagate': True,
                    'handlers': ['console'],
                },               
                'axl' : {
                    'level' : 'ERROR',
                    'propagate': True,
                    'handlers': ['console'],
                },
                'csdm' : {
                    'level' : 'ERROR',
                    'propagate': True,
                    'handlers': ['console'],
                },
                '__main__' : {
                    'level' : 'ERROR',
                    'propagate': True,
                    'handlers': ['console'],
                }
            }
        }