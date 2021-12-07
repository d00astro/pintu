# -*- coding: utf-8 -*-
"""
Various utility functions.
"""
__author__ = "Anders Åström"
__contact__ = "anders@astrom.sg"
__copyright__ = "2022, Anders Åström"
__licence__ = """The MIT License
Copyright © 2022 Anders Åström

Permission is hereby granted, free of charge, to any person obtaining a copy of this
 software and associated documentation files (the “Software”), to deal in the Software
 without restriction, including without limitation the rights to use, copy, modify,
 merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 permit persons to whom the Software is furnished to do so, subject to the following
 conditions:

The above copyright notice and this permission notice shall be included in all copies
 or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
 CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
 OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import collections
import datetime
import os
import pathlib
import statistics
import time
import typing
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import redis
import ulid

import pintu.default

if typing.TYPE_CHECKING:
    import enum

    class ellipsis(enum.Enum):
        Ellipsis = "..."

    Ellipsis = ellipsis.Ellipsis
else:
    ellipsis = type(Ellipsis)


RedisTypes = Union[str, bytes, int, float]
RedisKeyTypes = Union[str, bytes]
RedisMapping = Dict[RedisKeyTypes, RedisTypes]

# pydantic.BaseConfig.arbitrary_types_allowed = True
METADATA_FILE_NAME = "metadata.json"

UTC_DATETIME_MIN = datetime.datetime(
    1, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
)
UTC_DATETIME_MAX = datetime.datetime(
    9999, 12, 31, 23, 59, 59, 999999, tzinfo=datetime.timezone.utc
)

T = TypeVar("T")

KeyType = TypeVar("KeyType")
ValType = TypeVar("ValType")


Constructor = Union[Type, Callable[[Any], Any]]


class Metric(NamedTuple):
    """
    Collection of mean and standard deviation for a metric.
    """

    name: str
    "Metric name."

    mean: float
    "Metric mean."

    stdev: float
    "Metric standard deviation."

    nb_samples: int
    "Number of collected samples"


class LazyDict(Generic[KeyType, ValType], collections.UserDict):
    """Dictionary with the ability to load values lazily on demand."""

    def __init__(
        self,
        load_fn: Callable[[KeyType], ValType],
        items: Iterable[Tuple[KeyType, Optional[ValType]]] = None,
    ) -> None:
        """
        LazyDict

        :param load_fn:
            Load function that is invoked if a requested dictionary key is not
            present or if the corresponding value is `None`.
            The function should take the key as a single argument.

        :param items: (optional)
            Initial items
            Defaults to None.
        """
        self.data: Dict[KeyType, Optional[ValType]] = (
            dict(items) if items else {}
        )
        self._load_fn = load_fn

    def __getitem__(self, key: KeyType) -> ValType:
        try:
            val = self.data[key]
            if val is not None:
                return val
        except KeyError:
            pass
        val = self._load_fn(key)
        self.data[key] = val
        return val


class Profiler:
    """
    Container for runtime metrics, such as inference time.
    """

    on = bool(os.getenv("PROFILE"))

    _metrics: Dict[str, List[float]] = collections.defaultdict(list)

    @classmethod
    def capture(cls, metric: str, value: float):
        """
        Record the given value for a particular metric.


        :param metric:
            Metric name to capture.

        :param value:
            Value to record for the given metric.
        """
        cls._metrics[metric].append(value)

    @classmethod
    def report(cls) -> Iterable[Metric]:
        """
        Calculate mean and variance for the recorded metrics.


        :return:
            Iterable of tuples holding metric name, mean,
            standard deviation, number of samples
        """
        for name, values in cls._metrics.items():
            yield Metric(
                name,
                statistics.mean(values),
                statistics.stdev(values),
                len(values),
            )


def id_fun(x: T) -> T:
    return x


def now():
    """
    Get current datetime timestamp, with UTC timezone.


    :return:
        Current datetime timestamp, with UTC timezone.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def parse_timestamp(timestamp: Any) -> datetime.datetime:
    """
    Parse as a UTC datetime timestamp


    Supported formats include:

        - ISO 8601 formatted strings (e.g. "2021-10-18T18:56:22.1323"),
        - Compact %Y%m%dT%H%M%S%f format (e.g. "20210827T061031503119")
        - Stream ID %Y%m%d%H%M%S-%f format (e.g. "20210827061031-503119")
        - ULID (e.g. "01FJA6A6FNMXEC8EN9XVJYFV2G")

    :param timestamp:
        Value to parse

    :raises ValueError:
        If value could not be parsed

    :return:
        Datetime object
    """
    timestamp_str = str(timestamp)
    try:
        return datetime.datetime.fromisoformat(timestamp_str)
    except ValueError:
        timestamp_match = pintu.default.COMPACT_TIMESTAMP_REGEXP.search(
            timestamp_str
        )
        if timestamp_match:
            return datetime.datetime.strptime(
                timestamp_match[0], pintu.default.COMPACT_TIMESTAMP_FORMAT
            ).astimezone(datetime.timezone.utc)
        else:
            try:
                return datetime.datetime.strptime(
                    timestamp_str, pintu.default.STREAM_ID_TIMESTAMP_FORMAT
                ).replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                ulid_ts: ulid.ULID = ulid.ULID.from_str(timestamp_str)
                return ulid_ts.datetime
    raise ValueError(f"Not a recognized timestamp format: {timestamp}")


