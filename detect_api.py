from datetime import datetime
from multiprocessing.connection import Listener, Client
import os
from pathlib import Path
import random
import shutil
import time
from apiflask import APIBlueprint, HTTPError, abort
import cv2
from detect_models import Det, Image, AddWeight, ImageEx, UpdateWeight, Weight
from api_utils import base64_to_image, cv2_to_base64, base64_to_cv2, container_labels
from config import configs, reload_config
from services.logger import Logger
from services.yolov7_detect import Yolov7
import ftplib
import torch
from yolov7.utils.plots import plot_one_box


detect_api = APIBlueprint('detect_api', __name__, url_prefix='/api')

E500_0 = '未知错误，请联系管理员'

logger = Logger("uicr")

weight_dir = os.path.join(configs["DATA_DIR"], 'weights')
os.makedirs(weight_dir, exist_ok=True)
weight_defs = []
weights = []
procs = []
for each in weight_defs:
    weights.append(None)
    procs.append(None)

# @torch.no_grad()
# def load_weight(index = -1, reload:bool=False):
#     global weights
#     global yolov7s
    
#     for i in range(len(weights)):
#         if index == -1 or i == index:
#             if (reload or not yolov7s[i]) and weights[i]["file"]:
#                 file = os.path.join(weight_dir, weights[i]["file"])
#                 if os.path.isfile(file):
#                     if "device" in weights[i]:
#                         yolov7s[i] = Yolov7(file, img_size=weights[i]["img_size"], device=weights[i]["device"])
#                     else:
#                         yolov7s[i] = Yolov7(file, img_size=weights[i]["img_size"])
                    
#                     weights[i]["device"] = yolov7s[i].device
#                     weights[i]["names"] = yolov7s[i].names
    
#     torch.cuda.empty_cache()

def load_weight_async(index:int=-1, reload:bool=False):
    global weight_defs
    global procs
    
    for i in range(len(weight_defs)):
        if index == -1 or i == index:
            if (reload or not procs[i]) and weight_defs[i]["file"]:
                file = os.path.join(weight_dir, weight_defs[i]["file"])
                if os.path.isfile(file):
                    # close existing process
                    if procs[i]:
                        procs[i].send(["exit"])

                    weight = _load_weight(weight_defs[i])
                    
                    port = int("50000")
                    address = ('localhost', port)     # family is deduced to be 'AF_INET'

                    ctx = torch.multiprocessing.get_context("spawn")
                    p = ctx.Process(target=detector, args=(weight, address))
                    p.start()
                    # update weight_def from subprocess
                    listener = Listener(address)
                    conn = listener.accept()
                    print('connection accepted from', listener.last_accepted)
                    # weight_defs[i] = conn.recv()
                    procs[i] = conn

def detector(weight, address):
    with torch.no_grad():
        yolov7 = weight
        with Client(address) as conn:
            # conn.send(weight)
            while True:
                try:
                    command = conn.recv()
                    if command[0] == "reload":
                        pass
                    elif command[0] == "det":
                        args = command[1]
                        dets = yolov7.detect(args["img"], classes=args["classes"])
                        conn.send(dets)
                        torch.cuda.empty_cache()
                    elif command[0] == "exit":
                        return
                except Exception as err:
                    logger.exception(err)
                    conn.send("error:%s"%err.__str__())

def _load_weight(weight_def:dict):
    yolov7 = None
    file = os.path.join(weight_dir, weight_def["file"])
    if "device" in weight_def:
        yolov7 = Yolov7(file, img_size=weight_def["img_size"], device=weight_def["device"])
    else:
        yolov7 = Yolov7(file, img_size=weight_def["img_size"])
    
    weight_def["device"] = yolov7.device
    weight_def["names"] = yolov7.names

    torch.cuda.empty_cache()

    return yolov7

@detect_api.put('/yolov7/configs')
# @detect_api.auth_required(authen)
@detect_api.doc(responses=[200, 500])
def reload_config():
    try:
        configs.update(reload_config())
        return "", 200
    except Exception as err:
        logger.exception(err)
        abort(500, E500_0)
    finally:
        pass

@detect_api.post('/yolov7/weights/<int:index>')
# @detect_api.auth_required(authen)
@detect_api.input(AddWeight)
@detect_api.output(Weight(many=True))
@detect_api.doc(responses=[200, 500])
def add_weight(index:int, args):
    for each in weight_defs:
        if each["file"] == args["file"]:
            abort(500, "duplicate weight")
    
    try:
        new_weight = {}
        new_weight["file"] = args["file"]
        new_weight["img_size"] = args["img_size"]
        new_weight["device"] = args["device"]
        if index in range(len(weight_defs)):
            weight_defs.insert(index, new_weight)
            procs.insert(index, None)
        else:
            weight_defs.append(new_weight)
            procs.append(None)

        index = weight_defs.index(new_weight)
        load_weight_async(index, True)
        
        return weight_defs
    except Exception as err:
        logger.exception(err)
        abort(500, E500_0)
    finally:
        pass

