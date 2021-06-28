# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image
from datetime import datetime
from QR_webcam_noasyn import make_qr_code, decode_input, load_qr_images_from_path
from QR_webcam_noasyn import init_camera_settings, decode_input_camera, destroy_all_cv
from observer import Publisher, Subscriber
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sql_api.data import Data


class Model(Publisher):
    def __init__(self, events):
        super().__init__(events)
        # self.bg_fhdw = ImageTk.PhotoImage(file='FHDW_Logo.png')
        # self.bg_rhein = ImageTk.PhotoImage(file='RheinBergLogo.png')

        self.data = Data()

    def clearData(self):
        self.data.processing = None

    def init_virtual_camera_obs(self):
        settings = None
        self.data.camera_setting = init_camera_settings(settings)


    def load_qr_from_camera(self, name):
        self.set_process(name)
        if self.data.selected_geschaeft is None or self.data.selected_geschaeft_benefit is None:
            messagebox.showerror('Error', 'kein Benefit ausgewählt!')
            return
        self.check_camera_input()
        self.routine_load_qr_camera()
        self.delete_process()


    def check_camera_input(self):
        self.init_virtual_camera_obs()
        
    def read_all_qr(self):
        read_data = []
        for img in self.data.loaded_qr_data:
            read_data.append(self.routine_process_qr_loaded_data(img))


    def routine_load_qr_camera(self):
        read_data = []     
        
        read_data.append(decode_input_camera(self.data.camera_setting))
        self.data.camera_setting.release()

        qr_code = read_data[0][0][0].split('/')
        qr_code = qr_code[3]
        print('qr_code')
        print(qr_code)
        #status = self.data.connection.write_dummy_qr_code_in_database(qr_code)
        status = self.data.connection.write_qr_code_in_database(qr_code, self.data.selected_geschaeft_benefit)
        print(status)

    def routine_process_qr_loaded_data(self, data):
        return decode_input(data)

    def get_benefit_list_of_geschaeft(self, geschaeft):
        self.dispatch("update_geschaeft_benefit_List",
                      "update_geschaeft_benefit_List routine started! Notify subscriber!")

    def set_process(self, task):
        self.dispatch("data_changed", "{} started".format(task))
        self.data.processing = task

    def delete_process(self):
        self.dispatch("data_changed", "{} finished".format(self.data.processing))
        self.data.processing = None


