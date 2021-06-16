import json
import os
import glob
import random
import argparse
import uuid
from enum import Enum
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk


class LabelMode(Enum):
    plain = "plain"
    json = "json"
    json_single_file = "json_single_file"

    def __str__(self):
        return self.value


# colors for the bboxes
COLORS = ['red', 'blue', 'pink', 'cyan', 'green', 'black', 'gray50', 'forest green', 'tomato']
# image sizes for the examples
SIZE = 256, 256

LABEL_MODE = LabelMode.plain
LABEL_FILE_FORMAT = {LabelMode.json: ".json", LabelMode.plain: ".txt", LabelMode.json_single_file: ".json"}


class LabelTool():
    def __init__(self, master, label_mode=LabelMode.plain, init_params={}):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width=FALSE, height=FALSE)

        # initialize global state
        self.init_params = init_params
        self.imageDir = ''
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.label_mode = label_mode
        self.regions_all_images = None  # Used as a cache when reading labels from a single JSON file
        self.tkimg = None
        self.currentCaption = ''
        self.cla_can_temp = []
        self.classcandidate_filename = 'class.txt'

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None
        self.selected_box = None
        self.selected_box_index = -1

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        # input image dir button
        self.srcDirBtn = Button(self.frame, text="Image input folder", command=self.selectSrcDir)
        self.srcDirBtn.grid(row=0, column=0)
        self.parent.bind("i", self.selectSrcDir)  

        # input image dir entry
        self.svSourcePath = StringVar()
        self.entrySrc = Entry(self.frame, textvariable=self.svSourcePath)
        self.entrySrc.grid(row=0, column=1, sticky=W + E)
        self.svSourcePath.set(self.get_init_img_dir())

        # load button
        self.ldBtn = Button(self.frame, text="Load Dir", command=self.loadDir)
        self.ldBtn.grid(row=0, column=2, rowspan=2, columnspan=2, padx=2, pady=2, ipadx=5, ipady=5)
        self.parent.bind("l", self.loadDir)  

        # label file save dir button
        self.desDirBtn = Button(self.frame, text="Label output folder", command=self.selectDesDir)
        self.desDirBtn.grid(row=1, column=0)
        self.parent.bind("o", self.selectDesDir)  

        # label file save dir entry
        self.svDestinationPath = StringVar()
        self.entryDes = Entry(self.frame, textvariable=self.svDestinationPath)
        self.entryDes.grid(row=1, column=1, sticky=W + E)
        self.svDestinationPath.set(self.get_init_label_dir())

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<BackSpace>", self.cancelBBox)  # press <Espace> to cancel current bbox
        # Disable key bindings to allow typing in text box!
        # self.parent.bind("s", self.cancelBBox)
        
        # hotkey to save and load previous image
        self.parent.bind("<Left>", self.prevImage)  
        # hotkey to save and load next image
        self.parent.bind("<Right>", self.nextImage)  
        self.mainPanel.grid(row=2, column=1, rowspan=4, sticky=W + N)

        # # choose class
        # self.classname = StringVar()
        # # self.classcandidate = ttk.Combobox(self.frame, state='readonly', textvariable=self.classname)
        # self.captionText = ttk.Entry(self.frame, textvariable=self.classname)
        # self.captionText.grid(row=2, column=2)
        # self.currentCaption = self.captionText.get()
        # self.btnclass = Button(self.frame, text='Set label', command=self.setLabel)
        # self.btnclass.grid(row=2, column=3, sticky=W + E)

        # choose class
        self.classname = StringVar()
        self.classcandidate = ttk.Combobox(self.frame, state='readonly', textvariable=self.classname)
        self.classcandidate.grid(row=2, column=2)
        if os.path.exists(self.classcandidate_filename):
            with open(self.classcandidate_filename) as cf:
                for line in cf.readlines():
                    self.cla_can_temp.append(line.strip('\n'))
        self.classcandidate['values'] = self.cla_can_temp
        self.classcandidate.current(0)
        self.currentLabelclass = self.classcandidate.get()
        self.btnclass = Button(self.frame, text='ComfirmClass', command=self.setClass)
        self.btnclass.grid(row=2, column=3, sticky=W+E)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text='Bounding boxes:')
        self.lb1.grid(row=3, column=2, sticky=W + N)
        self.listbox = Listbox(self.frame, width=22, height=12)
        self.listbox.grid(row=4, column=2, sticky=N + S)
        self.listbox.bind('<<ListboxSelect>>', self.on_list_select)
        self.btnDel = Button(self.frame, text='Delete', command=self.delBBox)
        self.btnDel.grid(row=4, column=3, sticky=W + E + N)
        self.parent.bind("<Delete>", self.delBBox)  
        self.btnClear = Button(self.frame, text='ClearAll', command=self.clearBBox)
        self.btnClear.grid(row=4, column=3, sticky=W + E + S)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=6, column=1, columnspan=2, sticky=W + E)
        self.imagenameLabel = Label(self.ctrPanel, text="Image Name")
        self.imagenameLabel.pack(side=LEFT, padx=5)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width=10, command=self.prevImage)
        self.prevBtn.pack(side=LEFT, padx=5, pady=3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width=10, command=self.nextImage)
        self.nextBtn.pack(side=LEFT, padx=5, pady=3)
        self.progLabel = Label(self.ctrPanel, text="Progress:     /    ")
        self.progLabel.pack(side=LEFT, padx=5)
        self.tmpLabel = Label(self.ctrPanel, text="Go to Image No.")
        self.tmpLabel.pack(side=LEFT, padx=5)
        self.idxEntry = Entry(self.ctrPanel, width=5)
        self.idxEntry.pack(side=LEFT)
        self.goBtn = Button(self.ctrPanel, text='Go', command=self.gotoImage)
        self.goBtn.pack(side=LEFT)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side=RIGHT)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(4, weight=1)

    def get_init_img_dir(self):
        if 'img_folder' in self.init_params and self.init_params['img_folder'] is not None:
            return self.init_params['img_folder']
        return os.getcwd()

    def get_init_label_dir(self):
        if 'label_folder' in self.init_params and self.init_params['label_folder'] is not None:
            return self.init_params['label_folder']
        return os.path.join(os.getcwd(), "Labels")

    def selectSrcDir(self, event=None):
        path = filedialog.askdirectory(title="Select image source folder", initialdir=self.svSourcePath.get())
        self.svSourcePath.set(path)
        return

    def selectDesDir(self, event=None):
        path = filedialog.askdirectory(title="Select label output folder", initialdir=self.svDestinationPath.get())
        self.svDestinationPath.set(path)
        return

    def loadDir(self, event=None):
        self.parent.focus()
        # get image list
        # self.imageDir = os.path.join(r'./Images', '%03d' %(self.category))
        self.imageDir = self.svSourcePath.get()
        self.imageList = []
        if not os.path.isdir(self.imageDir):
            messagebox.showerror("Error!", message="The specified dir doesn't exist!")
            return

        extlist = ["*.JPEG", "*.jpeg", "*JPG", "*.jpg", "*.PNG", "*.png", "*.BMP", "*.bmp"]
        for e in extlist:
            filelist = sorted(glob.glob(os.path.join(self.imageDir, e)))
            self.imageList.extend(filelist)
        # self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPEG'))
        if len(self.imageList) == 0:
            print('No .JPEG images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

        # set up output dir
        # self.outDir = os.path.join(r'./Labels', '%03d' %(self.category))
        self.outDir = self.svDestinationPath.get()
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        # Load single label file
        if self.label_mode == LabelMode.json_single_file:
            # Use Visual Genome file name for now
            self.inputdir = self.imageDir.split(os.path.sep)[-1]
            self.labelfilename = os.path.join(self.outDir, self.inputdir + "-region.json")
            if not os.path.exists(self.labelfilename):
                open(self.labelfilename, 'a').close()  # create empty file

            print("Loading labels for all images from file: {}".format(self.labelfilename))
            self.regions_all_images = self.load_all_regions(self.labelfilename)

        self.loadImage()
        print('%d images loaded from %s' % (self.total, self.imageDir))

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        size = self.img.size
        self.factor = max(size[0] / 1000, size[1] / 1000., 1.)
        self.img = self.img.resize((int(size[0] / self.factor), int(size[1] / self.factor)))
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width=max(self.tkimg.width(), 400), height=max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))

        # load labels
        self.clearBBox()

        # self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        fullfilename = os.path.basename(imagepath)
        # self.imagename, _ = os.path.splitext(fullfilename)
        basepath, self.imagename = os.path.split(fullfilename)
        self.imagenameLabel.config(text=self.imagename)

        boxes = []

        # Load boxes from labels file
        if self.label_mode == LabelMode.json_single_file:
            # Load label from single file
            if self.imagename in self.regions_all_images:
                regions = self.regions_all_images[self.imagename]
                tmp = self.get_regions_from_regions_list(regions)
                boxes.extend(tmp)
        else:
            labelname = self.imagename + LABEL_FILE_FORMAT[self.label_mode]
            self.labelfilename = os.path.join(self.outDir, labelname)
            if os.path.exists(self.labelfilename):
                with open(self.labelfilename) as f:

                    if self.label_mode == LabelMode.json:
                        print("Loading labels from json file")
                        regions = json.load(f)["regions"]
                        tmp = self.get_regions_from_regions_list(regions)
                        boxes.extend(tmp)
                        # print("Region coordinates with w/h    : x: {}, y: {},  w:{},  h:{}".format(x, y, w, h))
                        # print("Region coordinates in image    : x: {}, y: {}, x2:{}, y2:{}".format(x_1, y_1, x_2, y_2))
                        # print("Region coordinates in GUI coord: x: {}, y: {}, x2:{}, y2:{}".format(tmp[0], tmp[1], tmp[2], tmp[3]))
                    else:
                        print("Loading labels from plain text file")
                        for (i, line) in enumerate(f):
                            tmp = line.split()
                            tmp[0] = int(int(tmp[0]) / self.factor)
                            tmp[1] = int(int(tmp[1]) / self.factor)
                            tmp[2] = int(int(tmp[2]) / self.factor)
                            tmp[3] = int(int(tmp[3]) / self.factor)
                            boxes.append(tmp)

        # Display loaded boxes
        for box in boxes:
            self.bboxList.append(tuple(box))
            color_index = (len(self.bboxList) - 1) % len(COLORS)
            tmpId = self.mainPanel.create_rectangle(box[0], box[1], \
                                                    box[2], box[3], \
                                                    width=2, \
                                                    outline=COLORS[color_index])
            # outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
            self.bboxIdList.append(tmpId)
            self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' % (box[4], box[0], box[1], box[2], box[3]))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[color_index])

    def saveImage(self):

        if self.labelfilename == '':
            return

        if self.label_mode == LabelMode.json_single_file:
            regions = self.get_regions_from_bbox_list(self.bboxList)
            self.regions_all_images[self.imagename] = regions

            # Convert dict to list of images
            result = []
            for id, regions in self.regions_all_images.items():
                result.append({"id": id, "regions": regions})

            # Sort by id - same as image_data.json in order for preprocessing to work
            result = sorted(result, key=lambda x: x["id"])
            output = dict(inputdir=self.inputdir, annotation=result)
            with open(self.labelfilename, 'w') as f:
                json.dump(output, f, indent=4)
        else:
            with open(self.labelfilename, 'w') as f:
                if self.label_mode == LabelMode.json:
                    regions = self.get_regions_from_bbox_list(self.bboxList)
                    json.dump({"regions": regions}, f)
                else:
                    # f.write('%d\n' %len(self.bboxList))
                    for bbox in self.bboxList:
                        f.write("{} {} {} {} {}\n".format(int(int(bbox[0]) * self.factor),
                                                          int(int(bbox[1]) * self.factor),
                                                          int(int(bbox[2]) * self.factor),
                                                          int(int(bbox[3]) * self.factor),
                                                          bbox[4]))
                        # f.write(' '.join(map(str, bbox)) + '\n')
        print('Image No. %d saved' % (self.cur))

    # def mouseClick(self, event):
    #     if self.STATE['click'] == 0:
    #         self.STATE['x'], self.STATE['y'] = event.x, event.y
    #     else:
    #         x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
    #         y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)

    #         self.currentCaption = self.captionText.get()
    #         self.bboxList.append((x1, y1, x2, y2, self.currentCaption))
    #         self.bboxIdList.append(self.bboxId)
    #         self.bboxId = None
    #         self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' % (self.currentCaption, x1, y1, x2, y2))
    #         self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    #         # Select new box in the image
    #         self.select_box(len(self.bboxList) - 1)
    #     self.STATE['click'] = 1 - self.STATE['click']

    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            # x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            # y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)

            x1, x2 = self.STATE['x1'], self.STATE['x2']
            y1, y2 = self.STATE['y1'], self.STATE['y2']

            self.bboxList.append((x1, y1, x2, y2, self.currentLabelclass))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' %(self.currentLabelclass, x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']

    def apply_aspect_ratio(self, x1, y1, x2, y2, aspect_ratio):
        x1new = min(x1, x2); y1new = min(y1, y2)
        x2new = max(x1, x2); y2new = max(y1, y2)

        # case of constraining aspect ration
        if (aspect_ratio[0] * aspect_ratio[1] != 0):
            target_width_over_height = aspect_ratio[0] / aspect_ratio[1]
            width = x2new - x1new; height = y2new - y1new

            if float(width) / float(height) > target_width_over_height:
                height = round(width / target_width_over_height)
                if y2 > y1:
                    y2new = y1new + height
                else:
                    y1new = y2new - height
            else:
                width = round(height * target_width_over_height)
                if x2 > x1:
                    x2new = x1new + width
                else:
                    x1new = x2new - width


        self.STATE['x1'], self.STATE['y1'] = x1new, y1new
        self.STATE['x2'], self.STATE['y2'] = x2new, y2new

        # print("x1new, y1new, x2new, y2new: ", x1new, y1new, x2new, y2new)
        return x1new, y1new, x2new, y2new

    def mouseMove(self, event):
        self.disp.config(text='x: %d, y: %d' % (event.x, event.y))

        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width=2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width=2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            COLOR_INDEX = len(self.bboxIdList) % len(COLORS)

            self.bboxId = self.mainPanel.create_rectangle(
                *self.apply_aspect_ratio(self.STATE['x'], self.STATE['y'], event.x, event.y, self.init_params['aspect_ratio']),
                width=2, \
                outline=COLORS[COLOR_INDEX])
            self.apply_aspect_ratio(self.STATE['x'], self.STATE['y'], event.x, event.y, self.init_params['aspect_ratio'])

            # self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
            #                                               event.x, event.y, \
            #                                               width=2, \
            #                                               outline=COLORS[COLOR_INDEX])

    def select_box(self, box_index=-1):
        """ Visually selects the currently selected box """
        bbox = self.bboxList[box_index]
        self.mainPanel.delete(self.selected_box)
        self.selected_box_index = -1
        if box_index < 0:
            print("Deselect")
            self.mainPanel.delete(self.selected_box)
            self.selected_box = None
            self.selected_box_index = box_index
        else:
            self.mainPanel.delete(self.selected_box)
            x_1 = bbox[0]
            y_1 = bbox[1]
            x_2 = bbox[2]
            y_2 = bbox[3]
            COLOR_INDEX = box_index % len(COLORS)
            self.selected_box = self.mainPanel.create_rectangle(x_1, y_1, x_2, y_2, fill=COLORS[COLOR_INDEX], stipple='gray12')
            self.selected_box_index = box_index
            print("Select box at index %i" % box_index)

    def on_list_select(self, event):
        w = event.widget
        selected_index = w.curselection()[0]
        self.select_box(selected_index)

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                if self.bboxId == self.selected_box_index:
                    self.mainPanel.delete(self.selected_box)
                    self.selected_box_index = -1
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self, event=None):
        sel = self.listbox.curselection()
        # if len(sel) != 1:
        #     return
        # idx = int(sel[0])
        idx = int(sel[0]) if len(sel) == 1 else len(self.bboxIdList) - 1
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

        if idx == self.selected_box_index:
            self.mainPanel.delete(self.selected_box)
            self.selected_box_index = -1

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event=None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event=None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()
    def setClass(self):
        self.currentLabelclass = self.classcandidate.get()
        print('set label class to : %s' % self.currentLabelclass)            

    def setLabel(self):
        self.currentCaption = self.captionText.get()

        # Change label of currently selected box
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        bbox = self.bboxList.pop(idx)
        bbox = (bbox[0], bbox[1], bbox[2], bbox[3], self.currentCaption)
        self.bboxList.insert(idx, bbox)

        self.listbox.delete(idx)
        self.listbox.insert(idx,
                            '%s : (%d, %d) -> (%d, %d)' % (self.currentCaption, bbox[0], bbox[1], bbox[2], bbox[3]))
        self.listbox.itemconfig(idx, fg=COLORS[(idx) % len(COLORS)])

        print('set label class to : %s' % self.currentCaption)

    def xy_to_xywh(self, x_1,  y_1, x_2, y_2):
        """
        Convert bounding box between two coordinates to xy coordinates with height and width.
        """
        w = x_2 - x_1
        h = y_2 - y_1
        return x_1, y_1, w, h

    def xywh_to_xy(self, x, y, w, h):
        """
        Convert bounding box with width/height to two coordinates
        """
        x_2 = x + w
        y_2 = y + h
        return x, y, x_2, y_2

    def get_regions_from_regions_list(self, regions):
        result = []
        for region in regions:
            x = region["x"]
            y = region["y"]
            w = region["width"]
            h = region["height"]
            x_1, y_1, x_2, y_2 = self.xywh_to_xy(x, y, w, h)

            # Map to this format to ensure compatability with box display GUI code
            # TODO: Fix rounding errors (also in original code)
            tmp = [int(x_1 / self.factor), int(y_1 / self.factor), int(x_2 / self.factor),
                   int(y_2 / self.factor), region["phrase"]]
            result.append(tmp)
        return result

    def load_all_regions(self, label_file_name):
        regions_all_images = {}
        with open(label_file_name) as f:
            # TODO: Handling of missing file: Create new file
            # TODO: Handling of empty file
            try:
                data = json.load(f)
            except json.decoder.JSONDecodeError:
                # data = {}
                return {}
        # Convert list to dict: {id: {regions:{...}}} for easier data manipulation
        for entry in data["annotation"]:
            regions_all_images[entry["id"]] = entry["regions"]
        return regions_all_images

    def get_regions_from_bbox_list(self, bboxList):
        regions = []
        for idx, bbox in enumerate(bboxList):
            x_1 = int(int(bbox[0]) * self.factor)
            y_1 = int(int(bbox[1]) * self.factor)
            x_2 = int(int(bbox[2]) * self.factor)
            y_2 = int(int(bbox[3]) * self.factor)

            x, y, w, h = self.xy_to_xywh(x_1, y_1, x_2, y_2)

            label = bbox[4]

            region = {
                "id": idx,
                "image": self.imagename,
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "phrase": label
            }
            regions.append(region)
        return regions


def arg_parser():
    parser = argparse.ArgumentParser("BBox Tool GUI")
    parser.add_argument("-l", "--label-mode", help="Specifies the label format. ", type=LabelMode,
                        choices=list(LabelMode), default=LabelMode.json_single_file)
    parser.add_argument("-i", "--input-folder", help="Input folder containing images", type=str,
                        default=None)
    parser.add_argument("-o", "--output-folder", help="Output folder for storing labels", type=str,
                        default=None)
    parser.add_argument("-a", "--aspect-ratio", type=int, nargs=2, default=[1,1],
                        help="Constrain width height aspect ratio of box")

    return parser

if __name__ == '__main__':
    parser = arg_parser()
    args = parser.parse_args()

    img_folder = args.input_folder
    label_folder = args.output_folder

    print("STARTUP")
    print("Starting with label mode {}".format(args.label_mode))
    print("Loading images from: %s" % img_folder)
    print("Storing labels to: %s" % label_folder)
    print("STARTED")

    root = Tk()
    tool = LabelTool(root, label_mode=args.label_mode, 
    init_params={"img_folder": img_folder, "label_folder": label_folder, "aspect_ratio": args.aspect_ratio})
    root.resizable(width=True, height=True)
    root.mainloop()
