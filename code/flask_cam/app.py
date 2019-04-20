from flask import Flask, redirect, render_template, url_for, request
from werkzeug.utils import secure_filename
import os
import ffmpy

app = Flask(__name__)
ALLOWED_EXTENSIONS = set('webm')
app.config['UPLOAD_FOLDER'] = '.'


@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video', methods=['GET', 'POST'])
def video():
    if request.method == 'POST':
        for k in request.files.keys():
            print(k)

        file = request.files['file']
        
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        ff = ffmpy.FFmpeg(inputs={'video.webm' : None},
                          outputs={'outputs.avi' : '-q:v 0'})
        ff.run()
        return redirect(url_for('index'))
    return render_template('video.html')


def gen():
    """Video streaming generator function."""
    app.logger.info("starting to generate frames!")
    while True:
        frame = camera.get_frame() #pil_image_to_base64(camera.get_frame())
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(app) # ssl_context='adhoc' pip install pyopenssl