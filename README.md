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

`-i inputdir` -> specify input image folder. Default = current working directory

`-o outputdir` -> specify output image folder. Annotation will be in a file `$inputdir-region.json` in this output folder. Default = folder Labels in current working directory

`-a width height` -> constrain width to height aspect ratio. Default = 1 1. Change either to 0 for unconstrained.

```bash
python poxabel.py -i "path/input" -o "path/output" -a 1 1 
```

## Usage
1. Launch the program
2. If not set at startup, press `I` or click on button `Image input folder` to choose input images dir
3. If not set at startup, press `O` or click on button `Label output folder` to choose output label dir
4. Press `L` or click `Load Dir` to load input images.

5. Left-click to create the first corner of the region. Moving the mouse to draw a rectangle, and left-click again to create the second corner.
  - Press `<BackSpace>` to cancel the bounding box you are currently drawing.
  - Select one region from the listbox, and press or click `Delete` to remove it. Delete without selection will delete the last bounding box.
  - Click `ClearAll` to remove all bounding boxes of the current image.

6. Press `RightArrow` or click `Next` to advance. 

Press `LeftArrow` or click `Prev` to reverse. 

Or, input an image number and click `Go` to navigate to the speficied image.

**Caveat**: Annotations are saved only after moving to another image. After finishing the last image, there is no more to load next. However, you still need to go next, or previous, to save the last annotation. 

7. If the image doesn't fit on screen, the tool will resizes both the bounding box and image on loading and back again on saving.

8. For multi-class task, modify 'class.txt' with your own class-candidates and before labeling bbox, choose the 'Current Class' in the Combobox and make sure you click `ComfirmClass` button.

9. Retrieve the annotation files from output dir

## Rectify
While drawing the regions, navigating to any previously annotated images will load your previous annotations.
You can delete a saved bounding box and draw a new one.

## Review
Keep related annotation output files in the same folder for easier reloading.

Suppose you finish annotating all images in input dir `inputpath/apple`. Annotations are saved in `apple-region.json` inside `outputpath/Labels`.

Now, you press `I` and change input folder to `inputpath/orange`. Annotations are saved in `orange-region.json` inside `outputpath/Labels`.

To review apple annotations, switch input dir back to `inputpath/apple`. Leave output dir as `outputpath/Labels`.
You can then review and rectify the previous apple annotations.

## Resume
Suppose you interrupt annotation at orange image 10/20.
Note the image number, the input dir and output dir.

To resume, start the program again with the same input dir and output dir, then jump to image number 10. Use the navigation at the bottom.


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

<br>
Support multiple image formats: `"*.JPEG", "*.jpeg", "*JPG", "*.jpg", "*.PNG", "*.png", "*.BMP", "*.bmp"`.
<br><br>
This is a fork of https://github.com/idobrusin/BBox-Label-Tool

A simple tool for labeling object bounding boxes in images, implemented with Python Tkinter.
