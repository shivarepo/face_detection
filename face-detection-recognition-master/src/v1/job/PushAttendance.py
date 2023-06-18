from tinydb import TinyDB, Query
import datetime
import logging
import json
import requests
from tinydb.storages import JSONStorage
from tinydb_serialization import SerializationMiddleware
from v1.util.DateTimeSerializer import DateTimeSerializer

class PushAttendance(object):
    def __init__(self):
        logging.basicConfig(
            filename="../log/attendance.log",
            level=logging.DEBUG,
            format="%(asctime)s:%(name)s:%(levelname)s:%(message)s"
            )

        self.logger = logging.getLogger("PushAttendance")
        self.serialization = SerializationMiddleware()
        self.serialization.register_serializer(DateTimeSerializer(), 'TinyDate')

        self.db = TinyDB('../resources/attendance.json', storage=self.serialization)
        self.table = self.db.table('attendance')

        # define the api endpoint
        self.url1 = "http://providencecnr.in/api/readerentry?rfiddata=1_"

        # http://providencecnr.in/api/readerentry?rfiddata=1_13748_2019-04-28_20:59:24

    def push(self):
        Atendance = Query()
        stud_present = self.table.search(Atendance.dateTime < datetime.datetime.today() and Atendance.push == 'N')
        for stud in stud_present:
            self.invoke_api(stud)
            self.table.upsert({'studentId':stud['studentId'], 'push':'Y'}, Atendance.studentId == stud['studentId'])

    def invoke_api(self, stud):
        try:
            attendance_api_endpoint = self.url1 + str(stud['studentId']) + '_' + str(stud['dateTime']).replace(" ","_")
            req = requests.get(attendance_api_endpoint)
        except Exception as exc:
            self.logger.debug('%r Exception occured - marking attendance call: %s' % (attendance_api_endpoint, exc))            

    def main(self):
        self.push()

if __name__ == "__main__":
    PushAttendance().main()        