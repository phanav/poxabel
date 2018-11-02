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

    def __str__(self):
        return self.value


# colors for the bboxes
COLORS = ['red', 'blue', 'pink', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256

LABEL_MODE = LabelMode.plain
LABEL_FILE_FORMAT = {LabelMode.json: ".json", LabelMode.plain: ".txt"}


class LabelTool():
    def __init__(self, master, label_mode=LabelMode.plain):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.label_mode = label_mode
        self.tkimg = None
        self.currentLabelclass = ''
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

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        # input image dir button
        self.srcDirBtn = Button(self.frame, text="Image input folder", command=self.selectSrcDir)
        self.srcDirBtn.grid(row=0, column=0)
        
        # input image dir entry
        self.svSourcePath = StringVar()
        self.entrySrc = Entry(self.frame, textvariable=self.svSourcePath)
        self.entrySrc.grid(row=0, column=1, sticky=W+E)
        self.svSourcePath.set(os.getcwd())

        # load button
        self.ldBtn = Button(self.frame, text="Load Dir", command=self.loadDir)
        self.ldBtn.grid(row=0, column=2, rowspan=2, columnspan=2, padx=2, pady=2, ipadx=5, ipady=5)

        # label file save dir button
        self.desDirBtn = Button(self.frame, text="Label output folder", command=self.selectDesDir)
        self.desDirBtn.grid(row=1, column=0)

        # label file save dir entry
        self.svDestinationPath = StringVar()
        self.entryDes = Entry(self.frame, textvariable=self.svDestinationPath)
        self.entryDes.grid(row=1, column=1, sticky=W+E)
        self.svDestinationPath.set(os.path.join(os.getcwd(),"Labels"))

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("p", self.prevImage) # press 'p' to go backforward
        self.parent.bind("n", self.nextImage) # press 'n' to go forward
        self.mainPanel.grid(row = 2, column = 1, rowspan = 4, sticky = W+N)

        # choose class
        self.classname = StringVar()
        # self.classcandidate = ttk.Combobox(self.frame, state='readonly', textvariable=self.classname)
        self.classcandidate = ttk.Entry(self.frame, textvariable=self.classname)
        self.classcandidate.grid(row=2, column=2)
        self.currentLabelclass = self.classcandidate.get()
        self.btnclass = Button(self.frame, text='Set label', command=self.setLabel)
        self.btnclass.grid(row=2, column=3, sticky=W+E)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 3, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 22, height = 12)
        self.listbox.grid(row = 4, column = 2, sticky = N+S)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 4, column = 3, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'ClearAll', command = self.clearBBox)
        self.btnClear.grid(row = 4, column = 3, sticky = W+E+S)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 6, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

    def selectSrcDir(self):
        path = filedialog.askdirectory(title="Select image source folder", initialdir=self.svSourcePath.get())
        self.svSourcePath.set(path)
        return

    def selectDesDir(self):
        path = filedialog.askdirectory(title="Select label output folder", initialdir=self.svDestinationPath.get())
        self.svDestinationPath.set(path)
        return

    def loadDir(self):
        self.parent.focus()
        # get image list
        #self.imageDir = os.path.join(r'./Images', '%03d' %(self.category))
        self.imageDir = self.svSourcePath.get()
        if not os.path.isdir(self.imageDir):
            messagebox.showerror("Error!", message = "The specified dir doesn't exist!")
            return

        extlist = ["*.JPEG", "*.jpeg", "*JPG", "*.jpg", "*.PNG", "*.png", "*.BMP", "*.bmp"]
        for e in extlist:
            filelist = glob.glob(os.path.join(self.imageDir, e))
            self.imageList.extend(filelist)
        #self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPEG'))
        if len(self.imageList) == 0:
            print('No .JPEG images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

        # set up output dir
        #self.outDir = os.path.join(r'./Labels', '%03d' %(self.category))
        self.outDir = self.svDestinationPath.get()
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        self.loadImage()
        print('%d images loaded from %s' %(self.total, self.imageDir))

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        size = self.img.size
        self.factor = max(size[0]/1000, size[1]/1000., 1.)
        self.img = self.img.resize((int(size[0]/self.factor), int(size[1]/self.factor)))
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearBBox()
        #self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        fullfilename = os.path.basename(imagepath)
        self.imagename, _ = os.path.splitext(fullfilename)
        labelname = self.imagename + LABEL_FILE_FORMAT[self.label_mode]
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                boxes = []

                # if self.label_mode == LabelMode.json_single:  # Label mode supporting a single json file
                #     pass
                if self.label_mode == LabelMode.json:
                    # TODO: box calculation
                    print("Loading labels from json file")
                    # boxes.append()
                    regions = json.load(f)["regions"]
                    for region in regions:
                        x = region["x"]
                        y = region["y"]
                        w = region["width"]
                        h = region["height"]
                        x_1, y_1, x_2, y_2 = self.xywh_to_xy(x,y,w,h)

                        # Map to this format to ensure compatability with box display GUI code
                        # TODO: Fix rounding errors (also in original code)
                        tmp = [int(x_1/self.factor), int(y_1/self.factor), int(x_2/self.factor), int(y_2/self.factor), region["phrase"]]
                        boxes.append(tmp)

                        # print("Region coordinates with w/h    : x: {}, y: {},  w:{},  h:{}".format(x, y, w, h))
                        # print("Region coordinates in image    : x: {}, y: {}, x2:{}, y2:{}".format(x_1, y_1, x_2, y_2))
                        # print("Region coordinates in GUI coord: x: {}, y: {}, x2:{}, y2:{}".format(tmp[0], tmp[1], tmp[2], tmp[3]))
                else:
                    print("Loading labels from plain text file")
                    for (i, line) in enumerate(f):
                        tmp = line.split()
                        tmp[0] = int(int(tmp[0])/self.factor)
                        tmp[1] = int(int(tmp[1])/self.factor)
                        tmp[2] = int(int(tmp[2])/self.factor)
                        tmp[3] = int(int(tmp[3])/self.factor)
                        boxes.append(tmp)

                for box in boxes:
                    self.bboxList.append(tuple(box))
                    color_index = (len(self.bboxList)-1) % len(COLORS)
                    tmpId = self.mainPanel.create_rectangle(box[0], box[1], \
                                                            box[2], box[3], \
                                                            width = 2, \
                                                            outline = COLORS[color_index])
                                                            #outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' %(box[4], box[0], box[1], box[2], box[3]))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[color_index])

    def saveImage(self):
        if self.labelfilename == '':
            return

        with open(self.labelfilename, 'w') as f:
            if self.label_mode == LabelMode.json:
                regions = []
                for bbox in self.bboxList:
                    x_1 = int(int(bbox[0]) * self.factor)
                    y_1 = int(int(bbox[1]) * self.factor)
                    x_2 = int(int(bbox[2]) * self.factor)
                    y_2 = int(int(bbox[3]) * self.factor)

                    x, y, w, h = self.xy_to_xywh(x_1, y_1, x_2, y_2)

                    label  = bbox[4]

                    region = {
                        "id": str(uuid.uuid4()),
                        "image": self.imagename,
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h,
                        "phrase": label
                    }
                    regions.append(region)
                json.dump({"regions": regions}, f)
            else:
                # f.write('%d\n' %len(self.bboxList))
                for bbox in self.bboxList:
                    f.write("{} {} {} {} {}\n".format(int(int(bbox[0])*self.factor),
                                                    int(int(bbox[1])*self.factor),
                                                    int(int(bbox[2])*self.factor),
                                                    int(int(bbox[3])*self.factor),
                                                      bbox[4]))
                    #f.write(' '.join(map(str, bbox)) + '\n')
        print('Image No. %d saved' %(self.cur))


    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)

            self.bboxList.append((x1, y1, x2, y2, self.currentLabelclass))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' %(self.currentLabelclass, x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))

        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            COLOR_INDEX = len(self.bboxIdList) % len(COLORS)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            event.x, event.y, \
                                                            width = 2, \
                                                            outline = COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
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

    def setLabel(self):
        self.currentLabelclass = self.classcandidate.get()

        # Change label of currently selected box
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        bbox = self.bboxList.pop(idx)
        bbox = (bbox[0], bbox[1], bbox[2], bbox[3], self.currentLabelclass)
        self.bboxList.insert(idx, bbox)

        self.listbox.delete(idx)
        self.listbox.insert(idx, '%s : (%d, %d) -> (%d, %d)' % (self.currentLabelclass, bbox[0], bbox[1], bbox[2], bbox[3]))
        self.listbox.itemconfig(idx, fg=COLORS[(idx-1) % len(COLORS)])

        print('set label class to : %s' % self.currentLabelclass)

    def xy_to_xywh(self, x_1, y_1, x_2, y_2):
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


def arg_parser():
    parser = argparse.ArgumentParser("BBox Tool GUI")
    parser.add_argument("-l", "--label-mode", help="Specifies the label format. ", type=LabelMode, choices=list(LabelMode), default=LabelMode.plain)

    # TODO: Add abbility to read and write annontations from single json file (similar to Visual Genome)
    # TODO: Add folder parameter for label and image folder

    return parser


if __name__ == '__main__':
    parser = arg_parser()
    args = parser.parse_args()

    print("Starting with label mode {}".format(args.label_mode))

    root = Tk()
    tool = LabelTool(root, label_mode=args.label_mode)
    root.resizable(width =  True, height = True)
    root.mainloop()