def if_none(value: Optional[T], default: T) -> T:
    """
    Use default a value if-and-only-if a value is explicitly `None`


    :param value:
        Value to check

    :param default:
        Default value to use if `value` is `None`

    :return:
        Either:
            `value` (if `value` is not `None`), or
            `default` (if `value` is `None`)
    """
    return default if value is None else value


def str_float(val: float, dec=4) -> str:
    """
    Compact string representation for floats.

    For example:
        `str_float(1/3)` creates `".3333"` instead of `"0.3333333333333333"`.


    :param val:
        Float value to stringify

    :param dec: (optional)
        Number of decimals.
        Defaults to 4.

    :return:
        A compact string-serialzed float
    """
    ret = f"{val:.{dec}}"
    if ret.startswith("0."):
        return ret[1:]
    if ret.startswith("-0."):
        return "-" + ret[2:]
    return ret


def safe_str(value: Any) -> str:
    if isinstance(value, str):
        return value

    if isinstance(value, bytes):
        return value.decode()

    return str(value)


def read_lines(file: pathlib.Path) -> List[str]:
    with file.open() as f:
        return [
            line.strip() for line in f.readlines() if not line.startswith("#")
        ]


def find_label_map(directory: pathlib.Path) -> pathlib.Path:
    """
    Find labelmap file in a directory.


    :param directory:
        Directory path

    :raises ValueError:
        If directory does not exist or no label-map files could be found.

    :return:
        Path to the first label-map file found in the directory.
    """
    candidates = list(directory.glob("*label*map*.*txt*"))
    if not candidates:
        raise ValueError(
            f"Unable to find any ontology definitions in directory {directory}"
        )

    if len(candidates) > 1:
        raise ValueError(
            "Unable to unambiguously deduce ontology definition "
            f"in directory {directory}. "
            f"Multiple ontology candidates: {candidates}"
        )
    return candidates[0]


