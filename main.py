import sys
import os
import socket
from threading import Thread
from flask_cors import CORS
from apiflask import APIFlask
# sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('yolov7'))
app = APIFlask(__name__, title='UICR', version='2.0')
CORS(app)
# app.config['AUTO_OPERATION_ID'] = True
# app.config['JSON_AS_ASCII'] = False
# app.config["HTTP_ERROR_SCHEMA"] = {}
# app.app_context().push()

from config import configs
# from services.consul_service import reg_daemon
from detect_api import detect_api

app.register_blueprint(detect_api)

@app.get('/')
@app.doc(hide=True)
def welcome():
    # print(request.url)
    return socket.gethostname()


if __name__ == '__main__':
    # Thread(target=reg_daemon).start()
    app.run(host="0.0.0.0", port=configs['PORT'], debug=True)
