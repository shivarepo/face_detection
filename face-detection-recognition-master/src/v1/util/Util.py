import os
import logging

class Util:

    def __init__(self):
        logging.basicConfig(
            filename="../log/util.log",
            level=logging.DEBUG,
            format="%(asctime)s:%(name)s:%(levelname)s:%(message)s"
            )  

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

    def say_done(self, name):
        name = "Attendance marked for   " + self.extract_name_for_voice(name)
        os.system('say ' + name)
           