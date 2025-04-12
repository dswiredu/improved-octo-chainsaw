import base64
import datetime
import struct

import lz4.block
import numpy

TIMESERIES_ARRAY_DTYPE = [("timestamps", "<datetime64[D]"), ("values", "<d")]

SERIALIZATION_TIMESTAMP_VALUE_LEN = struct.calcsize("<Qd")
SERIALIZATION_TIMESTAMP_LEN = struct.calcsize("<Q")


def make_timeseries(timestamps, values):
    """Return a Numpy array representing a timeseries."""
    size = len(timestamps)
    if size != len(values):
        raise ValueError("Timestamps and values must have the same length")
    arr = numpy.zeros(size, dtype=TIMESERIES_ARRAY_DTYPE)
    arr["timestamps"] = timestamps
    arr["values"] = values
    return arr


def merge(ts1, ts2):
    """Merge a series into a second series

    The timeseries does not need to be sorted.

    If a timestamp is present in both `ts1` and `ts2`, then value from `ts1`
    is used.

    :param ts: The timeseries to combine.
    :return: A new timeseries.
    """
    ts = numpy.concatenate((ts1, ts2))
    __, index = numpy.unique(ts["timestamps"], return_index=True)
    return ts[index]


def ffill(arr):
    prev = numpy.arange(len(arr))
    prev[arr == 0] = 0
    prev = numpy.maximum.accumulate(prev)
    return arr[prev]


def bfill(arr):
    back = numpy.arange(len(arr))
    back[arr == 0] = len(arr) - 1
    back = numpy.minimum.accumulate(back[::-1])[::-1]
    return arr[back]


def find_rate(ts, date):
    date = numpy.datetime64(date).astype("<datetime64[D]")
    idx = numpy.searchsorted(ts["timestamps"], date, side="right")
    return ts["values"][idx - 1] if idx > 0 else None


def iter_values(series, end_date, start, end):
    if start >= end_date:
        return
    e_offset = min((end - end_date).days, 0)
    series = series[(start - end_date).days : e_offset or None]
    s_date = (
        end_date
        + datetime.timedelta(days=e_offset)
        - datetime.timedelta(days=len(series))
    )
    for i in range(len(series)):
        yield s_date + datetime.timedelta(days=i), series[i]


def serialize(ts):
    return ts["timestamps"].tobytes() + ts["values"].tobytes()


def serialize_to_text(ts):
    return base64.b64encode(serialize(ts)).decode()


def deserialize(data):
    num_points = len(data) // SERIALIZATION_TIMESTAMP_VALUE_LEN
    timestamps = numpy.frombuffer(data, dtype="<Q", count=num_points)
    values = numpy.frombuffer(
        data, dtype="<d", offset=num_points * SERIALIZATION_TIMESTAMP_LEN
    )
    return make_timeseries(timestamps, values)


def deserialize_from_text(data):
    return deserialize(base64.b64decode(data))


def serialize_values(ts):
    return lz4.block.compress(ts["values"].tobytes())


def deserialize_values(data):
    return numpy.frombuffer(lz4.block.decompress(data), dtype="<d")
