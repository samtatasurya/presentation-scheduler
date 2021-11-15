from piccolo.columns import Date, Varchar
from piccolo.columns.readable import Readable
from piccolo.table import Table


TABLE_NAME = "schedules"


class ScheduleTable(Table, tablename=TABLE_NAME):
    """ DB table storing schedule information. """
    name = Varchar(index=True, unique=True)
    date = Date()

    @classmethod
    def get_readable(cls):
        return Readable(template="%s", columns=[cls.name])
