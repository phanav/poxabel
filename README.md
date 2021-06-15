## Installation
The only external dependeny is PIL.
If you already have PIL, skip this installation and launch the program.
Otherwise
```bash
pip install Pillow
```


## Usage
1. Launch the program
2. If not set at startup, press `I` or click on button `Image input folder` to choose input images dir
3. If not set at startup, press `O` or click on button `Label output folder` to choose output label dir
4. Press `L` or click `Load Dir`. The labeled file directory will automatically created if it does not  exist.
2. To create a new bounding box, left-click to select the first vertex. Moving the mouse to draw a rectangle, and left-click again to select the second vertex.
  - To cancel the bounding box while drawing, just press `<Esc>`.
  - To delete a existing bounding box, select it from the listbox, and click `Delete`.
  - To delete all existing bounding boxes in the image, simply click `ClearAll`.
3. After finishing one image, click `Next` to advance. Likewise, click `Prev` to reverse. Or, input an image id and click `Go` to navigate to the speficied image.
  - Be sure to click `Next` after finishing a image, or the result won't be saved. 
  - press 'p' to go prev image.
  - press 'n' to go next image.

4. If the image doesn't fit on screen, the tool will resizes both the bounding box and image on loading and back again on saving.

5. For multi-class task, modify 'class.txt' with your own class-candidates and before labeling bbox, choose the 'Current Class' in the Combobox and make sure you click `ComfirmClass` button.

6. If the image filename is `foo.var.baz.jpg`, the labeled file name will be `foo.var.baz.txt`, not `foo.txt` .
7. Support multiple image formats: `"*.JPEG", "*.jpeg", "*JPG", "*.jpg", "*.PNG", "*.png", "*.BMP", "*.bmp"`.

Sample run with input and output folder set: 
```bash
python main.py -l json_single_file -i "/home/dobrusii/Project/datasets/refexp_val_objects/refexp_data/images/all" -o "/home/dobrusii/Project/datasets/refexp_val_objects/refexp_data/"

# Alternative
python main.py -l json_single_file -i "/home/dobrusii/Project/datasets/table_objects_dataset/images/all" -o "/home/dobrusii/Project/datasets/table_objects_dataset"
```



Run for custom data set:
```bash
# Activate virtual env e.g. workon bbox_label
python main.py -l json_single_file -i "/vol/data/Documents/Uni/Master/2018-WS/Masterproject/datasets/table_objects_dataset/images/all" -o "/vol/data/Documents/Uni/Master/2018-WS/Masterproject/datasets/table_objects_dataset"
```

This is a fork of [xiaqunfeng/BBox-Label-Tool](https://github.com/xiaqunfeng/BBox-Label-Tool) with some added functionallity:
- Read / write visual genome annotations
- Allow arbitrary labels instead of pre-defined classes.

A simple tool for labeling object bounding boxes in images, implemented with Python Tkinter.

**Screenshot:**
![Label Tool](./example.jpg)

Data Organization
-----------------
LabelTool  
|  
|--main.py   *# source code for the tool*  
|  
|--class.txt   *# your class-candidates file*  
|  
|--Images/   *# direcotry containing the images to be labeled*  
|  
|--Labels/   *# direcotry for the labeling results*  
|  
|--Examples/  *# direcotry for the example bboxes*  

Environment
----------
```
▶ python3 --version
Python 3.6.5
▶ python3
>>> import PIL
>>> PIL.__version__
'4.2.1'
```

Run
-------
```
▶ python3 main.py
3 images loaded from /Users/xiaqunfeng/deeplearning/video_detection/BBox-Label-Tool/Images/001
set label class to : cat
set label class to : dog
Image No. 1 saved
Image No. 2 saved
```


Original  project address: [BBox-Label-Tool](https://github.com/puzzledqs/BBox-Label-Tool)



