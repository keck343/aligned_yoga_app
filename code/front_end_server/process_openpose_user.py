# Needs to be run from same directory that has models directory (openpose)
import boto3
import os
import subprocess
import pandas as pd
import shutil
import json
import sys
from io import StringIO


def df2csv_s3(df, s3_path, s3_path_avi, processed_path, bucket_name='alignedstorage'):
    """
    Convert Pandas dataframe to csv and upload to s3.
    """
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    bucket.put_object(Key=s3_path, Body=csv_buffer.getvalue(), ACL='public-read')
    bucket.put_object(Key=s3_path_avi, Body=open(processed_path, 'rb'), ACL='public-read')


def upload_and_delete(local_dir, s3_path, processed_path, s3_path_avi):
    """
    Convert pose keypoints from individual jsons to single df and
    upload to s3.
    """
    df = pd.DataFrame(columns=list(range(75)))
    for subdir, dirs, files in os.walk(local_dir):
        for i, file in enumerate(files):
            full_path = os.path.join(subdir, file)
            try:
                with open(full_path, 'r') as f:
                    json_file = json.load(f)
                data = json_file['people'][0]['pose_keypoints_2d']
                df.loc[i] = data
            except:
                continue
        df2csv_s3(df=df, s3_path=s3_path, bucket_name=bucket_name,
                  processed_path=processed_path, s3_path_avi=s3_path_avi)
    shutil.rmtree(subdir)   # delete directory and contents


def process_openpose(path_local):
    dir, file_name = os.path.split(path_local)
    name, _ = os.path.splitext(file_name)
    path_s3_csv = 'output/' + name + '.csv'
    path_s3_avi = 'processed_videos/' + name + '_processed.avi'
    output_dir = "/tmp/json_data"  # without extension
    processed_path = "/tmp/" + name + "_processed.avi"
    openpose_path = "/home/ubuntu/openpose/build/examples/openpose/openpose.bin"

    # Create output directory if necessary
    if os.path.isdir(output_dir) == False:
        os.mkdir(output_dir)

    # Run openpose on video
    openpose_cmd = [
        openpose_path,
        "--video",
        path_local,
        "--write_video",
        processed_path,
        "--write_json",
        output_dir,
        "--display",
        "0"]

    process = subprocess.Popen(openpose_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stderr != '':
        print(stderr)

    # Save output to s3 and delete locally
    upload_and_delete(local_dir=output_dir, processed_path=processed_path,
                      s3_path=path_s3_csv, s3_path_avi=path_s3_avi)
    #os.remove(path_local)
    #os.remove(processed_path)
