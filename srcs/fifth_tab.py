# -*- coding: utf-8 -*-

from srcs.const import *
import sys
import threading

import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import *
from tkinter.filedialog import *
from tkinter.scrolledtext import ScrolledText

from PIL import Image, ImageTk

import imutils

if SYSTEM != 'Rpi':
    from imutils.video import VideoStream
    import cv2
else:
    from picamera import PiCamera
    from picamera.array import PiRGBArray

from time import time, localtime, strftime, sleep

import srcs.Tk_Tooltips as ttp

import json
import numpy as np
import pandas as pd

class FifthTab(object):

    def __init__(self, app, devMode):
        self.app = app
        self.devMode = devMode

        self.snap_frame = Frame(self.app.fifth_tab)
        self.snap_frame.grid(row=0, column=0, sticky="nsew")
        self.snap_frame.grid_columnconfigure(0, weight=1)
        self.snap_frame.grid_columnconfigure(1, weight=1)
        self.snap_frame.grid_columnconfigure(2, weight=1)
        self.snap_frame.grid_rowconfigure(0, weight=1)

        self.frame = None
        self.vs = None
        self.thread = threading.Thread(target=self.videoLoop, args=())
        self.stopEvent = threading.Event()
        self.panel = None
        self.image = None

        self.model = None
        self.preds = StringVar()
        self.preds.set("None")

        self.snap_w = IntVar()
        self.snap_w.set(SNAP_W)
        self.snap_h = IntVar()
        self.snap_h.set(SNAP_H)

        self.h1 = IntVar()
        if self.app.second_tab.h1.get():
            self.h1.set(self.app.second_tab.h1.get())
        else:
            self.h1.set(0)

        self.h2 = IntVar()
        if self.app.second_tab.h2.get():
            self.h2.set(self.app.second_tab.h2.get())
        else:
            self.h2.set(self.snap_h.get())

        self.w1 = IntVar()
        if self.app.second_tab.w1.get():
            self.w1.set(self.app.second_tab.w1.get())
        else:
            self.w1.set(0)

        self.w2 = IntVar()
        if self.app.second_tab.w2.get():
            self.w2.set(self.app.second_tab.w2.get())
        else:
            self.w2.set(self.snap_w.get())

        self.load_model_pic = ImageTk.PhotoImage(Image.open('assets/import.png'))
        self.cam_pic = ImageTk.PhotoImage(Image.open('assets/webcam.png'))
        self.stop_pic = ImageTk.PhotoImage(Image.open('assets/stop.png'))
        self.settings_pic = ImageTk.PhotoImage(Image.open('assets/settings.png'))

        if SYSTEM == 'Rpi':
            self.camera = PiCamera()
            self.camera.resolution = (self.snap_w.get(), self.snap_h.get())
            self.camera.framerate = SNAP_FPS
            self.camera.hflip = True
            self.camera.vflip = True
            self.rawCapture = PiRGBArray(self.camera, size=(self.snap_w.get(), self.snap_h.get()))
        
        self.video_frame = Frame(self.snap_frame)
        self.video_frame.config(borderwidth=2, relief="sunken", height=SNAP_H, width=SNAP_W)
        self.video_frame.grid(row=0, column=1)
        self.video_frame.grid_propagate(0)

        command_frame = Frame(self.snap_frame)
        command_frame.grid(row=0, column=0)
        command_frame.grid_rowconfigure(0, weight=1)
        command_frame.grid_rowconfigure(1, weight=1)
        command_frame.grid_rowconfigure(2, weight=1)
        command_frame.grid_rowconfigure(3, weight=1)
        command_frame.grid_columnconfigure(0, weight=1)

        load_model_handler = lambda: self.load_model(self)
        cam_handler = lambda: self.open_cam(self)
        stop_handler = lambda: self.stop(self)
        settings_handler = lambda: self.set_video_param(self)

        self.load_model_but = Button(command_frame)
        self.load_model_but.config(image=self.load_model_pic, command=load_model_handler)
        self.load_model_but.grid(row=0, column=0, padx=10, pady=10)
        self.load_model_ttp = ttp.ToolTip(self.load_model_but, 'Import Model', msgFunc=None, delay=1, follow=True)

        settings_but = Button(command_frame)
        settings_but.config(image=self.settings_pic, command=settings_handler)
        settings_but.grid(row=1, column=0, padx=10, pady=5)
        settings_ttp = ttp.ToolTip(settings_but, 'Setup Camera', msgFunc=None, delay=1, follow=True)     

        self.play_but = Button(command_frame)
        self.play_but.config(image=self.cam_pic, command=cam_handler, state="disabled")
        self.play_but.grid(row=2, column=0, padx=10, pady=5)
        play_ttp = ttp.ToolTip(self.play_but, 'Start Camera', msgFunc=None, delay=1, follow=True)

        stop_but = Button(command_frame)
        stop_but.config(image=self.stop_pic, command=stop_handler)
        stop_but.grid(row=3, column=0, padx=10, pady=5)
        stop_ttp = ttp.ToolTip(stop_but, 'Stop Camera', msgFunc=None, delay=1, follow=True)

        label_frame = Frame(self.snap_frame, borderwidth=2, relief="sunken")
        label_frame.grid(row=0, column=2, sticky='e', padx=20)
        label_frame.grid_columnconfigure(0, weight=1)
        label_frame.grid_rowconfigure(0, weight=1)
        label_frame.grid_rowconfigure(1, weight=1)

        label_frame_title = Label(label_frame)
        label_frame_title.config(text="Label :", font=("Courier", 20))
        label_frame_title.grid(row=0, column=0, padx=10)

        snap_label = Label(label_frame)
        snap_label.config(font=("Courier", 20), textvariable=self.preds)
        snap_label.grid(row=1, column=0, padx=10)

    def load_model(self, event):
        self.app.config(cursor="wait")
        self.model_filename =  askopenfilename(title = "Select Model", filetypes = (("h5py files","*.h5"),("all files","*.*")))
        if self.model_filename:
            import keras
            from keras.models import load_model
            import keras.backend as K
            import tensorflow as tf

            self.tf_graph = tf.get_default_graph()
            
            self.model = load_model(self.model_filename)
            self.play_but.config(state="normal")

            # Set model input_dim on camera
            model_dict = json.loads(self.model.to_json())
            self.input_shape = model_dict['config'][0]['config']['batch_input_shape']
            w = self.input_shape[2]
            h = self.input_shape[1]
            self.save_video_param(w, h)
            
            self.app.config(cursor="")
            showinfo("Model Loaded", "Model '%s' loaded" % (self.model_filename.split('/')[-1]))
        else:
            self.app.config(cursor="")

    def videoLoop(self):
        if SYSTEM != 'Rpi':
            while not self.stopEvent.is_set():
                if self.stopEvent.is_set():
                    break
                ret, self.video = self.vs.read()
                if ret is True:
                    self.video = imutils.resize(self.video, width=self.snap_w.get() - 10)
                    image = cv2.cvtColor(self.video, cv2.COLOR_BGR2RGB)
                    
                    # Test model
                    with self.tf_graph.as_default():
                        test_image = np.array(image)
                        test_image = np.array([test_image[self.h1.get():self.h2.get(), self.w1.get():self.w2.get(), :]])
                        preds = self.model.predict(test_image)
                        self.preds.set(str(np.argmax(preds, axis=1)))
                        
                    image = Image.fromarray(image)
                    try:
                        image = ImageTk.PhotoImage(image)
                    except RuntimeError:
                        break
                    if self.panel is None:
                        self.panel = Label(self.video_frame, image=image)
                        self.panel.image = image
                        self.panel.grid()
                    else:
                        self.panel.configure(image=image)
                        self.panel.image = image
                else:
                    self.stop(self, self.path)
                    break
            self.panel.image = None
            self.vs.release()
            self.frame = None
            self.preds.set("None")
            
        else:
            for frame in self.camera.capture_continuous(self.rawCapture, format="rgb", use_video_port=True):
                if self.stopEvent.is_set():
                    self.rawCapture.truncate(0)
                    break
                self.image = frame.array
                
                # Test model
                with self.tf_graph.as_default():
                    test_image = np.array(self.image)
                    test_image = np.array([test_image[self.h1.get():self.h2.get(), self.w1.get():self.w2.get(), :]])
                    preds = self.model.predict(test_image)
                    self.preds.set(str(np.argmax(preds, axis=1)))
                    
                image = Image.fromarray(self.image)
                try:
                    image = ImageTk.PhotoImage(image)
                except RuntimeError:
                    break
                if self.panel is None:
                    self.panel = Label(self.video_frame, image=image)
                    self.panel.image = image
                    self.panel.grid()
                else:
                    self.panel.configure(image=image)
                    self.panel.image = image
                self.rawCapture.truncate(0)
            self.panel.image = None
            self.frame = None
            self.preds.set("None")

    def set_video_param(self, event):
        self.video_param_frame = tk.Toplevel()
        self.video_param_frame.geometry("%dx%d+%d+%d" % (LAYER_INFO_W, LAYER_INFO_H, 200, 200))
        self.video_param_frame.title("Set Video Size")
        self.video_param_frame.transient(self.app)
        self.video_param_frame.grab_set()

        labels = tk.Label(self.video_param_frame)
        labels.grid(row=0, column=0, sticky='nsw')
        labels.grid_rowconfigure(0, weight=1)
        labels.grid_rowconfigure(1, weight=1)
        labels.grid_rowconfigure(2, weight=1)
        labels.grid_rowconfigure(3, weight=1)
        labels.grid_columnconfigure(0, weight=1)
        labels.grid_columnconfigure(1, weight=1)
        labels.grid_columnconfigure(2, weight=1)

        label_0 = tk.Label(labels)
        label_0.config(text='Video Settings:', font=("Helvetica", 18))
        label_0.grid(row=0, column=0, sticky='new', columnspan=3, padx=10, pady=10)
        
        label_1 = tk.Label(labels)
        label_1.config(text='Width:', font=("Helvetica", 14))
        label_1.grid(row=1, column=0, sticky='nsw', padx=5, pady=10)

        self.width = tk.StringVar()
        self.width.set(str(self.snap_w.get() - 10))
        
        val_1 = tk.Entry(labels, width=10, textvariable=self.width)
        val_1.grid(row=1, column=2, sticky='nse', padx=5, pady=10)

        self.heigth = tk.StringVar()
        self.heigth.set(str(self.snap_h.get()))

        if SYSTEM == 'Rpi':
            label_2 = tk.Label(labels)
            label_2.config(text='Heigth:', font=("Helvetica", 14))
            label_2.grid(row=2, column=0, sticky='nsw', padx=5, pady=10)

            val_2 = tk.Entry(labels, width=10, textvariable=self.heigth)
            val_2.grid(row=2, column=2, sticky='nse', padx=5, pady=10)
        else:
            self.heigth.set(str(round((3/4) * int(self.width.get()))))
            
        save_dense = lambda _: self.save_video_param(self.width, self.heigth)
        
        save_but = tk.Button(labels)
        save_but.config(text='Save', font=("Helvetica", 16))
        save_but.bind("<ButtonPress-1>", save_dense)
        save_but.bind("<Return>", save_dense)
        save_but.grid(row=3, column=1, sticky='nsew', padx=5, pady=10)

        val_1.focus_set()

    def save_video_param(self, width, heigth):
        if width <= SNAP_W and heigth <= SNAP_H:
            self.snap_w.set(width + 10)
            self.snap_h.set(heigth)

    def open_cam(event, self):
        if self.thread.is_alive():
            showwarning("Video already running", "Please stop the video before you start again")
        else:
            self.thread = threading.Thread(target=self.videoLoop, args=())
            self.stopEvent = threading.Event()
            if SYSTEM != 'Rpi':
                self.vs = cv2.VideoCapture(0)
            sleep(0.2)
            self.thread.start()

    def stop(event, self):
        self.stopEvent.set()

    def on_quit(self):
        if self.thread.is_alive():
            showwarning("Video running", "Please stop the video before you quit")
            return 0
        else:
            return 1