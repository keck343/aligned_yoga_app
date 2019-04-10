#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response
from base_camera import Camera
import time

app = Flask(__name__)


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    prev_frame = None
    while True:
        frame = camera.get_frame()
        if frame == None:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    print('here')
    spf = camera.VIDEO_SECS/len(camera.playback)
    print(spf*len(camera.playback)*5)
    for i in range(int(spf*len(camera.playback)*5)):
        for f in camera.playback[int(2*1/spf):]:
            yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + f + b'\r\n')
            time.sleep(spf)

    camera.save_video()
    camera.out.release()


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
