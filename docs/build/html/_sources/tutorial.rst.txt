Code Tutorial
=============
1) Modify user_definitions.py with the EC2 user and EC2 address to run script on. Also provide location of pem file relative to your local home directory
2) Modify user_definitions.py with origin and destination coordinates to be used by calculate_driving_time.py
3) Run $python deploy.py in your terminal within the same directory as user_definitions.py

The script will clone the remote master branch of this repo onto the specified EC2 instance, setup a conda virtual environment as specified in environment.yml, and set a cronjob to execute calculate_driving_time.py every minute.