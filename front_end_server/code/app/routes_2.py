#from app import application
from flask import render_template, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField
from werkzeug import secure_filename
import os
import paramiko
import sys
from os.path import expanduser
from os.path import exists
import time

def send_file():
    file = open('testfile.txt', 'w')
    file.write('test')
    file.close()
    return None

def open_pose():
    #ssh into OpenPose server
    ec2_address = 'ec2-54-193-96-157.us-west-1.compute.amazonaws.com'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ec2_address, username='ec2-user', key_filename='aligned.pem')

    stdin, stdout, stderr = ssh.exec_command("ls ./")
    return str(stdout.read())

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
    output = open_pose()
    return ("<h1> Aligned Yoga " + output + "</h1>")


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

        send_file()

        return redirect(url_for('index'))  # Redirect to / (/index) page.

    return render_template('upload.html', form=file)


if __name__ == '__main__':
  application.run(host='0.0.0.0', port=5001)