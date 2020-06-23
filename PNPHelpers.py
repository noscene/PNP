import time
import copy
import cv2
import math
import numpy as np

scale = 3.0   # just for test zoom, should be 1.0
base = 720     # this is screen height, need to flip cords
# https://stackoverflow.com/questions/456481/cant-get-python-to-import-from-a-different-folder
#class PNPPoint(): # just a helper to handle points
#    def __init__(self,x,y):
#        self.x_mm = x 
#        self.y_mm = y 


class Point():
    def __init__(self,x,y):
        self.x = float(x)
        self.y = float(y)
        #print("Point",x,y)

class PNPImageBase(): # just a helper to draw smd parts, panels etc on opencv window
    #scale = 3.0
    # base = 720
    def __init__(self):
        pass

    def drawRect(self,img,x,y,w,h,color,width):
        p1 = (int(x * self.scale),int(self.base - y * self.scale ))
        p2 = (int((x+w) * self.scale),int(self.base-((y+h) * self.scale )))
        cv2.rectangle(img,p1 ,p2 , color, width)
    def drawCenterRect(self,img,xi,yi,wi,hi,rotation,color,width):
        w_temp = wi
        h_temp = hi
        w=w_temp
        h=h_temp
        if(rotation==90 or rotation==270):
            h=w_temp
            w=h_temp
        x = xi-w/2
        y = yi-h/2  
        p1 = (int(x * self.scale),int(self.base - y * self.scale ))
        p2 = (int((x+w) * self.scale),int(self.base-((y+h) * self.scale )))
        cv2.rectangle(img,p1 ,p2 , color, width)
    def drawText(self,img,x,y,text,color, size):
        p1 = ( int(x * self.scale), int(self.base - y * self.scale) )
        cv2.putText(img, text, p1 , cv2.FONT_HERSHEY_SIMPLEX, size, color, 1, cv2.LINE_AA)
        
class PNPVision():
    def __init__(self):
        self.info = 'i am a vision class'

class PNPFootprint(): # just use a dictionary to hold data
    def __init__(self,parms):
        self.parms = parms

class PNPNozzle():  # nozzle on head with delta positon and footprintList
    def __init__(self,x,y,foodprints):
        self.x_pos_delta_cam_mm = x  # 45.0 
        self.y_pos_delta_cam_mm = y  # 36.0         
        self.foodprints = foodprints # 36.0         
        #print(foodprints)

class PNPHead():
    def __init__(self,vision,nozzles):
        self.nozzles = nozzles
        self.vision  = vision

class PNPPart():    
    def __init__(self,name,x,y,r,foodprint,value):
        self.name = name
        self.x = x # x pos
        self.y = y # y pos
        self.r = r # rotation
        self.foodprint = foodprint # 36.0
        self.value = value
    def __getitem__(self,key):
        #print ("Inside `__getitem__` method!")
        return getattr(self,key)
class PNPSinglePcb():
    def __init__(self,parts,w,h,fiducial1,fiducial2):
        self.parts = parts 
        self.w = w 
        self.h = h 
        self.toPlace = True
        self.fiducial1 = fiducial1 # names
        self.fiducial2 = fiducial2 # names
        self.number = 0

