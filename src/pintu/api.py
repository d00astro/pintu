# -*- coding: utf-8 -*-
"""
Pintu API
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
import asyncio
import logging

import fastapi
import redis
import uvicorn

import pintu
import pintu.gpio
import pintu.imaging
import pintu.util

log = logging.getLogger(__name__)


def create_api() -> fastapi.applications.FastAPI:
    """
    Create Pintu API

    :return:
        Pintu API object
    """
    log.info(f"API scheme: {pintu.config.api_scheme}")
    log.info(f"API root: {pintu.config.api_route_prefix}")

    fast_api = fastapi.applications.FastAPI(
        title="Pintu API",
        description="""By [Anders Astrom](https://github.com/d00astro)

A basic API for "smart door" control
""",
        version=str(pintu.config.version),
        openapi_tags=[
            {"name": "status", "description": "Status functions"},
        ],
        servers=[
            {
                "url": pintu.config.api_base_endpoint,
            },
        ],
        root_path=pintu.config.api_route_prefix,
    )
    return fast_api


api = create_api()


@api.get("/", response_class=fastapi.responses.HTMLResponse)
async def index(unlock: bool = False):
    """
    Generate a super simple, JavaScript free HTML page.

    :param unlock: (optional)
        Unlock the door. Who cares about security?
        Defaults to False.

    :return:
        HTML page
    """
    if unlock:
        await do_unlock_door()
        return fastapi.responses.RedirectResponse(
            url=api.url_path_for("index")
        )
    return f"""<!DOCTYPE html>
<html>
    <head>
        <style>
            body {{
                background-color: black;
            }}
            h1 {{
                font: bold 24px Arial;
                color: #FFFFFF;
            }}
            .button {{
                font: bold 12px Arial;
                text-decoration: none;
                background-color: #EEEEEE;
                color: #333333;
                padding: 6px 18px 6px 18px;
                border-top: 1px solid #CCCCCC;
                border-right: 1px solid #333333;
                border-bottom: 1px solid #333333;
                border-left: 1px solid #CCCCCC;
            }}
            .container {{
                position: relative;
                overflow: hidden;
                width: 100%;
                padding-top: 75%; /* 480/640 */
            }}
            .video {{
                position: absolute;
                top: 0;
                left: 0;
                bottom: 0;
                right: 0;
                width: 100%;
                height: 100%;
            }}
        </style>
    </head>
    <body>
        <h1>{pintu.config.camera_name}</h1>
        <div>
            <a href="{pintu.config.api_link("/?unlock=true")}" class="button">
                Unlock
            </a>
        </div>
        <div/>
        <div class="container">
            <iframe
                class="video"
                src={pintu.config.api_link('/live?detections=true')}
                title="{pintu.config.camera_name}"
            >
            </iframe>
        </div>
    </body>
</html>
"""


@api.get("/door/state")
async def get_door_state():
    """Get the state of the door sensor

    :return:
        Dict containing two fields:

            - `"open"`, which is `true` if door is open, `false` if door is closed.
            - `"unlocked"`, which is `true` if door is unlocked,
                `false` if door is locked.
    """
    log.info("Door state requested.")
    return {
        "open": pintu.gpio.is_door_open(),
        "unlocked": pintu.gpio.is_door_unlocked(),
    }


@api.post("/door/unlock")
async def do_unlock_door():
    """Unlock the door.

    :return:
        Dict containing two fields:
            - `"open"`, which is `true` if door is open, `false` if door is closed.
            - `"unlocked"`, which is `true` if door is unlocked,
                `false` if door is locked.
    """
    log.info("Door unlock requested.")
    pintu.gpio.unlock_door()
    await asyncio.sleep(
        pintu.config.door_unlock_signal_duration.total_seconds()
    )
    pintu.gpio.lock_door()
    return await get_door_state()


@api.post("/door/lock")
async def do_lock_door():
    """Lock the door.

    Or rather, stop sending the "unlock" signal.


    :return:
        Dict containing two fields:
            - `"open"`, which is `true` if door is open, `false` if door is closed.
            - `"unlocked"`, which is `true` if door is unlocked,
                `false` if door is locked.
    """
    log.info("Door lock requested.")
    pintu.gpio.lock_door()
    return await get_door_state()


@api.post("/door/open")
async def do_open_door():
    """Open the door


    Not implemented.

    :return:
        Dict containing two fields:
            - `"open"`, which is `true` if door is open, `false` if door is closed.
            - `"unlocked"`, which is `true` if door is unlocked,
                `false` if door is locked.

    raises:
        NotImplementedError
    """
    log.info("Door open requested.")
    pintu.gpio.open_door()
    return await get_door_state()


@api.post("/door/close")
async def do_close_door():
    """Close the door

    Not implemented.

    :return:
        Dict containing two fields:
            - `"open"`, which is `true` if door is open, `false` if door is closed.
            - `"unlocked"`, which is `true` if door is unlocked,
                `false` if door is locked.

    raises:
        NotImplementedError
    """
    log.info("Door close requested.")
    pintu.gpio.close_door()
    return await get_door_state()


def image_stream(
    stream_key: str, image_kind: str = "input", detections: bool = False
):
    """Generate a real-time MJPEG stream of frames from a capture or detection
    stream in Redis.

    :param stream_key:
        Redis key for the stream to sample from

    :param image_kind:
        Version of image to use.
        Defaults to `"input`

    :param detections: (optional)
        Draw detections on the video.
        Defaults to False.

    :yield:
        MJPEG stream of real-time frames.
    """
    bus = redis.Redis(
        host=pintu.config.redis_host, port=pintu.config.redis_port
    )
    for record in pintu.util.sample_stream(bus, stream_key):
        image_bytes = bus.get(record[image_kind])
        if not image_bytes:
            continue
        log.debug(f"Read an image: {record['timestamp']}")

        if detections:
            frame = pintu.imaging.Frame.decode(image_bytes)
            for detection_key in bus.lrange(record["detections"], 0, -1):
                try:
                    detection = bus.hgetall(detection_key)
                    if not detection:
                        log.warning(
                            "No detection data found at detection key: "
                            f"'{pintu.util.safe_str(detection_key)}'"
                        )
                        continue
                    frame.draw_detection(
                        cls=pintu.util.safe_str(detection[b"class"]),
                        left=float(detection[b"left"]),
                        top=float(detection[b"top"]),
                        right=float(detection[b"right"]),
                        bottom=float(detection[b"bottom"]),
                        confidence=float(detection[b"confidence"]),
                    )
                except Exception as ex:
                    log.error(f"Unable to draw detections: {ex}")
                    raise
            image_bytes = frame.encode()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + image_bytes + b"\r\n"
        )


@api.get("/live")
async def live_video(detections: bool = False, image="input"):
    """MJPEG stream

    :param detections: (optional)
        Draw detections on the video.
        Defaults to False.

    :param image: (optional)
        Version of image to use.
        Defaults to `"input"`.

    :return:
        MJPEG video
    """
    log.info("Live MJPEG stream requested.")

    stream_key = (
        f"/pintu/camera/{pintu.config.camera_name}/detection"
        if detections
        else f"/pintu/camera/{pintu.config.camera_name}/capture"
    )

    return fastapi.responses.StreamingResponse(
        image_stream(stream_key, image, detections),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# video_path = pathlib.Path("recordings/2021/1205/2327/door_00.mp4")
# CHUNK_SIZE = 1024 * 1024


# @api.get("/recording")
# async def recorded_video(range: str = fastapi.Header(None)):
#     start_str, end_str = range.replace("bytes=", "").split("-")
#     start = int(start_str)
#     end = int(end_str) if end_str else start + CHUNK_SIZE
#     with open(video_path, "rb") as video:
#         video.seek(start)
#         data = video.read(end - start)
#         filesize = str(video_path.stat().st_size)
#         headers = {
#             "Content-Range": f"bytes {str(start)}-{str(end)}/{filesize}",
#             "Accept-Ranges": "bytes",
#         }
#         return fastapi.Response(
#             data, status_code=206, headers=headers, media_type="video/mp4"
#         )


# List Historic Events
#   Date/Time filter
# View event


@api.get("/config")
def get_config():
    """Get current configuration.

    :return:
        Dict of the configuration values.
    """
    log.info("Configuration requested.")
    return pintu.config.dict()


@api.on_event("startup")
async def startup_event():
    """
    Initialization
    """
    log.info("Starting up...")
    pintu.gpio.initialize()


@api.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown
    """
    log.info("Shutting down...")
    pintu.gpio.graceful_shutdown()


if __name__ == "__main__":
    log.info(f"Starting API on port {pintu.config.api_port}")
    uvicorn.run("api:api", host="0.0.0.0", port=pintu.config.api_port)
    log.info("API exited ")
