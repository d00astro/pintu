# -*- coding: utf-8 -*-
"""
Object Detection
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
from typing import Dict, List, Tuple

import ncnn
import ncnn.model_zoo
import ncnn.utils.functional
import numpy
import redis

import pintu.default
import pintu.imaging
import pintu.util

log = logging.getLogger(__name__)

# Shorthand
ffmt = pintu.util.str_float


class Detector:
    """Detector

    On instantiation loads a NCNN FCOS-style one-stage, anchor-free object detection
    model, using ATSS for target sampling and GFL for classification and box regression.

    Once instaniated the detector can be invoked with images to detect the
    presence of objects.
    """

    def __init__(
        self,
        param_file: pathlib.Path,
        bin_file: pathlib.Path,
        name: str = None,
        input_shape: Tuple[int, ...] = (320, 320, 3),
        prob_threshold: float = pintu.default.CONFIDENCE_TRESHOLD,
        nms_threshold: float = 1 - pintu.default.NMS_IOU_THRESHOLD,
        num_threads: int = 1,
        use_gpu: bool = False,
        mean_vals: List[float] = None,
        norm_vals: List[float] = None,
        reg_max: int = 7,
        strides: List[int] = None,
        num_candidate: int = 1000,
        top_k: int = -1,
        class_names: List[str] = None,
        input_name: str = "input.1",
        score_output_names=None,
        boxes_output_names=None,
    ):
        """
        Instantiate detector.

        :param param_file:
            NCNN model parameters definition file.

        :param bin_file:
            NCNN model bin / weights file.

        :param name: (optional)
            Name of the model.
            Defaults to None - The base of the bin/weights file.

        :param input_shape: (optional)
            Shape of the input layer.
            Defaults to (320, 320, 3).

        :param prob_threshold: (optional)
            Confidence threshold for detected objects.
            Defaults to pintu.default.CONFIDENCE_TRESHOLD.

        :param nms_threshold: (optional)
            NMS threshold for de-duplication.
            Defaults to 1-pintu.default.NMS_IOU_THRESHOLD.

        :param num_threads: (optional)
            Maximum number of execution threads to use for inference.
            Defaults to 1.

        :param use_gpu: (optional)
            Use GPU (if present)
            Defaults to False.

        :param mean_vals: (optional)
            Expected input image range mean values ([B,G,R]), for normalization:
            `(input - mean_vals) * norm_vals`
            Defaults to [103.53, 116.28, 123.675].

        :param norm_vals: (optional)
            Expected input image range normalization values ([B,G,R]):
            `(input - mean_vals) * norm_vals`
            Defaults to [0.017429, 0.017507, 0.017125].

        :param reg_max: (optional)
            Max box regression.
            Defaults to 7.

        :param strides: (optional)
            Backbone strides.
            Defaults to None.

        :param num_candidate: (optional)
            Number of candidates.
            Defaults to 1000.

        :param top_k: (optional)
            NMS selection.
            Defaults to -1.

        :param class_names: (optional)
            List of detection classes names (in order).
            Defaults to None.

        :param input_name: (optional)
            Name of the input node.
            Defaults to "input.1".

        :param score_output_names: (optional)
            Names of the output nodes for the scores.
            Default: ["cls_pred_stride_8", "cls_pred_stride_16", "cls_pred_stride_32"].

        :param boxes_output_names: (optional)
            Names of the output nodes for the boxes.
            Default: ["dis_pred_stride_8", "dis_pred_stride_16", "dis_pred_stride_32"]
        """
        self.name = name or bin_file.stem
        self.input_shape = input_shape
        self.prob_threshold = prob_threshold
        self.nms_threshold = nms_threshold
        self.num_threads = num_threads
        self.use_gpu = use_gpu

        self.mean_vals = mean_vals or [103.53, 116.28, 123.675]
        self.norm_vals = norm_vals or [0.017429, 0.017507, 0.017125]

        self.reg_max = reg_max
        self.strides = strides or [8, 16, 32]
        self.num_candidate = num_candidate
        self.top_k = top_k

        self.class_names = class_names or pintu.util.read_lines(
            pintu.default.DETECTION_NAMES_FILE
        )

        self.input_name = input_name
        self.score_output_names = score_output_names or [
            "cls_pred_stride_8",
            "cls_pred_stride_16",
            "cls_pred_stride_32",
        ]
        self.boxes_output_names = boxes_output_names or [
            "dis_pred_stride_8",
            "dis_pred_stride_16",
            "dis_pred_stride_32",
        ]
        self.net = ncnn.Net()
        self.net.opt.use_vulkan_compute = self.use_gpu
        self.net.opt.num_threads = self.num_threads
        self.net.load_param(str(param_file))
        self.net.load_model(str(bin_file))

    @property
    def input_size(self):
        """Width & Height of the input.

        :return:
            Tuple with the input (width, height)
        """
        return (self.input_shape[1], self.input_shape[0])

    def __del__(self):
        """Delete the model net"""
        self.net = None

    def __call__(self, image: pintu.imaging.Image) -> List[Dict]:
        """
        Perform object detection inference on an image

        :param image:
            Image to detect objects in.

        :return:
            List one dictionary per detected object, each dictionars containing
            the following fields:

            - "class"       : (str)     The name of the object detected.
            - "confidence"  : (float)   The confidence in the detection.
            - "left"        : (float)   Absolute x-coordinate of the left edge.
            - "top"         : (float)   Absolute y-coordinate of the top edge.
            - "right"       : (float)   Absolute x-coordinate of the right edge.
            - "bottom"      : (float)   Absolute y-coordinate of the bottom edge.
        """
        scale = 1.0
        if image.width > image.height:
            scale = float(self.input_shape[1]) / image.width
            w = self.input_shape[1]
            h = int(image.height * scale)
        else:
            scale = float(self.input_shape[0]) / image.height
            h = self.input_shape[0]
            w = int(image.width * scale)

        mat_in = ncnn.Mat.from_pixels_resize(
            image.data,
            ncnn.Mat.PixelType.PIXEL_BGR,
            image.width,
            image.height,
            w,
            h,
        )

        # pad to target_size rectangle
        wpad = (w + 31) // 32 * 32 - w
        hpad = (h + 31) // 32 * 32 - h
        mat_in_pad = ncnn.copy_make_border(
            mat_in,
            hpad // 2,
            hpad - hpad // 2,
            wpad // 2,
            wpad - wpad // 2,
            ncnn.BorderType.BORDER_CONSTANT,
            0,
        )

        # Normalize image
        mat_in_pad.substract_mean_normalize(self.mean_vals, self.norm_vals)

        #
        ex = self.net.create_extractor()
        ex.input(self.input_name, mat_in_pad)

        scores = [ex.extract(x)[1] for x in self.score_output_names]
        scores = [numpy.reshape(x, (-1, 80)) for x in scores]

        raw_boxes = [ex.extract(x)[1] for x in self.boxes_output_names]
        raw_boxes = [numpy.reshape(x, (-1, 32)) for x in raw_boxes]

        # generate centers
        decode_boxes = []
        select_scores = []
        for stride, box_distribute, score in zip(
            self.strides, raw_boxes, scores
        ):
            # centers
            if mat_in_pad.w > mat_in_pad.h:
                fm_w = mat_in_pad.w // stride
                fm_h = score.shape[0] // fm_w
            else:
                fm_h = mat_in_pad.h // stride
                fm_w = score.shape[1] // fm_h
            h_range = numpy.arange(fm_h)
            w_range = numpy.arange(fm_w)
            ww, hh = numpy.meshgrid(w_range, h_range)
            ct_row = (hh.flatten() + 0.5) * stride
            ct_col = (ww.flatten() + 0.5) * stride
            center = numpy.stack((ct_col, ct_row, ct_col, ct_row), axis=1)

            # box distribution to distance
            reg_range = numpy.arange(self.reg_max + 1)
            box_distance = box_distribute.reshape((-1, self.reg_max + 1))
            box_distance = ncnn.utils.functional.softmax(box_distance)
            box_distance = box_distance * numpy.expand_dims(reg_range, axis=0)
            box_distance = numpy.sum(box_distance, axis=1).reshape((-1, 4))
            box_distance = box_distance * stride

            # top K candidate
            topk_idx = numpy.argsort(score.max(axis=1))[::-1]
            topk_idx = topk_idx[: self.num_candidate]
            center = center[topk_idx]
            score = score[topk_idx]
            box_distance = box_distance[topk_idx]

            # decode box
            decode_box: List[int] = center + [-1, -1, 1, 1] * box_distance

            select_scores.append(score)
            decode_boxes.append(decode_box)

        # nms
        bboxes = numpy.concatenate(decode_boxes, axis=0)
        confidences = numpy.concatenate(select_scores, axis=0)
        picked_box = []
        picked_probs = []
        picked_labels = []
        for class_index in range(0, confidences.shape[1]):
            probs = confidences[:, class_index]
            mask = probs > self.prob_threshold
            probs = probs[mask]
            if probs.shape[0] == 0:
                continue
            subset_boxes = bboxes[mask, :]
            picked = ncnn.utils.functional.nms(
                subset_boxes,
                probs,
                iou_threshold=self.nms_threshold,
                top_k=self.top_k,
            )

            picked_box.append(subset_boxes[picked])
            picked_probs.append(probs[picked])
            picked_labels.extend([class_index] * len(picked))

        if not picked_box:
            return []

        picked_box = numpy.concatenate(picked_box)
        picked_probs = numpy.concatenate(picked_probs)

        return [
            {
                "class": str(self.class_names[label]),
                "confidence": float(score),
                "left": float(
                    (bbox[0] - wpad / 2) / scale if bbox[0] > 0 else 0
                ),
                "top": float(
                    (bbox[1] - hpad / 2) / scale if bbox[1] > 0 else 0
                ),
                "right": float(
                    (bbox[2] - wpad / 2) / scale
                    if bbox[2] < mat_in_pad.w
                    else mat_in_pad.w / scale
                ),
                "bottom": float(
                    (bbox[3] - wpad / 2) / scale
                    if bbox[3] < mat_in_pad.h
                    else mat_in_pad.h / scale
                ),
            }
            for label, score, bbox in zip(
                picked_labels, picked_probs, picked_box
            )
        ]


def analyze_stream(
    bus: redis.Redis,
    camera_name: str,
    detector: Detector,
    inference_image: pintu.imaging.ImageKind = pintu.imaging.ImageKind(
        pintu.default.INFERENCE_IMAGE
    ),
    retention: datetime.timedelta = pintu.default.RETENTION,
):
    """
    Analyze a captured stream of images, by means of sampling the last captured image.

    :param bus:
        Redis instace to connect to.

    :param camera_name:
        Name of the camera, stream to sample.

    :param detector:
        Detector to use for inference.

    :param inference_image: (optional)
        Version of the image to sample.
        Defaults to pintu.imaging.ImageKind( pintu.default.INFERENCE_IMAGE ).

    :param retention: (optional)
        Duration to re
        Defaults to pintu.default.RETENTION.
    """
    camera_stream_key = f"/pintu/camera/{camera_name}/capture"
    detection_stream_key = f"/pintu/camera/{camera_name}/detection"
    ttl = retention * 1.10

    for record in pintu.util.sample_stream(bus, camera_stream_key):
        image_key = record[inference_image]

        image_bytes = bus.get(image_key)
        if not image_bytes:
            log.error(f"No data at image key: {image_key}")
            continue

        frame = pintu.imaging.Frame.decode(image_bytes)

        detections = detector(frame)
        # detections = model.detect(frame)

        frame_key = pintu.util.safe_str(record["key"])
        detection_base_key = f"{frame_key}/{detector.name}"
        detections_data: pintu.util.RedisMapping = {}
        detections_data["detections"] = detection_base_key

        pipe = bus.pipeline()
        log.debug(
            f"Frame {frame.timestamp} contains {len(detections)} objects."
        )
        for det_ix, detection in enumerate(detections):
            log.debug(f"Detection {det_ix}: {detection}")
            detection_key = f"{detection_base_key}/{det_ix}"
            detections_data[str(det_ix)] = detection_key
            pipe.hset(detection_key, mapping=detection)
            pipe.expire(detection_key, ttl)
            pipe.rpush(detection_base_key, detection_key)

        detections_data["count"] = len(detections)
        pipe.hset(frame_key, mapping=detections_data)
        detections_data.update(record)
        pipe.expire(detection_base_key, ttl)
        pipe.expire(frame_key, ttl)
        pipe.xadd(
            detection_stream_key,
            detections_data,
            id=pintu.util.stream_id(frame.timestamp),
            maxlen=1000,
            approximate=True,
        )
        try:
            pipe.execute(True)
            log.log(
                5,
                f"Detections recorded for frame at {frame.timestamp}: "
                f"{len(detections)}",
            )
        except redis.exceptions.ResponseError as ex:
            log.error(
                f"Failed to push detections to detection stream : {frame}. "
                f"Error: {ex}"
            )


if __name__ == "__main__":
    import pathlib

    import redis

    import pintu
    import pintu.detection

    bus = redis.Redis(
        host=pintu.config.redis_host, port=pintu.config.redis_port
    )

    mod_dir = pintu.config.detection_model_dir
    mod_nm = pintu.config.detection_model_name
    detector = pintu.detection.Detector(
        mod_dir / f"{mod_nm}.param", mod_dir / f"{mod_nm}.bin"
    )

    pintu.detection.analyze_stream(
        bus=bus,
        camera_name=pintu.config.camera_name,
        detector=detector,
        inference_image=pintu.config.inference_image,
        retention=pintu.config.retention,
    )