class PNPPcbPannel(PNPImageBase):
    def __init__(self,pcb,x,y,layout):
        #self.pcb = pcb # TODO: make this as array
        self.scale = 3.0
        self.base = 720
        self.x = x              # orgin fix
        self.y = y              # orgin fix
        self.layout = layout    # (x_xount, y_count)
        self.pcbs  = [[0 for x in range(self.layout[0])] for y in range(self.layout[1])]
        cnt=0
        for ty in range(self.layout[1]):
            for tx in range(self.layout[0]):
                self.pcbs[ty][tx] = copy.deepcopy(pcb)
                self.pcbs[ty][tx].number=cnt
                cnt+=1 # eindeutig numerieren
    def drawPcbs(self,img,footprints):
        for ty in range(self.layout[1]):
            for tx in range(self.layout[0]):
                pcb = self.pcbs[ty][tx]
                xpos = tx * pcb.w + self.x
                ypos = ty * pcb.h + self.y
                w = pcb.w 
                h = pcb.h 
                self.drawRect(img,xpos,ypos,w,h,(0,0,128), 2)
                self.drawText(img,xpos-1,ypos-2,str(pcb.number),(0,255,0), 0.7)
                for p in pcb.parts:
                    px = xpos + p.x
                    py = ypos + p.y
                    # print([self.pcb.fiducial1,self.pcb.fiducial2])
                    if p.name in [pcb.fiducial1,pcb.fiducial2]:
                        self.drawCenterRect(img,px,py,1,1,p.r,(255,255,0), 3) # draw fiducial
                    elif p.foodprint in footprints:
                        fp = footprints[p.foodprint].parms
                        # print(fp)
                        self.drawCenterRect(img,px,py,fp['x'],fp['y'],p.r,(128,128,128), 1)
                        self.drawText(img,px,py,p.name,(0,255,255), self.scale * 0.05)
                    else:
                        self.drawCenterRect(img,px,py,2,2,p.r,(255,0,0), 3) # draw missing footprint
                    
                
class PNPFeeder():
    def __init__(self,typ,x,y,w,h): # typ und Position
        self.typ = typ
        self.x   = x
        self.y   = y
        self.w   = w
        self.h   = h
        self.footprint = None # e.g. 'C0603'
        self.value = None     # e.g. '10uF'
    def setConfig(self,footprint,value):
        self.footprint = footprint
        self.value = value
        
class PNPFeederSet(PNPImageBase):
    def __init__(self,typ,x,y,feeders): # typ und Position
        self.typ       = typ
        self.x         = x
        self.y         = y
        self.feeders   = feeders
    def drawTrays(self,img):
        cnt=0
        for t in self.feeders:
            xpos = self.x + t.x
            ypos = self.y + t.y
            self.drawRect(img,xpos,ypos,t.w,t.h,(0,255,0), 2)
            self.drawText(img,xpos+2,ypos+2,str(cnt),(0,255,0), self.scale * 0.1)
            if(t.value): 
                self.drawText(img,xpos+2,ypos+5, t.value,(255,255,255), self.scale * 0.1)
            cnt+=1
                
# PNPPcbPannel -> PNPSinglePcb -> PNPPart(s) -> PNPFootprint
# PNPHead -> PNPNozzle -> PNPFootprint(s)
      
#pcb = pannel.pcbs[0][0]
#my_id0 = list(filter(lambda p: p['name'] == 'C14', pcb.parts))[0]
#my_fd0 = list(filter(lambda p: p['name'] == pcb.fiducial1, pcb.parts))[0]
#my_fd1 = list(filter(lambda p: p['name'] == pcb.fiducial2, pcb.parts))[0]
#print ( my_fd0.x, my_fd0.y)
#print ( my_fd1.x, my_fd1.y)
#print ( my_id0.x, my_id0.y, my_id0.r, my_id0.foodprint)
#c = convertRect(my_fd0,my_fd1,my_id0)
#m.driveto((c[0],c[1]))

