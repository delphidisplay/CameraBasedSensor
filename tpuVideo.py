import numpy as np
import time
import cv2
from find_intersect import intersection_of_polygons
import matplotlib.pyplot as plt

from detect_image import main_detection, load_labels
from tpu_tiny_yolo_inference import image_inf
from tpu_utils_tiny_yolo import get_anchors, get_classes


class YoloVideo:
  """
    Detection model to identify cars and trucks within a specific region of interest (ROI)
  """

  def __init__(self, net, modelType):
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
    self.pickedClass = ['car', 'motorcycle', 'truck', 'bus'] # detection classes to keep
    self.debug = False
    self.detection_info = None
    self.modelType = modelType # choose tiny-yolo or mobilenet
    self.labels = load_labels(self.get_yolo_labels()) if self.get_yolo_labels() else {}


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

    if self.modelType == "tpu-mobilenet":
        objs, labeledImage = main_detection(self.net, 
            labels=self.labels, image=self.frame, pickedClass=self.pickedClass,
            threshold=self.confidence, labeledOutputImage=False)

    elif self.modelType == "tpu-tiny-yolo": 
        anchorsPath = "models/tiny_yolo_anchors.txt"
        classesPath = "models/coco.names"

        anchors = get_anchors(anchorsPath)
        classes = get_classes(classesPath)
        
        objs, labeledImage = image_inf(self.net, anchors, 
            self.frame, classes, self.confidence, labeledOutputImage=False)
    

    #print(objs)
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
              
              x = int(detection.bbox.xmin)
              y = int(detection.bbox.ymin)
              width = int(detection.bbox.xmax - detection.bbox.xmin)
              height = int(detection.bbox.ymax - detection.bbox.ymin)

              # update our list of bounding box coordinates,confidences and class IDs
              boxes.append([x, y, width, height])
              confidences.append(float(score_confidence))
              classIDs.append(classID)

    self.detection_info = (boxes,confidences,classIDs)


  def apply_suppression(self):
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
    LABELS = self.labels

    boxes = self.detection_info[0]
    confidences = self.detection_info[1]
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
        
        if LABELS.get(classIDs[i], classIDs[i]) in self.pickedClass:
          intersects_flag = intersection_of_polygons(self.ROI,bounding_box)
          if intersects_flag:
            carAmount += 1
            print(f"DETECTED: {LABELS.get(classIDs[i], classIDs[i])}, CONFIDENCE: {confidences[i]}")
            print("Intersection with ROI: TRUE")

      return carAmount
    return 0

'''
if __name__ == "__main__":
  yolo_model = YoloVideo(cv2.imread("images/car.jpg"),[[116, 28], [115, 87], [204, 297], [431, 278], [503, 138], [481, 37], [295, 27], [117, 22], [116, 28]],"yolo-coco")
  self.net = yolo_model.get_yolo_object()
  yolo_model.detect_intersections(self.net)
'''