@detect_api.delete('/yolov7/weights/<int:index>')
# @detect_api.auth_required(authen)
@detect_api.doc(responses=[200, 500])
def delete_weight(index:int):
    try:
        if index not in range(len(weight_defs)):
            abort(500, "index is out of range")
        
        weight_defs.pop(index)
        yolov7 = procs.pop(index)
        if yolov7:
            yolov7.send(["exit"])
        
        return '', 200
    except Exception as err:
        logger.exception(err)
        abort(500, E500_0)
    finally:
        torch.cuda.empty_cache()

@detect_api.put('/yolov7/weights/<int:index>')
# @detect_api.auth_required(authen)
@detect_api.input(UpdateWeight)
@detect_api.output(Weight(many=True))
@detect_api.doc(responses=[200, 500])
def update_weight(index:int, args):
    if index not in range(len(weight_defs)):
        abort(500, "index is out of range")
    try:
        if "file" in args:
            if args["file"] != weight_defs[index]["file"]:
                # for file in Path(weight_dir).glob(weight_defs[index]["file"]):
                #     os.remove(os.path.join(weight_dir, file.name))
                weight_defs[index]["file"] = args["file"]
        
        if "img_size" in args:
            weight_defs[index]["img_size"] = args["img_size"]

        if "device" in args:
            weight_defs[index]["device"] = args["device"]
        
        load_weight_async(index, True)
        
        return weight_defs
    except Exception as err:
        logger.exception(err)
        abort(500, E500_0)
    finally:
        pass

@detect_api.get('/yolov7/weights')
# @detect_api.auth_required(authen)
@detect_api.output(Weight(many=True))
@detect_api.doc(responses=[200, 500])
def get_weights():
    try:
        return weight_defs
    except Exception as err:
        logger.exception(err)
        abort(500, E500_0)

@detect_api.post('/yolov7/detect')
# @detect_api.auth_required(authen)
@detect_api.input(Image)
@detect_api.output(Det(many=True))
@detect_api.doc(responses=[500])
def detect(args):
    try:
        res = []

        dets = detect_async(args)

        for i in range(len(dets)):
            each = dets[i]
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
        abort(500, E500_0)
    finally:
        pass

@detect_api.post('/yolov7/detect_tree')
# @detect_api.auth_required(authen)
@detect_api.input(Image)
@detect_api.output(Det(many=True))
@detect_api.doc(responses=[500])
def detect_tree(args):
    try:
        res = []

        dets = detect_async(args)
    
        for i in range(len(dets)):
            each = dets[i]
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
        abort(500, E500_0)
    finally:
        pass

@detect_api.post('/yolov7/detect_container')
# @detect_api.auth_required(authen)
@detect_api.input(ImageEx)
@detect_api.output(Det(many=True))
@detect_api.doc(responses=[500])
def detect_container(args):
    try:
        res = []

        detect_args = {
            "img":args["img"],
            "names": []
        }
        detect_args["names"].extend(args["names"])
        detect_args["names"].extend(args["containers"])

        dets = detect_async(detect_args)
    
        for i in range(len(dets)):
            each = dets[i]
            det = Det()
            det.index = i
            det.obj_name = each[0]
            det.confidence = each[1]
            det.x_left = each[2]
            det.y_top = each[3]
            det.x_right = each[4]
            det.y_bottom = each[5]
            if det.obj_name in args["containers"]:
                det.children = []
            
            res.append(det)
        
        for item in res.copy():
            if item.obj_name in args["names"]:
                item_square = (item.x_right - item.x_left) * (item.y_bottom - item.y_top)
                item_center_x = (item.x_left + item.x_right) / 2
                item_center_y = (item.y_top + item.y_bottom) / 2
                for container in res.copy():
                    if container.obj_name in args["containers"]:
                        container_square = (container.x_right - container.x_left) * (container.y_bottom - container.y_top)
                        # each_center_x = (each.x_left + each.x_right) / 2
                        # each_center_y = (each.y_top + each.y_bottom) / 2
                        if item_square < container_square:
                            if item_center_x > container.x_left and item_center_x < container.x_right and item_center_y > container.y_top and item_center_y < container.y_bottom:
                                container.children.append(item)
                                if item in res:
                                    res.remove(item)

        return res
    except Exception as err:
        logger.exception(err)
        abort(500, E500_0)
    finally:
        pass

