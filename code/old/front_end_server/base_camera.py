import time
import threading
import cv2
import numpy as np
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame
    is available.
    """
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event()
            # and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class Camera(object):
    video_source = 0
    camera = cv2.VideoCapture(video_source)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera
    first_access = 0
    video = []
    playback = []
    event = CameraEvent()
    VIDEO_SECS = 5

    def __init__(self):
        """Start the background camera thread if it isn't running yet."""
        if Camera.thread is None:
            Camera.first_access = time.time()
            Camera.last_access = time.time()

            # start background frame thread
            Camera.thread = threading.Thread(target=self._thread)
            Camera.thread.start()

            # wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    def get_frame(self):
        """Return the current camera frame."""
        if Camera.thread is None:
            return None
        Camera.last_access = time.time()
        # wait for a signal from the camera thread
        print('waiting')
        Camera.event.wait()
        print('done waiting')
        Camera.event.clear()

        return Camera.frame

    @classmethod
    def frames(cls):
        if not cls.camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while cls.camera.isOpened():
            # read current frame
            ret, img = cls.camera.read()
            # gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            cls.video.append(img)
            # encode as jpeg
            jpeg = cv2.imencode('.jpg', img)[1].tobytes()
            cls.playback.append(jpeg)

            # return for streaming
            yield jpeg

    @classmethod
    def _thread(cls):
        """Camera background thread."""
        print('Starting camera thread.')
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            Camera.frame = frame
            Camera.event.set()  # send signal to clients
            time.sleep(0)

            # if there hasn't been any clients asking for frames in
            # the last 10 seconds then stop the thread
            if Camera.last_access - Camera.first_access > cls.VIDEO_SECS:
                frames_iterator.close()
                print('Stopping camera thread.')
                break
        Camera.thread = None
        cls.camera.release()

    @classmethod
    def save_video(cls):
        fps = int(len(cls.video)/cls.VIDEO_SECS)
        # print(f"Fps: {fps}, Length: {len(cls.video)}")
        prev = None
        for i in cls.video[2*fps:]:
            # if prev is None:
            #     prev = i
            # else:
            #     print(f"diff: {np.sum(i) - np.sum(prev)}")
            cls.out.write(i)
