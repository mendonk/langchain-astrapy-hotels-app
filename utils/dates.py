import datetime


def dt_to_int(dt: datetime.datetime) -> int:
    return int(dt.timestamp())

def int_to_dt(dt_int: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(dt_int)
