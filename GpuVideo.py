import cv2 
import numpy
import pycuda.autoinit

from trt_utils.ssd import TrtSSD

class GpuVideo(YoloVideo):

	def __init__(self,trt_ssd):
		super(GpuVideo, self).__init__(trt_ssd)
		self.trt_ssd = trt_ssd

	def detect_in_frame(self, output_time=False):
		return self.trt_ssd.detect(self.frame, self.confidence)
		
	def extract_detection_information(self):
		boxes= []
		confidences = []
		classIDs = []
		output_boxes, confidences, classIDs = self.detect_in_frame()
		
		for bb in output_boxes:
			x_min, y_min, x_max, y_max = bb[0], bb[1], bb[2], bb[3] 
			x = int(x_min) 
			y = int(y_min) 
			width = int(xmax - xmin)
			height = int(ymax - ymin)

			boxes.append([x,y,width, height])
		self.detection_info = (boxes, confidences,classIDs)
	
