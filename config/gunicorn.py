#from gevent import monkey  # 导入补丁模块
#monkey.patch_all()  # 创建补丁
import os
import multiprocessing
from config import configs

bind = '%s:%s' % ("0.0.0.0", configs['PORT'])
# backlog = 512
# timeout = 30
worker_class = 'sync' #'gevent'
workers = 1 #multiprocessing.cpu_count() * 2 + 1
# chdir = os.path.abspath("./") + '/' + 'app'
# reload = True
accesslog = os.path.join(configs["LOG_DIR"], "gunicorn_access.log")
errorlog = os.path.join(configs["LOG_DIR"], "gunicorn_error.log")
