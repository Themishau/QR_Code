# -*- coding: utf-8 -*-
import qrcode
import os
from picamera.array import PiRGBArray
from picamera import PiCamera
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
# CAMERA_PORT = 0

async def init_camera_settings(settings):
    
    return rawCapture

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


async def decode_input_camera(cam):
    img_data = []

    # with PiCamera() as camera:
    camera = PiCamera()
    camera.resolution = (1024, 768)
    camera.framerate = 60
    rawCapture = PiRGBArray(camera, size=(1024, 768))
    

    for frame in camera.capture_continuous(rawCapture, format="bgr"):
        image = frame.array
        cv2.imshow('Testing-QR', image)
        for code in decode(image):
            img_data.append([code.data.decode('utf-8'), code.type])
            cv2.destroyAllWindows()
            camera.close()
            return img_data
        
        rawCapture.truncate(0)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            camera.close()
            break