import base64
import cv2
import numpy as np

container_labels = ('button', 'input', "window", "taskbar", "list")

def image_to_base64(image_path:str):
    with open(image_path, "rb") as f:
        bytes_content = f.read() # bytes
        bytes_64 = base64.b64encode(bytes_content)
    return bytes_64.decode('utf-8') # bytes--->str  (remove `b`)

def base64_to_image(bytes_64:str, to_file:str):
    bytes_64 = bytes_64.encode('utf-8') # str---> bytes (add `b`)
    bytes_content = base64.decodebytes(bytes_64) # bytes
    with open(to_file, "wb") as f:
        f.write(bytes_content)

def cv2_to_base64(img):
    bytes_content = cv2.imencode('.jpg', img)[1].tostring()
    bytes_64 = base64.b64encode(bytes_content)
    return bytes_64.decode('utf-8') # bytes--->str  (remove `b`)

def base64_to_cv2(bytes_64):
    img_data = base64.b64decode(bytes_64)
    nparr = np.fromstring(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img
