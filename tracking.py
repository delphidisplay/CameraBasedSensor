import cv2
from time import sleep
import imutils

from find_intersect import intersection_of_polygons

# used for tracking vehicles in streams

# steps to success
# 1. modify self.isTracked = True once detection in ROI occurs
# 2. initialize tracker if self.isTracked = True
# 3. update tracker until self.isTracked = False


class TrackingStream: # SPEED UP - TESTING reduces frame in half before feeding to tracker for speed

	def __init__(self, bbox, frame):
		
		self.bbox = bbox # FIGURE OUT WHAT BOUNDING BOX IS INPUT, should be top left, bottom right
		self.tracker = None
		self.init_tracker(frame)
	

	def init_tracker(self, frame, trackerType="kcf"):
		"""initializes the OpenCV multitracker object"""
		multiTracker = cv2.MultiTracker_create()

		frame = imutils.resize(frame, width=int(frame.shape[1]/2), height=int(frame.shape[0]/2)) # SPEED UP - TESTING
		
		for bbox in self.bbox:
		
			bbox = tuple([int(v/2) for v in bbox]) # SPEED UP - TESTING
		
			multiTracker.add(createTrackerByName(trackerType), frame, bbox)
	
		self.tracker = multiTracker


	def update_tracker(self, frame, ROI):
		"""returns bbox after updating tracker on new frame"""		
		frame = imutils.resize(frame, width=int(frame.shape[1]/2), height=int(frame.shape[0]/2)) # SPEED UP - TESTING
		success, boxes = self.tracker.update(frame)
		
		if not success:
			return False, None
		
		#extract the bounding box coordinates
		(x, y, w, h) = [int(v*2) for v in boxes[0]] # gets only first box, SPEED UP - TESTING

		#get shape of bounding box to get intersection with ROI
		bounding_box = [(x,y),(x,y+h),(x+w,y+h),(x+w,y),(x,y)]
		
		intersects_flag = intersection_of_polygons(ROI,bounding_box) # ALWAYS FALSE FOR SOME REASON
		
		###if intersects_flag: # COMMENTED OUT BECAUSE intersects_flag is always false
		###	self.bbox = boxes
		###	return success, self.bbox
		
		###return False, None
		
		self.bbox = boxes
		return success, boxes
 	
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
    
    
    
    
    
    
    