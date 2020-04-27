# Python-specific imports
from threading import Lock

"""									 MODULE OVERVIEW
 Contains all of the Global Variables that are used when the flask server starts running. 
"""

# Flag that indicates the current camera
CURRENT_CAMERA = "1"

# Boolean flag that allows a stream to end prematurely if the flag is raised in stream.py::stream_camera_frame()
# TODO: Make this object a dictionary to store whether a camera stream should end
END_STREAM = False

# thread for a camera streaming to the frontend; only one thread is run at a time for frontend
# TODO: Make this object a dictionary to store the each camera's streaming thread
# TODO: Look into the decision of why the threads are running using a daemon.
CAMERA_THREAD = None 

# current frame that is ready to be shown on the frontend
# TODO: Make this object a dictionary that stores the latest frame for each camera.
OUTPUT_FRAME = None
 
# Lock to ensure that we are not writing a new frame to OUTPUT_FRAME while it is being read.
# TODO: Make this object a dictionary to store the each camera's lock
LOCK = Lock() 

# holds VideoStream() object necessary to read frames from physical camera specified by the camera url
# TODO: Make this object a dictionary to store each camera's stream object.
VS = None
