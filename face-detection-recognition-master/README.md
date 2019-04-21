# face-detection-recognition
Detect faces that were already trained. Others mark as unknown

# There are two steps:
1. Encode the faces (detect 128 points from face and learn the face). <br>
   `python encode_faces.py --dataset ../dataset --encodings ../resources/encodings.pickle`
2. Recognize faces from the video streaming. <br>
   `python recognize_faces_from_video.py --encodings ../resources/encodings.pickle --detection-method hog --output ../output`

# How it works?
It saves the list of learnt faces in encodings.pickle file. When a face is detected, it encodes the face and compares with all the encodings it learnt already. It ranks the pobablity of the match with the detected face. I take the one with highest probability among them. When no match found the face is called "Unknown".

Once the face is matched and got the top probability face, it is not registered immediately. I want to confirm that this match occurs for the face continously 25 times to ascertain that the face is recognized correctly. (this is configurable.)

# Marking attendance:
Attendance is marked only when all the faces moves out of the camera. This is to make sure, we utilize all the frames to detect and recognize the faces with more confidence.
 
# Continous learning:
When Unknown face is found in a frame, it is saved in a video file (mp4). To make the video file with manageable size, a new video file is created for every minute. (only when Unknown face is detected. Else no video file is created). At a regular interval, these video files can be archived and then feed as input for the encoding program to detected better next time.

# Voice greetings:
I have added voice based greetings once a face is recognized and attendance is marked. You need to install mpg321 on your mac to get this working. <br>
`$brew install mpg321`
<br> and uncomment the below lines in trackerutil.py
    #self.tts = gTTS(text='Good morning. Welcome '+ student_name, lang='en')
    #self.tts.save("good.mp3")
    #os.system("mpg321 good.mp3")
# Note: 
I have not tested this for multiple scenarios. So, this is still underdevelopment

Some Python libraries that are required are,
`pip install face-recognition`; 
`pip install dlib`; 
`pip install gTTS`

# Pending:
1. I am working on performance improvement by introducing face tracking on those faces that are recognized with confidence.

