# -*- coding: utf-8 -*-
import qrcode
import os
import cv2
from pyzbar.pyzbar import decode
import random
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
from IPython import get_ipython
from IPython.display import display
CAMERA_PORT = 1

async def init_camera_settings(settings):

    cam_settings =  cv2.VideoCapture(CAMERA_PORT, cv2.CAP_DSHOW)
    cam_settings.set(3, 640)
    cam_settings.set(4, 480)
    return cam_settings

async def make_qr_code(data, type):
    return qrcode.make(data)

async def save_qr_as_jpg(data, output_name):
    data.save(output_name)

async def load_qr_images_from_path(data_path):
    data = []
    path = os.path.join(data_path)
    for img in os.listdir(path):
        try:
            img_array = cv2.imread(os.path.join(path, img))
            data.append([img_array, img])
        except Exception as e:
            print (e)
            pass
    print(data)
    return data

async def decode_input(img):
    img_data = []
    for code in decode(img[0]):
        img_data.append([code.data.decode('utf-8'), code.type])
    print(img_data)


async def decode_input_camera(camera_settings):
    camera = True
    img_data = []
    while camera == True:
        success, frame = camera_settings.read()
        for code in decode(frame):
            img_data.append([code.data.decode('utf-8'), code.type])
            cv2.destroyAllWindows()
            return img_data
        cv2.imshow('Testing-QR', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