class Controller(Publisher, Subscriber):
    def __init__(self, events, name):
        Publisher.__init__(self, events)
        Subscriber.__init__(self, name)

        # init tk
        self.root = tk.Tk()

        #init window size
        self.root.geometry("605x700+200+100")
        self.root.resizable(1, 1)
        self.root.configure(bg='powder blue')
        #self.root.overrideredirect(1)

        #counts running threads
        self.runningAsync = 0

        #init model and viewer
        #init model and viewer with publisher
        self.model = Model(['update_geschaeft_benefit_List',
                            'data_changed',
                            'clear_data'])
        self.view = View(self.root, self.model, ['select_geschaeft',
                                                 'select_geschaeft_benefit',
                                                 'load_qr_from_camera',
                                                 'close_button'],
                                                 'viewer')

        #init Observer
        self.view.register('select_geschaeft', self)  # Achtung, sich selbst angeben und nicht self.controller
        self.view.register('select_geschaeft_benefit', self)  # Achtung, sich selbst angeben und nicht self.controller
        self.view.register('load_qr_from_camera', self)
        self.view.register('close_button', self)

        #init Observer
        self.model.register('update_geschaeft_benefit_List', self.view)  # Achtung, sich selbst angeben und nicht self.controller
        self.model.register('data_changed', self.view) # Achtung, sich selbst angeben und nicht self.controller
        self.model.register('clear_data', self.view)

        self.register("update_process", self.view)


    def update(self, event, message):
        self.view.write_gui_log("{} button clicked...".format(event))

        if event == "select_geschaeft_benefit":
            self.select_geschaeft_benefit()

        elif event == "select_geschaeft":
            self.select_geschaeft()

        if event == 'close_button':
            return self.closeprogram(event)

        self.do_tasks(event)
        self.view.write_gui_log("{} routine finished".format(event))

    #
    def select_geschaeft(self):
        try:
            # doch so kompliziert, denn sonst wird die benefit liste neu geladen und weil kein geschäft ausgewählt mit none.
            selection = None
            for geschaeft in self.model.data.gesch_bene_df.itertuples():
                if geschaeft.Geschaeft == self.view.main.geschaefte_List.selection_get():
                    selection = geschaeft.Geschaeft
            if selection is not None:
                self.model.data.selected_geschaeft = self.model.data.gesch_bene_df.loc[self.model.data.gesch_bene_df['Geschaeft'] == selection]
            else:
                return None
            self.model.get_benefit_list_of_geschaeft(self.model.data.selected_geschaeft)
        except TypeError:
            messagebox.showerror('Error SELECT select_geschaeft', 'Nothing Selected!')

    #
    def select_geschaeft_benefit(self):
        geschaeft = 'Error'
        benefit = 'Error'
        try:
            selection = self.view.main.geschaeft_benefits_List.selection_get()
            if selection is not None:
                self.model.data.selected_geschaeft_benefit = self.model.data.selected_geschaeft.loc[self.model.data.selected_geschaeft['Benefit'] == selection]
                for row in self.model.data.selected_geschaeft_benefit.itertuples():
                    geschaeft = row.Geschaeft
                    benefit = row.Benefit
                self.view.write_gui_log("Geschäft: {}, Benefit: {} ausgewählt.".format(geschaeft, benefit))
            else:
                return None
        except TypeError:
            messagebox.showerror('Error SELECT ROUTE', 'Nothing Selected!')


    def run(self):
        self.root.title("QR Code Simple GUI")
        self.view.update_geschaeft_List()
        #sets the window in focus
        self.root.deiconify()
        self.root.mainloop()

    def closeprogram(self, event):
        try:
            destroy_all_cv()
            self.model.data.camera_setting.release()
            self.model.data.connection.close_connection()
        except:
            print('no active camera')
        self.root.destroy()

    def closeprogrammenu(self):
        try:   
            destroy_all_cv()
            self.model.data.camera_setting.release()
            self.model.data.connection.close_connection()
        except:
            print('no active camera')
        self.root.destroy()

    def do_tasks(self, task):
        """ Function/Button starting the asyncio part. """
        try:
            self.async_do_task(task)
        except:
            return
        return

    def async_do_task(self, task):
        visit_task = getattr(self.model, task, self.generic_task)
        return visit_task(task)

    def generic_task(self, name):
        raise Exception('No {} method'.format(name))


class View(Publisher, Subscriber):
    def __init__(self, parent, model, events, name):
        Publisher.__init__(self, events)
        Subscriber.__init__(self, name)

        #init viewer
        self.model = model
        self.frame = tk.Frame(parent)
        self.frame.configure(bg='powder blue')
        self.frame.grid(sticky="NSEW")
        self.main = Main(parent)
        self.sidePanel = InfoBottomPanel(parent)
        self.canvas = None

        # hidden and shown widgets
        self.hiddenwidgets = {}
        self.main.geschaefte_List.bind('<<ListboxSelect>>', self.select_geschaeft)
        self.main.geschaeft_benefits_List.bind('<<ListboxSelect>>', self.select_geschaeft_benefit)
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

    def select_geschaeft(self, event):

        self.dispatch("select_geschaeft", "select_geschaeft routine started! Notify subscriber!")

    def select_geschaeft_benefit(self, event):

        self.dispatch("select_geschaeft_benefit", "select_geschaeft_benefit routine started! Notify subscriber!")

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
        elif event == "update_geschaeft_benefit_List":
            self.update_geschaeft_benefit_List()
        elif event == "update_geschaeft_List":
            self.update_geschaeft_List()

    def update_geschaeft_List(self):
        inserted_geschaeft = []
        self.set_process("updating update_geschaeft_List list...")
        for geschaeft in self.model.data.gesch_bene_df.itertuples():
            schon_in_liste = False
            for gesch in inserted_geschaeft:
                if gesch == geschaeft.Geschaeft:
                    schon_in_liste = True
            if not schon_in_liste:
                self.main.geschaefte_List.insert("end", geschaeft.Geschaeft)
                inserted_geschaeft.append(geschaeft.Geschaeft)
            # self.view.main.agency_List.grid(row=0, column=0, columnspan=1)
        self.set_process("geschaeft list updated")

    def update_geschaeft_benefit_List(self):
        self.set_process("updating update_geschaeft_benefit_List list...")
        if self.main.geschaeft_benefits_List is not None:
            self.main.geschaeft_benefits_List.delete(0, 'end')
        for geschaeft_benefit in self.model.data.selected_geschaeft.itertuples():
            self.main.geschaeft_benefits_List.insert("end", geschaeft_benefit.Benefit)
            # self.view.main.agency_List.grid(row=0, column=0, columnspan=1)
        self.set_process("geschaeft_benefit list updated")

    def update_plot(self):
        #todo am besten eine funktion starten, die diese infos kriegt und dann im view ändert
        self.canvas = FigureCanvasTkAgg(self.model.fig, master=self.frame)
        self.show_instance_attribute('self.canvas.get_tk_widget()')

    def write_gui_log(self, text):
        time_now = datetime.now().strftime("%d-%b-%Y (%H:%M:%S)")
        self.sidePanel.log.insert("end", str(time_now) + ': ' + text)
        self.sidePanel.log.yview("end")

    def set_process(self, task):
        self.update("update_process", "{} started".format(task))
        self.process = task

    def delete_process(self):
        self.update("update_process", "{} finished".format(self.process))
        self.process = None


