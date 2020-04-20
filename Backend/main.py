from flask import Flask, request
from flask_restful import Resource, Api
from collections import defaultdict

app = Flask(__name__)
api = Api(app)

cameras = defaultdict(list)

"""FORMAT: 
curl --header "Content-Type: application/json"\
	--request POST \
	--data '{"dimensions":"", "top-left":"","top-right":"","bottom-left":"","bottom-right":""}' \
	<our_url>

"""
class ReceiveCoordinates(Resource):
	def post(self, camera_id):
		print("FORM: {}".format(request.form))

		# TODO: Validate coordinates if legit.
		

		# TODO: Change bounding box size of the algorithm
		cameras[camera_id] = []
		
		# TODO: Return successful message.
	
		return 'Update'

"""Data depends on the camera. YMMV"""
class ReceiveCameraFeed(Resource):
	# Points the to drivethru box where someone places their order. Part 1
	def post(self, camera_id):
		print("FORM: {}".format(request.form))
		# TODO: Convert the camera feed to the specified format needed. (.mp4 or .avi)
		# TODO: OPTIONAL: Compress the feed based on certain factors (EX: only certain frames, video quality, etc) 
		# TODO: Send the feed into the algorithm. (Ask the algorithm team how
		# TODO: Get the result from the algorithm.
		# Return 
		return 'Feed'



api.add_resource(ReceiveCoordinates, '/<string:camera_id>/update')
api.add_resource(ReceiveCameraFeed, '/<string:camera_id>/feed')

if __name__ == '__main__':
	app.run(host="0.0.0.0",port = 3000,debug=True)

