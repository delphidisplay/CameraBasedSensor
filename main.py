# Python-specific imports
from flask import Flask, request, render_template, Response, flash
from collections import deque
from argparse import ArgumentParser
from threading import Thread, Lock
import time
import serial

# Package-specific imports
from camera import Camera
from utils import *

# Threading variables
data_lock = Lock()
ACTIVE_YOLO_THREAD = False

# Global variables
detection_algo = None
camera_dictionary = {}
current_camera = None

# JSON Logging related global variables.
min_frames = 5
car_counts = deque([-1]*min_frames)
in_lane = False
out_lane = True
total_cars_count = 0
first = 0
prev = 0

# Main Flask used for routing.
app = Flask(__name__)
app.secret_key = "secret key"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def __log_car_detection(numCars):
    '''
        Method sends json messages whenever a car is detected and enough frames have passed
        User can determine how many frames should pass before a message is sent by modifying
        the variable min_frames above
        Parameters:
        numCars: the number of cars detected in the frame by the model
    '''
    global in_lane
    global out_lane
    global min_frames

    # Gets current time in epoch from Jan 1 1970
    s1 = time.time()
    ser = serial.Serial(4663)  # open serial port

    json_message = {
            "camera_id": current_camera,
            "timestamp":s1,
            "vehicle_id": camera_dictionary[current_camera].car_count,
            "status": "000"
    }

    if numCars is None or min_frames < 1:
        print(json_message)
        return

    car_counts.append(numCars)
    car_counts.popleft()

    if car_counts == (deque([0]*min_frames)) and in_lane:
        #Car left ROI
        json_message["status"] = "002"
        camera_dictionary[current_camera].car_count += 1
        #print("NUM CARS: " + str(numCars))
        print(json_message)
        #ser.write(json_message)
        out_lane = True
        in_lane = False
        #with open('log.txt', 'a') as file:
        #    file.write(json.dumps(json_message))

    elif car_counts == (deque([1]*min_frames)) and out_lane:
        #Car entered ROI
        json_message["status"] = "001"
        #print("NUM CARS: " + str(numCars))
        print(json_message)
        #ser.write(json_message)
        in_lane = True
        out_lane = False
        #with open('log.txt', 'a') as file:
        #    file.write(json.dumps(json_message))

    ser.close() 

def __test_json_messages():
    '''
        Method to test the __log_car_detection method
    '''
    print("TESTING __log_car_detection")
    numCars = 0
    for i in range(10):
        __log_car_detection(numCars)
        if i == 2:
            numCars = 1
        if i == 6:
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
                thread = Thread(target=__perform_detection,args=(frame,), daemon = True)
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

	roi_coord = []
	for rc in range(len(request.form)//2): # translate the received ROI in request.form into a Python list of coordinates
            x_coord, y_coord = request.form["roi_coord[{}][x]".format(rc)], request.form["roi_coord[{}][y]".format(rc)]
            roi_coord.append([int(x_coord), int(y_coord)])

	if is_valid_roi(roi_coord): # validate the ROI coordinates
            camera_dictionary[current_camera].set_roi_coordinates(roi_coord)
	else:
            print("INVALID ROI: COORDINATES MADE INVALID POLYGON")

	return render_template('show_stream.html', camera_dict=camera_dictionary, current_camera=current_camera)

@app.route('/choose_camera', methods=['POST'])
def choose_camera():
	"""
		Switches the camera stream that's being displayed on the frontend.
	"""
	global current_camera
	current_camera = request.form["camera_view"]

	# Special case which indicates the computer's webcam
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

    # Parses the user given command for command line arguemnts.
    parser = ArgumentParser("Run Detection Flask App")
    parser.add_argument("--model", required=True, help="Model to load. Choose between cpu-yolov3, cpu-tiny-yolov3, tpu-tiny-yolov3, tpu-mobilenetv2")
    parser.add_argument("--webcam", type=int, default=0, help="Enter 1 for webcam, 0 for default IP cameras")
    args = parser.parse_args()


    if args.model == "cpu-tiny-yolov3" or args.model == "cpu-yolov3":
        # Non-tpu version of the algo
        from YoloVideo import YoloVideo
        detection_algo = YoloVideo(initialize_yolo(modelType=args.model))

    elif args.model == "tpu-tiny-yolov3" or args.model == "tpu-mobilenetv2":
        # TPU version of the algo
        from tpuVideo import tpuVideo
        detection_algo = tpuVideo(initialize_tpu(modelType=args.model), modelType=args.model)

    if args.webcam == 1:
        # Using local camera's webcam
        first_camera = 0
        camera_dictionary[first_camera] = Camera(first_camera)
    else:
        # Using Delphi's testing cameras.
        first_camera = 'rtsp://admin:12345@172.16.15.12'
        camera_dictionary[first_camera] = Camera(first_camera)

        second_camera = 'rtsp://admin:!hylanD3550@172.16.15.11:554/1/h264major'
        camera_dictionary[second_camera] = Camera(second_camera)

    current_camera = first_camera


if __name__ == "__main__":
    __parseArguments()
    app.run(host="0.0.0.0", debug=False)
    #__test_json_messages()
