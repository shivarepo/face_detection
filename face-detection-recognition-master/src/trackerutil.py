# import the necessary packages
import requests
import face_recognition
import pickle
from gtts import gTTS
import os
import numpy as np
import cv2
import math
from concurrent.futures import ThreadPoolExecutor
import logging
from pygame import mixer
from google.cloud import texttospeech


class TrackerAndRegisterUtil():

    def __init__(self, maxDisappeared=25, maxAppeared=25):
        logging.basicConfig(
            filename="test.log",
            level=logging.DEBUG,
            format="%(asctime)s:%(name)s:%(levelname)s:%(message)s"
            )

        self.logger = logging.getLogger("TrackerAndRegisterUtil")

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
        self.maxDisappeared = maxDisappeared

        # store the number of maximum consecutive frames a person has
        # appeared with more than 80% prediction
        self.maxAppeared = maxAppeared

        self.data=pickle.loads(open('../resources/encodings.pickle', "rb").read())
        self.names = []
        self.percentageSize = []
        self.tts = None
        self.mp3_path = '../resources/welcome_messages/'

        # define the api endpoint
        self.url1 = "http://providencecnr.in/api/readerentry?$99999&99&"
        self.url2 = "&16122017143623*"

        # For making future calls
        self.executor = ThreadPoolExecutor(max_workers=3)

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
            self.welcome_student(personName)

    def deregister(self, personName):
        # to deregister an object ID we delete the object ID from
        # both of our respective dictionaries
        del self.objects[personName]
        del self.disappeared[personName]
        if any(personName in s for s in self.names):
            self.names.remove(personName)
        self.logger.debug('marking attendance ' + personName)
        self.mark_attendance(personName)

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

                self.logger.debug("diagonal square of face: " + str(diagonal))
                self.logger.debug("weightage of face: " + str(weightage))

            counter = counter + 1

            try:
                self.appeared[name] += (1*weightage)
            except KeyError:
                self.appeared[name] = (1*weightage)

            # if we have reached a maximum number of consecutive
            # frames where a given object has been marked as
            # appeared, register it
            if self.appeared[name] > self.maxAppeared:
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
        return self.names


    def invoke_api(self, endpoint):
        req = requests.get(endpoint)
        return 1

    def extract_name(self, name):
        student_idname = name.split('_')
        student_name = student_idname[1]
        return student_name

    def extract_name_for_voice(self, name):
        name = self.extract_name(name)
        #if(name.lower() == 'sruthika'):
        #   name = 'Sruthika'
        return name.title()


    def extract_id(self, name):
        student_idname = name.split('_')
        student_id = student_idname[0]
        return student_id

    def mark_attendance(self, student_idname):
        try:

            student_id = self.extract_id(student_idname)
            attendance_api_endpoint = self.url1 + student_id + self.url2

            future = self.executor.submit(self.invoke_api(attendance_api_endpoint))
            print("making attendance for {0}".format(student_id))

        except Exception as exc:
            self.logger.debug('%r Exception occured - marking attendance call: %s' % (attendance_api_endpoint, exc))


    def recognize_boxes_in_frame(self, rgb, detection_method):
        # detect the (x, y)-coordinates of the bounding boxes
        # corresponding to each face in the input frame, then compute
        # the facial embeddings for each face
        boxes = face_recognition.face_locations(rgb, model=detection_method)
        return boxes

    def add_identified_thumbnails(self, frame, names, path_to_thumbnails):
        #identified_names = list(set(self.names).union(names))
        identified_names = self.objects.keys()
        x_offset = 50
        y_offset = 50

        for id_name in identified_names:
            image_path = path_to_thumbnails + "/"+ id_name + "/face.jpg"
            face = cv2.imread(image_path)
            if (id_name != 'Unknown_Unknown'):
                frame[y_offset:y_offset + face.shape[0], x_offset:x_offset + face.shape[1]] = face
                y_offset = y_offset + face.shape[0]
        #print("thumbnail image stitching done!")
        return frame

    def welcome_student(self, person_name):
        mixer.init()
        mixer.music.load(self.mp3_path + '/' + person_name + '/welcome.mp3')
        mixer.music.play()

    # function to get unique values
    def unique(self, list1):

        # insert the list to the set
        list_set = set(list1)
        # convert the set to the list
        unique_list = (list(list_set))
        for x in unique_list:
            print
            x,
        return unique_list

    def generate_welcome_mgs(self, names):
        names = self.unique(names)
        for name in names:
            self.synthesize_text(name, "Hi {0}. Welcome!")

    def synthesize_text(self, name, text):
        """Synthesizes speech from the input string of text."""
        client = texttospeech.TextToSpeechClient()

        text = text.format(self.extract_name_for_voice(name))
        input_text = texttospeech.types.SynthesisInput(text=text)

        # Note: the voice can also be specified by name.
        # Names of voices can be retrieved with client.list_voices().
        voice = texttospeech.types.VoiceSelectionParams(
            language_code='en-US',
            name='en-US-Wavenet-D')

        audio_config = texttospeech.types.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.MP3)

        response = client.synthesize_speech(input_text, voice, audio_config)

        # The response's audio_content is binary.
        directory = self.mp3_path + name
        if not os.path.exists(directory):
            os.makedirs(directory)
        path = directory + '/welcome.mp3'

        with open(path, 'wb') as out:
            out.write(response.audio_content)
            print('Audio content written to file "output.mp3"')

