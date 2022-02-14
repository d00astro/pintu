# -*- coding: utf-8 -*-
"""
Video Capture
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
import datetime
import logging
import pathlib
from typing import Any, Dict, List

import cv2
import redis

import pintu.default
import pintu.imaging
import pintu.util

log = logging.getLogger(__name__)


def record(
    bus: redis.Redis,
    camera_name: str,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
):
    start_time_key = f"/pintu/camera/{camera_name}/record_queue"
    end_time_key = f"/pintu/camera/{camera_name}/record_until"

    bus.set(end_time_key, end_time.isoformat())
    bus.rpush(start_time_key, start_time.isoformat())


def get_recordings(
    bus: redis.Redis,
    camera_name: str,
    start_time: datetime.datetime = None,
    end_time: datetime.datetime = None,
) -> List[Dict[str, Any]]:
    recordings_stream_key = f"/pintu/camera/{camera_name}/recording"

    if end_time is None:
        end_time = pintu.util.now()

    if start_time is None:
        start_time = end_time - datetime.timedelta(days=1)

    recordings: List[Dict[str, Any]] = []

    for recording in pintu.util.slice_stream(
        bus,
        recordings_stream_key,
        start_time=start_time,
        end_time=end_time,
        types={
            "finished": pintu.util.safe_bool,
            "start": pintu.util.parse_timestamp,
            "end": pintu.util.parse_timestamp,
            "file": lambda x: pathlib.Path(pintu.util.safe_str(x)),
        },
        default_type=pintu.util.safe_str,
        wait=None,
    ):

        if not recordings or not recording["finished"]:
            recordings.append(recording)
        else:
            recordings[-1] = recording

    return recordings


def _record_on_demand_loop(
    bus: redis.Redis,
    camera_name: str,
    # min_interval: datetime.timedelta,
    detections: bool = False,
):

    recordings_stream_key = f"/pintu/camera/{camera_name}/recording"
    stream_key = (
        f"/pintu/camera/{camera_name}/detection"
        if detections
        else f"/pintu/camera/{camera_name}/capture"
    )
    start_time_key = f"/pintu/camera/{camera_name}/record_queue"
    end_time_key = f"/pintu/camera/{camera_name}/record_until"
    start_timestamp = pintu.util.UTC_DATETIME_MIN
    end_timestamp = pintu.util.UTC_DATETIME_MIN
    last_recorded_frame_timestamp = pintu.util.UTC_DATETIME_MIN
    while True:
        # Block until a start time is (r)pushed to the `start_time_key` (list)
        # Then read the latest end time from `end_time_key` (string)

        _, start_binstr = bus.blpop(start_time_key)
        start_timestamp_str = pintu.util.safe_str(start_binstr)
        end_timestamp_str = pintu.util.safe_str(
            bus.getset(end_time_key, pintu.util.UTC_DATETIME_MIN.isoformat())
        )

        try:
            start_timestamp = max(
                start_timestamp,
                datetime.datetime.fromisoformat(start_timestamp_str),
            )
            end_timestamp = max(
                end_timestamp,
                datetime.datetime.fromisoformat(end_timestamp_str),
            )
        except ValueError as ex:
            log.error(
                "Invalid start and/or stop date/times "
                f"({start_timestamp_str}-{end_timestamp_str}): "
                f"{ex}"
            )
            continue

        recording_file = (
            pintu.config.recordings_dir
            / start_timestamp.strftime(
                pintu.default.RECORDINGS_FILENAME_FORMAT
            )
        )
        recording_file.parent.mkdir(parents=True, exist_ok=True)
        video_writer = None

        if start_timestamp > last_recorded_frame_timestamp:
            log.info(
                f"Recording camera '{camera_name}' from {start_timestamp.isoformat()} "
                f"to file '{recording_file}'"
            )
            bus.xadd(
                recordings_stream_key,
                fields={
                    "camera": camera_name,
                    "finished": 0,
                    "start": start_timestamp.isoformat(),
                    "end": end_timestamp.isoformat(),
                    "file": str(recording_file),
                },
                id=pintu.util.stream_id(start_timestamp),
            )

        rec_verb = "Scheduling"
        while last_recorded_frame_timestamp < end_timestamp:
            log.info(
                f"{rec_verb} recording of '{recording_file}' "
                f"until {end_timestamp.isoformat()}"
            )
            log.debug(f"Current start: {start_timestamp.isoformat()}")
            log.debug(f"Current end:   {end_timestamp.isoformat()}")

            for record in pintu.util.slice_stream(
                bus,
                stream_key=stream_key,
                start_time=max(start_timestamp, last_recorded_frame_timestamp),
                end_time=end_timestamp,
            ):
                image_key = record["input"]

                image_bytes = bus.get(image_key)
                if not image_bytes:
                    log.error(f"No data at image key: {image_key}")
                    continue

                frame = pintu.imaging.Frame.decode(image_bytes)

                if not video_writer:
                    video_writer = cv2.VideoWriter(
                        str(recording_file),
                        cv2.VideoWriter_fourcc(*"VP80"),
                        pintu.config.sample_rate,
                        (frame.width, frame.height),
                    )
                    log.debug("Created new recorder")

                video_writer.write(frame.data)
                log.debug(f"Wrote frame {frame} to '{recording_file}'")
                last_recorded_frame_timestamp = frame.timestamp

            rec_verb = "Extending scheduled"
            log.info(
                f"Finished recording camera '{camera_name}' "
                f"from {start_timestamp_str} until {end_timestamp_str} "
                f"to file '{recording_file}'"
            )
            end_timestamp_str = pintu.util.safe_str(
                bus.getset(
                    end_time_key, pintu.util.UTC_DATETIME_MIN.isoformat()
                )
            )
            try:
                end_timestamp = datetime.datetime.fromisoformat(
                    end_timestamp_str
                )
            except ValueError as ex:
                log.error(
                    "Invalid start and/or stop date/times "
                    f"({start_timestamp_str}-{end_timestamp_str}): "
                    f"{ex}"
                )

        if video_writer:
            video_writer.release()
            bus.xadd(
                recordings_stream_key,
                fields={
                    "camera": camera_name,
                    "finished": 1,
                    "start": start_timestamp.isoformat(),
                    "end": last_recorded_frame_timestamp.isoformat(),
                    "file": str(recording_file),
                },
                id=pintu.util.stream_id(last_recorded_frame_timestamp),
            )


def main():
    import pintu

    bus = redis.Redis(
        host=pintu.config.redis_host, port=pintu.config.redis_port
    )

    _record_on_demand_loop(bus=bus, camera_name=pintu.config.camera_name)


if __name__ == "__main__":
    main()
