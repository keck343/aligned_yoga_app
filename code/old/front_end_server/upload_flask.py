import ffmpy
import boto3
import time
import os
from os.path import expanduser

# from app import application, classes, db
from flask import Flask
from flask import flash, render_template, redirect, url_for, request, Response
from flask_login import current_user, login_user, login_required, logout_user, UserMixin

from werkzeug import secure_filename
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import PasswordField, StringField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email

from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from process_openpose_user import *
from modeling import *


# def open_pose(filepath):
#     """Connect to OpenPose server and run bash command"""
#
#     # Change this to Open_pose IP
#     ec2_address = 'http://ec2-54-188-181-40.us-west-2.compute.amazonaws.com'
#
#     ssh = paramiko.SSHClient()
#     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#
#     # try:
#     # Use OpenPose PEM file
#     ssh.connect(ec2_address,
#                 username='ubuntu',
#                 key_filename=expanduser("~") +
#                 f"/product-analytics-group-project-group10/" +
#                 f"code/front_end_server/emcalkins_oregon.pem")
#     # except:
#     #     ssh.connect(ec2_address,
#     #                 username='ubuntu',
#     #                 key_filename=expanduser("~") +
#     #                              '/desktop/credentials/aligned.pem')
#
#     # stdin, stdout, stderr = ssh.exec_command("ls ./")
#     print("Connected")
#     # Change to testing data
#     stdin, stdout, stderr = ssh.exec_command(
#         f"cd openpose/ \n python3 process_openpose_user.py {filepath}")
#     print(stderr)
#
#     print("OpenPose command excuted")
#     print(filepath)
#     return filepath


def push2s3(filename, filepath=''):
    """Save files to S3 bucket"""
    # bucket_name = 'alignedstorage'
    #
    # s3 = boto3.resource('s3')
    # bucket = s3.Bucket(bucket_name)
    # bucket.put_object(Key=f'input/{filename}',
    #                   Body=csv_buffer.getvalue(),
    #                   ACL='public-read')

    access_key_id = 'AKIAJYPGAZE3RUOKVKVA'
    sec_access_key = 'ZFJNzLFv/2UkVa+mdsIqf1QHm8V8Z8+FtoWTlrw2'

    s3 = boto3.resource('s3',
                        aws_access_key_id=access_key_id,
                        aws_secret_access_key=sec_access_key)
    BUCKET = "alignedstorage"

    try:
        s3.Bucket(BUCKET).upload_file(expanduser("~") + f"/product-analytics-group-project-group10/code/front_end_server/{filepath}{filename}", f"training_input/{filename}")
    except:
        s3.Bucket(BUCKET).upload_file(expanduser(
            "~") + f"/Desktop/product-analytics-group-project-group10/code/front_end_server/{filepath}{filename}",
                                      f"training_input/{filename}")

    # try:
    s3.Bucket(BUCKET).upload_file(
        expanduser("~") +
        f"/product-analytics-group-project-group10/"
        f"code/front_end_server/{filepath}{filename}",
        f"training_input/{filename}",
        ExtraArgs={"ACL": 'public-read'})
    # except:
    #     s3.Bucket(BUCKET).upload_file(
    #         expanduser("~") +
    #         f"/Desktop/product-analytics-group-project-group10/"
    #         f"code/front_end_server/instance/files/{filename}",
    #         f"training_input/{filename}")

    return "training_input/" + filename


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY=os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'trial.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = True # flask-login uses sessions which require a secret Key


# Initialization
# Create an application instance (an object of class Flask)  which handles all requests.
application = Flask(__name__)
application.config.from_object(Config)
db = SQLAlchemy(application)
db.create_all()
db.session.commit()
application.config['UPLOAD_FOLDER'] = '.'

# login_manager needs to be initiated before running the app
login_manager = LoginManager()
login_manager.init_app(application)

bootstrap = Bootstrap(application)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    labels = []

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


