# Python-specific imports
from flask import Flask, request, render_template, Response, flash
from datetime import datetime
import cv2
import threading

from datetime import datetime
import time
import argparse


# Package-specific imports
from camera import Camera
from video import Video
from utils import *


# Threading variables
data_lock = threading.Lock()
ACTIVE_YOLO_THREAD = False

# Global variables
detection_algo = None
camera_dictionary = {}

current_camera = None

total_cars_count = 0

first = 0
prev = 0

# Main Flask used for routing.
app = Flask(__name__)
app.secret_key = "secret key"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def __log_car_detection(numCars):
	global first
	global prev

	#Gets current time
	now = datetime.now()
	s1 = now.strftime("%Y/%m/%d, %H:%M:%S")


	camera =  camera_dictionary[current_camera]

	json_message = {
		"camera_id": current_camera,
		"timestamp":s1,
		"vehicle_id": camera.car_count,
		"status": "000"

	}


	if numCars is None or prev is None or first is None:
		print(json_message)
		return

	#print("NUMCARS: " + str(numCars) + " Prev: " + str(prev) + " FIRST: " + str(first))

	if numCars == prev and prev < first:
		#Car left ROI
		json_message["status"] = "002"
		camera.car_count += 1
		
		print()
		print(json_message)
		#with open('log.txt', 'a') as file:
		#    file.write(json.dumps(json_message))

	elif numCars == prev and prev > first:
		#Car entered ROI
		json_message["status"] = "001"
		print()
		print(json_message)
		#with open('log.txt', 'a') as file:
		#    file.write(json.dumps(json_message))

	first = prev
	prev = numCars



def __test_json_messages():
	print("IN TEST AREA")
	numCars = 0
	for i in range(10):
		__log_car_detection(numCars)
		if i == 4:
			numCars = 1
		if i == 7:
			numCars = 0
		print(i)
		time.sleep(1)


def __perform_detection(frame):
	"""
		Kickstarts the yolo algorithm detection on the given frame. This is run on a thread concurrent to the main server.
	"""

	global ACTIVE_YOLO_THREAD
	global total_cars_count
	global detection_algo

	with data_lock:
		detection_algo.set_frame_and_roi(frame, camera_dictionary[current_camera]) 
		numCars = detection_algo.detect_intersections() 
		__log_car_detection(numCars)
	
		#print("Detection Complete", time.strftime('%a %H:%M:%S')) 
	
		if numCars > 0:
			total_cars_count += numCars
			#print('Number of Vehicles Detected: {}'.format(numCars))
			#print('Total Vehicles Counted: {}'.format(total_cars_count))
			
	ACTIVE_YOLO_THREAD = False


def __get_frames():
	"""
		Generator function to get frames constantly to the frontend and to kickstart the detection on each frame.
	"""
	global thread, ACTIVE_YOLO_THREAD

	for frame in camera_dictionary[current_camera]:
		roi = camera_dictionary[current_camera].ROI

		# Check to make sure that the current camera has a specified ROI and that there's no thread running.
		if roi and not ACTIVE_YOLO_THREAD:
			thread = threading.Thread(target=__perform_detection,args=(frame,), daemon = True)
			thread.start()
			ACTIVE_YOLO_THREAD = True

		yield(prepare_frame_for_display(frame, current_camera))

@app.route('/')
def show_stream():
	"""
		Function called when Flask boots up for the first time.
	"""
	return render_template('show_stream.html', camera_dict=camera_dictionary, current_camera=current_camera)

