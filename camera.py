# Python-specific imports
from imutils.video import VideoStream

class Camera:

	""" 
		url: The camera url passed in
		ROI: A list containing all of the coordinates of the Bounding Box.
		VS: A VideoStream object that streams from the camera url
		dimensions: A list containing the width and height of each frame we would receive.
	"""

	def __init__(self, url):
		"""
			Basic setup of the object, instanstiates url and starts a new video stream 
		"""
		self.url = url
		self.ROI = None
		self.initialize_video_stream(url)

	def __iter__(self):
		""" 
			Overwrites the default iter function so that you can iterate through this camera. 
		"""
		return CameraIterator(self)
	
	def __repr__(self):
		""" 
			String representation of the object. 
		"""
		return 'URL: {}, ROI: {}'.format(self.url,self.ROI)

	def set_roi_coordinates(self, coordinates):
		""" 
			Updates Region of Interest(ROI) with the coordinates specified from the frontend. 
		"""
		self.ROI = coordinates
		
	def initialize_video_stream(self,camera_url):
		""" 
			Given a camera url, build a stream object and get the dimensions of it. 
		"""
		# Build Stream
		self.VS = VideoStream(src=camera_url).start()
		
		# If we are not able to read a proper frame from the stream, this will fail.
		sample_frame = self.VS.read()
		assert sample_frame is not None

		# Set the width and height.
		self.dimensions = sample_frame.shape		

	def stop_video_stream(self):
		""" 
			Turns off the Video Stream 
		"""
		self.VS.stop()
		
class CameraIterator:

	""" 
		This object is created so that you can iterate through a camera object 
	"""

	def __init__(self, camera):
		""" 
			Basic setup of iterator object. 
		"""
		self.camera = camera

	def __next__(self):
		""" 
			Allows iterating over this object to get each frame. Ex: "for frame in camera..." 
		"""

		# If we are not able to read a proper frame from the stream, this will fail.
		frame = self.camera.VS.read()
		assert frame is not None

		return frame

""" 
	Testing to check for how long it takes to run 
"""
if __name__ == '__main__':
	sample = Camera(url = 0)
	i = 0
	for frame in sample:
		if i > 1:
			break
		print(frame)
		i += 1
