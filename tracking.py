import cv2
from time import sleep
import imutils
import numpy as np

from find_intersect import intersection_of_polygons

# used for tracking vehicles in streams

# steps to success
# 1. modify self.isTracked = True once detection in ROI occurs
# 2. initialize tracker if self.isTracked = True
# 3. update tracker until self.isTracked = False


class TrackingStream: # SPEED UP - TESTING reduces frame in half before feeding to tracker for speed

	def __init__(self, bbox, frame, trackedClass, ROI):
		
		self.bbox = bbox # FIGURE OUT WHAT BOUNDING BOX IS INPUT, should be top left, bottom right
		self.tracker = None
		self.init_tracker(frame)
		self.debug = True
		self.trackedClass = trackedClass
		self.ROI = ROI
		self.DEBUG_IMAGE = np.ones([100,100,3],dtype=np.uint8) * 200
	

	def init_tracker(self, frame, trackerType="kcf"):
		"""initializes the OpenCV multitracker object"""
		multiTracker = cv2.MultiTracker_create()

		frame = imutils.resize(frame, width=int(frame.shape[1]/2), height=int(frame.shape[0]/2)) # SPEED UP - TESTING
		
		for bbox in self.bbox:
		
			bbox = tuple([int(v/2) for v in bbox]) # SPEED UP - TESTING
		
			multiTracker.add(createTrackerByName(trackerType), frame, bbox)
	
		self.tracker = multiTracker


	def update_tracker(self, frame):
		"""returns bbox after updating tracker on new frame"""		
		small_frame = imutils.resize(frame, width=int(frame.shape[1]/2), height=int(frame.shape[0]/2)) # SPEED UP - TESTING
		success, boxes = self.tracker.update(small_frame)
		sleep(0.01) # tracking is very fast, may crash otherwise
		if not success:
			return False, self.DEBUG_IMAGE
		
		#extract the bounding box coordinates
		(x, y, w, h) = [int(v*2) for v in boxes[0]] # gets only first box, SPEED UP - TESTING

		#get shape of bounding box to get intersection with ROI
		bounding_box = [(x,y),(x,y+h),(x+w,y+h),(x+w,y),(x,y)]
		
		intersects_flag = intersection_of_polygons(self.ROI, bounding_box)
		
		if self.debug: # create debug image
			self.draw_debug_setup(frame)
			self.draw_debug_bbox([x, y, w, h], intersects_flag, frame)

		self.bbox = [[x, y, w, h]]
		return intersects_flag, self.DEBUG_IMAGE



	def draw_debug_setup(self, frame): # draw roi and setup text
		self.DEBUG_IMAGE = frame
		
		cv2.putText(self.DEBUG_IMAGE, text=f"TRACKING MODE", 
					org=(int(self.DEBUG_IMAGE.shape[1]*0.75), 40), fontFace=cv2.FONT_HERSHEY_SIMPLEX, 
					fontScale=1, color=(255,255,150), thickness=2, lineType=cv2.LINE_AA)
		
		cv2.polylines(self.DEBUG_IMAGE, [np.asarray(self.ROI, np.int32).reshape((-1,1,2))], True, (255,255,150), 3) #roi

	
	def draw_debug_bbox(self, bbox, intersects_flag, frame):
		x, y, w, h = bbox	
				
		debugColor = (0, 0, 255) # red
		if intersects_flag:
			debugColor = (0,255,0) # green

		cv2.rectangle(self.DEBUG_IMAGE, (x, y), (x+w, y+h), debugColor, 2)
		cv2.putText(self.DEBUG_IMAGE, text=f"TRACKING {self.trackedClass}", 
					org=(x,y-5), fontFace=cv2.FONT_HERSHEY_SIMPLEX, 
					fontScale=1, color=debugColor, thickness=2, lineType=cv2.LINE_AA)	
		
		
def createTrackerByName(trackerType):
	"""returns correct tracker from OpenCV object tracker API"""

	OPENCV_OBJECT_TRACKERS = {
		"csrt": cv2.TrackerCSRT_create,
		"kcf": cv2.TrackerKCF_create,
		"boosting": cv2.TrackerBoosting_create,
		"mil": cv2.TrackerMIL_create,
		"tld": cv2.TrackerTLD_create,
		"medianflow": cv2.TrackerMedianFlow_create,
		"mosse": cv2.TrackerMOSSE_create
	}

	return OPENCV_OBJECT_TRACKERS[trackerType]()
    
    
    
    
    
    
    