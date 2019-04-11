from flask import render_template, redirect, url_for, Response
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField
from werkzeug import secure_filename
import os
import paramiko
from os.path import expanduser
import boto3
from base_camera import Camera
import time



def open_pose(filename):
    """Connect to OpenPose server and run bash command"""

    ec2_address = 'ubuntu@ec2-52-36-226-72.us-west-2.compute.amazonaws.com' # Change this to Open_pose IP

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(ec2_address, username='ubuntu', key_filename=expanduser("~") + "/product-analytics-group-project-group10/code/front_end_server/emcalkins_oregon.pem") # OPenPose PEM file
    except:
        ssh.connect(ec2_address, username='ubuntu', key_filename=expanduser("~") + '/desktop/credentials/aligned.pem')

    #stdin, stdout, stderr = ssh.exec_command("ls ./")
    stdin, stdout, stderr = ssh.exec_command(f"python process_training_data.py {filename}") # Change to testing data

    return filename


def push2s3(filename):
    """Save files to S3 bucket"""
    s3 = boto3.resource('s3',aws_access_key_id='AKIAJYPGAZE3RUOKVKVA',aws_secret_access_key='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')
    BUCKET = "alignedstorage"
    try:
        s3.Bucket(BUCKET).upload_file(expanduser("~") + f"/product-analytics-group-project-group10/code/front_end_server/instance/files/{filename}", f"training_input/{filename}")
    except:
        s3.Bucket(BUCKET).upload_file(expanduser(
            "~") + f"/Desktop/product-analytics-group-project-group10/code/front_end_server/instance/files/{filename}",
                                      f"training_input/{filename}")

    return filename


from flask import Flask
application = Flask(__name__)
application.secret_key = os.urandom(24)

class UploadFileForm(FlaskForm):
    """Class for uploading file when submitted"""
    file_selector = FileField('File', validators=[FileRequired()])
    submit = SubmitField('Submit')


@application.route('/index')
@application.route('/')
def index():
    """Index Page : Renders index.html with author name."""

    return ("<h1> Aligned Yoga </h1>")


@application.route('/upload', methods=['GET', 'POST'])
def upload():
    """upload a file from a client machine."""
    file = UploadFileForm()  # file : UploadFileForm class instance
    if file.validate_on_submit():  # Check if it is a POST request and if it is valid.
        f = file.file_selector.data  # f : Data of FileField
        filename = secure_filename(f.filename)
        # filename : filename of FileField
        # secure_filename secures a filename before storing it directly on the filesystem.


        file_dir_path = os.path.join(application.instance_path, 'files')
        file_path = os.path.join(file_dir_path, filename)
        f.save(file_path) # Save file to file_path (instance/ + 'files’ + filename)


        filename = push2s3(filename)
        filename = open_pose(filename)

        return redirect(url_for('index'))  # Redirect to / (/index) page.

    return render_template('upload.html', form=file)


@application.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

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


if __name__ == '__main__':
  application.run(host='0.0.0.0', port=5001)