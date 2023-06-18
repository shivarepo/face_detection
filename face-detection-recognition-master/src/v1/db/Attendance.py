from tinydb import TinyDB, Query
import datetime
import logging
import json
from tinydb.storages import JSONStorage
from tinydb_serialization import SerializationMiddleware
from v1.util.DateTimeSerializer import DateTimeSerializer

class Attendance(object):
    def __init__(self):
        logging.basicConfig(
            filename="../log/attendance.log",
            level=logging.DEBUG,
            format="%(asctime)s:%(name)s:%(levelname)s:%(message)s"
            )

        self.logger = logging.getLogger("Attendance")
        self.serialization = SerializationMiddleware()
        self.serialization.register_serializer(DateTimeSerializer(), 'TinyDate')

        self.db = TinyDB('../resources/attendance.json', storage=self.serialization)
        self.table = self.db.table('attendance')

    def mark_attendance(self, student_id):
        self.table.insert({
            "studentId": student_id,
            "dateTime": datetime.datetime.now()
            "pushed" : 'N'
        })     

    def show(self):
        Atendance = Query()
        stud_present = self.table.search(Atendance.dateTime < datetime.datetime.today())
        for stud in stud_present:
            print(stud['studentId'])
            print(stud['dateTime'])

    def main(self):
        #self.mark_attendance(13748)
        self.show()

if __name__ == "__main__":
    Attendance().main()        