def file_datetime(file_path: pathlib.Path) -> datetime.datetime:
    """
    Attempt to parse a datetime timestamp from a file name.

    It is sufficient that the filename contains a parseable timestamp, it may
    contain other characters as prefix or suffix.

    Supported formats include:
        - Compact %Y%m%dT%H%M%S%f format (e.g. "20210827T061031503119")
        - ULID (e.g. "01FJA6A6FNMXEC8EN9XVJYFV2G")


    :param file_path:
        File to parse

    :raises ValueError:
        If no timestamp could be parsed.

    :return:
        UTC Datetime object
    """
    timestamp_str = file_path.stem
    timestamp = pintu.default.COMPACT_TIMESTAMP_REGEXP.search(timestamp_str)
    if not timestamp:
        return datetime.datetime.fromisoformat(timestamp_str).astimezone(
            datetime.timezone.utc
        )
    try:
        return datetime.datetime.strptime(
            timestamp[0], pintu.default.COMPACT_TIMESTAMP_FORMAT
        ).astimezone(datetime.timezone.utc)
    except (ValueError, IndexError) as err:
        raise ValueError(
            f"Unable to parse timedtamp from {timestamp_str} ({file_path})"
        ) from err


def sample_dir(source_id: str, sample_id: ulid.ULID) -> pathlib.Path:
    """
    Construct a sample directory path.

    Assumes relative path from 'current' directory, which contains a "data"
    directory of samplings.


    :param source_id:
        Name / id of the source / camera.

    :param sample_id:
        Sample id.

    :return:
        Relative path to the sample directory.
    """
    return (
        pathlib.Path("data")
        .joinpath(source_id)
        .joinpath("samples")
        .joinpath(sample_id.datetime.strftime("%Y%m%d"))
        .joinpath(sample_id.datetime.strftime("%H%M"))
        .joinpath(str(sample_id))
    )


def annotation_dir(
    source_id: str, sample_id: ulid.ULID, annotation_id: str = None
) -> pathlib.Path:
    """
    Construct an annotation directory path.

    Assumes relative path from 'current' directory, which contains a "data"
    directory of samplings.


    :param source_id:
        Name / id of the source / camera.

    :param sample_id:
        Sample id.

    :param annotation_id: (optional)
        Name / id of annotation
        Defaults to None.

    :return:
        Relative path to the sample directory.
    """
    return sample_dir(source_id, sample_id)


def stream_id(
    timestamp: datetime.datetime,
    naive_tz: Union[datetime.timezone, ellipsis] = None,
):
    if timestamp.tzinfo is None:
        if naive_tz is None:
            raise ValueError(
                "Unable to create a stream id from naive / timezone-unaware timestamp. "
                "Either provide a timestamp with a timezone or use the 'naive_tz' "
                "argument to specify which timezone the timestamp should be "
                "interpreted as (Use Elipsis / '...' for local time zone). "
            )

        if naive_tz is not Ellipsis:
            timestamp = timestamp.replace(tzinfo=naive_tz)

    if timestamp.tzinfo != datetime.timezone.utc:
        timestamp = timestamp.astimezone(datetime.timezone.utc)

    return timestamp.strftime(pintu.default.STREAM_ID_TIMESTAMP_FORMAT)


def sample_stream(
    bus: redis.Redis,
    stream_key: str,
    types: Dict[str, Constructor] = None,
    default_type: Constructor = id_fun,
    timeout: datetime.timedelta = None,
    sleep: datetime.timedelta = datetime.timedelta(seconds=0.05),
) -> Iterable[Dict]:
    last_processed_id = b"0-0"
    last_fetched_time = now()

    if not types:
        types = {}

    if default_type:
        types = collections.defaultdict(lambda: default_type, types)

    while True:
        # Get the latest decoded image
        records = bus.xrevrange(stream_key, min=last_processed_id, count=1)

        # Take a nap if nothing was returned
        if not records:
            if timeout and now() - last_fetched_time > timeout:
                break
            time.sleep(sleep.total_seconds())
            continue

        # Take a nap if we got the last read record again.
        id, record = records[0]
        if id == last_processed_id:
            if timeout and now() - last_fetched_time > timeout:
                break
            time.sleep(sleep.total_seconds())
            continue

        yield {safe_str(k): types[safe_str(k)](v) for k, v in record.items()}

        last_processed_id = id
        last_fetched_time = now()
