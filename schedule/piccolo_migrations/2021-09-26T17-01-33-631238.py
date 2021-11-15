from piccolo.apps.migrations.auto import MigrationManager
from piccolo.columns.column_types import Date
from piccolo.columns.column_types import Varchar
from piccolo.columns.defaults.date import DateNow
from piccolo.columns.indexes import IndexMethod


ID = "2021-09-26T17:01:33:631238"
VERSION = "0.50.0"
DESCRIPTION = "Initial migration for 'schedules' table."


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="schedule", description=DESCRIPTION
    )

    manager.add_table("ScheduleTable", tablename="schedules")

    manager.add_column(
        table_class_name="ScheduleTable",
        tablename="schedules",
        column_name="name",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 255,
            "default": "",
            "null": False,
            "primary_key": False,
            "unique": True,
            "index": True,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="ScheduleTable",
        tablename="schedules",
        column_name="date",
        column_class_name="Date",
        column_class=Date,
        params={
            "default": DateNow(),
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    return manager
