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


def open_pose():
    """Connect to OpenPose server and run bash command"""
    ec2_address = 'ec2-13-57-221-10.us-west-1.compute.amazonaws.com'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(ec2_address, username='ubuntu', key_filename=expanduser("~") + "/product-analytics-group-project-group10/code/front_end_server/aligned.pem")
    except:
        ssh.connect(ec2_address, username='ubuntu', key_filename=expanduser("~") + '/desktop/credentials/aligned.pem')

    stdin, stdout, stderr = ssh.exec_command("ls ./")
    return str(stdout.read())


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


from flask import Flask
application = Flask(__name__)
application.secret_key = os.urandom(24)


from user_class import *
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from db_config import Config

application.config.from_object(Config)
db = SQLAlchemy(application)

# login_manager needs to be initiated before running the app
login_manager = LoginManager()
login_manager.init_app(application)


class UploadFileForm(FlaskForm):
    """Class for uploading file when submitted"""
    file_selector = FileField('File', validators=[FileRequired()])
    submit = SubmitField('Submit')


# @application.route('/index')
# @application.route('/')
# def index():
#     """Index Page : Renders index.html with author name."""
#     output = open_pose()
#     return "<h1> Aligned Yoga " + output + "</h1>"


@application.route('/register')
@application.route('/')
def register():
    username = 'diane'
    password = 'pwd'
    email = 'diane@gmail.com'

    user_count = user_class.User.query.filter_by(username=username).count() \
        + user_class.User.query.filter_by(email=email).count()

    if user_count > 0:
        return '<h1> Error - Existing user: ' + username + ' or ' \
            + email + ' </h1>'
    else:
        user = user_class.User(username, email, password)
        db.session.add(user)
        db.session.commit()
        return '<h1> Registered : ' + username + '</h1>'


@application.route('/login', methods=['GET', 'POST'])
def login():
    username = 'diane'
    password = 'pwd'

    # Look for it in the database.
    user = user_class.User.query.filter_by(username=username).first()

    # Login and validate the user.
    if user is not None and user.check_password(password):
        login_user(user)
        # return '<h1> Logged in : ' + username + '</h1>'
        return redirect(url_for('upload'))

    else:
        return '<h1> Invalid username and password combination! </h1>'


@application.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """upload a file from a client machine."""
    file = UploadFileForm()  # file : UploadFileForm class instance
    if file.validate_on_submit():  # Check if it is a POST request and if it is valid.
        f = file.file_selector.data  # f : Data of FileField
        filename = secure_filename(current_user.id)
        # filename : filename of FileField
        # secure_filename secures a filename before storing it directly on the filesystem.

        file_dir_path = os.path.join(application.instance_path, 'files')
        file_path = os.path.join(file_dir_path, filename)
        f.save(file_path) # Save file to file_path (instance/ + 'files’ + filename)

        push2s3(filename)
        return redirect(url_for('index'))  # Redirect to / (/index) page.

    return render_template('upload.html', form=file)


@application.route('/video_feed')
@login_required
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
