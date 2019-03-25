# brew install ffmpeg
# to save files to a subdirectory change to s3://alignedstorage/videos/<dir_name>

for f in *.mov
do
ffmpeg -i $f -acodec copy -vcodec copy ${f/.mov/.avi}
echo "Converted file $f"
aws s3 cp ${f/.mov/.avi} s3://alignedstorage/videos/ --acl bucket-owner-full-control
echo "Saved file $f to s3"
done
