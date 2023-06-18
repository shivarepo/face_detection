from threading import Thread
import cv2
import face_recognition
import os
import numpy as np
import math
import logging
from v1.util.TextToSpeechUtil import TextToSpeechUtil
from v1.db.Attendance import Attendance
from v1.util.Util import Util
from concurrent.futures import ThreadPoolExecutor

class DetectFace:

    def __init__(self, data):
        logging.basicConfig(
            filename="../log/detect.log",
            level=logging.DEBUG,
            format="%(asctime)s:%(name)s:%(levelname)s:%(message)s"
            )

        self.logger = logging.getLogger("DetectFace")
        self.data = data
        # initialize the next unique object ID along with two ordered
        # dictionaries used to keep track of mapping a given object
        # ID to its centroid and number of consecutive frames it has
        # been marked as "disappeared", respectively
        self.nextObjectID = 0
        self.objects = dict()
        self.disappeared = dict()
        self.appeared = dict()  # {'CN1002':23}

        # store the number of maximum consecutive frames a given
        # object is allowed to be marked as "disappeared" until we
        # need to deregister the object from tracking
        self.maxDisappeared = 5

        # store the number of maximum consecutive frames a person has
        # appeared with more than 80% prediction
        self.maxAppeared = 5        

        # For making future calls
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        self.names = []
        self.percentageSize = [] 
        self.tts = TextToSpeechUtil()
        self.att = Attendance()      
        self.util = Util()

    def detect(self, r, rgb, boxes):
            return self.update(r,rgb, boxes)

    def extract_id(self, name):
        student_idname = name.split('_')
        student_id = student_idname[0]
        return student_id

    def register(self, personName):
        # when registering an object we use the next available object
        # ID to store the personName
        if(personName in self.objects):
            self.logger.debug('already registered {0}, {1}'.format(personName, self.appeared[personName]))
            self.disappeared[personName] = 0
            self.appeared[personName] = 0

        elif (personName != 'Unknown_Unknown'):
            self.objects[personName] = personName
            self.logger.debug('registered ' + personName)
            future = self.executor.submit(self.tts.welcome_student(personName))

    def deregister(self, personName):
        # to deregister an object ID we delete the object ID from
        # both of our respective dictionaries
        del self.objects[personName]
        del self.disappeared[personName]
        if any(personName in s for s in self.names):
            self.names.remove(personName)
        self.logger.debug('marking attendance ' + personName)
        self.att.mark_attendance(self.extract_id(personName)) 
        future = self.executor.submit(self.tts.play_alert())     

    def recognize_faces_in_boxes(self, r, frame, boxes):
        encodings = face_recognition.face_encodings(frame, boxes, num_jitters=1)

        self.names = []
        self.percentageSize = []
        counter = 0
        # loop over the facial embeddings
        for encoding in encodings:
            # attempt to match each face in the input image to our known
            # encodings
            matches = face_recognition.compare_faces(self.data["encodings"],
                                                    encoding, tolerance=0.4)
            name = "Unknown_Unknown"
            weightage = 0.5 # default set to 50% match

            # check to see if we have found a match
            if True in matches:
                # find the indexes of all matched faces then initialize a
                # dictionary to count the total number of times each face
                # was matched
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}

                # loop over the matched indexes and maintain a count for
                # each recognized face face
                for i in matchedIdxs:
                    name = self.data["names"][i]
                    counts[name] = counts.get(name, 0) + 1

                # determine the recognized face with the largest number
                # of votes (note: in the event of an unlikely tie Python
                # will select first entry in the dictionary)
                name = max(counts, key=counts.get)

            # update the list of names
            self.names.append(name)
            if (name != "Unknown_Unknown"):
                (top, right, bottom, left) = boxes[counter]
                # rescale the face coordinates
                top = int(top * r)
                right = int(right * r)
                bottom = int(bottom * r)
                left = int(left * r)

                length = (right - left)
                breadth = (bottom - top)
                diagonal = math.sqrt((length * 2) + (breadth * 2))
                weightage = diagonal / 40

                #self.logger.debug("diagonal square of face: " + str(diagonal))
                #self.logger.debug("weightage of face: " + str(weightage))

            counter = counter + 1

            try:
                self.appeared[name] += (1*weightage)
            except KeyError:
                self.appeared[name] = (1*weightage)

            # if we have reached a maximum number of consecutive
            # frames where a given object has been marked as
            # appeared, register it
            if self.appeared[name] > self.maxAppeared:
                if (name != "Unknown_Unknown"):
                    self.register(name)

        return self.names

    def update(self, r, frame, boxes):
        # check to see if the list of input bounding box rectangles
        # is empty
        if len(boxes) == 0:
            ##self.names = []
            # loop over any existing tracked objects and mark them
            # as disappeared
            for personName in self.disappeared.keys():
                self.disappeared[personName] += 1

                # if we have reached a maximum number of consecutive
                # frames where a given object has been marked as
                # missing, deregister it
                if self.disappeared[personName] > self.maxDisappeared:
                    self.deregister(personName)
                    break

            # return early as there are no centroids or tracking info
            # to update
            return self.names

        names = self.recognize_faces_in_boxes(r, frame, boxes)

        # return the set of trackable objectsq
        return names

    def add_identified_thumbnails(self, frame, names, path_to_thumbnails):
        identified_names = self.objects.keys()
        x_offset = 5
        y_offset = 500

        for id_name in identified_names:
            image_path = path_to_thumbnails + "/"+ id_name + "/face.jpg"
            face = cv2.imread(image_path)
            if (id_name != 'Unknown_Unknown'):
                height, width = face.shape[:2]
                resized_face = cv2.resize(face, (round(width/3), round(height/3)), interpolation = cv2.INTER_CUBIC)

                frame[y_offset:y_offset + resized_face.shape[0], x_offset:x_offset + resized_face.shape[1]] = resized_face
                y_offset = y_offset + resized_face.shape[0]
                
        return frame        