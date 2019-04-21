# USAGE
# python encode_faces.py --dataset ../dataset --encodings ../resources/encodings.pickle

# import the necessary packages
from imutils import paths
import face_recognition
import argparse
import pickle
import cv2
import os
import logging
from trackerutil import TrackerAndRegisterUtil


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--dataset", required=True,
	help="path to input directory of faces + images")
ap.add_argument("-e", "--encodings", required=True, default='encodings.pickle',
	help="path to serialized db of facial encodings")
ap.add_argument("-d", "--detection-method", type=str, default='hog',
	help="face detection model to use: either `hog` or `cnn`")
args = vars(ap.parse_args())

# grab the paths to the input images in our dataset

logging.basicConfig(
	filename="encode.log",
	level=logging.DEBUG,
	format="%(asctime)s:%(name)s:%(levelname)s:%(message)s"
	)

logger = logging.getLogger("EncodeFaces")

logger.info("quantifying faces...")

imagePaths = list(paths.list_images(args["dataset"]))

tu = TrackerAndRegisterUtil()

# initialize the list of known encodings and known names
knownEncodings = []
knownNames = []

# loop over the image paths
for (i, imagePath) in enumerate(imagePaths):
	# extract the person name from the image path
	logger.info("Processing image {}/{}".format(i + 1,
		len(imagePaths)))
	name = imagePath.split(os.path.sep)[-2]

	# load the input image and convert it from RGB (OpenCV ordering)
	# to dlib ordering (RGB)
	image = cv2.imread(imagePath)
	rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

	# detect the (x, y)-coordinates of the bounding boxes
	# corresponding to each face in the input image
	boxes = face_recognition.face_locations(rgb,
		model=args["detection_method"])

	# compute the facial embedding for the face
	encodings = face_recognition.face_encodings(rgb, boxes)

	# loop over the encodings
	for encoding in encodings:
		# add each encoding + name to our set of known names and
		# encodings
		knownEncodings.append(encoding)
		knownNames.append(name)

#generating welcome messages
logger.info("generating welcome messages...")
tu.generate_welcome_mgs(knownNames)

# dump the facial encodings + names to disk
logger.info("serializing encodings...")
data = {"encodings": knownEncodings, "names": knownNames}
f = open(args["encodings"], "wb")
f.write(pickle.dumps(data))
f.close()


