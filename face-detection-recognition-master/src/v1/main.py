import argparse
import cv2
import pickle
import imutils
import face_recognition

from v1.CaptureVideo import CaptureVideo
from v1.DetectFace import DetectFace

def start(source=0):

    data=pickle.loads(open('../resources/encodings.pickle', "rb").read())
    video_getter = CaptureVideo(source).start()
    face_detector = DetectFace(data)

    while True:
        if video_getter.stopped:
            video_getter.stop()
            break

        frame = video_getter.frame
        # convert the input frame from BGR to RGB then resize it to have
        # a width of 750px (to speedup processing)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #gave 1050 to support wide angle camera resolution
        rgb = imutils.resize(rgb,width=1050)
        r = frame.shape[1]/float(rgb.shape[1])

        names = []

        # detect the (x, y)-coordinates of the bounding boxes
        # corresponding to each face in the input frame, then compute
        # the facial embeddings for each face
        boxes = recognize_boxes_in_frame(rgb)
        names = face_detector.detect(r, rgb, boxes)

        show_faces(r, frame, boxes, names)

        #frame = face_detector.add_identified_thumbnails(frame, names, "../resources/faces")

        show_frame(frame)


def recognize_boxes_in_frame(rgb):
    # detect the (x, y)-coordinates of the bounding boxes
    # corresponding to each face in the input frame, then compute
    # the facial embeddings for each face
    boxes = face_recognition.face_locations(rgb, model='hog')
    return boxes 

def show_faces(r, frame, boxes, names):
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

def show_frame(frame):
        height, width = frame.shape[:2]
        resized_frame = cv2.resize(frame, (round(width/2), round(height/2)), interpolation = cv2.INTER_CUBIC)
        cv2.imshow("Live stream", resized_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            self.stopped = True

def main():
    display = 1
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", "-s", default=0,
        help="Path to video file or integer representing webcam index"
            + " (default 0).")

    args = vars(ap.parse_args())

    start(args["source"])

if __name__ == "__main__":
    main()