@app.route("/stream_feed")
def stream_feed():
	"""
		Utilizes the generator function main.py::__get_frames() to send frames from the current_camera stream into the frontend.
	"""
	return Response(__get_frames(), mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route('/record_roi', methods=['POST'])
def record_roi():
	"""
		Updates the current camera stream's ROI coordinates.
	"""
	print("RECEIVED ROI")
	#print(request.form)

	roi_coord_is_NaN = False

	roi_coord = []
	for rc in range(len(request.form)//2): # translate the received ROI in request.form into a Python list of coordinates
		x_coord, y_coord = request.form["roi_coord[{}][x]".format(rc)], request.form["roi_coord[{}][y]".format(rc)]
		#print("x_coord", x_coord, type(x_coord), "y_coord", y_coord, type(y_coord))
		
		if x_coord == "NaN" or y_coord == "NaN":
			roi_coord_is_NaN = True
			break
		else:
			roi_coord.append([int(x_coord), int(y_coord)])
	
	#print(roi_coord)

	if is_valid_roi(roi_coord) and not roi_coord_is_NaN: # validate the ROI coordinates
		print("VALID ROI SPECIFIED")
		camera_dictionary[current_camera].set_roi_coordinates(roi_coord)
	
	if not is_valid_roi(roi_coord):
		print("INVALID ROI: MUST SPECIFY POLYGON")

	return render_template('show_stream.html', camera_dict=camera_dictionary, current_camera=current_camera)

@app.route('/choose_camera', methods=['POST'])
def choose_camera():
	"""
		Switches the camera stream that's being displayed on the frontend.
	"""
	global current_camera
	current_camera = request.form["camera_view"]

	if current_camera == '0':
		current_camera = 0

	print("CURRENT CAMERA IS NOW {}".format(current_camera))

	return render_template('show_stream.html', camera_dict=camera_dictionary, current_camera=current_camera)

@app.route('/add_camera', methods=['POST'])
def add_camera():
	"""
		Adds a new camera to the system with the user specified camera url.
	"""

	camera_name = request.form["camera_name"]
	camera_url = request.form["stream_url"]

	# Special case which indicates the computer's webcam
	if camera_url == "0":
		camera_url = 0

	if camera_name not in camera_dictionary:
		camera_dictionary[camera_name] = Camera(camera_url)
	else:
		print("ERROR: CAMERA EXISTS")

	return render_template('show_stream.html', camera_dict=camera_dictionary, current_camera=current_camera)

@app.route('/remove_camera', methods=['POST'])
def remove_camera():
	"""
		Removes a camera from the system and ends the camera's video stream.
	"""
	camera_name = request.form["remove_name"]

	if camera_name in camera_dictionary:
		camera_dictionary[camera_name].stop_video_stream()
		del(camera_dictionary[camera_name])

		# If the camera being removed was the current camera, set a new camera stream to display onto the frontend
		if camera_dictionary and current_camera == camera_name:
			current_camera = next(camera_dictionary)

	else:
		print("INVALID ENTRY: CAMERA NAME TO REMOVE DOES NOT EXIST")

	return render_template('show_stream.html', camera_dict=camera_dictionary, current_camera=current_camera)

def __parseArguments():
	"""Choose arguments to run flask application. Arguments are --model and --webcam"""
	global camera_dictionary
	global detection_algo
	global current_camera
	
	parser = argparse.ArgumentParser("Run Detection Flask App")
	parser.add_argument("--model", default="cpu-tiny-yolov3", help="Model to load. Choose between cpu-yolov3, cpu-tiny-yolov3, tpu-tiny-yolov3, tpu-mobilenetv2")
	parser.add_argument("--webcam", default="camera", help="Type webcam for webcam, camera for default IP cameras, or video path for video input")
	parser.add_argument("--videoOutput", type=int, default=0, help="Enter 1 for video output and output")
	args = parser.parse_args()
	
	
	if args.model == "cpu-tiny-yolov3" or args.model == "cpu-yolov3":
		from YoloVideo import YoloVideo
		detection_algo = YoloVideo(initialize_yolo(modelType=args.model))

	elif args.model == "tpu-tiny-yolov3" or args.model == "tpu-mobilenetv2":
		from tpuVideo import tpuVideo
		detection_algo = tpuVideo(initialize_tpu(modelType=args.model), modelType=args.model)
	
	if args.webcam == "webcam":
		first_camera = 0 
		camera_dictionary[first_camera] = Camera(first_camera)
	elif args.webcam =="camera":
		first_camera = 'rtsp://admin:12345@172.16.15.12'
		camera_dictionary[first_camera] = Camera(first_camera)

		second_camera = 'rtsp://admin:!hylanD3550@172.16.15.11:554/1/h264major'
		camera_dictionary[second_camera] = Camera(second_camera)
	
	elif args.webcam =="video":		
		first_camera = "./inputVideos/video1.mp4" 
		camera_dictionary[first_camera] = Video(first_camera)
		
		second_camera = "./inputVideos/video2.mp4" 
		camera_dictionary[second_camera] = Video(second_camera)	
	
	else:
		first_camera = args.webcam
		camera_dictionary[first_camera] = Video(first_camera)
 
	current_camera = first_camera

		
if __name__ == "__main__":
	__parseArguments()
	app.run(host="0.0.0.0", debug=False)
	
	
	
	
	
	
	
	