# thx @flo ;-)
def convertRect(my_fd0,my_fd1,my_id0, 
                r_fd0_x = 68.1, r_fd0_y = 54.9,
                r_fd1_x = 31.2, r_fd1_y = 87.0):
     # X68.1 Y54.9
     #X31.2 Y87.0
    

    # SCHRITT 1: Hilfswerte Berechnen
    # Distanz A-B
    abDistance1 = math.sqrt( (my_fd1.x - my_fd0.x) * (my_fd1.x - my_fd0.x) + 
                             (my_fd1.y - my_fd0.y) * (my_fd1.y - my_fd0.y) )
    #print('abDistance1' , abDistance1)

    # Mitte des Rects
    middle1_x = my_fd0.x + ((my_fd1.x - my_fd0.x) / 2.0)
    middle1_y = my_fd0.y + ((my_fd1.y - my_fd0.y) / 2.0)
    #print('middle1' , middle1_x,middle1_y)

    # SCHRITT 2: Rect1 (A, B & P) auf lokales Koordinatensystem umrechnen
    r1Local_a_x = my_fd0.x - middle1_x
    r1Local_a_y = my_fd0.y - middle1_y
    r1Local_b_x = my_fd1.x - middle1_x
    r1Local_b_y = my_fd1.y - middle1_y
    r1Local_p_x = my_id0.x - middle1_x
    r1Local_p_y = my_id0.y - middle1_y
    #print('r1Local a' , r1Local_a_x,r1Local_a_y)
    #print('r1Local b' , r1Local_b_x,r1Local_b_y)
    #print('r1Local p' , r1Local_p_x,r1Local_p_y)

    # SCHRITT 3: Winkel zwischen P & A berechnen
    angle1 = math.atan2(r1Local_p_y, r1Local_p_x) - math.atan2(r1Local_a_y, r1Local_a_x)
    #Länge von Mitte zu P berechnen
    pLength1 = math.sqrt((r1Local_p_x * r1Local_p_x) + (r1Local_p_y * r1Local_p_y))
    angle_grad =  angle1 * (180.0 / math.pi)
    print('angle1 p' , angle_grad )

    #print('pDistance1' , pLength1 )

    #SCHRITT 4: Wiederhole 1 & 2 mit Ziel-Rect, ohne Punkt P
    #Distanz A-B
    abDistance2 = math.sqrt( (r_fd1_x - r_fd0_x) * (r_fd1_x - r_fd0_x) + (r_fd1_y - r_fd0_y) * (r_fd1_y - r_fd0_y))
    #print('abDistance2' , abDistance2 )

    #Mitte des Rects
    middle2_x = r_fd0_x + ((r_fd1_x - r_fd0_x) / 2.0)
    middle2_y = r_fd0_y + ((r_fd1_y - r_fd0_y) / 2.0)
    #print('middle2' , middle2_x,middle2_y )

    # Rect2 (A & B) auf lokales Koordinatensystem umrechnen
    r2Local_a_x = r_fd0_x - middle2_x
    r2Local_a_y = r_fd0_y - middle2_y
    r2Local_b_x = r_fd1_x - middle2_x
    r2Local_b_y = r_fd1_y - middle2_y
    #print('r2Local a' , r2Local_a_x,r2Local_a_y )
    #print('r2Local b' , r2Local_b_x,r2Local_b_y )

    # SCHRITT 5: Richtungsvektor für P2 berechnen
    p2Direction_x = r2Local_a_x * math.cos(angle1) - r2Local_a_y * math.sin(angle1)
    p2Direction_y = r2Local_a_x * math.sin(angle1) + r2Local_a_y * math.cos(angle1)
    # in Einheitsvektor (Länge 1) umwandeln
    pLength2 = math.sqrt((p2Direction_x * p2Direction_x) + (p2Direction_y * p2Direction_y))
    p2Direction_x = p2Direction_x / pLength2
    p2Direction_y = p2Direction_y / pLength2

    # SCHRITT 6: Länge des P-Vektors anpassen
    # Skalierung von Rect1 zu Rect 2 berechnen
    scaleFactor = abDistance2 / abDistance1

    #P2-Richtungsvektor mit ursprünglicher Länge und Skalierung multiplizieren
    p2_x = p2Direction_x * pLength1 * scaleFactor
    p2_y = p2Direction_y * pLength1 * scaleFactor
    # SCHRITT 7: P in ursprüngliches Koordinatensystem zurückrechnen
    p2_x = middle2_x + p2_x
    p2_y = middle2_y + p2_y

    print('r2Local b' , p2_x,p2_y )    
    return (p2_x,p2_y,angle_grad)
