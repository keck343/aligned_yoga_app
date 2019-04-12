Code Tutorial
=============
1) Launch new EC2 with the specs: Ubuntu Deep Learning AMI version 22.0 - t2.small. Use the aligned.pem file given in the code/front_end_server directory.

2) Add custom TCP port 5001 - 0.0.0.0

3) Modify code/user_definitions.py with the EC2 user, EC2 address, and IP address to run script on. Also provide location of pem file relative to your local home directory.

4) Run $python deploy.py in your terminal within the same directory as user_definitions.py.

5) Go to browser and visit {ip}:5001/upload to view our upload page.

The script will clone the remote master branch of this repo onto the specified EC2 instance, setup a conda virtual environment as specified in environment.yml, and launch our web page where users can upload their videos.