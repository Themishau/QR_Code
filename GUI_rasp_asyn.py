# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from QR_rasp_asyn import make_qr_code, decode_input, load_qr_images_from_path
from QR_rasp_asyn import init_camera_settings, decode_input_camera
from observer import Publisher, Subscriber
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import asyncio
import threading
import time


class Model(Publisher):
    def __init__(self, events):
        super().__init__(events)
        # init gpu

        self.camera_setting = None

        self.input_qr_img_path = None
        self.output_path = None
        self.save_qr_data = None

        self.generated_qr_data = None
        self.loaded_qr_data = None
        self.decoded_qr_data = None

        self.filepath = None
        self.processing = None


    def clearData(self):
        self.input_qr_img_path = None
        self.output_path = None
        self.loaded_qr_data = None
        self.filepath = None
        self.processing = None

    async def init_virtual_camera_obs(self):
        settings = None
        self.camera_setting = await init_camera_settings(settings)

    async def load_qr_from_img(self, name):
        await self.set_process(name)
        await self.check_input_path()
        await self.routine_load_qr_img()
        await self.read_all_qr()
        await self.delete_process()

    async def load_qr_from_camera(self, name):
        await self.set_process(name)
        await self.check_camera_input()
        await self.routine_load_qr_camera()
        await self.delete_process()


    async def generate_qr(self, type):
        self.generated_qr_data = await make_qr_code(self.save_qr_data, type)
        print()

    async def check_input_path(self):
        if self.input_qr_img_path is not None:
            return True
        else:
            print("no input")
            return False

    async def check_camera_input(self):
        await self.init_virtual_camera_obs()


    async def read_all_qr(self):
        read_data = []
        for img in self.loaded_qr_data:
            read_data.append(await self.routine_process_qr_loaded_data(img))

    async def routine_load_qr_img(self):
        self.loaded_qr_data = await load_qr_images_from_path(self.input_qr_img_path)

    async def routine_load_qr_camera(self):
        read_data = []
        read_data.append(await decode_input_camera(self.camera_setting))
        print(read_data)

    async def routine_process_qr_loaded_data(self, data):
        return await decode_input(data)



    async def set_process(self, task):
        self.dispatch("data_changed", "{} started".format(task))
        self.processing = task

    async def delete_process(self):
        self.dispatch("data_changed", "{} finished".format(self.processing))
        self.processing = None


class Controller(Subscriber):
    def __init__(self, name):
        super().__init__(name)

        # init tk
        self.root = tk.Tk()

        #init window size
        self.root.geometry("485x750+200+200")
        self.root.resizable(0, 0)
        #counts running threads
        self.runningAsync = 0

        #init model and viewer
        #init model and viewer with publisher
        self.model = Model(['data_changed', 'clear_data'])
        self.view = View(self.root, self.model, ['load_qr_from_img',
                                                 'load_qr_from_camera',
                                                 'close_button'],
                                                 'viewer')

        #init Observer
        self.view.register('load_qr_from_img', self)  # Achtung, sich selbst angeben und nicht self.controller
        self.view.register('load_qr_from_camera', self)
        self.view.register('close_button', self)

        #init Observer
        self.model.register('data_changed', self.view) # Achtung, sich selbst angeben und nicht self.controller
        self.model.register('clear_data', self.view)

    def update(self, event, message):
        self.view.write_gui_log("{} button clicked...".format(event))
        if event == 'load_qr_from_img':
            try:
                self.model.input_qr_img_path = self.view.main.input_path.get()
            except FileNotFoundError:
                messagebox.showerror('Error', 'no input path')
                return
            try:
                self.model.output_path = self.view.main.output_path.get()
            except FileNotFoundError:
                messagebox.showerror('Error', 'no output path')
                return

        if event == 'close_button':
            self.closeprogram(event)

        self.do_tasks(event)

        self.view.write_gui_log("{} routine finished".format(event))

    def run(self):
        self.root.title("QR Code Simple GUI")

        #sets the window in focus
        self.root.deiconify()
        self.root.mainloop()

    def closeprogram(self, event):
        self.root.destroy()

    def closeprogrammenu(self):
        self.root.destroy()

    def do_tasks(self, task):
        """ Function/Button starting the asyncio part. """
#        return threading.Thread(target=self.async_do_task(task), args=()).start()
        return self.async_do_task(task)

    def async_do_task(self, task):
        loop = asyncio.new_event_loop()
        self.runningAsync = self.runningAsync + 1
        visit_task = getattr(self.model, task, self.generic_task)
        loop.run_until_complete(visit_task(task))
        while self.model.processing is not None:
            time.sleep(1)
            print('status: {} please wait...'.format(self.model.processing))
        loop.close()
        self.runningAsync = self.runningAsync - 1

    async def task(self, task):
        # create an generic method call
        # self.model_grey -> model_grey
        # self       -> controller
        visit_task = getattr(self.model, task, self.generic_task)
        return await visit_task(task)

    async def generic_task(self, name):
        raise Exception('No {} method'.format(name))


