#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright (c) Megvii, Inc. and its affiliates.

import argparse
import os
import time
from datetime import datetime
from loguru import logger
import numpy as np

import cv2

import torch

import socketserver
import socket
import threading
from threading import Thread, enumerate
import pymysql

import torch.multiprocessing
import multiprocessing
import socket
import selectors
import random
import cv2
import numpy as np

from yolox.data.data_augment import ValTransform
from yolox.data.datasets import COCO_CLASSES
from yolox.exp import get_exp
from yolox.utils import fuse_model, get_model_info, postprocess, vis
from yolox.utils import visualize

db = pymysql.connect(host='localhost',port=0,user='root',passwd='NorthTransilVania',db='VESMO')
cur = db.cursor()

manager = multiprocessing.Manager()
shared_list = manager.list()


IMAGE_EXT = [".jpg", ".jpeg", ".webp", ".bmp", ".png"]

def handle(connection, address):
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("process-%r" % (address,))
    try:
        logger.debug("Connected %r at %r", connection, address)
        name = ''
        data = ''
        while True:
            length = recvall(connection,16)

            if int(length)>1000:
                stringData = recvall(connection,int(length))
                data = np.fromstring(stringData, dtype = 'uint8')
            elif int(length)<1000:
                name = recvname(connection,int(length))
                name = name.decode('utf-8')
            if data!='' and name !='':
                shared_list.append([data,address[0],address[1],name])
            #print(len(shared_list))
            '''if data == "":
                logger.debug("Socket closed remotely")
                break'''
    except:
        logger.exception("Problem handling request")
    finally:
        logger.debug("Closing socket")
        connection.close()

def recvall(sock, count):
    # 바이트 문자열
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def recvname(sock, count):
    # 바이트 문자열
    name = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        name += newbuf
        count -= len(newbuf)
    return name

class Server(object):
    def __init__(self, hostname, port):
        import logging
        self.logger = logging.getLogger("server")
        self.hostname = hostname
        self.port = port

    def start(self):
        self.logger.debug("listening")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # for fast close
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(1) # client count cuz we use mulit-proccessing, we use just 1
        
        while True:
            conn, address = self.socket.accept()
            self.logger.debug("Got connection")
            process = multiprocessing.Process(target=handle, args=(conn, address))
            process.daemon = True
            process.start()
            self.logger.debug("Started process %r", process)


def make_parser():
    parser = argparse.ArgumentParser("YOLOX Demo!")
    parser.add_argument(
        "demo", default="image", help="demo type, eg. image, video and webcam"
    )
    parser.add_argument("-expn", "--experiment-name", type=str, default=None)
    parser.add_argument("-n", "--name", type=str, default=None, help="model name")

    parser.add_argument(
        "--path", default="./assets/dog.jpg", help="path to images or video"
    )
    parser.add_argument("--camid", type=int, default=0, help="webcam demo camera id")
    parser.add_argument(
        "--save_result",
        action="store_true",
        help="whether to save the inference result of image/video",
    )

    # exp file
    parser.add_argument(
        "-f",
        "--exp_file",
        default=None,
        type=str,
        help="pls input your experiment description file",
    )
    parser.add_argument("-c", "--ckpt", default=None, type=str, help="ckpt for eval")
    parser.add_argument(
        "--device",
        default="cpu",
        type=str,
        help="device to run our model, can either be cpu or gpu",
    )
    parser.add_argument("--conf", default=0.3, type=float, help="test conf")
    parser.add_argument("--nms", default=0.3, type=float, help="test nms threshold")
    parser.add_argument("--tsize", default=None, type=int, help="test img size")
    parser.add_argument(
        "--fp16",
        dest="fp16",
        default=False,
        action="store_true",
        help="Adopting mix precision evaluating.",
    )
    parser.add_argument(
        "--legacy",
        dest="legacy",
        default=False,
        action="store_true",
        help="To be compatible with older versions",
    )
    parser.add_argument(
        "--fuse",
        dest="fuse",
        default=False,
        action="store_true",
        help="Fuse conv and bn for testing.",
    )
    parser.add_argument(
        "--trt",
        dest="trt",
        default=False,
        action="store_true",
        help="Using TensorRT model for testing.",
    )
    return parser


def get_image_list(path):
    image_names = []
    for maindir, subdir, file_name_list in os.walk(path):
        for filename in file_name_list:
            apath = os.path.join(maindir, filename)
            ext = os.path.splitext(apath)[1]
            if ext in IMAGE_EXT:
                image_names.append(apath)
    return image_names


