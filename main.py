# Flask imports
from flask import Flask, request, render_template, Response, flash

# Import Global Variables
import config # global variables

# Import helper functions from other files
from stream import stream_camera_frame, generate, stream_thread
from camera import create_new_camera_specs, get_camera_specs, save_camera_spec, \
	save_all_camera_specs, valid_camera_url, set_next_available_camera
from roi import is_valid_roi

# Main Flask used for routing.
app = Flask(__name__)
app.secret_key = "secret key"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/')
def show_stream():
	"""Function called when Flask boots up for the first time."""
	create_new_camera_specs(create=True) # creates toy camera_specs object for testing purposes only
	return render_template('show_stream.html', camera_dict=get_camera_specs(), current_camera=config.CURRENT_CAMERA)

@app.route("/stream_feed")
def stream_feed():
	"""
	Frontend continuously calls this function to show the current stream. This returns the response generated
	(current streaming frame) along with the specific media type that is understood by the frontend in order
	to render the frame.
	"""
	return Response(generate(), mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route('/record_roi', methods=['POST'])
def record_roi():
	"""
	When the user defines and submits a Region Of Interest (ROI) on the frontend this function is called.
	The POST request retrieves a list of x,y ROI coordinates created from a JavaScript object stored in request.form
	which must be parsed into a Python list of  [x,y] coordinates. If the coordinates are valid
	ie. no edges of the polygon created intersect, then the ROI is saved for the respective camera in camera_specs.
	Coordinates are saved as list of [x,y] instead of list of (x,y) because JavaScript allows easier manipulation
	of lists. The ROI coordinates are used by JavaScript to render the ROI dynamically on the frontend.

	IMPORTANT:
	As of 4/26/2020 the ROI x,y coordinates are relative to the stream dimensions on the frontend.
	This will need to be updated to have the ROI coordinates relative to the frame size of the input to the YOLO model
	in order to have the ROI against the YOLO model's produced bounding boxes to determine if a vehicle is in the ROI.
	"""
	print(request.form)
	camera_name = config.CURRENT_CAMERA # get the camera the ROI coordinates submitted are meant to be associated with

	roi_coord = []
	for rc in range(len(request.form)//2): # translate the received ROI in request.form into a Python list of coordinates
		x_coord, y_coord = request.form["roi_coord[{}][x]".format(rc)], request.form["roi_coord[{}][y]".format(rc)]
		roi_coord.append([int(x_coord), int(y_coord)])

	print(roi_coord)

	if is_valid_roi(roi_coord): # validate the ROI coordinates
		print("VALID ROI SPECIFIED")
		save_camera_spec(camera_name, "ROI", roi_coord) # save the ROI for the specific camera_name to camera_specs
	else:
		print("INVALID ROI: MUST SPECIFY POLYGON")

	return render_template('show_stream.html', camera_dict=get_camera_specs(), current_camera=config.CURRENT_CAMERA)

@app.route('/choose_camera', methods=['POST'])
def choose_camera():
	"""
	When the user selects a camera stream to view on the frontend this function is called. This POST request retrieves
	the camera name. This function sets the current camera from config to be the chosen camera and calls stream_thread
	that kills the current stream and enables the stream from the chosen camera onto the frontend.
	"""
	camera_name = request.form["camera_view"]
	config.CURRENT_CAMERA = camera_name # set the current camera

	camera_dict = get_camera_specs()
	camera_url = camera_dict[camera_name]["url"] # get the current camera url

	print("CHOOSE_CAMERA", camera_name)
	stream_thread(camera_name, camera_url) # start streaming from the chosen camera

	return render_template('show_stream.html', camera_dict=get_camera_specs(), current_camera=config.CURRENT_CAMERA)

@app.route('/add_camera', methods=['POST'])
def add_camera():
	"""
	When the user creates a new camera on the frontend this function is called. The POST request retrieves
	the camera name and camera url. If the camera url is validated to work, then the camera is saved in camera_specs.
	"""
	camera_name = request.form["camera_name"]
	camera_url = request.form["stream_url"]

	if camera_url == "0": # special command to enable streaming from computer webcam
		camera_url = 0

	is_valid_camera_url, width, height = valid_camera_url(camera_url) # validate camera url and retrieve dimensions
	if is_valid_camera_url:
		camera_dict = get_camera_specs()

		if camera_name not in camera_dict: # save camera to camera_specs if camera_name does not exist
			camera_dict[camera_name]={"url":camera_url, "width": width, "height":height, "ROI": None}
			# structure for camera_specs entry above; takes url, width, height, and ROI; camera_name is the key
			save_all_camera_specs(camera_dict) # saves camera_dict as camera_specs
		else:
			print("INVALID ENTRY: CAMERA NAME TO ADD ALREADY IN USE")
	else:
		print("INVALID ENTRY: NO CONNECTION TO RTSP URL")

	return render_template('show_stream.html', camera_dict=get_camera_specs(), current_camera=config.CURRENT_CAMERA)

@app.route('/remove_camera', methods=['POST'])
def remove_camera():
	"""
	When the user removes a camera from the frontend this function is called. The POST request retrieves the camera
	name to be removed. The camera name is checked to be a valid camera currently in camera_specs before it is removed.
	If the removed camera is the camera currently streaming to the frontend, then a new camera is chosen to be the
	current streamed camera.
	"""
	camera_name = request.form["remove_name"]
	camera_dict = get_camera_specs()

	if camera_name in camera_dict: # check if camera name exists
		camera_dict.pop(camera_name, None)
		save_all_camera_specs(camera_dict) # save camera_dict to camera_specs since camera is removed

		if config.CURRENT_CAMERA == camera_name: # check if camera removed is the current camera being streamed
			set_next_available_camera() # choose another camera to stream to the frontend
	else:
		print("INVALID ENTRY: CAMERA NAME TO REMOVE DOES NOT EXIST")

	return render_template('show_stream.html', camera_dict=get_camera_specs(), current_camera=config.CURRENT_CAMERA)

if __name__ == "__main__":

	app.run(host="0.0.0.0", debug=True)

	if config.VS is not None:
		config.VS.stop() # kill connection to current physical camera
