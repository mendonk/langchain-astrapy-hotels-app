import datetime
import time


# custom methods to manually apply the conversion
#   <datetime>   ==>  {"$date": timestamp_milliseconds}
# as per EJSON and json API conventions
#
# Note: this whole module be removed when astrapy
#       introduces native support for this part of EJSON.

def datetime_to_timestamp_ms(dt):
    return int(time.mktime(dt.timetuple()) * 1000.0)

def timestamp_ms_to_datetime(ts_ms):
    return datetime.datetime.fromtimestamp(ts_ms / 1000.0)


# higher-level conversion

def datetime_to_json_block(dt):
    return {"$date": datetime_to_timestamp_ms(dt)}

def json_block_to_datetime(jb):
    assert "$date" in jb
    assert len(jb) == 1
    return timestamp_ms_to_datetime(jb["$date"])


# document-wide fix

def restore_doc_dates(doc):
    """
    Ad-hoc (inelegant) solution to restore $date fields
    back to datetimes in docs coming from API calls.
    NOTE: top-level fields only!
    """

    def _restore(val):
        if isinstance(val, dict) and "$date" in val:
            return json_block_to_datetime(val)
        else:
            return val

    return {
        k: _restore(v)
        for k, v in doc.items()
    }
