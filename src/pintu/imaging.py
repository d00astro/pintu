# -*- coding: utf-8 -*-
"""
Basic Image classses and functions.
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
import enum
import json
import logging
import pathlib
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import cv2
import numpy

import pintu.default
import pintu.util

log = logging.getLogger(__name__)

_Image = TypeVar("_Image", bound="Image")


class ImageKind(str, enum.Enum):
    """
    Type of image - Indicates the image purpose.
    """

    input = "input"
    """Unmodified image, as from the capture device."""
    background = "background"
    """Estimated (static) background image, with foreground objects removed."""
    foreground = "foreground"
    """Estimated foreground image, with background removed/reduced."""
    detections = "detections"
    """Input image, with detections drawn for visualization purposes."""
    redacted_input = "redacted_input"
    """Input image, with uncertain objects removed. Used for training only."""
    redacted_foreground = "redacted_foreground"
    """Foreground image, with uncertain objects removed. For training only."""
    other = "other"
    """Other image types, such as masks or heatmaps."""

    def __str__(self) -> str:
        return self.name

    @property
    def inference(self) -> "ImageKind":
        """
        Gets the corresponding image kind, suitable for inference.


        :return:
            The image used for inference.
        """
        if self == ImageKind.redacted_foreground:
            return ImageKind.foreground
        return ImageKind.input

    @property
    def redacted(self) -> "ImageKind":
        """
        Gets the corresponding redacted image kind.


        :return:
            The redacted image kind.
        """
        if self == ImageKind.foreground:
            return ImageKind.redacted_foreground
        return ImageKind.redacted_input

    @staticmethod
    def sample_images() -> List["ImageKind"]:
        """
        Image kinds that are available in samples, prior to any annotations
        have been added.


        :return:
            List of image kinds.
        """
        return [ImageKind.input, ImageKind.background, ImageKind.foreground]

    @staticmethod
    def annoation_images():
        """
        Image kinds that are available in annotations.


        :return:
            List of image kinds.
        """
        return [
            ImageKind.detections,
            ImageKind.redacted_input,
            ImageKind.redacted_foreground,
        ]


class PaddedImage(NamedTuple):
    """
    A padded image matching a network's input structure.
    """

    pixel_data: numpy.ndarray
    """
    Raw pixels of an image matching the a network's input signature.

    A gray border may have been added to obtain the proper input size.
    """

    box_translation: numpy.ndarray
    """
    A translation vector for shifting detected boxes to the original image.
    """


class Color(NamedTuple):
    """Simple RGB color representation."""

    blue: int
    """Blue color componenet."""
    green: int
    """Green color component."""
    red: int
    """Red color component."""


RED = Color(red=230, green=25, blue=75)
"""Red"""
GREEN = Color(red=60, green=180, blue=75)
"""Green"""
YELLOW = Color(red=255, green=255, blue=200)
"""Yellow"""
BLUE = Color(red=0, green=130, blue=200)
"""Blue"""
ORANGE = Color(red=245, green=130, blue=200)
"""Trump"""
PURPLE = Color(red=145, green=30, blue=180)
"""Purple"""
CYAN = Color(red=70, green=240, blue=240)
"""Cyan"""
MAGENTA = Color(red=240, green=50, blue=230)
"""Magenta"""
LIME = Color(red=210, green=245, blue=60)
"""Lime"""
PINK = Color(red=250, green=190, blue=212)
"""Pink"""
TEAL = Color(red=0, green=128, blue=128)
"""Teal"""
LAVENDER = Color(red=220, green=190, blue=255)
"""Lavender"""
BROWN = Color(red=170, green=110, blue=40)
"""Brown"""
BEIGE = Color(red=255, green=250, blue=200)
"""Beige"""
MAROON = Color(red=128, green=0, blue=0)
"""Maroon"""
MINT = Color(red=170, green=255, blue=195)
"""Mint"""
OLIVE = Color(red=128, green=128, blue=0)
"""Olive"""
APRICOT = Color(red=255, green=215, blue=180)
"""Apricot"""
NAVY = Color(red=0, green=0, blue=128)
"""Navy"""
GREY = Color(red=128, green=128, blue=128)
"""Grey"""
WHITE = Color(red=255, green=255, blue=255)
"""White"""
BLACK = Color(red=0, green=0, blue=0)
"""Black"""


COLORS = [
    RED,
    GREEN,
    YELLOW,
    BLUE,
    ORANGE,
    PURPLE,
    CYAN,
    MAGENTA,
    LIME,
    PINK,
    TEAL,
    LAVENDER,
    BROWN,
    BEIGE,
    MAROON,
    MINT,
    OLIVE,
    APRICOT,
    NAVY,
    GREY,
    WHITE,
]
"""Colors to use for detections etc"""


def indexed_color(class_name: str) -> Color:
    """Return a color based on object hash."""

    def default_color(class_name: str) -> Color:
        ix = hash(class_name) % len(COLORS)
        return COLORS[ix]

    return collections.defaultdict(
        lambda: default_color(class_name), {"car": BLUE}
    )[class_name]


class Image:
    """Image representation"""

    def __init__(self, data: numpy.ndarray, kind: ImageKind, **kwargs) -> None:
        """
        Image


        :param image_data:
            Numpy array with the image data (bgr).

        :param kind:
            Image kind of the image.

        :raises ValueError:
            If the image data is not a numpy array.
        """
        if not isinstance(data, numpy.ndarray):
            raise ValueError(
                "Image 'image_data' must be of type 'numpy.ndarray'. "
                f"Got: {type(data)}"
            )

        self.data = data
        self.kind = ImageKind(kind)

        self._metadata = kwargs

    def copy(self, kind=None) -> "Image":
        return Image(data=self.data.copy(), kind=kind or self.kind)

    @property
    def shape(self) -> Tuple:
        """Numpy-style shape of the image."""
        return self.data.shape

    @property
    def height(self) -> int:
        """
        Pixel-height of the image.


        :return:
            Vertical height of the image, in pixels.
        """
        return self.shape[0]

    @property
    def width(self) -> int:
        """
        Pixel-width of the image.


        :return:
            Horizontal width of the image, in pixels.
        """
        return self.shape[1]

    @property
    def size(self) -> int:
        """
        Size of the image, in bytes.


        :return:
            Number of bytes utilized by the uncopressed image.
        """
        return numpy.size(self.data)

    @property
    def metadata(self) -> Dict:
        metadata = dict(self._metadata)
        metadata["kind"] = self.kind
        return metadata

    def draw_detection(
        self,
        cls: str,
        left: float,
        top: float,
        right: float,
        bottom: float,
        confidence: float = None,
        thickness: int = 2,
    ):
        """
        Draw a detection on the image.

        :param cls:
            Name of the detection class.

        :param left:
            Absolute x-coordinate of the left edge of the detection\

        :param top:
            Absolute y-coordinate of the top edge of the detection.

        :param right:
            Absolute x-coordinate of the right edge of the detection.

        :param bottom:
            Absolute y-coordinate of the bottom edge of the detection.

        :param confidence: (optional)
            Object confidence.
            Defaults to None.

        :param thickness: (optional)
            Box thickness.
            Defaults to 2.
        """

        if max(left, top, right, bottom) <= 1.0:
            left *= self.width
            top *= self.height
            right *= self.width
            bottom *= self.height

        left = int(left)
        top = int(top)
        right = int(right)
        bottom = int(bottom)

        color = indexed_color(cls)
        cv2.rectangle(
            self.data, (left, top), (right, bottom), color, thickness
        )
        cv2.rectangle(
            self.data,
            (left - int(thickness / 2), top - 13),
            (right + int(thickness / 2), top),
            color,
            -1,
        )
        confidence_str = (
            pintu.util.str_float(confidence, dec=2) if confidence else ""
        )
        cv2.putText(
            self.data,
            f"{cls} {confidence_str}",
            (left, top),
            cv2.FONT_HERSHEY_PLAIN,
            1,
            color=BLACK,
            thickness=1,
        )

    @classmethod
    def load(
        cls: Type[_Image], path: pathlib.Path, kind: ImageKind = None
    ) -> _Image:
        """
        Load Image from file


        :param path:
            Path of the image to load.

        :param kind:
            Kind of image, defaults to None

        :return:
            Image
        """
        image_bytes = path.read_bytes()
        return cls.decode(image_bytes)

        # image_data = cv2.imread(str(path))
        # if image_data is None:
        #     raise ValueError(f"No such file: {path}")

        # image_kind = kind or deduce_image_kind(path)

        # return Image(image_data=image_data, kind=image_kind)

    def save(
        self,
        path: pathlib.Path,
        base: Any = None,
        format: str = pintu.default.IMAGE_FORMAT,
    ) -> Dict:
        """
        Save image to file.


        :param path:
            Directory to save the image to.

        :param base:
            Base name / prefix to add to the file name, defaults to None

        :param fmt:
            Image format to save as, defaults to 'jpg'.

        :return:
            Additional meta-data that was not saved along with the image.
        """
        if path.is_dir():
            if base:
                if self.kind == ImageKind.input:
                    filename = base
                else:
                    filename = f"{base}_{self.kind}"
            else:
                filename = self.kind
            path = path / f"{filename}.{format}"
        save_path = path
        if not save_path.exists():
            save_path.write_bytes(self.encode(format=format))

        metadata = self.metadata
        metadata["path"] = str(save_path)

        return metadata

    def __str__(self) -> str:
        return f"{self.kind}:{self.width}x{self.height}"

    def __repr__(self) -> str:
        data_repr = f"{self.width}x{self.height}x{self.shape[2]}@{self.size}b"
        return (
            f"{self.__class__.__name__}("
            f"data=<{data_repr}>,"
            f"kind='{self.kind}'"
            ")"
        )

    def __bytes__(self) -> bytes:
        return self.encode()

    def encode(
        self,
        format="jpg",  # pintu.default.IMAGE_FORMAT,
    ) -> bytes:
        """
        Encode the image to an image bytes.

        :param format: (optional)
            Image format to encode.
            Defaults to "jpg".

        :return:
            bBtes of the encoded image.
        """
        _, img_array = cv2.imencode(f".{format}", self.data)

        metadata_json = json.dumps(self.metadata, separators=(",", ":"))
        mver = 1
        mlen = len(metadata_json) + 10
        metadata_str = f"{metadata_json}@{mlen:05}#{mver:03}"

        metadata_array = numpy.frombuffer(
            f"{metadata_str}".encode(), dtype=numpy.uint8
        )
        return numpy.concatenate((img_array, metadata_array)).tobytes()

    @classmethod
    def decode(cls: Type[_Image], image_bytes: bytes) -> _Image:
        """
        Decode encoded image bytes into an image (or frame)

        :param cls:
            Image subclass to decode to.

        :param image_bytes:
            Encoded image bytes

        :raises ValueError:
            If something cocks up.

        :return:
            Image object (or whatever subclass was specified).
        """
        img_array = numpy.frombuffer(image_bytes, numpy.uint8)
        img_data = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        # Check the last four bytes if the image is encoded with meta-data
        mver = image_bytes[-4:]
        if mver == b"#001":
            # Meta-data version 001#
            # Read the length of the meta-data in the preceding five bytes
            try:
                metadata_len = int(image_bytes[-9:-4].decode())
                metadata_raw = image_bytes[-metadata_len:]
                metadata_json = metadata_raw.decode().split("@")[0]
                metadata = json.loads(metadata_json)
            except ValueError as err:
                raise ValueError(
                    f"Unable to parse metadata of version {mver.decode()}"
                ) from err
        else:
            metadata = None

        metadata = metadata or {
            "kind": ImageKind.input,
        }

        return cls(img_data, **metadata)


class Frame(Image):
    """Frames are Images, but with a timetamp."""

    def __init__(
        self,
        data: numpy.ndarray,
        kind: ImageKind = ImageKind.input,
        timestamp: Union[str, datetime.datetime] = None,
        **kwargs,
    ) -> None:
        """
        Frame


        :param image_data:
            Raw image data buffer

        :param image_kind:
            Image kind, defaults to ImageKind.input

        :param timestamp:
            Timestamp when the frame was captured,
            Defaults to None = `now`.
        """
        super().__init__(data, kind, **kwargs)

        if isinstance(timestamp, str):
            timestamp = pintu.util.parse_timestamp(timestamp)

        self.timestamp = timestamp or pintu.util.now()

    @property
    def metadata(self) -> Dict:
        metadata = super().metadata
        metadata["timestamp"] = self.timestamp.isoformat()
        return metadata


class ImageLayers:
    """
    Collection of the different 'layers' of an image.

    - Background : Image with the foreground objects removed.
    - Foreground : Foreground objects with the background neutral grey.
    - Mask : Bitmask of teh pixels that constitute the foreground.
    """

    def __init__(
        self,
        background: numpy.ndarray,
        foreground: numpy.ndarray,
        mask: numpy.ndarray,
    ) -> None:
        """
        ImageLayers


        :param background:
            Raw image data of the background

        :param foreground:
            Raw image data of the foreground

        :param mask:
            Raw image data of the foreground mask
        """
        self.background: Image = Image(background, kind=ImageKind.background)
        self.foreground: Image = Image(foreground, kind=ImageKind.foreground)
        self.mask: Image = Image(mask, kind=ImageKind.other)


class FrameBuffer(collections.deque):
    """
    A Frame buffer / shift-register of frames,
    used to extract the layers of an image.
    """

    @property
    def full(self):
        """Checks if the buffer is full."""
        return len(self) >= self.maxlen

    def shift(self, item: Frame) -> Optional[Frame]:
        """
        Shift a new frame in, and pop the oldest frame if the buffer is full.


        :param item:
            Frame to add

        :return:
            The popped Frame, if any.
        """
        return_item = self.popleft() if self.full else None
        self.append(item)
        return return_item

    def median(self) -> Image:
        """
        Calculate the median image of the Frames in the buffer.


        :return:
            Median image, which is often a reasonable approximation of
            thebackground.
        """
        return Image(
            data=numpy.asarray(
                numpy.median([frame.data for frame in self], axis=0),
                dtype=numpy.uint8,
            ),
            kind=ImageKind.background,
        )

    def extract_layers(
        self,
        image: Image,
        diff_threshold: int = pintu.default.DIFF_THRESHOLD,
    ) -> ImageLayers:
        """
        Extract foreground/background layers from an image, using the history
        in the buffer.


        :param image:
            Image to extract layers from

        :param diff_threshold:
            Difference threshold used when segmenting foreground from
            background.
            Only pixels with a distance / difference between foreground and
            background
            pixel values greater than the threshold are classified as
            foreground.
            Defaults to camodel.default.DIFF_THRESHOLD

        :return:
            Object containing image layers.
        """
        background = self.median()

        diff = cv2.absdiff(image.data, background.data)

        mask = diff > diff_threshold

        foreground_data = numpy.full_like(
            image.data,
            GREY,
            numpy.uint8,
        )
        foreground_data[mask] = image.data[mask]

        return ImageLayers(
            background=background.data, foreground=foreground_data, mask=mask
        )


def deduce_image_kind(image_path: pathlib.Path) -> ImageKind:
    """
    Attempt to deduce the image kind of an image

    It does this by looking at (in order):

    - File name : If it contains any of the kind strings
    - Parent directory name : If it contains any of the kind strings
    - metadata.json file in same dir :
        - If it has a top-level key "path" that matches the image path
            AND a top-level key "kind" : the kind value is taken. e.g:
            {
                ...
                "path": <image_path>,
                "kind": "background",
                ...
            }
        - If it has a top-level key "images" : iterate through its sub-key and
            check if any matches the image path: take the sub-key as kind. e.g:
            {
                ...
                "images": {
                    ...
                    "foreground": <image_path>
                    ...
                }
                ...
            }
    - Fallback to 'other' type.


    :param image_path:
        Path to the image.

    :return:
        The deduced image kind, or ImageKind.other if unsuccessful.
    """
    image_kinds = list(ImageKind)
    image_kinds.reverse()  # Reversed order to test longer kinds first

    for path_part in [image_path.stem, image_path.parent.stem]:
        for img_kind in image_kinds:
            if img_kind in path_part:
                return img_kind

    metadata_file = image_path.parent.joinpath(pintu.util.METADATA_FILE_NAME)
    if metadata_file.is_file():
        with metadata_file.open("r") as f:
            metadata = json.load(f)

        # Check if the image path and kind is referred to at base level
        if (
            "kind" in metadata
            and "path" in metadata
            and pathlib.Path(metadata["path"]).samefile(image_path)
        ):
            return ImageKind(metadata["kind"])

        # Check if there are images indexed by kind
        if "images" in metadata:
            for kind, img_info in metadata["images"].items():
                if isinstance(img_info, str) and pathlib.Path(
                    img_info
                ).samefile(image_path):
                    return ImageKind(kind)
                if (
                    isinstance(img_info, dict)
                    and "path" in img_info
                    and pathlib.Path(img_info["path"]).samefile(image_path)
                ):
                    return img_info.get("kind", kind)

    return ImageKind.other


def frames_from_image_dir(
    directory_path: pathlib.Path,
    start_time: datetime.datetime = None,
    image_interval: datetime.timedelta = None,
    sample_rate: float = None,
    duration: datetime.timedelta = None,
) -> Iterable[Frame]:
    """
    Read a stream of Frames form a directory of images.


    :param directory_path:
        Directory containing the images.

    :param start_time:
        Starting timestamp of the first frame.
        If not set, the timestamp will be deduced from the image name,
        if possible.
        This parameter is only required in conjunction with `image_interval` if
        the image file names do not contain the frame timestamps.
        Defaults to None

    :param image_interval:
        Time interval between images.
        This parameter is only required in conjunction with `start_time` if the
        image file names do not contain the frame timestamps.
        Defaults to None

    :param sample_rate:
        Maximum rate at which to sample images.
        Any images with (deduced or calculated) timestamps with more frequent
        rate than this will be skipped.
        Defaults to None - All frames.

    :param duration:
        Stop emitting frames when the (deduced or calculated) timestamps
        of the frames have exceeded this amount beyond the start time.
        Defaults to None - All frames.

    :raises ValueError:
        If the timestamps can't be deduced or calculated for the frames.
        E.g. if the file names does not contain the time stamps *and*
        the`start_time` and `image_interval` were not provided.

    :yield:
        Frame
    """
    files = directory_path.glob("*input.*")

    duration_seconds = duration.total_seconds() if duration else float("inf")

    sample_interval_seconds = 0.0
    if sample_rate:
        sample_interval_seconds = 1.0 / sample_rate

    next_sample_seconds: float = 0.0
    file_timestamp: Optional[datetime.datetime]
    for i, file in enumerate(sorted(files)):
        try:
            file_timestamp = pintu.util.file_datetime(file)
        except ValueError:
            file_timestamp = None

        start_time = (
            start_time
            or file_timestamp
            or datetime.datetime.now(datetime.timezone.utc)
        )

        if not file_timestamp:
            if not image_interval:
                raise ValueError(
                    "Unable to derive image interval. "
                    "Either provide `image_interval` argument "
                    "or use images with names including timestamps, with "
                    f"format: '{pintu.default.COMPACT_TIMESTAMP_FORMAT}'"
                )
            file_timestamp = start_time + (i * image_interval)

        progress_seconds = (file_timestamp - start_time).total_seconds()
        if progress_seconds > duration_seconds:
            log.info("Capture reached end duration.")
            break

        if progress_seconds < next_sample_seconds:
            log.debug("Skipping")
            continue

        next_sample_seconds += sample_interval_seconds

        image = cv2.imread(str(file))

        if image is not None:
            log.debug(f"Read file: {file}")
            yield Frame(image, timestamp=file_timestamp)


def frames_from_video(
    source_uri: str,
    start_time: datetime.datetime = None,
    sample_rate: float = None,
    duration: datetime.timedelta = None,
) -> Iterable[Frame]:
    """
    Extract Frames from video url or file.


    :param source_uri:
        URI of the video file or stream URL (e.g. camera stream).

    :param start_time:
        Start time of the first frame.
        Only meaningful for recordings / files.
        Defaults to None - Now

    :param sample_rate:
        Maximum rate to sample frames at, defaults to None

    :param duration:
        Duration of capture, defaults to None

    :yield:
        Frames
    """
    log.info(f"Capturing video from: '{str(source_uri)}'")
    cap = cv2.VideoCapture(str(source_uri))

    start_time = start_time or datetime.datetime.now(datetime.timezone.utc)
    log.info(f"Capture started at : {start_time.isoformat()}")

    sample_interval_milliseconds = 0.0
    if sample_rate:
        sample_interval_milliseconds = 1000.0 / sample_rate

    end_pos_milliseconds = (
        duration.total_seconds() * 1000.0 if duration else float("inf")
    )

    next_sample_pos_milliseconds: float = 0.0
    while True:

        if not cap.grab():
            log.warning("Unable to capture frame. End of stream?")
            break

        frame_pos_milliseconds = cap.get(cv2.CAP_PROP_POS_MSEC)
        if frame_pos_milliseconds > end_pos_milliseconds:
            log.info("Capture reached end duration.")
            break

        if frame_pos_milliseconds < next_sample_pos_milliseconds:
            continue

        ok, frame_image = cap.retrieve()

        if not ok:
            log.warning("Unable to retrieve frame data. End of stream?")
            break

        next_sample_pos_milliseconds += sample_interval_milliseconds
        yield Frame(
            frame_image,
            timestamp=start_time
            + datetime.timedelta(milliseconds=frame_pos_milliseconds),
        )
