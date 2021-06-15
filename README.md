## Screenshot
![poxabel](./example.jpg)

## Installation
The only external dependeny is PIL.
If you already have PIL, skip this installation and launch the program.
Otherwise
```bash
pip install Pillow
```

## Launch
```bash
python poxabel.py
```
Optional command line argument

`-i` inputdir -> specify input image folder. Default = current working directory

`-o` outputdir -> specify output image folder. Annotation will be in a file `$iputdir-region.json` in this output folder. Default = folder Labels in current working directory

`-à` width height -> constrain width to height aspect ratio

```bash
python poxabel.py -i "path/input" -o "path/output" -a 1 1 
```

## Usage
1. Launch the program
2. If not set at startup, press `I` or click on button `Image input folder` to choose input images dir
3. If not set at startup, press `O` or click on button `Label output folder` to choose output label dir
4. Press `L` or click `Load Dir` to load input images.

5. Left-click to create the first corner of the region. Moving the mouse to draw a rectangle, and left-click again to create the second corner.
  - To cancel the bounding box while drawing, just press `<BackSpace>`.
  - To delete an existing bounding box, select from the listbox, and press or click `Delete`. Delete without selection will delete the last bounding box.
  - To delete all existing bounding boxes in the image, simply click `ClearAll`.

6. Press `RightArrow` or click `Next` to advance. Press `LeftArrow` or click `Prev` to reverse. Or, input an image number and click `Go` to navigate to the speficied image.

**Caveat**: Annotations are saved only after moving to another image. After finishing the last image, there is no more to load next. However, you still need to go next, or previous, to save the last annotation. 

7. If the image doesn't fit on screen, the tool will resizes both the bounding box and image on loading and back again on saving.

8. For multi-class task, modify 'class.txt' with your own class-candidates and before labeling bbox, choose the 'Current Class' in the Combobox and make sure you click `ComfirmClass` button.

7. Support multiple image formats: `"*.JPEG", "*.jpeg", "*JPG", "*.jpg", "*.PNG", "*.png", "*.BMP", "*.bmp"`.

<br><br>
This is a fork of https://github.com/idobrusin/BBox-Label-Tool

A simple tool for labeling object bounding boxes in images, implemented with Python Tkinter.


Repository Structure
-----------------
poxabel  
|  
|--poxabel.py   *# source code for the tool*  
|  
|--class.txt   *# your class-candidates file*  
|  
|--Images/   *# sample image directory *  
|  
|--Labels/   *# annotation output directory*  


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
