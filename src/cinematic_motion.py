from dataclasses import dataclass

import numpy as np
from PIL import Image


FRAME_WIDTH = 1080
FRAME_HEIGHT = 1920


@dataclass(frozen=True)
class MotionWindow:
    scale: float
    resize_width: float
    resize_height: float
    crop_left: float
    crop_top: float


def _transform_filter():
    if hasattr(Image, "Resampling"):
        return Image.Resampling.BICUBIC

    return Image.BICUBIC


def _smoothstep(progress: float) -> float:
    return progress * progress * (3.0 - 2.0 * progress)


def calculate_motion_window(
    *,
    t: float,
    duration: float,
    index: int,
    pan_enabled: bool,
    pan_intensity: float,
    zoom_intensity: float,
    frame_width: int = FRAME_WIDTH,
    frame_height: int = FRAME_HEIGHT,
) -> MotionWindow:
    safe_duration = max(float(duration), 0.001)
    progress = min(max(float(t) / safe_duration, 0.0), 1.0)
    eased_progress = _smoothstep(progress)
    safe_zoom = max(float(zoom_intensity), 1.0)
    safe_pan = max(float(pan_intensity), 0.0)

    scale = 1.0 + (safe_zoom - 1.0) * eased_progress
    resize_width = max(float(frame_width), frame_width * scale)
    resize_height = max(float(frame_height), frame_height * scale)

    max_left = max(0, resize_width - frame_width)
    max_top = max(0, resize_height - frame_height)
    center_left = max_left / 2
    center_top = max_top / 2

    drift = 0.0
    if pan_enabled and max_left > 0:
        max_offset = min(frame_width * safe_pan, center_left)
        direction = -1 if index % 2 == 0 else 1
        drift = direction * max_offset * eased_progress

    crop_left = min(max(center_left + drift, 0.0), max_left)
    crop_top = center_top

    return MotionWindow(
        scale=scale,
        resize_width=resize_width,
        resize_height=resize_height,
        crop_left=crop_left,
        crop_top=crop_top,
    )


def render_motion_frame(
    frame: np.ndarray,
    *,
    t: float,
    duration: float,
    index: int,
    pan_enabled: bool,
    pan_intensity: float,
    zoom_intensity: float,
    frame_width: int = FRAME_WIDTH,
    frame_height: int = FRAME_HEIGHT,
) -> np.ndarray:
    window = calculate_motion_window(
        t=t,
        duration=duration,
        index=index,
        pan_enabled=pan_enabled,
        pan_intensity=pan_intensity,
        zoom_intensity=zoom_intensity,
        frame_width=frame_width,
        frame_height=frame_height,
    )

    image = Image.fromarray(frame)
    if (
        abs(window.scale - 1.0) < 1e-9
        and abs(window.crop_left) < 1e-9
        and abs(window.crop_top) < 1e-9
    ):
        return np.array(image)

    transformed_image = image.transform(
        (frame_width, frame_height),
        Image.AFFINE,
        (
            1.0 / window.scale,
            0.0,
            window.crop_left / window.scale,
            0.0,
            1.0 / window.scale,
            window.crop_top / window.scale,
        ),
        resample=_transform_filter(),
    )

    return np.array(transformed_image)
