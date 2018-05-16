# -*- coding: utf-8 -*-

from srcs.const import *
import sys

import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import *
from tkinter.filedialog import *
from tkinter.scrolledtext import ScrolledText

import os
import configparser
from time import time, localtime, strftime, sleep

import imutils
from imutils.video import VideoStream
import cv2
import numpy as np
import threading

import Tk_Tooltips

class SecondTab(object):

    def __init__(self, app):
        self.labelize_frame = Frame(app.second_tab)
        self.labelize_frame.grid(row=0, column=0, stick='n')
        self.labelize_frame.grid_columnconfigure(0, weight=1)
        self.labelize_frame.grid_rowconfigure(0, weight=1)
