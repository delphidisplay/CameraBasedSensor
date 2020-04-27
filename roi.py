# Region Of Interest (ROI) related functions

from shapely.geometry import Polygon
from find_intersect import list_of_tuples

def is_valid_roi(nested_list):
	"""
	Validates the list of [x,y] coordinates that defines the ROI to see if it is a valid shape.
	A valid shape is defined as a Polygon with no intersecting edges ie. no hourglass/bowtie shapes.
	"""
	try:
		shape = Polygon(list_of_tuples(nested_list)) # Polygon object only accepts list of (x,y) tuples
		return shape.is_valid # determines shape validity
	except Exception as e: # exception if Polygon was not able to be created for any reason ie. bad input
		print(e)
		return False