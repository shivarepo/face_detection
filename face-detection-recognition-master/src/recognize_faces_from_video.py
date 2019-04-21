# USAGE
# python recognize_faces_from_video.py --encodings ../resources/encodings.pickle --detection-method hog --output ../output

# import the necessary packages
from imutils.video import VideoStream
import face_recognition
import argparse
import imutils
import pickle
import time
import cv2
from trackerutil import TrackerAndRegisterUtil
import datetime
import logging

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-e", "--encodings", required=True,
	help="path to serialized db of facial encodings")
ap.add_argument("-o", "--output", type=str,
	help="path to output video")
ap.add_argument("-y", "--display", type=int, default=1,
	help="whether or not to display output frame to screen")
ap.add_argument("-d", "--detection-method", type=str, default="hog",
	help="face detection model to use: either `hog` or `cnn`")
ap.add_argument("-tn", "--faces", type=str,
    help="face of the registered student", default="../resources/faces")
#ap.add_argument("-m", "--mp3", type=str, help="path to mp3 welcome sounds", default='../resources/welcome_messages/')


args = vars(ap.parse_args())

logging.basicConfig(
	filename="faceid.log",
	level=logging.DEBUG,
	format="%(asctime)s:%(name)s:%(levelname)s:%(message)s"
	)

logger = logging.getLogger("RecognizeFacesFromVideo")

# load the known faces and embeddings
logger.info('loading encodings... ')
data = pickle.loads(open(args["encodings"], "rb").read())

tu = TrackerAndRegisterUtil()

# initialize the video stream and pointer to output video file, then
# allow the camera sensor to warm up
logger.info('starting video stream... ')
vs = VideoStream(src=0).start()

#url = 'rtsp://admin:admin@192.168.1.101/1'
#vs = VideoStream(src=url).start()

writer = None
time.sleep(2.0)
counter = 0

# loop over frames from the video file stream
while True:
	# grab the frame from the threaded video stream
	frame = vs.read()

	names = []
	# convert the input frame from BGR to RGB then resize it to have
	# a width of 750px (to speedup processing)
	rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	#rgb = imutils.resize(rgb, width=750)

	#gave 1050 to support wide angle camera resolution
	rgb = imutils.resize(rgb,width=1050)
	r = frame.shape[1] / float(rgb.shape[1])

	# detect the (x, y)-coordinates of the bounding boxes
	# corresponding to each face in the input frame, then compute
	# the facial embeddings for each face
	boxes = tu.recognize_boxes_in_frame(rgb, detection_method=args["detection_method"])

	names = tu.update(r, rgb, boxes)

	# loop over the recognized faces
	for ((top, right, bottom, left), name) in zip(boxes, names):

		# rescale the face coordinates
		top = int(top * r)
		right = int(right * r)
		bottom = int(bottom * r)
		left = int(left * r)

		# splitting name from student_idname
		try:
			student_idname = name.split('_')
			student_id = student_idname[0]
			student_name = student_idname[1]
		except Exception as e:
			logger.error('Please provide folder name like <rollnumber>_<name> -' + name)

		# draw the predicted face name on the image
		cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
		y = top - 15 if top - 15 > 15 else top + 15
		cv2.putText(frame, student_name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

	frame = tu.add_identified_thumbnails(frame, names, args["faces"])


	# if the video writer is None *AND* we are supposed to write
	# the output video to disk initialize the writer
	# Define the codec and create VideoWriter object to save the video
	if writer is None and args["output"] is not None:
		fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
		uniq_filename = args["output"] +'/' + str(datetime.datetime.now().date()) + '_' + str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S"))
		writer = cv2.VideoWriter(uniq_filename+'_output.m4v', fourcc, 20.0, (frame.shape[1], frame.shape[0]))

	# if the writer is not None, write the frame with recognized
	# faces to disk
	if writer is not None and 'Unknown_Unknown' in names:
		writer.write(frame)

	# check to see if we are supposed to display the output frame to
	# the screen
	if args["display"] > 0:
		height, width = frame.shape[:2]
		resized_frame = cv2.resize(frame, (round(width/2), round(height/2)), interpolation = cv2.INTER_CUBIC)
		cv2.imshow("Live stream", resized_frame)
		key = cv2.waitKey(1) & 0xFF

		# if the `q` key was pressed, break from the loop
		if key == ord("q"):
			break

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()

# check to see if the video writer point needs to be released
if writer is not None:
	writer.release()
