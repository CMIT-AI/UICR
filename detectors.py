import json
from multiprocessing import shared_memory, Process
import sys
import time
import os
sys.path.append(os.path.abspath('yolov7'))
from services.yolov7_detect import Yolov7

from multiprocessing import Pool, Manager
from ctypes import py_object

weight_dir = os.path.join('yolov7', 'weights')
weight = None
yolov7 = None
yolov7_a = None
yolov7_b = None

def load_weight_a(reload:bool=False):
    global yolov7_a
    if reload or not yolov7_a:
        yolov7_a = Yolov7(os.path.join(weight_dir, "r9.2b-e6e.1.pt"))

def load_weight_b(reload:bool=False):
    global yolov7_b
    if reload or not yolov7_b:
        yolov7_b = Yolov7(os.path.join(weight_dir, "r9.2c-e6d.1.pt"))

def func(model:Yolov7, my_list:list):
    dets = model.value.detect('d:\\04.jpg')
    my_list.extend(dets)



if __name__ == '__main__':
    load_weight_a()
    load_weight_b()

    manager = Manager()
    model_a = manager.Value("O", yolov7_a)
    model_b = manager.Value("O", yolov7_b)
    res_a = manager.list()
    res_b = manager.list()
    my_dict = manager.dict()

    pool = Pool(processes=2)
    pool.apply_async(func, (model_a, res_a))
    pool.apply_async(func, (model_b, res_b))
    pool.close()
    pool.join()
    print(res_a)
    print(res_b)

shm_name = 'shm1'

def fun1(name:str):
    a = shared_memory.ShareableList(["test"], name=name)
    # a[0] = None
    print(a[0])
    load_weight_a()
    load_weight_b()
    det_a = yolov7_a.detect('d:\\2022118_152323_583.jpg')
    det_b = yolov7_b.detect('d:\\2022118_152323_583.jpg')
    while True:
        if a[0] != "test" and not a[0]["return"]:
            print(a[0])
            try:
                if a[0]["method"] == "detect":
                    detect(a[0]["args"])
                    a[0]["return"] = {"code":200,"data":"","error":""}
                elif a[0]["method"] == "get_weight":
                    data = get_weight()
                    a[0]["return"] = {"code":200,"data":data,"error":""}
            except Exception as err:
                a[0]["return"] = {"code":500,"data":"","error":err.__str__()}
            finally:
                print(a[0])

def fun2(name):
    time.sleep(5)
    c=shared_memory.ShareableList(name=name)
    c[0] = json.dumps({"method":"get_weight"})
    print("fun2: %s" % c[0])
    while True:
        if c[0]["return"]:
            print("fun2: %s" % c[0])
            break
    # print('测试%s多进程' %name)

# if __name__ == '__main__':
#     process_list = []
#     # for i in range(5):  #开启5个子进程执行fun1函数
#     p = Process(target=fun1,args=(shm_name,)) #实例化进程对象
#     p.start()
#     process_list.append(p)

#     # p = Process(target=fun2,args=(shm_name,)) #实例化进程对象
#     # p.start()
#     # process_list.append(p)

#     for i in process_list:
#         p.join()

#     print('结束测试')



from pathlib import Path
import shutil
import subprocess
from detect_models import Det, Image, Weight
from api_utils import base64_to_image, cv2_to_base64, container_labels
from services.logger import Logger
from services.yolov7_detect import Yolov7
import ftplib


# subprocess.Popen(os.getenv('python') + ' -m gunicorn --preload -c config/gunicorn.py main:app', shell=True)




def load_weight(reload:bool=False):
    global yolov7
    global weight
    if reload or not yolov7:
        for file in Path(weight_dir).glob('*.pt'):
            weight = file.name
            yolov7 = Yolov7(os.path.join(weight_dir, weight))
            break
            


logger = Logger("uicr")

def update_weight(args):
    global weight
    try:
        file_orig = '/Hawkeye/yolov7/%s' % args['weight']
        file_copy = os.path.join(weight_dir, 'pt_temp')

        with ftplib.FTP() as ftp:
            ftp.connect('devftp01.cmit.local', 8021)
            ftp.login('cmgetest', 'qwer1234!')

            with open(file_copy, 'wb') as fp:
                res = ftp.retrbinary('RETR %s' % file_orig, fp.write)
                if not res.startswith('226 Transfer complete'):
                    raise Exception("Download failed")
        
        shutil.move(file_copy, os.path.join(weight_dir, args['weight']))
        for file in Path(weight_dir).glob('*.pt'):
            if args['weight'] != file.name:
                os.remove(os.path.join(weight_dir, file.name))
        load_weight(True)
    # except ftplib.all_errors as e:
    #     print('FTP error:', e) 
    except Exception as err:
        logger.exception(err)
        raise err
    finally:
        if os.path.isfile(file_copy):
            os.remove(file_copy)


def get_weight():
    return {'weight':weight}


def detect(args):
    try:
        res = []
        load_weight()

        temp_img = str(time.time_ns()) + '.jpg'
        base64_to_image(args['img'], temp_img)
        objs = yolov7.detect(temp_img)
        for i in range(len(objs)):
            each = objs[i]
            obj = Det()
            obj.index = i
            obj.obj_name = each[0]
            obj.confidence = each[1]
            obj.x_left = each[2]
            obj.y_top = each[3]
            obj.x_right = each[4]
            obj.y_bottom = each[5]
            res.append(obj)
        
        return res
    except Exception as err:
        logger.exception(err)
        raise err
    finally:
        if os.path.exists(temp_img):
            os.remove(temp_img)

def detect_tree(args):
    try:
        res = []
        load_weight()

        temp_img = str(time.time_ns()) + '.jpg'
        base64_to_image(args['img'], temp_img)
        objs = yolov7.detect(temp_img)
        for i in range(len(objs)):
            each = objs[i]
            obj = Det()
            obj.index = i
            obj.obj_name = each[0]
            obj.confidence = each[1]
            obj.x_left = each[2]
            obj.y_top = each[3]
            obj.x_right = each[4]
            obj.y_bottom = each[5]
            obj.children = []
            
            add_to_tree(obj, res)

        return res

    except Exception as err:
        logger.exception(err)
        raise err
    finally:
        if os.path.exists(temp_img):
            os.remove(temp_img)

def add_to_tree(obj, tree):
    tree.append(obj)
    for each in tree:
        if obj.x_left > each.x_left and obj.y_top > each.y_top and obj.x_right < each.x_right and obj.y_bottom < each.y_bottom:
            if each.obj_name in container_labels:
                tree.remove(obj)
                add_to_tree(obj, each.children)
                break
        elif obj.x_left < each.x_left and obj.y_top < each.y_top and obj.x_right > each.x_right and obj.y_bottom > each.y_bottom:
            if obj.obj_name in container_labels:
                tree.remove(each)
                obj.children.append(each)
                break


def preview(args):
    try:
        load_weight()

        temp_img = str(time.time_ns()) + '.jpg'
        base64_to_image(args['img'], temp_img)
        res = yolov7.detect(temp_img, save_img=True)
        res = cv2_to_base64(res)
        return {'img': res}
    except Exception as err:
        logger.exception(err)
        raise err
    finally:
        if os.path.exists(temp_img):
            os.remove(temp_img)

