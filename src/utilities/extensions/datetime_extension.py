from datetime import datetime, timezone

def get_utc_epoch():
    return int(datetime.timestamp(datetime.utcnow().replace(tzinfo=timezone.utc)) * 1000)


def convert_utc_timestamp_to_epoch(timestamp_value):
    return int(datetime.timestamp(timestamp_value.replace(tzinfo=timezone.utc)) * 1000)


def convert_epoch_to_utc_timestamp(val: int):
    if len(str(val)) == 10:
        return datetime.fromtimestamp(val, tz=timezone.utc)
    return datetime.fromtimestamp(val / 1000,  tz=timezone.utc)
