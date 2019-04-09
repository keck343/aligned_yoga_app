#from app import application
from flask import render_template, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField
from werkzeug import secure_filename
import os
import paramiko
from os.path import expanduser
import boto3



def open_pose():
    #ssh into OpenPose server
    ec2_address = 'ec2-13-57-221-10.us-west-1.compute.amazonaws.com'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(ec2_address, username='ubuntu', key_filename=expanduser("~") + '/front_end_server/code/app/aligned.pem')
    except:
        ssh.connect(ec2_address, username='ubuntu', key_filename=expanduser("~") + '/desktop/credentials/aligned.pem')

    stdin, stdout, stderr = ssh.exec_command("ls ./")
    return str(stdout.read())


def push2s3(filename):
    s3 = boto3.resource('s3',aws_access_key_id='AKIAJYPGAZE3RUOKVKVA',aws_secret_access_key='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')
    BUCKET = "alignedstorage"
    try:
        s3.Bucket(BUCKET).upload_file(expanduser("~") + f"/front_end_server/code/app/instance/files/{filename}", f"training_input/{filename}")
    except:
        s3.Bucket(BUCKET).upload_file(expanduser(
            "~") + f"/Desktop/product-analytics-group-project-group10/front_end_server/code/app/instance/files/{filename}",
                                      f"training_input/{filename}")


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


        push2s3(filename)
        return redirect(url_for('index'))  # Redirect to / (/index) page.

    return render_template('upload.html', form=file)


if __name__ == '__main__':
  application.run(host='0.0.0.0', port=5001)