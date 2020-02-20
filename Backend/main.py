from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

class Client(Resource):
	def post(self):
		# Call Neural Net class and pass in coordinates
		print(request.form)
		pass



api.add_resource(Client, '/')

if __name__ == '__main__':
	app.run(debug=True)
