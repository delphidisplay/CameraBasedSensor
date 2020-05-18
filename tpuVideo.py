import numpy as np
import time
import cv2
from find_intersect import intersection_of_polygons
import matplotlib.pyplot as plt

from detect_image import main_detection

#show_frame = True

#if show_frame:
#  cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
#  cv2.resizeWindow('frame', 1280, 720)

class YoloVideo:
  """
    Detection model to identify cars and trucks within a specific region of interest (ROI)
  """

  def __init__(self, net):
    """
      self.frame: frame from stream
      self.ROI: nested list defining region of intereest in frame in which we detect vehicles
      self.confidence: minimum probability to filter weak detections
      self.threshold: threshold when applying non-maxima suppression
    """
    self.net = net
    self.frame = None
    self.ROI = []
    self.confidence = 0.25
    self.threshold = 0.3
    self.debug = False
    self.detection_info = None

  def set_frame_and_roi(self,frame,camera):
    self.frame = frame

    # Ratios needed to resize the ROI coordinates to match the original frame
    x_ratio = camera.frontend_ratio[0]* camera.prepare_ratio[0]
    y_ratio = camera.frontend_ratio[1]* camera.prepare_ratio[1]

    self.ROI = []

    for coord in camera.ROI:
      self.ROI.append([coord[0]/x_ratio,coord[1]/y_ratio])

  def get_yolo_labels(self):
    """
      return the COCO class labels our YOLO model was trained on
    """
    labels_file = "models/coco_labels.txt"
    return labels_file


  def initiailize_colors(self, labels):
    """
      return a list of colors to represent each possible class label
    """
    np.random.seed(42)
    return  np.random.randint(0,255, size=(len(labels), 3), dtype="uint8")

  def get_layer_names(self):
    """
      determine only the *output* layer names that we need from YOLO
      returns layer names
    """
    ln = self.net.getLayerNames()
    return [ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]

  def detect_in_frame(self, output_time=False):
    """
      detect vehicle in frame
      returns layer outputs, which contains class id and confidence probabilities
    """

    objs, image = main_detection(self.net, 
            labels=self.get_yolo_labels(), image=self.frame, 
            threshold=self.confidence, count=1, 
            output=True)

    #if show_frame:
    #    cv2.imshow('frame', image)

    return objs

  def extract_detection_information(self):
    """
      returns lists of detected bounding boxes, confidences, and class IDs, respectively
    """

    # initialize our lists of detected bounding boxes, confidences,and class IDs, respectively
    boxes = []
    confidences= []
    classIDs = []
    output = self.detect_in_frame()

    #grab frame dimensions
    (H,W) = self.frame.shape[:2]

    # loop over each of the detections
    for detection in output:
        # extract the class ID and confidence (i.e., probability) of the current object detection
        classID = detection.id
        score_confidence = detection.score

        # filter out weak predictions by ensuring the detected
        # probability is greater than the minimum probability
        if score_confidence > self.confidence:
              # scale the bounding box coordinates back relative to
              # the size of the image, keeping in mind that YOLO height
              
              ###box = detection[0:4] * np.array([W, H, W, H])
              ###(centerX, centerY, width, height) = box.astype("int")

              # use the center (x, y)-coordinates to derive the top
              # and and left corner of the bounding box
              
              x = int(detection.bbox.xmin)
              y = int(detection.bbox.ymin)
              width = int(detection.bbox.xmax - detection.bbox.xmin)
              height = int(detection.bbox.ymax - detection.bbox.ymin)

              # update our list of bounding box coordinates,confidences and class IDs
              boxes.append([x, y, width, height])
              confidences.append(float(score_confidence))
              classIDs.append(classID)

    self.detection_info = (boxes,confidences,classIDs)
    
    #return (boxes,confidences,classIDs)


  def apply_suppression(self):
    #boxes = self.extract_detection_information()[0]
    #confidences = self.extract_detection_information()[1]
    boxes = self.detection_info[0]
    confidences = self.detection_info[1]
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence, self.threshold)
    return idxs

  def detect_intersections(self):
    """
      detects if the detected vehicle is within the ROI
      self.net: yolo object
    """
    
    self.extract_detection_information()

    idxs = self.apply_suppression()
    LABELS = self.get_yolo_labels()
    #boxes = self.extract_detection_information()[0]
    #classIDs = self.extract_detection_information()[2]

    boxes = self.detection_info[0]
    classIDs = self.detection_info[2]

    #ensure at least one detection exists
    if len(idxs) > 0:
      #loop over indexes we are keeping
      carAmount = 0
      for i in idxs.flatten():
        #extract the bounding box coordinates
        (x, y) = (boxes[i][0], boxes[i][1])
        (w, h) = (boxes[i][2], boxes[i][3])

        #get shape of bounding box to get intersection with ROI
        bounding_box = [(x,y),(x,y+h),(x+w,y+h),(x+w,y),(x,y)]

        if self.debug:
          #plot bounding box and ROI to see if they make sense
          bounding_box_x = [x,x,x+w,x+w,x]
          bounding_box_y = [y,y+h,y+h,y,y]
          ROI_x = [i[0] for i in self.ROI]
          ROI_y = [i[1] for i in self.ROI]
          print("bounding_box: " , bounding_box)
          print("self.ROI: ", self.ROI)
          # plt.plot(bounding_box_x,bounding_box_y, label="BBOX", linewidth=4, color="orange")
          # plt.plot(ROI_x, ROI_y, label="ROI", linewidth=4, color="magenta")
          # plt.title("Figure {}, Intersect Threshold: {}, Vehicle Counted: {}".format("1", "0", True))
          # plt.show()

        intersects_flag = intersection_of_polygons(self.ROI,bounding_box)
        if intersects_flag:
          #if LABELS[classIDs[i]] == "car" or LABELS[classIDs[i] == "truck"]:
          carAmount += 1
          print("Intersection with ROI: TRUE")

      #carsAmount = str(carAmount) + " vehicles in ROI"
      return carAmount
    return 0

'''
if __name__ == "__main__":
  yolo_model = YoloVideo(cv2.imread("images/car.jpg"),[[116, 28], [115, 87], [204, 297], [431, 278], [503, 138], [481, 37], [295, 27], [117, 22], [116, 28]],"yolo-coco")
  self.net = yolo_model.get_yolo_object()
  yolo_model.detect_intersections(self.net)
'''
