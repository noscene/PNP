import cv2 


from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class VideoThread(QThread):
    changePixmap = pyqtSignal(QImage)

    def setImageToGUI(self, image):
        self.myVideoFrame.setPixmap(QPixmap.fromImage(image))

    def run(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if ret:
                # https://stackoverflow.com/a/55468544/6622587
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgbImage.shape
                self.draw_crosshair(rgbImage,w,h)
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(1024, 768, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)

    def draw_crosshair(self,frame,w,h): #fadenkreuz, absehen
        cv2.line(img=frame, pt1=(0, int(h/2)), pt2=(w, int(h/2)), color=(0, 255, 255), thickness = 2, lineType = 8, shift = 0)
        cv2.line(img=frame, pt1=(int(w/2), 0), pt2=(int(w/2), h), color=(0, 255, 255), thickness = 2, lineType = 8, shift = 0)
        lines = 32
        for x in range(lines):
            cv2.line(img=frame, pt1=(int(w/lines*x), int(h/2-10) ), pt2=(int(w/lines*x), int(h/2+10) ), color=(0, 255, 255), thickness = 2, lineType = 8, shift = 0)
            cv2.line(img=frame, pt1=(int(w/2-10), int(h/lines*x) ), pt2=( int(w/2+10), int(h/lines*x) ), color=(0, 255, 255), thickness = 2, lineType = 8, shift = 0)
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
    def angle_between(self, p1, p2):
        ang1 = np.arctan2(*p1[::-1])
        ang2 = np.arctan2(*p2[::-1])
        return np.rad2deg((ang1 - ang2) % (2 * np.pi))

            
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