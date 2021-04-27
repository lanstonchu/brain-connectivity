# Spherical Histogram Approximation for Maximum Flow of Brain Connectivity

 ---------------------------

**Procedures:**

- run `sph_histogram.py` to download data.json
- alternative, hide/unhide some codes in `sph_histogram.py` to read `htmlResponseSample_XXXX_YYYY_ZZZZ.html` instead of using api for quick debugging purpose)
- Visit `localhost:80` to visualize data.json

----------------------------

Spherical Histogram Result at LGd  | Location of LGd
------------- | -------------
![Image 2 - Result at LGd][2]  | ![Image 1 - Location of LGd][1]

 ---------------------------
 **Main Folder Structure:**

     /
     ├──/paper and slide   <-   paper and slide of the project
     ├──/*   <-   other directories for WebGL Library
     |
     ├──/sph_histogram.py   <-   main Python file
     ├──/lines.js   <-   main WebGL file
     ├──/index.html   <-   main Web Page file
     |     
     ├──/download_data.py   <-   to download lines and injection/destination site
     ├──/download_injection_only.py   <-   to download injection/destination site only
     ├──/api.py   <-   to be called by download_*.py
     |          
     ├──htmlResponseSample_XXXX_YYYY_ZZZZ.html   <-   Use this to replace api as sometimes the Allen Institute's server occasionally doesn't work
     ├──data.json   <-   sph_histogram.py/download_data.py Would draw lines in this file; WebGL will call this file.
     ├──Spherical Histogram.nb   <-   3D Spherical Histogram Visualization
     |          
     └──README.md

[1]: https://github.com/lanstonchu/brain-connectivity/blob/main/images/mouse_brain.png
[2]: https://github.com/lanstonchu/brain-connectivity/blob/main/images/lines_LGd.gif
