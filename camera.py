# Python-specific imports
import pickle
from imutils.video import VideoStream

# Package-specific imports
import config
from stream import stream_thread

"""									MODULE OVERVIEW
	Contains all of the functions needed to manage and modify a camera.
"""


def create_new_camera_specs(create=False):
	"""
		Creates a toy dictionary to be saved into camera_specs to allow fast functionality testing on the frontend.
		For testing purposes only.
	"""
	if not create: # don't create a toy dictionary (use if you want to use already stored dictionary in camera_specs)
		return

	camera_dict = {"1": {"url": 0, "height": 720, "width": 1280,
					  "ROI": [[1, 1], [2, 3], [5, 5], [6, 6], [1, 1]]},
		   		"2": {"url": 0, "height": 720, "width": 1280,
					  "ROI": [[10, 10], [20, 30], [50, 20], [60, 100], [10, 10]]}
		   }

	# the format of the dictionary to be stored into camera_specs is as follows:
	# the camera name is the key and the value is another dictionary with the following keys:
	# url (specifies the stream path to connect to the physical camera)
	# height (specifies the height of the camera stream frame)
	# width (specifies the width of the camera stream frame)
	# ROI (specifies the coordinates of the Region Of Interest created by the user on the frontend)

	save_all_camera_specs(camera_dict) # saves the camera_dict to camera_specs

def get_camera_specs():
	"""
		Retrieves the camera specification dictionary saved in camera_specs. See create_new_camera_specs() for
		details on dictionary configuration.
	"""
	
	# Retrieves the pickle file and loads the pickle into the camera dictionary
	with open('pickle_objects/camera_specs', "rb") as pickle_file: 
		camera_dict = pickle.load(pickle_file)
	return camera_dict

def save_camera_spec(camera_name, key, coordinates):
	"""
		Updates the camera in the camera dictionary with a new ROI with the given coordinates.
	"""

	# Loads up the camera dictionary
	camera_dict = get_camera_specs()

	camera_dict[camera_name][key] = value # save key, value pair for specific camera_name

	# Stores the modified dictionary into the camera dictionary
	save_all_camera_specs(camera_dict) # save camera_dict into camera_specs

def save_all_camera_specs(camera_dict):
	"""
		Stores the camera dictionary as a pickle object which is named pickle_objects/camera_specs
	"""

	# Retrives the file and saves the camera dictionary into the file
	with open('pickle_objects/camera_specs', "wb") as pickle_file:
		pickle.dump(camera_dict, pickle_file)

def valid_camera_url(camera_url):
	"""
		Takes in a camera url as input and checks if the camera url produces a valid video stream. Returns the validity,
		height, and width of the video stream specified by the camera url.
	"""

	# Attempts to connect to the steram specified by the camera_url
	vs = VideoStream(src=camera_url).start()
 
	# Reads a single frame so that we can test the validity of the stream
	vs_frame = vs.read()

	# Stops the stream. 
	vs.stop()

	# If the stream has issues, then we would not have a frame stored in vs_frame.
	is_valid = True if vs_frame is not None else False 
	width, height = (vs_frame.shape[0], vs_frame.shape[1]) if vs_frame is not None else (0,0) # get stream dimensions

	return is_valid, width, height

def set_next_available_camera():
	"""
		Sets the current camera to the next available camera for streaming on the frontend. This function is invoked when
		the user removes the camera that is currently streaming to the frontend.
	"""
	camera_dict = get_camera_specs()

	cameras_available = list(camera_dict.keys()) # get names of camera's available
	if len(cameras_available) != 0:
		new_camera_name = list(camera_dict.keys())[0] # choose first camera in the list to stream
		new_camera_url = camera_dict[new_camera_name]["url"] # get the camera url of new_camera_name

		config.CURRENT_CAMERA = new_camera_name # set the current camera
		stream_thread(new_camera_name, new_camera_url) # start streaming from the chosen camera

	else:  # if no cameras available, handle here
		config.CURRENT_CAMERA = None # no camera is available, CURRENTLY PRODUCES ERROR
		config.CAMERA_THREAD.join() # kills the current thread used to stream
