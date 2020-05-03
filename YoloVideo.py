import numpy as np
import imutils
import time
import cv2
import os
import find_intersect
from shapely.geometry import Polygon
import matplotlib.pyplot as plt

class YoloVideo:
	"""
	detection model to identify cars and trucks within a specific region of interest (ROI)
	""" 

	def __init__(self, frame, ROI, yolo_path):
		"""
			self.frame: frame from stream
			self.ROI: nested list defining region of intereest in frame in which we detect vehicles 
			self.yolo_path: path to folder containing yolo weights and labels
			self.confidence: minimum probability to filter weak detections
			self.threshold: threshold when applying non-maxima suppression
		"""
		self.frame = frame
		self.ROI = ROI
		self.yolo_path = yolo_path
		self.confidence = 0.5
		self.threshold = 0.3
		self.debug = False


	def get_yolo_labels(self):
		"""
			return the COCO class labels our YOLO model was trained on
		"""
		return open(os.path.sep.join([self.yolo_path, "coco.names"])).read().strip().split("\n")
		

	def initiailize_colors(self, labels):
		"""
			return a list of colors to represent each possible class label
		"""
		np.random.seed(42)
		return  np.random.randint(0,255, size=(len(labels), 3), dtype="uint8")
	
	
	def get_yolo_path(self, file_name):
		"""
			return the path to the YOLO file
		"""
		return os.path.sep.join([self.yolo_path, file_name])

	def get_yolo_object(self):
		"""
			load our YOLO object detector trained on COCO dataset (80 classes)
			returns yolo object dector
		"""
		print("[INFO] loading YOLO from disk...")
		configPath = self.get_yolo_path("yolov3.cfg")
		weightsPath = self.get_yolo_path("yolov3.weights")
		net =  cv2.dnn.readNetFromDarknet(configPath, weightsPath)
		return net


	def get_layer_names(self, yolo_object):
		"""
			determine only the *output* layer names that we need from YOLO
			returns layer names
		"""
		ln = yolo_object.getLayerNames()
		return [ln[i[0] - 1] for i in yolo_object.getUnconnectedOutLayers()]

	def detect_in_frame(self, net,output_time=False):
		"""
			detect vehicle in frame
			returns layer outputs, which contains class id and confidence probabilities 
		"""	

		#get yolo object and layer names 
		#net = self.get_yolo_object()
		ln = self.get_layer_names(net)

		# construct a blob from the input frame and then perform a forward
		# pass of the YOLO object detector, giving us our bounding boxes
		# and associated probabilities
		blob = cv2.dnn.blobFromImage(self.frame, 1 / 255.0, (416, 416),swapRB=True, crop=False)
		net.setInput(blob)
		start = time.time()
		layerOutputs = net.forward(ln)
		end = time.time() 
		if output_time == True:
			elap = (end - start)
			print("[INFO] single frame took {:.4f} seconds".format(elap))
		return layerOutputs

	def extract_detection_information(self,net):
		"""
			returns lists of detected bounding boxes, confidences, and class IDs, respectively
		"""

		# initialize our lists of detected bounding boxes, confidences,and class IDs, respectively
		boxes = []
		confidences= []
		classIDs = []
		layerOutputs = self.detect_in_frame(net)
		
		#grab frame dimensions
		(H,W) = self.frame.shape[:2]
		
		# loop over each of the layer outputs
		for output in layerOutputs:
			# loop over each of the detections
			for detection in output:
				# extract the class ID and confidence (i.e., probability) of the current object detection
				scores = detection[5:]
				classID = np.argmax(scores)
				score_confidence = scores[classID]

				# filter out weak predictions by ensuring the detected
				# probability is greater than the minimum probability
				if score_confidence > self.confidence:
					# scale the bounding box coordinates back relative to
					# the size of the image, keeping in mind that YOLO height
					box = detection[0:4] * np.array([W, H, W, H])
					(centerX, centerY, width, height) = box.astype("int")

					# use the center (x, y)-coordinates to derive the top
					# and and left corner of the bounding box
					x = int(centerX - (width / 2))				
					y = int(centerY - (height / 2))

					# update our list of bounding box coordinates,confidences and class IDs
					boxes.append([x, y, int(width), int(height)])
					confidences.append(float(score_confidence))
					classIDs.append(classID)

		return (boxes,confidences,classIDs)


	def apply_suppression(self,net):
		boxes = self.extract_detection_information(net)[0]
		confidences = self.extract_detection_information(net)[1]
		idxs = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence, self.threshold)
		return idxs 

	def detect_intersections(self,net):
		"""
			detects if the detected vehicle is within the ROI
			net: yolo object
		"""
		idxs = self.apply_suppression(net)
		LABELS = self.get_yolo_labels() 
		boxes = self.extract_detection_information(net)[0]
		classIDs = self.extract_detection_information(net)[2]

		#ensure at least one detection exists
		if len(idxs) > 0:
			#loop over indexes we are keeping
			carAmount = 0 
			for i in idxs.flatten():
				#extract the bounding box coordinates
				(x, y) = (boxes[i][0], boxes[i][1])
				(w, h) = (boxes[i][2], boxes[i][3])

				#get shape of bounding box to get intersection with ROI
				bounding_box = [(x,y),(x,y+h),(x+w,y+h),(x+w,y),(x,y)]
				bounding_box_x = [x,x,x+w,x+w,x]
				bounding_box_y = [y,y+h,y+h,y,y]
				ROI_x = [i[0] for i in self.ROI] 
				ROI_y = [i[1] for i in self.ROI] 
				print("bounding_box: " , bounding_box)
				print("self.ROI: ", self.ROI)
				#plt.plot(bounding_box_x,bounding_box_y, label="BBOX", linewidth=4, color="orange")
				#plt.plot(ROI_x, ROI_y, label="ROI", linewidth=4, color="magenta")
				plt.title("Figure {}, Intersect Threshold: {}, Vehicle Counted: {}".format("1", "0", True))
				#plt.show()
				intersects_flag = find_intersect.intersection_of_polygons(self.ROI,bounding_box,showPlot=True)
				if intersects_flag:
					if LABELS[classIDs[i]] == "car" or LABELS[classIDs[i] == "truck"]:
						carAmount += 1

			carsAmount = str(carAmount) + " vehicles in ROI"
			print(carsAmount)
		
		
			

if __name__ == "__main__":
	yolo_model = YoloVideo(cv2.imread("images/car.jpg"),[[116, 28], [115, 87], [204, 297], [431, 278], [503, 138], [481, 37], [295, 27], [117, 22], [116, 28]],"yolo-coco")
	net = yolo_model.get_yolo_object()
	yolo_model.detect_intersections(net)