class Main(tk.Frame):
    def __init__(self, root, **kw):

        super().__init__(**kw)
        self.mainFrame = tk.Frame(root)
        self.mainFrame.grid(sticky="NSEW")
        self.mainFrame.configure(bg='powder blue')
        self.logofhdw = ImageTk.PhotoImage(Image.open("FHDW_Logo.png"))
        self.logorhein = ImageTk.PhotoImage(Image.open("RheinBergLogo.png"))
        self.logo_label_fhdw = tk.Label(self.mainFrame, image = self.logofhdw)
        self.logo_label_fhdw.grid(row=0, column=0, sticky=tk.N, pady=0)
        self.logo_label_rhein = tk.Label(self.mainFrame, image = self.logorhein)
        self.logo_label_rhein.grid(row=0, column=1, sticky=tk.N, pady=0)
        # lists of geschaefte
        self.geschaefte_List = tk.Listbox(self.mainFrame, width=100)
        self.geschaefte_List_scrollbar = tk.Scrollbar(self.geschaefte_List, orient="vertical")
        self.geschaefte_List.config(yscrollcommand=self.geschaefte_List_scrollbar.set)
        self.geschaefte_List_scrollbar.config(command=self.geschaefte_List.yview)
        self.geschaefte_List.grid(row=1, column=0, sticky=tk.N, pady=4, columnspan=4)

        # lists of geschaeft_benefits
        self.geschaeft_benefits_List = tk.Listbox(self.mainFrame, width=100)
        self.geschaeft_benefits_List_scrollbar = tk.Scrollbar(self.geschaeft_benefits_List, orient="vertical")
        self.geschaeft_benefits_List.config(yscrollcommand=self.geschaeft_benefits_List_scrollbar.set)
        self.geschaeft_benefits_List_scrollbar.config(command=self.geschaeft_benefits_List.yview)
        self.geschaeft_benefits_List.grid(row=2, column=0, sticky=tk.N, pady=4, columnspan=4)

        #button load_qr_from_camera
        self.load_qr_from_camera = tk.Button(self.mainFrame, text="Load QR from Camera", width=30, borderwidth=5, bg='#FBD975')
        self.load_qr_from_camera.grid(row = 3, column = 0, sticky = tk.N, padx = 40)

        #button quit
        self.quitButton = tk.Button(self.mainFrame, text="Quit", width=30, borderwidth=5, bg='#FBD975')
        self.quitButton.grid(row = 3, column = 1, sticky = tk.N, pady = 0)


class InfoBottomPanel(tk.Frame):
    def __init__(self, root, **kw):
        super().__init__(**kw)
        self.sidepanel_frame = tk.Frame(root)
        self.sidepanel_frame.grid(sticky="NSEW")
        self.sidepanel_frame.configure(bg='powder blue')
        self.log = tk.Listbox(self.sidepanel_frame, width=80)
        self.log_scroll = tk.Scrollbar(self.sidepanel_frame, orient="vertical")
        self.log.config(yscrollcommand=self.log_scroll.set)
        self.log_scroll.config(command=self.log.yview)
        self.log.grid(row=2, column=1, sticky=tk.N, pady=50, padx=50,columnspan=4)
