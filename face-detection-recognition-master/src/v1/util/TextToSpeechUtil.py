from google.cloud import texttospeech
import os
from pygame import mixer

class TextToSpeechUtil:

    def __init__(self):
        self.mp3_path = '../resources/welcome_messages/'
        self.resource = '../resources/'

    def extract_name(self, name):
        student_idname = name.split('_')
        student_name = student_idname[1]
        return student_name

    def extract_name_for_voice(self, name):
        name = self.extract_name(name)
        return name.title()
    
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

    def welcome_student(self, person_name):
        mixer.init()
        mixer.music.load(self.mp3_path + '/' + person_name + '/welcome.mp3')
        mixer.music.play()     

    def play_alert(self):
        mixer.init()
        mixer.music.load(self.resource + 'alert.mp3')
        mixer.music.play()            