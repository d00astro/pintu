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

import redis

import pintu.default
import pintu.imaging
import pintu.util

log = logging.getLogger(__name__)


def capture(
    video_uri: pathlib.Path,
    bus: redis.Redis,
    camera_name: str = pintu.default.CAMERA_NAME,
    sample_rate: float = pintu.default.SAMPLE_RATE,
    duration: datetime.timedelta = None,
    retention: datetime.timedelta = pintu.default.RETENTION,
    buffer_size: int = pintu.default.BUFFER_SIZE,
    buffer_interval: datetime.timedelta = pintu.default.BUFFER_INTERVAL,
    diff_threshold: int = pintu.default.DIFF_THRESHOLD,
):
    """Capture Video from a video source

    Publish video frames from a video source into a Redis instance (bus).
    Video source could be a camera device id, file path or a video (e.g. "rtsp") url.

    Video Capture should not to be confused with recording, as captured frames are
    only stored temporarily in Redis (memory).


    :param video_uri:
        Video uri

    :param bus:
        Redis connection

    :param camera_name: (optional)
        Name of camera.
        Defaults to pintu.default.CAMERA_NAME.

    :param sample_rate: (optional)
        Number of frames per second to attempt to pull from the video source.
        This is just to save computation and memory from high framerate cameras
        when it is not needed.
        Defaults to pintu.default.SAMPLE_RATE.

    :param duration: (optional)
        Capture for this duration.
        Defaults to None - Indefinitely (or until the stream ends).

    :param retention: (optional)
        Approximate duration of time to retain frames in memory.
        Frames older than this may be deleted.
        Defaults to pintu.default.RETENTION.

    :param buffer_size: (optional)
        Number of frames to use for background estimation, if any.
        Defaults to pintu.default.BUFFER_SIZE.

    :param buffer_interval: (optional)
        Duration between background estimation samples, if any.
        Defaults to pintu.default.BUFFER_INTERVAL.

    :param diff_threshold: (optional)
        Minimum pixel value difference from estimated background,
        to be considered a pixel of a foreground object.
        Defaults to pintu.default.DIFF_THRESHOLD.
    """

    frames = pintu.imaging.frames_from_video(
        str(video_uri),
        sample_rate=sample_rate,
        duration=duration,
    )
    buffer = (
        pintu.imaging.FrameBuffer(frames, buffer_size) if buffer_size else None
    )

    next_buffer_timestamp = pintu.util.UTC_DATETIME_MIN

    stream_length = int(retention.total_seconds() * sample_rate + 0.5)
    stream_key = f"/pintu/camera/{camera_name}/capture"
    ttl = retention * 1.10

    for frame in frames:

        if frame.data is None:
            log.warning(  # type: ignore
                f"No data in frame at :{frame.timestamp.isoformat()}"
            )
            continue

        frame_key = (
            f"/pintu/camera/{camera_name}"
            f"/frame/{pintu.util.stream_id(frame.timestamp)}"
        )

        input_image_key = f"{frame_key}/{frame.kind}"
        background_image_key = ""
        foreground_image_key = ""
        # mask_image_key = ""

        pipe = bus.pipeline()

        if buffer and frame.timestamp >= next_buffer_timestamp:
            buffer.shift(frame)
            next_buffer_timestamp += buffer_interval

            if buffer.full:
                # Shift out / pop the oldest frame if the buffer is full
                layers = buffer.extract_layers(
                    frame, diff_threshold=diff_threshold
                )

                background_image_key = f"{frame_key}/{layers.background.kind}"
                pipe.set(
                    background_image_key, bytes(layers.background.data), ex=ttl
                )

                foreground_image_key = f"{frame_key}/{layers.foreground.kind}"
                pipe.set(
                    foreground_image_key, bytes(layers.foreground.data), ex=ttl
                )

                # mask_image_key = f"{frame_key}/{layers.mask.kind}"
                # redis.set(mask_image_key, bytes(layers.mask.data))

        frame_data: pintu.util.RedisMapping = {
            "timestamp": frame.timestamp.isoformat(),
            "width": frame.width,
            "height": frame.height,
            "key": frame_key,
            frame.kind: input_image_key,
        }

        if background_image_key:
            frame_data[
                pintu.imaging.ImageKind.background
            ] = background_image_key

        if foreground_image_key:
            frame_data[
                pintu.imaging.ImageKind.foreground
            ] = foreground_image_key

        # if mask_image_key:
        #     frame_data["mask"] = mask_image_key

        pipe.set(input_image_key, bytes(frame), ex=ttl)
        pipe.hset(frame_key, mapping=frame_data)
        pipe.expire(frame_key, ttl)
        pipe.xadd(
            stream_key,
            frame_data,
            id=pintu.util.stream_id(frame.timestamp),
            maxlen=stream_length,
            approximate=True,
        )
        try:
            pipe.execute(True)
        except redis.exceptions.ResponseError as ex:
            log.error(
                f"Failed to push frame to capture stream : {frame} . Error: {ex}"
            )


if __name__ == "__main__":
    import redis

    import pintu

    bus = redis.Redis(
        host=pintu.config.redis_host, port=pintu.config.redis_port
    )
    capture(
        video_uri=pintu.config.video,
        bus=bus,
        camera_name=pintu.config.camera_name,
        sample_rate=pintu.config.sample_rate,
        duration=None,
        retention=pintu.config.retention,
        buffer_size=pintu.config.buffer_size,
        buffer_interval=pintu.config.buffer_interval,
        diff_threshold=pintu.config.diff_treshold,
    )