db.create_all()
db.session.commit()


class UploadFileForm(FlaskForm):
    """Class for uploading file when submitted"""
    file_selector = FileField('File', validators=[FileRequired()])
    submit = SubmitField('Submit')


class RegistrationForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired()])
    email = EmailField('Email:', validators=[DataRequired(), Email()])
    password = PasswordField('Password:', validators=[DataRequired()])
    submit = SubmitField('Submit')


class LogInForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired()])
    password = PasswordField('Password:', validators=[DataRequired()])
    submit = SubmitField('Login')


@application.route('/index')
@application.route('/')
def index():
    """Index Page : Renders index.html with author name."""
    return "<h1> Aligned Yoga </h1>"


@application.route('/register', methods=('GET', 'POST'))
def register():
    registration_form = RegistrationForm()
    if registration_form.validate_on_submit():
        username = registration_form.username.data
        password = registration_form.password.data
        email = registration_form.email.data

        user_count = User.query.filter_by(username=username).count() \
                     + User.query.filter_by(email=email).count()
        if user_count > 0:
            flash('Error - Existing user : ' + username + ' OR ' + email)

        else:
            user = User(username, email, password)
            db.session.add(user)
            db.session.commit()

            user_id = user.id
            return redirect(url_for('upload', fname=user_id))

    return render_template('register.html', form=registration_form)


@application.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LogInForm()
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data
        # Look for it in the database.
        user = User.query.filter_by(username=username).first()

        # Login and validate the user.
        if user is not None and user.check_password(password):
            login_user(user)
            uid = user.id
            return redirect(url_for('video'), uid=uid)
        else:
            flash('Invalid username and password combination!')

    return render_template('login.html', form=login_form)


@application.route('/upload/<fname>', methods=['GET', 'POST'])
def upload(fname):
    """upload a file from a client machine"""
    # file : UploadFileForm class instance
    file = UploadFileForm()

    # Check if it is a POST request and if it is valid.
    if file.validate_on_submit():
        # f : Data of FileField
        f = file.file_selector.data
        # filename = secure_filename(f.filename)
        filename = secure_filename(fname)
        # filename : filename of FileField
        # secure_filename secures a filename before
        # storing it directly on the filesystem.

        file_dir_path = os.path.join(application.instance_path, 'files')
        file_path = os.path.join(file_dir_path, filename)
        # Save file to file_path (instance/+'files’+filename)
        f.save(file_path)

        filepath = push2s3(filename, 'instance/files/')
        filepath = process_openpose(filepath)

        return redirect(url_for('index'))  # Redirect to / (/index) page.

    return render_template('upload.html', form=file)


@application.route('/video/<uid>', methods=['GET', 'POST'])
def video(uid):
    if request.method == 'POST':
        file = request.files['file']
        
        filename = secure_filename(file.filename + uid)
        print(type(file))
        file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
        timestr = time.strftime("%Y%m%d-%H%M%S")
        local_path = f"/tmp/user_video_{timestr}.avi"
        ff = ffmpy.FFmpeg(inputs={filename : None},
                          outputs={local_path : '-q:v 0 -vcodec mjpeg -r 30'})
        ff.run()
        timestr = time.strftime("%Y%m%d-%H%M%S")
        # filepath = push2s3(name, '') #filename without tmp

        # Process video with openpose on same server & return df
        df = process_openpose(local_path)
        # Add modeling function call (pull csv from s3, run through rules-based system
        labels, values = warrior2_label_csv(df)
        user = load_user(uid)
        user.labels = labels
        print(user.labels)

        return url_for('index')
    return render_template('video.html')


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


if __name__ == '__main__':
    # path = '~/product-analytics-group-project-group10/code/front_end_server/'
    cert = 'cert.pem'
    key = 'key.pem'
    application.run(host='0.0.0.0', port=5001, ssl_context=(cert, key))
