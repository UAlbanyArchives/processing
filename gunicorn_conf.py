bind = '0.0.0.0:5000'
loglevel = 'debug'
accesslog = '/var/log/gunicorn_access.log'
acceslogformat ="%(h)s %(l)s %(u)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s"
errorlog =  '/var/log/gunicorn_error.log'