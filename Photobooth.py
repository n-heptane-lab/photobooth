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

class Mode(Enum):
    SLIDESHOW = 1
    PREVIEW   = 2
    REVIEW    = 3

res = (2592,1944)
camera = PiCamera(resolution=res, framerate=15)
camera.vflip = True
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

    review = Image.new('RGB', res);
    review_o = None;


    while True:
        msg = q.get()
        filename = ""

        if mode == Mode.SLIDESHOW and  msg.payload == b'preview':
            print("PREVIEW")
            mode = Mode.PREVIEW
            camera.start_preview(fullscreen=True)
        elif mode == Mode.PREVIEW and msg.payload == b'shutter':
            print("SHUTTER");
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
            review_jpg = Image.open(filename)

            review_o = camera.add_overlay(review_jpg.tobytes(), size=review_jpg.size)
            review_o.alpha=255
            review_o.layer=3
            print("REVIEW")
            mode = Mode.REVIEW
        elif mode == Mode.REVIEW and msg.payload == b'approve':
            print("SLIDESHOW")
            camera.remove_overlay(review_o);
            mode = Mode.SLIDESHOW
        elif mode == Mode.REVIEW and msg.payload == b'reject':
            print("SLIDESHOW")
            camera.remove_overlay(review_o);            
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

client.loop_forever()




