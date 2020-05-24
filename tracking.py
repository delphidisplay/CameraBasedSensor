import cv2
from find_intersect import intersection_of_polygons

# used for tracking vehicles in streams

# steps to success
# 1. modify self.isTracked = True once detection in ROI occurs
# 2. initialize tracker if self.isTracked = True
# 3. update tracker until self.isTracked = False


class TrackingStream:

	def __init__(self, bbox, frame):
		self.bbox = bbox # FIGURE OUT WHAT BOUNDING BOX IS INPUT, should be top left, bottom right
		self.tracker = self.init_tracker(frame)
	

	def init_tracker(self, frame, trackerType="csrt"):
		"""initializes the OpenCV multitracker object"""
		multiTracker = cv2.MultiTracker_create()
		for bbox in self.bbox:
			multiTracker.add(createTrackerByName(trackerType), frame, bbox)
	
		self.tracker = multiTracker


	def update_tracker(self, frame, ROI):
		"""returns bbox after updating tracker on new frame"""
		success, boxes = self.tracker.update(frame)
		
		#extract the bounding box coordinates
		(x, y) = (boxes[0][0], boxes[0][1])
		(w, h) = (boxes[0][2], boxes[0][3])

		#get shape of bounding box to get intersection with ROI
		bounding_box = [(x,y),(x,y+h),(x+w,y+h),(x+w,y),(x,y)]
		
		intersects_flag = intersection_of_polygons(ROI,bounding_box)
		if intersects_flag:
			self.bbox = boxes
			return success, self.bbox
		
		return False, None

 	
#def createTrackerByName(trackerType):
#	"""returns correct tracker from OpenCV object tracker API"""
#
#	OPENCV_OBJECT_TRACKERS = {
#		"csrt": cv2.TrackerCSRT_create(),
#		"kcf": cv2.TrackerKCF_create,
#		"boosting": cv2.TrackerBoosting_create,
#		"mil": cv2.TrackerMIL_create,
#		"tld": cv2.TrackerTLD_create,
#		"medianflow": cv2.TrackerMedianFlow_create,
#		"mosse": cv2.TrackerMOSSE_create
#	}
#
#	return OPENCV_OBJECT_TRACKERS[trackerType]
	
	
def createTrackerByName(trackerType):
  """returns correct tracker from OpenCV object tracker API"""
  trackerTypes = ['boosting', 'mil', 'kcf', 'tld', 'medianflow', 'goturn', 'mosse', 'csrt']

  # Create a tracker based on tracker name
  if trackerType == trackerTypes[0]:
    tracker = cv2.TrackerBoosting_create()
  elif trackerType == trackerTypes[1]:
    tracker = cv2.TrackerMIL_create()
  elif trackerType == trackerTypes[2]:
    tracker = cv2.TrackerKCF_create()
  elif trackerType == trackerTypes[3]:
    tracker = cv2.TrackerTLD_create()
  elif trackerType == trackerTypes[4]:
    tracker = cv2.TrackerMedianFlow_create()
  elif trackerType == trackerTypes[5]:
    tracker = cv2.TrackerGOTURN_create()
  elif trackerType == trackerTypes[6]:
    tracker = cv2.TrackerMOSSE_create()
  elif trackerType == trackerTypes[7]:
    tracker = cv2.TrackerCSRT_create()
  else:
    tracker = None
    print('Incorrect tracker name')
    print('Available trackers are:')
    for t in trackerTypes:
      print(t)

  return tracker
    
    
    
    
    
    
    