class Predictor(object):
    def __init__(
        self,
        model,
        exp,
        cls_names=COCO_CLASSES,
        trt_file=None,
        decoder=None,
        device="cpu",
        fp16=False,
        legacy=False,
    ):
        self.model = model
        self.cls_names = cls_names
        self.decoder = decoder
        self.num_classes = exp.num_classes
        self.confthre = exp.test_conf
        self.nmsthre = exp.nmsthre
        self.test_size = exp.test_size
        self.device = device
        self.fp16 = fp16
        self.preproc = ValTransform(legacy=legacy)
        if trt_file is not None:
            from torch2trt import TRTModule

            model_trt = TRTModule()
            model_trt.load_state_dict(torch.load(trt_file))

            x = torch.ones(1, 3, exp.test_size[0], exp.test_size[1]).cuda()
            self.model(x)
            self.model = model_trt

    def inference(self, img):
        img_info = {"id": 0}
        if isinstance(img, str):
            #print(img)
            img_info["file_name"] = os.path.basename(img)
            img = cv2.imread(img)
            #cv2.imshow("??",img)
            #cv2.waitKey(0)
        else:
            img_info["file_name"] = None
        height, width = img.shape[:2]
        img_info["height"] = height
        img_info["width"] = width
        img_info["raw_img"] = img

        ratio = min(self.test_size[0] / img.shape[0], self.test_size[1] / img.shape[1])
        img_info["ratio"] = ratio
        img, _ = self.preproc(img, None, self.test_size)

        #print(len(img))
        img = torch.from_numpy(img).unsqueeze(0)
        #print(len(img))
        img = img.float()
        if self.device == "gpu":
            img = img.cuda()
            if self.fp16:
                img = img.half()  # to FP16
        #cv2.imwrite('/home/untermensi/Test.jpg',img)
        with torch.no_grad():
            t0 = time.time()
            outputs = self.model(img)
            if self.decoder is not None:
                outputs = self.decoder(outputs, dtype=outputs.type())
            outputs = postprocess(
                outputs, self.num_classes, self.confthre,
                self.nmsthre, class_agnostic=True
            )
            #logger.info("Infer time: {:.4f}s".format(time.time() - t0))
        return outputs, img_info

    def visual(self, output, img_info, cls_conf=0.35):
        global cls
        global class_list
        ratio = img_info["ratio"]
        img = img_info["raw_img"]
        if output is None:
            return img
        output = output.cpu()

        bboxes = output[:, 0:4]

        # preprocessing: resize
        bboxes /= ratio

        cls = output[:, 6]
        scores = output[:, 4] * output[:, 5]
        #print(self.cls_names)
        vis_res,class_list = vis(img, bboxes, scores, cls, cls_conf, self.cls_names)
        return vis_res


def image_demo(predictor, vis_folder, path, current_time, save_result,IP_Address,Port_Address,name):
    global outputs
    global db
    global cur
    detect=0
    detect_time = time.time()
    if os.path.isdir(path):
        files = get_image_list(path)
    else:
        files = [path]
    files.sort()
    for image_name in files:
        outputs, img_info = predictor.inference(image_name)
        result_image = predictor.visual(outputs[0], img_info, predictor.confthre)
        directory = "/home/cilab/flask_test/static/"+str(IP_Address)
        if outputs[0] is not None:
            try:
                save_time = time.time()
                string_class_list = str(class_list).replace("'","")
                cur_time = str(time.time())
                img_name = cur_time+"_"+str(IP_Address)+"_"+str(name)
                detect = detect+1
                if not os.path.exists(directory):
                    os.makedirs(directory)
                save_file_name = os.path.join(directory, img_name+".jpg")
                cv2.imwrite(save_file_name, result_image)
                cur.execute("INSERT INTO detect_information(IP,path,species,time,client_name) values(%s,%s,%s,%s,%s)",(str(IP_Address),"static/"+IP_Address+"/"+img_name+".jpg",string_class_list,str(datetime.now()),str(name)))
                # flask can not use absolute path
                db.commit()
                logger.info("save time: {:.4f}s".format(time.time()-save_time))
                ch = cv2.waitKey(0)
                if ch == 27 or ch == ord("q") or ch == ord("Q"):
                    break
            except Exception:
                db.close()
                db = pymysql.connect(host='localhost',port=0,user='root',passwd='NorthTransilVania',db='VESMO')
                cur = db.cursor()
    #print(detect/len(files))
    #logger.info("detect time: {:.4f}s".format(time.time()-detect_time))

