import cv2 
import numpy as np
import sys
import time

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class VideoThread(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self):
        super(QThread, self).__init__()
        self.parms={    } # TODO: add area treshold, limit
        self.mode = 0
        self.min_obj_distance = 9999
        self.min_obj_x = 0
        self.min_obj_y = 0
        self.min_obj_angel = 0
        self.w = 1280
        self.h = 960
        self.cam = 0
        self.crosshair_color = (0, 255, 255)
        self.flip = False
        self.real_w = 0
        self.real_h = 0
        self.cap = None


    def openVideo(self):
        self.cap = cv2.VideoCapture(self.cam) # cv2.CAP_V4L on jetson
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,self.w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,self.h)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE,1)   # disable auto belichtung

    def run(self):

        # disable auto exposure
        # sven@sven-desktop:~$ v4l2-ctl -d /dev/video1  --set-ctrl exposure_auto=1
        # sven@sven-desktop:~$ v4l2-ctl -d /dev/video0  --set-ctrl exposure_auto=1

        # now can Set manual
        # v4l2-ctl -d /dev/video0  --set-ctrl exposure_absolute=1000 

        # print("sys.platform",sys.platform)

        '''
        4K TopCam
		Size: Discrete 1600x1200			Interval: Discrete 0.067s (15.000 fps)
		Size: Discrete 3264x2448			Interval: Discrete 0.067s (15.000 fps)
		Size: Discrete 2592x1944			Interval: Discrete 0.067s (15.000 fps)
		Size: Discrete 2048x1536			Interval: Discrete 0.067s (15.000 fps)
		Size: Discrete 1280x960			    Interval: Discrete 0.067s (15.000 fps)
		Size: Discrete 1024x768			    Interval: Discrete 0.033s (30.000 fps)
		Size: Discrete 800x600			    Interval: Discrete 0.033s (30.000 fps)
		Size: Discrete 640x480			    Interval: Discrete 0.033s (30.000 fps)
		Size: Discrete 320x240			    Interval: Discrete 0.033s (30.000 fps)
		Size: Discrete 1600x1200			Interval: Discrete 0.067s (15.000 fps)


        4K BottomCam
		Size: Discrete 1280x720			Interval: Discrete 0.100s (10.000 fps)
		Size: Discrete 640x480			Interval: Discrete 0.033s (30.000 fps)
		Size: Discrete 352x288			Interval: Discrete 0.033s (30.000 fps)
		Size: Discrete 320x240			Interval: Discrete 0.033s (30.000 fps)
		Size: Discrete 176x144			Interval: Discrete 0.033s (30.000 fps)
		Size: Discrete 160x120			Interval: Discrete 0.033s (30.000 fps)
		Size: Discrete 800x600			Interval: Discrete 0.050s (20.000 fps)
		Size: Discrete 960x720			Interval: Discrete 0.067s (15.000 fps)
        '''






        self.cap.set(cv2.CAP_PROP_EXPOSURE,self.parms["expose"])

        #while True:

        self.min_obj_distance = 9999
        ret, frame = self.cap.read()
            
        if ret:
            # https://stackoverflow.com/a/55468544/6622587
            
            if self.flip:
                frame = cv2.flip(frame, 0)
            
            rgbImage2=self.searchForRectangles(frame)

            rgbImage = cv2.cvtColor(rgbImage2, cv2.COLOR_BGR2RGB)
            h, w, ch = rgbImage.shape

            #print("rgbImage",w,h,self.flip)

            self.real_w = w
            self.real_h = h

            self.draw_crosshair(rgbImage,w,h)
            bytesPerLine = ch * w
            convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
            p = convertToQtFormat.scaled(1280, 960, Qt.KeepAspectRatio)
            self.changePixmap.emit(p)

    def draw_crosshair(self,frame,w,h): #fadenkreuz, absehen
        cv2.line(img=frame, pt1=(0, int(h/2)), pt2=(w, int(h/2)), color=self.crosshair_color , thickness = 1, lineType = 8, shift = 0)
        cv2.line(img=frame, pt1=(int(w/2), 0), pt2=(int(w/2), h), color=self.crosshair_color , thickness = 1, lineType = 8, shift = 0)
        lines = 32
        for x in range(lines):
            cv2.line(img=frame, pt1=(int(w/lines*x), int(h/2-10) ), pt2=(int(w/lines*x), int(h/2+10) ), color=self.crosshair_color , thickness = 1, lineType = 8, shift = 0)
            cv2.line(img=frame, pt1=(int(w/2-10), int(h/lines*x) ), pt2=( int(w/2+10), int(h/lines*x) ), color=self.crosshair_color , thickness = 1, lineType = 8, shift = 0)

        if(self.flip):
            cv2.circle(img=frame, center=(int(w/2), int(h/2) ), radius=100, color=self.crosshair_color, thickness = 1)

        return frame

    def stackImages(self,scale,imgArray):
        rows = len(imgArray)
        cols = len(imgArray[0])
        rowsAvailable = isinstance(imgArray[0], list)
        width = imgArray[0][0].shape[1]
        height = imgArray[0][0].shape[0]
        if rowsAvailable:
            for x in range ( 0, rows):
                for y in range(0, cols):
                    if imgArray[x][y].shape[:2] == imgArray[0][0].shape [:2]:
                        imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                    else:
                        imgArray[x][y] = cv2.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]), None, scale, scale)
                    if len(imgArray[x][y].shape) == 2: imgArray[x][y]= cv2.cvtColor( imgArray[x][y], cv2.COLOR_GRAY2BGR)
            imageBlank = np.zeros((height, width, 3), np.uint8)
            hor = [imageBlank]*rows
            hor_con = [imageBlank]*rows
            for x in range(0, rows):
                hor[x] = np.hstack(imgArray[x])
            ver = np.vstack(hor)
        else:
            for x in range(0, rows):
                if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                    imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
                else:
                    imgArray[x] = cv2.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None,scale, scale)
                if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
            hor= np.hstack(imgArray)
            ver = hor
        return ver
    #def angle_between(self, p1, p2):
    #    ang1 = np.arctan2(*p1[::-1])
    #    ang2 = np.arctan2(*p2[::-1])
    #    return np.rad2deg((ang1 - ang2) % (2 * np.pi))

            
    def subimage(self, image, center, theta, width, height):
       ''' 
       https://stackoverflow.com/questions/11627362/how-to-straighten-a-rotated-rectangle-area-of-an-image-using-opencv-in-python
       Rotates OpenCV image around center with angle theta (in deg)
       then crops the image according to width and height.
       call it as: image = subimage(image, center=(110, 125), theta=30, width=100, height=200)
       '''

       # Uncomment for theta in radians
       #theta *= 180/np.pi
       shape = ( image.shape[1], image.shape[0] ) # cv2.warpAffine expects shape in (length, height)
       matrix = cv2.getRotationMatrix2D( center=center, angle=theta, scale=1 )
       image = cv2.warpAffine( src=image, M=matrix, dsize=shape )
       x = int( center[0] - width/2  )
       y = int( center[1] - height/2 )
       image = image[ y:y+height, x:x+width ]
       return image   
    
    def searchForRectangles(self, frame0):

        #use cv2.flip(frame,1) -> spiegelt für BottomCam Später und Overlayzu bauen auf PCB

        parms=self.parms

        ks = parms['kernel'] 
        kernel = np.ones((ks,ks),np.uint8)

        imgHSV      = cv2.cvtColor(frame0,cv2.COLOR_BGR2HSV)
        imgHSV2     = cv2.GaussianBlur(imgHSV,(parms['gauss_v1'],parms['gauss_v2']),cv2.BORDER_DEFAULT)
        lower       = np.array([parms['h_min'],parms['s_min'],parms['v_min']])
        upper       = np.array([parms['h_max'],parms['s_max'],parms['v_max']])
        mask        = cv2.inRange(imgHSV2,lower,upper)
       # mask        = cv2.bitwise_not(mask)

        imgResult   = cv2.bitwise_and(frame0,frame0,mask=mask)
        gray2       = cv2.cvtColor(imgResult, cv2.COLOR_BGR2GRAY) 
        gray        = cv2.GaussianBlur(gray2,(parms['gauss_v1'],parms['gauss_v2']),cv2.BORDER_DEFAULT)
        edged       = cv2.Canny(gray, parms['canny_thrs1'], parms['canny_thrs2'],7) 
        imgDilation = cv2.dilate(edged, kernel, iterations = parms['dilate_count'])    
        imgEroded   = cv2.erode(imgDilation, kernel, iterations = parms['erode_count'])

        contours, hierarchy = cv2.findContours(imgEroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) 

        cnt_rects = 0
        cnt_rects2 = 0
        boxes = []
        apdb = 1.0 / (parms['a_fac']+1)
        imgContour = frame0.copy()    
        
        angle= 0.0
        
        objNumber=0

        for contour in contours:
            # https://stackoverflow.com/questions/34237253/detect-centre-and-angle-of-rectangles-in-an-image-using-opencv/34285205
            myarea = cv2.contourArea(contour)
            if myarea > (parms['a_min'] * parms['a_min']) and myarea < (parms['a_max'] * parms['a_max']) :
                cv2.drawContours(imgContour, contour, -1, (0, 0, 200), 3)
                peri = cv2.arcLength(contour,True)
                approx = cv2.approxPolyDP(contour, apdb * peri,True)
                alpha = 0
                cX=0
                cY=0

                #print("len approx", len(approx))

                if( len(approx) == 4 or len(approx) == 11 ): # 11= SOT363
                    M = cv2.moments(approx)

                    objNumber+=1

                    if(M["m00"] > 0): # avoid div/0 again
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        cv2.circle(imgContour, (cX, cY), 12, (0, 255, 0), -1)
                        
                    # draw min Rect rotated
                    rect = cv2.minAreaRect(approx)
                    
                    # https://www.pyimagesearch.com/2017/02/20/text-skew-correction-opencv-python/
                    angle = rect[-1]
                    if angle < -45: angle = -(90 + angle)
                    else:           angle = -angle
                        
                        
                    # TODO eval rotation by max(w),max(h)
                    
                    # Just for visual
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    cv2.drawContours(imgContour,[box],0,(0,128,255),2)                
                    
                    cv2.drawContours(imgContour, approx, -1, (0, 0, 255), 20)
                    objCor = len(approx)    # Kanten anzahl
                    x1, y1, w1, h1 = cv2.boundingRect(approx)
                    cv2.putText(imgContour, str(objNumber) + ' ' + str(round(angle,1)) + ' ' + str(cX) + ' ' + str(cY)
                                , (x1,y1), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2, cv2.LINE_AA)
                
                    # compute shortest Part
                    fh, fw, fch = frame0.shape
                    distance_x = abs(cX-fw/2.0)
                    distance_y = abs(cY-fh/2.0)
                    distance_to_center = cv2.sqrt(distance_x*distance_x + distance_y*distance_y)[0][0]
                    #print(distance_x,distance_y,distance_to_center)

                    if self.min_obj_distance > distance_to_center:
                        self.min_obj_x = cX
                        self.min_obj_y = cY
                        self.min_obj_angel = round(angle,1)
                        self.min_obj_distance = distance_to_center

                    # check orientation , real size
                    #        (x,y,w,h) = cv2.boundingRect(contour)
                    #        if(w > 50 and w <500 and h < w * 0.6 and h > w * 0.4  ):
                    #            boxes.append([x, y, w, h])
                    #            cnt_rects+=1
                    #        else:
                    #            cnt_rects2+=1

        
        if self.mode==4 :

            # simg = self.subimage(frame0, center=(512, 384), theta=30, width=512, height=384)

            imgstack = self.stackImages(0.3, (  [edged,         frame0,  mask],
                                                [imgContour,    imgHSV2, imgEroded] ) )
            return imgstack
        else: 

            return imgContour


        #cv2.imshow('nanoCam',imgstack)
        
        #imgContour2 = cv2.resize(imgContour, (1024, 768))
        #cv2.imshow('nanoCam2',imgContour2)
        
        
        #mykey = cv2.waitKey(1)
        #if(mykey == ord('q')): break
        #if(mykey == ord('p')):
        #    plt.imshow(imgstack)
        #    plt.show()
        #    plt.imshow(imgContour)
        #    plt.show()
        