class View(Publisher, Subscriber):
    def __init__(self, parent, model, events, name):
        Publisher.__init__(self, events)
        Subscriber.__init__(self, name)

        #init viewer
        self.model = model
        self.sidePanel = InfoBottomPanel(parent)
        self.frame = tk.Frame(parent)
        self.frame.grid(sticky="NSEW")
        self.main = Main(parent)
        self.canvas = None

        # hidden and shown widgets
        self.hiddenwidgets = {}

        self.main.load_qr_from_img.bind("<Button>", self.load_qr_from_img)
        self.main.load_qr_from_camera.bind("<Button>", self.load_qr_from_camera)

        self.main.quitButton.bind("<Button>", self.closeprogram)

    def hide_instance_attribute(self, instance_attribute, widget_variablename):
        print(instance_attribute)
        self.hiddenwidgets[widget_variablename] = instance_attribute.grid_info()
        instance_attribute.grid_remove()

    def show_instance_attribute(self, widget_variablename):
        try:
            # gets the information stored in
            widget_grid_information = self.hiddenwidgets[widget_variablename]
            print(widget_grid_information)
            # gets variable and sets grid
            eval(widget_variablename).grid(row=widget_grid_information['row'], column=widget_grid_information['column'],
                                           sticky=widget_grid_information['sticky'],
                                           pady=widget_grid_information['pady'],
                                           columnspan=widget_grid_information['columnspan'])
        except:
            messagebox.showerror('Error show_instance_attribute', 'contact developer')

    # four events:
    # 'create_training_data',
    # 'create_model',
    # 'save_model',
    # 'close_button'
    def load_qr_from_img(self, event):
        self.dispatch("load_qr_from_img", "load_qr_from_img clicked! Notify subscriber!")

    def load_qr_from_camera(self, event):
        self.dispatch("load_qr_from_camera", "load_qr_from_camera clicked! Notify subscriber!")

    def closeprogram(self, event):
        self.dispatch("close_button", "quit button clicked! Notify subscriber!")

    def closeprogrammenu(self):
        self.dispatch("close_button", "quit button clicked! Notify subscriber!")


    def update(self, event, message):
        if event == "data_changed":
            self.write_gui_log("{}".format(message))

    def update_plot(self):
        #todo am besten eine funktion starten, die diese infors kriegt und dann im view ändert
        self.canvas = FigureCanvasTkAgg(self.model.fig, master=self.frame)
        self.show_instance_attribute('self.canvas.get_tk_widget()')

    def write_gui_log(self, text):
        time_now = datetime.now().strftime("%d-%b-%Y (%H:%M:%S)")
        self.sidePanel.log.insert("end", str(time_now) + ': ' + text)
        self.sidePanel.log.yview("end")


class Main(tk.Frame):
    def __init__(self, root, **kw):

        super().__init__(**kw)
        self.mainFrame = tk.Frame(root)
        self.mainFrame.grid(sticky="NSEW")

        #text input
        self.input = tk.Label(self.mainFrame, text="Enter input path ")
        self.input.grid(row = 0, column = 0, sticky = tk.N, pady = 2, columnspan = 4)

        #entry input
        self.input_path = tk.Entry(self.mainFrame, width=80)
        self.input_path.insert(0, 'Input_QR/')
        self.input_path.grid(row = 1, column = 0, sticky = tk.N, pady = 2, columnspan = 4)

        #text output
        self.output = tk.Label(self.mainFrame, text="Enter outputpath")
        self.output.grid(row = 2, column = 0, sticky = tk.N, pady = 2, columnspan = 4)

        #entry output
        self.output_path = tk.Entry(self.mainFrame, width=80)
        self.output_path.insert(0,'Output')
        self.output_path.grid(row = 3, column = 0, sticky = tk.N, pady = 2, columnspan = 4)

        #button load_qr_from_img
        self.load_qr_from_img = tk.Button(self.mainFrame, text="Load QR from IMG", width=30, borderwidth=5, bg='#FBD975')
        self.load_qr_from_img.grid(row = 7, column = 1, sticky = tk.N, pady = 0)

        #button load_qr_from_camera
        self.load_qr_from_camera = tk.Button(self.mainFrame, text="Load QR from Camera", width=30, borderwidth=5, bg='#FBD975')
        self.load_qr_from_camera.grid(row = 7, column = 2, sticky = tk.N, pady = 0)

        #button quit
        self.quitButton = tk.Button(self.mainFrame, text="Quit", width=30, borderwidth=5, bg='#FBD975')
        self.quitButton.grid(row = 15, column = 2, sticky = tk.N, pady = 0)


class InfoBottomPanel(tk.Frame):
    def __init__(self, root, **kw):
        super().__init__(**kw)
        self.sidepanel_frame = tk.Frame(root)
        self.sidepanel_frame.grid(sticky="NSEW")
        self.entry = tk.Label(self.sidepanel_frame, text="Log")
        self.entry.grid(row=0, column=0, sticky=tk.N, pady=0, columnspan=4)
        self.log = tk.Listbox(self.sidepanel_frame, width=80)
        self.log_scroll = tk.Scrollbar(self.sidepanel_frame, orient="vertical")
        self.log.config(yscrollcommand=self.log_scroll.set)
        self.log_scroll.config(command=self.log.yview)
        self.log.grid(row=1, column=0, sticky=tk.N, pady=0, columnspan=4)