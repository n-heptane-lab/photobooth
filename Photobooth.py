#!/usr/bin/env python3
from time import sleep
from picamera import PiCamera
# form Image import
import paho.mqtt.client as mqtt
from queue import Queue, Empty
from threading import Thread
from enum import Enum
from PIL import Image
import datetime
import time
import os

class Mode(Enum):
    SLIDESHOW = 1
    PREVIEW   = 2
    REVIEW    = 3

monitor_res = (640,480)
res = (2592,1944)
camera = PiCamera(resolution=res, framerate=15)
print("max resolution = " + str(camera.MAX_RESOLUTION))
camera.vflip = True
camera.hflip = True
#camera.awb_mode = 'off'
#camera.awb_gains=(1.0, 2.0)
camera.exposure_mode = 'auto'
#camera.shutter_speed = 1000000
g = camera.awb_gains
print ('awb_gains = '+ str(g))
##camera.awb_mode = 'off'
##camera.awb_gains = g
# camera.image_effect='sketch';
eventQ = Queue(maxsize=0)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("photobooth")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("on_message start")
    eventQ.put(msg);
    print("on_message end")

#    camera.start_preview()
#    sleep(1)
#    camera.capture('foo.jpg')

def slideshow_timer(q):
    while True:
        msg = mqtt.MQTTMessage("photobooth")
        msg.payload = b'next'
        q.put(msg)
        sleep(5)

def handle_event(q):
    mode = Mode.SLIDESHOW
    three_png = Image.open('3.png')    
    three = Image.new('RGB',
        (((three_png.size[0] + 31) // 32) * 32,
         ((three_png.size[1] + 15) // 16) * 16,
        ))
    three.paste(three_png, (0, 0))    
    two_png = Image.open('2.png')
    two = Image.new('RGB',
        (((two_png.size[0] + 31) // 32) * 32,
         ((two_png.size[1] + 15) // 16) * 16,
        ))
    two.paste(two_png, (0, 0))        
    one_png = Image.open('1.png')
    one = Image.new('RGB',
        (((one_png.size[0] + 31) // 32) * 32,
         ((one_png.size[1] + 15) // 16) * 16,
        ))
    one.paste(one_png, (0, 0))        

    take_photo_png = Image.open("take-photo.png")
    take_photo = Image.new('RGB',
        (((take_photo_png.size[0] + 31) // 32) * 32,
         ((take_photo_png.size[1] + 15) // 16) * 16,
        ))
    take_photo.paste(take_photo_png, (0, 0))        
    take_photo_o = None;
    
    approve_reject_png = Image.open("approve-reject.png")
    approve_reject = Image.new('RGB',
        (((approve_reject_png.size[0] + 31) // 32) * 32,
         ((approve_reject_png.size[1] + 15) // 16) * 16,
        ))
    approve_reject.paste(approve_reject_png, (0, 0))        
    approve_reject_o = None;

    
#    review = Image.new('RGB', res);
    review_o = None;
    filename = ""


    
    slideshow_files = [f for f in os.listdir("approve") if f.endswith('.jpg')]
    slideshow_index = 0
    slideshow_o = None;
    while True:
        msg = q.get()

        if mode == Mode.SLIDESHOW and msg.payload == b'preview':
            print("PREVIEW")            
            mode = Mode.PREVIEW
            if slideshow_o != None:
                camera.remove_overlay(slideshow_o)
                slideshow_o = None;

            take_photo_o = camera.add_overlay(take_photo.tobytes(), size=take_photo.size)
            take_photo_o.alpha=128
            take_photo_o.layer=3
            take_photo_o.fullscreen = False;
            take_photo_o.window=((monitor_res[0]-512)//2, monitor_res[1]-96,512,96)
                
            camera.start_preview(fullscreen=True)
            
        if mode == Mode.SLIDESHOW and msg.payload == b'next':
            print("NEXT")
            slideshow_index = slideshow_index + 1
            if slideshow_index >= len(slideshow_files):
                slideshow_index = 0
            if slideshow_o != None:
                camera.remove_overlay(slideshow_o)
            slideshow_jpg = Image.open("approve/"+slideshow_files[slideshow_index])
            slideshow_o = camera.add_overlay(slideshow_jpg.tobytes(), size=slideshow_jpg.size)
            slideshow_o.alpha=255
            slideshow_o.layer=3
            
        elif mode == Mode.PREVIEW and msg.payload == b'shutter':
            print("SHUTTER");
            if (take_photo_o != None):
                camera.remove_overlay(take_photo_o)
                take_photo_o = None
            o = camera.add_overlay(three.tobytes(), size=three.size)
            o.alpha = 32
            o.layer = 3
            sleep(1)
            camera.remove_overlay(o);
            o = camera.add_overlay(two.tobytes(), size=two.size)
            o.alpha = 32
            o.layer = 3
            sleep(1)
            camera.remove_overlay(o);
            o = camera.add_overlay(one.tobytes(), size=one.size)
            o.alpha = 32
            o.layer = 3
            sleep(1)
            camera.remove_overlay(o);
            filename = datetime.datetime.fromtimestamp(time.time()).strftime('photobooth-%Y-%m-%d-%H:%M:%S.jpg')
            print(filename)
            camera.capture(filename);
            camera.stop_preview();
            print("REVIEW")
            
            review_jpg = Image.open(filename)
            review_o = camera.add_overlay(review_jpg.tobytes(), size=review_jpg.size)
            review_o.alpha=255
            review_o.layer=1

            approve_reject_o = camera.add_overlay(approve_reject.tobytes(), size=approve_reject.size)
            approve_reject_o.alpha=128
            approve_reject_o.layer=2
            approve_reject_o.fullscreen = False;
            approve_reject_o.window=((monitor_res[0]-512)//2, monitor_res[1]-96,512,96)
            mode = Mode.REVIEW
            
        elif mode == Mode.REVIEW and msg.payload == b'approve':
            print("APPROVED")
            if approve_reject_o != None:
                camera.remove_overlay(approve_reject_o)
                approve_reject_o = None
            camera.remove_overlay(review_o);
            os.rename(filename, "approve/"+filename);
            slideshow_files.append(filename);
            filename = ""
            print("SLIDESHOW")
            mode = Mode.SLIDESHOW
        elif mode == Mode.REVIEW and msg.payload == b'reject':
            print("REJECTED")
            if approve_reject_o != None:
                camera.remove_overlay(approve_reject_o)
                approve_reject_o = None
            camera.remove_overlay(review_o);            
            os.rename(filename, "reject/"+filename);
            filename = ""
            print("SLIDESHOW")            
            mode = Mode.SLIDESHOW
        else:
            print (mode, str(msg.payload))
        try:
            while True:
                q.get(False);
        except Empty:
            pass
        
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set ("remote", "remote");
client.connect("127.0.0.1", 1883, 60)

worker = Thread(target=handle_event, args=(eventQ,))
worker.setDaemon(True);
worker.start()


slideshow_timer_worker = Thread(target=slideshow_timer, args=(eventQ,))
slideshow_timer_worker.setDaemon(True);
slideshow_timer_worker.start()

client.loop_forever()




