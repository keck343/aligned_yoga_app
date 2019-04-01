import boto3
import os
import subprocess
import sh
import shutil


def upload_and_delete(path, s3_path):
    for subdir, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(subdir, file)
            with open(full_path, 'rb') as data:
                bucket.put_object(Key=s3folder + full_path[len(path) + 1:], Body=data)
            os.remove(full_path)  # delete file
        shutil.rmtree(subdir)  # delete directory and contents
        # os.rmdir(subdir)


# bucket_name = 'alignedstorage'
bucket_name = 'aligned2'
bucket = boto3.resource('s3').Bucket(bucket_name)

for obj in bucket.objects.all():
    path, file = os.path.split(obj.key)

    # 1. grab name of the file
    file_name = str(file)
    # print(file_name)
    name, _ = os.path.splitext(file_name)

    # 2. save file in temp
    file_path = '/tmp/' + file_name
    bucket.download_file(file_name, file_path)
    # 3. create folder for json
    output_path = '/tmp/json_data'  # without extension
    if os.path.isdir(output_path) == False:
        os.mkdir(output_path)
    s3_path = 'training_data/' + name + '/'

    # 4. Run openpose
    openpose_cmd = [
        "~/openpose/build/examples/openpose/openpose.bin", # this is where the binary file is on my ec2
        "--video",
        file_path,
        # "--write_video", # writing video perhaps not necessary?
        #  "tmp/"+name+".avi",
        "--write_json",
        output_path,
        "--display",
        "0"]

    # process = sh.swfdump(_ for _ in openpose_cmd)     # alternative way to run bash command
    process = subprocess.Popen(openpose_cmd, stderr=subprocess.PIPE)
    process.wait()
    print(process)  # Should print any potential error

    # 5. save output to s3 and delete locally
    upload_and_delete(output_path, s3_path=s3_path)
    os.remove(file_path)
