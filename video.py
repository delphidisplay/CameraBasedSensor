from camera import Camera 
import cv2

class Video(Camera):

	def __init__(self,url):
		super(Video,self).__init__(url)
		
	def __iter__(self):
		return VideoIterator(self)

	def build_video_stream(self,video_path):
		self.VS = cv2.VideoCapture(video_path) 
		grabbed, sample_frame = self.VS.read()
		return sample_frame



class VideoIterator:
	def __init__(self, video):
		self.video = video
		#self.VS = cv2.VideoCapture(self.video.url)

	def __next__(self):

		grabbed,frame = self.video.VS.read()
		if grabbed == False: 
			self.video.initialize_video_stream(self.video.url)
			grabbed,frame = self.video.VS.read()
		return frame 