def imageflow_demo(predictor, vis_folder, current_time, args):
    cap = cv2.VideoCapture(args.path if args.demo == "video" else args.camid)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)  # float
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float
    fps = cap.get(cv2.CAP_PROP_FPS)
    save_folder = os.path.join(
        vis_folder, time.strftime("%Y_%m_%d_%H_%M_%S", current_time)
    )
    os.makedirs(save_folder, exist_ok=True)
    if args.demo == "video":
        save_path = os.path.join(save_folder, args.path.split("/")[-1])
    else:
        save_path = os.path.join(save_folder, "camera.mp4")
    #logger.info(f"video save_path is {save_path}")
    vid_writer = cv2.VideoWriter(
        save_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (int(width), int(height))
    )
    while True:
        ret_val, frame = cap.read()
        if ret_val:
            outputs, img_info = predictor.inference(frame)
            result_frame = predictor.visual(outputs[0], img_info, predictor.confthre)
            if args.save_result:
                vid_writer.write(result_frame)
            ch = cv2.waitKey(1)
            if ch == 27 or ch == ord("q") or ch == ord("Q"):
                break
        else:
            break


def main(exp, args):

    global predictor
    global vis_folder
    global current_time

    if not args.experiment_name:
        args.experiment_name = exp.exp_name

    weight_name = os.path.join("/home/untermensi/YOLOX/weight")
    file_name = os.path.join(exp.output_dir, args.experiment_name)
    os.makedirs(file_name, exist_ok=True)

    vis_folder = None
    if args.save_result:
        vis_folder = os.path.join(file_name, "vis_res")
        os.makedirs(vis_folder, exist_ok=True)

    if args.trt:
        args.device = "gpu"

    logger.info("Args: {}".format(args))

    if args.conf is not None:
        exp.test_conf = args.conf
    if args.nms is not None:
        exp.nmsthre = args.nms
    if args.tsize is not None:
        exp.test_size = (args.tsize, args.tsize)

    model = exp.get_model()
    logger.info("Model Summary: {}".format(get_model_info(model, exp.test_size)))

    if args.device == "gpu":
        model.cuda()
        if args.fp16:
            model.half()  # to FP16
    model.eval()

    if not args.trt:
        if args.ckpt is None:
            ckpt_file = os.path.join(weight_name, "best_ckpt.pth")
        else:
            ckpt_file = args.ckpt
        logger.info("loading checkpoint")
        ckpt = torch.load(ckpt_file, map_location="cpu")
        # load the model state dict
        model.load_state_dict(ckpt["model"])
        logger.info("loaded checkpoint done.")

    if args.fuse:
        logger.info("\tFusing model...")
        model = fuse_model(model)

    if args.trt:
        assert not args.fuse, "TensorRT model is not support model fusing!"
        trt_file = os.path.join(file_name, "model_trt.pth")
        assert os.path.exists(
            trt_file
        ), "TensorRT model is not found!\n Run python3 tools/trt.py first!"
        model.head.decode_in_inference = False
        decoder = model.head.decode_outputs
        logger.info("Using TensorRT to inference")
    else:
        trt_file = None
        decoder = None
    predictor = Predictor(
        model, exp, COCO_CLASSES, trt_file, decoder,
        args.device, args.fp16, args.legacy,
    )
    current_time = time.localtime()
    #Thread(target=runServer,args=()).start()

    '''ctx = mp.get_context('spawn')
    q = ctx.Queue()
    p = ctx.Process(target=runServer, args=(predictor,vis_folder,current_time))
    p.start()
    print(q.get())
    p.join()'''
    '''if args.demo == "image":
        image_demo(predictor, vis_folder, "/home/untermensi/Extract", current_time, args.save_result,"Test_1","Test_2","Test_3")
    elif args.demo == "video" or args.demo == "webcam":
        imageflow_demo(predictor, vis_folder, current_time, args)'''


def print_Shared_List(save_result):
    count = 0
    while True:
        if len(shared_list)>0:
            #print("Pass!")
            info_list = shared_list.pop(0)
            #print(info_list)
            frame = cv2.imdecode(info_list[0], cv2.IMREAD_COLOR)
            IP = info_list[1]
            Port = info_list[2]
            Serial =  info_list[3]
            #cv2.imwrite("/home/ci/Detect_Test_YOLOX/"+str(count)+".jpg", frame)
            image_demo(predictor, vis_folder, frame, current_time, save_result,IP,Port,Serial)
            count = count+1

if __name__ == "__main__":
    args = make_parser().parse_args()
    exp = get_exp(args.exp_file, args.name)
    main(exp, args)
    import logging
    logging.basicConfig(level=logging.DEBUG)
    server = Server("220.69.240.221", 9000)
    try:
        logging.info("Listening")    
        p = multiprocessing.Process(target=server.start, name="SubProcess", args=())
        p.start()

    except:
        logging.exception("Unexpected exception")
    '''finally:
        logging.info("Shutting down")
        for process in multiprocessing.active_children():
            logging.info("Shutting down process %r", process)
            process.terminate()
            process.join()'''
    logging.info("All done")
    print_Shared_List(args.save_result)
