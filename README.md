\# PDF Region Selector (Windows)



This repository contains a simple Tkinter-based GUI for selecting text regions in PDF files.  

It generates JSON files describing rectangular areas that can be processed by the companion code.



---



\## Overview



\- Open a PDF visually  

\- Draw rectangles over the regions you want to extract  

\- Save coordinates to a JSON file (`<pdfname>\_page<page>.json`)



These JSONs define extraction zones and are later used in Linux to extract and clean text from the same PDF.



---



\## Usage



```bash

python copy\_coordinates.py



Select a PDF file.



Draw one or more rectangles with your mouse.



Click Save JSON when finished.



The JSON files are stored under regions/.



\## Requirements



Python 3.10+

pymupdf pillow