@detect_api.post('/yolov7/preview')
# @detect_api.auth_required(authen)
@detect_api.input(Image)
@detect_api.output(Image)
@detect_api.doc(responses=[500])
def preview(args):
    try:
        names = configs["NAMES"]
        if "COLORS" not in configs:
            configs["COLORS"] = [[random.randint(0, 255) for _ in range(3)] for _ in names]
        colors = configs["COLORS"]

        res = None
        
        dets = detect_async(args)

        im0 = base64_to_cv2(args["img"])
        for det in dets:
            index = names.index(det[0])
            xyxy = [det[2],det[3],det[4],det[5]]
            plot_one_box(xyxy, im0, label="%s:%s"%(det[0],det[1]), color=colors[index], line_thickness=1)

        res = cv2_to_base64(im0)
        return {'img': res}
    except Exception as err:
        logger.exception(err)
        abort(500, E500_0)
    finally:
        pass

# @torch.no_grad()
# def detect_sync(args):
#     try:
#         temp_img = str(time.time_ns()) + '.jpg'
#         base64_to_image(args['img'], temp_img)

#         load_weight_async()

#         dets = []

#         classes = parse_classes(args["names"] if "names" in args else None)
#         if len(classes) > 0:
#             for key in classes.keys():
#                 dets.extend(yolov7s[key].detect(temp_img, classes=classes[key]))
#         return dets
#     except:
#         raise
#     finally:
#         torch.cuda.empty_cache()
#         if os.path.exists(temp_img):
#             os.remove(temp_img)

def detect_async(args):
    try:
        # temp_img = str(time.time_ns()) + '.jpg'
        # base64_to_image(args['img'], temp_img)

        im0 = base64_to_cv2(args["img"])
        # save image locally
        localtime = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
        jpg_name = localtime +  ".jpg"
        temp_img = os.path.join(configs["SAVE_IMG_DIR"], jpg_name)
        cv2.imencode(".jpg", im0)[1].tofile(temp_img)

        load_weight_async()

        dets = []

        classes = parse_classes(args["names"] if "names" in args else None)
        if len(classes) > 0:
            for key in classes.keys():
                arg_dict = {}
                arg_dict["img"] = temp_img
                arg_dict["classes"] = classes[key]
                procs[key].send(["det", arg_dict])

            error = None
            for key in classes.keys():
                mess = procs[key].recv()
                if isinstance(mess, str) and mess.startswith("error:"):
                    error = Exception(mess.strip("error:"))
                else:
                    dets.extend(mess)

            if error:
                raise error

        dets.sort(key=det_key)
        return dets
    except Exception as err:
        raise err
    finally:
        torch.cuda.empty_cache()
        if os.path.exists(temp_img) and not configs["SAVE_IMG_DIR"]:
            os.remove(temp_img)

def parse_classes(classes):
    res = {}

    if classes:
        pass
    else:
        classes = []
        for weight in weight_defs:
            for each in weight["names"]:
                if each not in classes:
                    classes.append(each)
    
    for obj in classes:
        for i in range(len(weight_defs)):
            if obj in weight_defs[i]["names"]:
                if i not in res.keys():
                    res[i] = []
                res[i].append(weight_defs[i]["names"].index(obj))
                break
    
    return res

def add_to_tree(obj, tree_nodes):
    tree_nodes.append(obj)
    obj_square = (obj.x_right - obj.x_left) * (obj.y_bottom - obj.y_top)
    obj_center_x = (obj.x_left + obj.x_right) / 2
    obj_center_y = (obj.y_top + obj.y_bottom) / 2
    for each in tree_nodes:
        if each == obj:
            continue

        each_square = (each.x_right - each.x_left) * (each.y_bottom - each.y_top)
        each_center_x = (each.x_left + each.x_right) / 2
        each_center_y = (each.y_top + each.y_bottom) / 2
        if obj_square < each_square:
            if each.obj_name in container_labels:
                if obj_center_x > each.x_left and obj_center_x < each.x_right and obj_center_y > each.y_top and obj_center_y < each.y_bottom:
                    tree_nodes.remove(obj)
                    add_to_tree(obj, each.children)
                    break
        elif obj.obj_name in container_labels:
            if obj.x_left < each_center_x and obj.x_right > each_center_x and obj.y_top < each_center_y and obj.y_bottom > each_center_y:
                tree_nodes.remove(each)
                add_to_tree(each, obj.children)
                break

def det_key(det:list):
    return "%s%s" % (str(int(det[3])).zfill(4), str(int(det[2])).zfill(4))