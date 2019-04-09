import cv2
from base_camera import BaseCamera


class Camera(BaseCamera):
    video_source = 0
    camera = cv2.VideoCapture(video_source)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi',fourcc, 20.0, (640,480))

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    @classmethod
    def stop_video_source(cls):
        cls.camera.release()
        cls.out.release()

    @classmethod
    def frames(cls):
        if not cls.camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            # read current frame
            _, img = cls.camera.read()
            cls.out.write(img)
            #encode as jpeg
            jpeg = cv2.imencode('.jpg', img)[1].tobytes()

            # return for streaming
            yield jpeg
