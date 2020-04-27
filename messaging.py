# Includes JSON messaging function to notify Delphi Track System of vehicle entering/leaving camera ROI
# Includes CameraNode Class and initCameras() to manage identifying vehicle ID at each camera

import datetime
from time import sleep

class CameraNode:
	"""
	CameraNode allows each Camera to keep track of the vehicles it has in queue waiting, the current vehicle
	being serviced, and where to send the current vehicle once service is complete. The methods vehicle_entered()
	and vehicle_left() also perform error checking to ensure vehicles go to where there belong from beginning to finish.
	"""
	def __init__(self, camera_name, next_camera):
		self.queue = [] # vehicles enter the queue via insertion on index 0 and leave the queue via popping
		self.camera_name = camera_name # name of camera for messaging to Delphi Track System and debug statements
		self.next_camera = next_camera # when vehicle_left() is called, self.current_vehicle is sent to self.next_camera.queue
		self.current_vehicle = None # stores vehicle id in service
		self.start = False # used to know where start of camera chain is
		self.debug = True # print debug messages

	def vehicle_entered(self):
		"""
		If called, pops vehicle from the queue and sets that vehicle as the current vehicle.
		Creates a JSON message for use to communicate with the Delphi Track System when ready.
		"""
		if self.current_vehicle is None and self.queue != []:
			self.current_vehicle = self.queue.pop()

			if self.debug:
				print("VEH {} ENTER CAM {}".format(self.current_vehicle, self.camera_name))

			send_vehicle_message(self.camera_name, self.current_vehicle, 1)

		else:
			if self.current_vehicle is not None:
				if self.debug:
					print("ERROR ON ENTER {}: vehicle {} is already at station".format(self.camera_name, self.current_vehicle))
			if self.queue == []:
				if self.debug:
					print("ERROR ON ENTER {}: No vehicles in queue".format(self.camera_name, self.current_vehicle))

			send_vehicle_message(self.camera_name, self.current_vehicle, 0)

	def vehicle_left(self):
		"""
		If called, inserts current vehicle into the next camera's queue and sets the current vehicle to None.
		Creates a JSON message for use to communicate with the Delphi Track System when ready.
		"""
		if self.current_vehicle is not None:
			if self.debug:
				print("VEH {} LEFT CAM {}".format(self.current_vehicle, self.camera_name))
			send_vehicle_message(self.camera_name, self.current_vehicle, 2)

			self.next_camera.queue.insert(0, self.current_vehicle)
			self.current_vehicle = None

		else:
			if self.debug:
				print("ERROR ON LEFT {}: No vehicle present to leave".format(self.camera_name, self.current_vehicle))
			send_vehicle_message(self.camera_name, self.current_vehicle, 0)

def initCameras(camera_names=["1", "2", "3"], debug=True): #in order of access
	"""
	Initializes the names in camera_names each as a CameraNode stored in a dictionary where the key is the camera_name.
	This initializes the vehicle tracking system using CameraNode objects properly.
	"""
	camera_nodes = {} # Empty dictionary
	camera_nodes[camera_names[0]] = None # Initialize dummy value in dictionary

	for idx in reversed(range(len(camera_names))): # store CameraNode for each camera_name in camera_nodes dictionary
		nextidx = idx+1 if idx+1 < len(camera_names) else 0

		current_name = camera_names[idx]
		next_name = camera_names[nextidx] # used to get the next CameraNode that this CameraNode will point to in self.next_camera

		camera_nodes[current_name]=CameraNode(current_name, camera_nodes[next_name])

	camera_nodes[camera_names[-1]].next_camera=camera_nodes[camera_names[0]]
	# attaches last camera's self.next_camera to first camera so vehicles leaving the last camera will go to first camera's queue
	camera_nodes[camera_names[0]].queue=list(range(10, 0, -1)) # initialize 10 vehicles starting in the queue of the first camera
	camera_nodes[camera_names[0]].start = True # initialize starting camera as True

	if debug:
		for name in camera_names:
			print("CURRENT CAMERA: ", camera_nodes[name].camera_name)
			print("NEXT CAMERA: ", camera_nodes[name].next_camera.camera_name)
			print()

		print("CAMERA NODES: ", camera_nodes)

	return camera_nodes

def send_vehicle_message(camera_name, vehicle_name, status):
	"""
	Print a JSON message specifying the state of a specific camera's current events.
	This message will eventually be sent to the Delphi Track System when that system is ready to keep track of vehicles.
	"""
	message={}
	message["camera_id"]=camera_name
	message["timestamp"]= datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # millisecond accuracy to 3 digits
	message["vehicle_id"]=vehicle_name
	message["status"]=status # status 0 is error, 1 is vehicle entered, 2 is vehicle left

	#print("MESSAGE: ", message) #uncomment to see message

def prettify_messaging(camera_nodes):
	"""Print a text representation of the state of all the CameraNode objects in camera_nodes"""
	prettyText = "S | ---"

	all_keys = list(camera_nodes.keys()) # get all camera names

	for key in all_keys:
		if camera_nodes[key].start == True: # find start of camera chain
			break

	count = len(all_keys)-1

	while count >= 0: # show the queue, camera name, and current vehicle for the CameraNode
		prettyText+= " {} --- {} ({}) --- ".format(camera_nodes[key].queue, camera_nodes[key].camera_name, camera_nodes[key].current_vehicle)
		key = camera_nodes[key].next_camera.camera_name
		count -= 1

	prettyText+="| E"

	print(prettyText)
	print()

def testMessageSystem():
	"""
	Test the camera node vehicle tracking and messaging system. Try your own method calls.
	"""
	print("TESTING MESSAGE SYSTEM")

	dict = initCameras(camera_names=["MENU", "PAY", "PICKUP"], debug=False) # initialize at least one item in camera_names

	dict["MENU"].vehicle_entered(); prettify_messaging(dict); sleep(.01)
	dict["MENU"].vehicle_left(); prettify_messaging(dict); sleep(.01)
	dict["PAY"].vehicle_entered(); prettify_messaging(dict); sleep(.01)
	dict["MENU"].vehicle_entered(); prettify_messaging(dict); sleep(.01)
	dict["PAY"].vehicle_left(); prettify_messaging(dict); sleep(.01)
	dict["MENU"].vehicle_left(); prettify_messaging(dict); sleep(.01)
	dict["MENU"].vehicle_left(); prettify_messaging(dict); sleep(.01) # testing error state
	dict["PICKUP"].vehicle_entered(); prettify_messaging(dict); sleep(.01)
	dict["PICKUP"].vehicle_left(); prettify_messaging(dict); sleep(.01)
	dict["MENU"].vehicle_entered(); prettify_messaging(dict); sleep(.01)
	dict["MENU"].vehicle_left(); prettify_messaging(dict); sleep(.01)
	dict["PAY"].vehicle_entered(); prettify_messaging(dict); sleep(.01)

if __name__ == "__main__":
	testMessageSystem()
