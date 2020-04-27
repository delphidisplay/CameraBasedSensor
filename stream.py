# Python-specific imports
from cv2 import imencode, FONT_HERSHEY_SIMPLEX, putText
from imutils import resize
from imutils.video import VideoStream
from time import sleep
from datetime import datetime
from threading import Thread
# Package-specific imports
import config

"""									MODULE OVERVIEW
Handles all of the streaming between the cameras and the flask application.
"""

def add_frame_overlay(frame, camera_name="NOT SPECIFIED"):
	"""
	Add the date, time, and camera name on the frame and returns the modified frame.
	"""

	timestamp = datetime.now()

	# Puts the date and time onto the frame
	putText(frame, timestamp.strftime(
		"%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
				FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

	# Puts in the camera name onto the frame
	putText(frame, "CAMERA: {}".format(camera_name), (10, frame.shape[0] - 40),
				FONT_HERSHEY_SIMPLEX, 0.50, (0, 0, 255), 1) # add camera name

	return frame

def stream_camera_frame(camera_name, camera_url):
	"""
	Creates a VideoStream() connection to the camera specified by the camera url and
	constantly updates config.OUTPUT_FRAME with the latest frame from the VideoStream() object.
	"""
	print("STREAM_CAMERA: {}".format(camera_name))

	#* TODO START: Due to the change in structure of VS, we don't kill any stream.
	if config.VS is not None:
		config.VS.stop() # stops any current VideoStream() object from running
	config.VS = VideoStream(src=camera_url).start() # initiate VideoStream() object with camera url
	#* TODO END

	#* TODO START: Due to the change in structure of END_STREAM AND VS, we have to read from specific stream.
	while True: # constantly updates config.OUTPUT_FRAME
		if config.END_STREAM: # break if END_STREAM flag is raised
			print("STREAM {} IS FINISHED".format(camera_name))
			break

		frame = config.VS.read() # read currently available frame from VideoStream()
		sleep(.1) # reduce computing power
		frame = resize(frame, width=800) # used so all camera streams have same width on frontend

		frame = add_frame_overlay(frame, camera_name) # add overlay to frame such as date/time and camera name

		with config.LOCK: # wait until lock is acquired
			config.OUTPUT_FRAME = frame.copy() # copy frame to config.OUTPUT_FRAME, used by generate() function
	#* TODO END

def generate():
	"""
	Generator object to yield config.OUTPUT_FRAME which is encoded in a jpg and byte format. This is called by
	stream_feed() on main.py
	"""
	# loop over frames from the output stream
	while True:
		# wait until the lock is acquired
		with config.LOCK:
			# check if the output frame is available, otherwise skip
			# the iteration of the loop
			if config.OUTPUT_FRAME is None:
				continue
			# encode the frame in JPEG format
			(flag, encodedImage) = imencode(".jpg", config.OUTPUT_FRAME)
			# ensure the frame was successfully encoded
			if not flag:
				continue
		# yield the output frame in the byte format
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
			bytearray(encodedImage) + b'\r\n')

def stream_thread(camera_name, camera_url):
	"""
	The camera stream shown on the frontend is initiated by a thread. This function joins any running threads
	and creates a new thread to stream the specified camera url. The thread runs stream_camera_frame() which
	constantly updates config.OUTPUT_FRAME with the current frame of the camera stream.
	"""
	print("THREAD: {} IS CALLED".format(camera_name))

	#* TODO START: Due to change in structure of CAMERA_THREADS AND END_STREAMS, this needs to be changed.
	if config.CAMERA_THREAD is not None: # kill thread if available
		print("SET CURRENT THREAD TO FINISH")
		config.END_STREAM=True # used to break on stream.py::stream_camera_frame()
		config.CAMERA_THREAD.join() # join thread

	config.END_STREAM = False
	config.CAMERA_THREAD = Thread(target=stream_camera_frame, args=(camera_name, camera_url,)) # create thread
	config.CAMERA_THREAD.daemon = True # allows main python program to exit while threads continue to run
	config.CAMERA_THREAD.start() # start running thread
	#* TODO END
