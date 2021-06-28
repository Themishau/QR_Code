# -*- coding: utf-8 -*-
#from GUI_rasp_noasyn import *
from GUI_rasp__webcam_noasyn_new import *

if __name__ == '__main__':
    print("start")
    menu = Controller(['update_process'], 'controller')
    menu.run()
