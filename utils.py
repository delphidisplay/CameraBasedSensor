# Python-specific imports
import cv2
from datetime import datetime
from shapely.geometry import Polygon
from imutils import resize
from detect_image import make_interpreter

def add_frame_overlay(frame, camera_name="NOT_SPECIFIED"):
	"""
	Add the date, time, and camera name on the frame.
	"""
	timestamp = datetime.now()
	cv2.putText(frame, timestamp.strftime(
		"%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
				cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1) # add date and time

	cv2.putText(frame, "CAMERA: {}".format(camera_name), (10, frame.shape[0] - 40),
				cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 0, 255), 1) # add camera name

	return frame

def is_valid_roi(nested_list):
	"""
	Validates the list of [x,y] coordinates that defines the ROI to see if it is a valid shape.
	A valid shape is defined as a Polygon with no intersecting edges ie. no hourglass/bowtie shapes.
	"""
	try:
		shape = Polygon([tuple(i) for i in nested_list]) # Polygon object only accepts list of (x,y) tuples
		return shape.is_valid # determines shape validity
	except Exception as e: # exception if Polygon was not able to be created for any reason ie. bad input
		print(e)
		return False

def prepare_frame_for_display(frame,camera_name="NOT_SPECIFIED"):
	""" Takes in a frame, converts it into bytes as flask requires it and returns the encoded frame. """
	frame = resize(frame, width=800)
	frame = add_frame_overlay(frame,camera_name)
	_,frame = cv2.imencode(".jpg", frame)
	return b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +  bytearray(frame) + b'\r\n' 

def initialize_yolo():
	print("[INFO] loading YOLO from disk...")
	configPath = "yolo-coco/yolov3.cfg"
	weightsPath = "yolo-coco/yolov3.weights"
	net =  cv2.dnn.readNetFromDarknet(configPath, weightsPath)
	return net

def initialize_tpu():
    model = "models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite"
    interpreter = make_interpreter(model)
    return interpreter

