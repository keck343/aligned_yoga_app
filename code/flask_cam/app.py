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
        file = request.files['file']
        
        filename = secure_filename(file.filename)
        print(type(file))
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        ff = ffmpy.FFmpeg(inputs={'video.webm' : None},
                          outputs={'outputs.avi' : '-q:v 0'})
        ff.run()
        return url_for('index')
    return render_template('video.html')


if __name__ == '__main__':
    app.run(app) # ssl_context='adhoc' pip install pyopenssl