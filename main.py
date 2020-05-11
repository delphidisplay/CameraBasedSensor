# Python-specific imports
from flask import Flask, request, render_template, Response, flash
from datetime import datetime
import cv2
import threading
import atexit
from datetime import datetime

# Package-specific imports
from camera import Camera
from utils import *
from YoloVideo import YoloVideo



# Threading variables
data_lock = threading.Lock()
ACTIVE_YOLO_THREAD = False

camera_dictionary = {}
current_camera = 0 #'rtsp://admin:12345@172.16.15.12'
camera_dictionary[current_camera] = Camera(current_camera)
#second_camera = 'rtsp://admin:!hylanD3550@172.16.15.11:554/1/h264major'
#camera_dictionary[second_camera] = Camera(second_camera)
yolo_detection_algo = YoloVideo(initialize_yolo())
prev_cars = 0
camera_cars_count = [0]*len(camera_dictionary)


# Main Flask used for routing.
app = Flask(__name__)
app.secret_key = "secret key"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024



'''
Function to print out JSON messages to terminal whenever a car
enters or leaves ROI
'''
def __log_car_detection(numCars):
    global prev_cars

    now = datetime.now()
    s1 = now.strftime("%Y/%m/%d, %H:%M:%S")

    json_message = {
        "camera_id":current_camera,
	    "timestamp":s1,
	    "vehicle_id":camera_cars_count[current_camera],
	    "status": "000"

    }

    if not numCars:
        print("numCars is None")
        return 0
    elif prev_cars is None:
        print("prev_cars is none")
        return 0

    if prev_cars < numCars:
        ## TODO: Log Car arrived
        prev_cars = numCars
        json_message["status"] = "001"
        camera_cars_count[current_camera] += 1

        print(json_message)
        #with open('log.txt', 'a') as file:
        #    file.write(json.dumps(json_message))



    elif prev_cars > numCars:
        prev_cars = numCars
        ## TODO: Log car left
        json_message["status"] = "002"
        print(json_message)
        #with open('log.txt', 'a') as file:
        #    file.write(json.dumps(json_message))


def __perform_detection(frame):
    global prev_cars
    global ACTIVE_YOLO_THREAD
    with data_lock:
        #print('Starting')
        yolo_detection_algo.set_frame_and_roi(frame, camera_dictionary[current_camera].ROI)
        #print('Intersections')
        numCars = yolo_detection_algo.detect_intersections()
        print(prev_cars)
        __log_car_detection(numCars)
        print('Number of Cars Detected: {}'.format(numCars))
    ACTIVE_YOLO_THREAD = False


def __get_frames():
    """
        Generator function to get frames constantly to the frontend.
    """
    global thread, ACTIVE_YOLO_THREAD
    for frame in camera_dictionary[current_camera]:
        roi = camera_dictionary[current_camera].ROI
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

    # TODO: Make the x and y coordinates relative to the frame size of the input to the YOLO model.

    print(request.form)

    roi_coord = []
    for rc in range(len(request.form)//2): # translate the received ROI in request.form into a Python list of coordinates
        x_coord, y_coord = request.form["roi_coord[{}][x]".format(rc)], request.form["roi_coord[{}][y]".format(rc)]
        roi_coord.append([int(x_coord), int(y_coord)])

    print(roi_coord)

    if is_valid_roi(roi_coord): # validate the ROI coordinates
        #print("VALID ROI SPECIFIED")
        camera_dictionary[current_camera].set_roi_coordinates(roi_coord)
    else:
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
