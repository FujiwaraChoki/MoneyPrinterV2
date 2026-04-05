import os
import sys
import unittest

import numpy as np
from moviepy.editor import ImageClip


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


from cinematic_motion import calculate_motion_window
from cinematic_motion import FRAME_WIDTH
from cinematic_motion import render_motion_frame


class CinematicMotionTests(unittest.TestCase):
    def _build_source_frame(self) -> np.ndarray:
        height = 1920
        width = 1080
        x = np.linspace(60, 220, width, dtype=np.uint8)
        y = np.linspace(80, 240, height, dtype=np.uint8)
        red = np.tile(x, (height, 1))
        green = np.tile(y[:, None], (1, width))
        blue = np.full((height, width), 140, dtype=np.uint8)
        return np.dstack((red, green, blue))

    def test_render_motion_frame_keeps_canvas_filled_during_zoom_and_pan(self) -> None:
        source_frame = self._build_source_frame()

        for t in (0.0, 1.0, 2.5, 5.0):
            actual_frame = render_motion_frame(
                source_frame,
                t=t,
                duration=5.0,
                index=0,
                pan_enabled=True,
                pan_intensity=0.03,
                zoom_intensity=1.12,
            )

            self.assertEqual(actual_frame.shape, source_frame.shape)
            self.assertGreaterEqual(int(actual_frame.min()), 50)

    def test_calculate_motion_window_reverses_pan_direction_by_index(self) -> None:
        baseline_window = calculate_motion_window(
            t=5.0,
            duration=5.0,
            index=0,
            pan_enabled=False,
            pan_intensity=0.03,
            zoom_intensity=1.12,
        )
        even_window = calculate_motion_window(
            t=5.0,
            duration=5.0,
            index=0,
            pan_enabled=True,
            pan_intensity=0.03,
            zoom_intensity=1.12,
        )
        odd_window = calculate_motion_window(
            t=5.0,
            duration=5.0,
            index=1,
            pan_enabled=True,
            pan_intensity=0.03,
            zoom_intensity=1.12,
        )

        self.assertEqual(even_window.crop_top, baseline_window.crop_top)
        self.assertLess(even_window.crop_left, baseline_window.crop_left)
        self.assertGreater(odd_window.crop_left, baseline_window.crop_left)

    def test_calculate_motion_window_even_scene_stays_left_of_center(self) -> None:
        offsets = []

        for t in (0.0, 1.25, 2.5, 3.75, 5.0):
            window = calculate_motion_window(
                t=t,
                duration=5.0,
                index=0,
                pan_enabled=True,
                pan_intensity=0.03,
                zoom_intensity=1.12,
            )
            centered_left = (window.resize_width - FRAME_WIDTH) / 2
            offsets.append(window.crop_left - centered_left)

        self.assertTrue(all(offset <= 0 for offset in offsets))
        self.assertEqual(offsets, sorted(offsets, reverse=True))

    def test_calculate_motion_window_odd_scene_stays_right_of_center(self) -> None:
        offsets = []

        for t in (0.0, 1.25, 2.5, 3.75, 5.0):
            window = calculate_motion_window(
                t=t,
                duration=5.0,
                index=1,
                pan_enabled=True,
                pan_intensity=0.03,
                zoom_intensity=1.12,
            )
            centered_left = (window.resize_width - FRAME_WIDTH) / 2
            offsets.append(window.crop_left - centered_left)

        self.assertTrue(all(offset >= 0 for offset in offsets))
        self.assertEqual(offsets, sorted(offsets))

    def test_calculate_motion_window_uses_eased_zoom_progress(self) -> None:
        quarter_window = calculate_motion_window(
            t=1.25,
            duration=5.0,
            index=0,
            pan_enabled=True,
            pan_intensity=0.03,
            zoom_intensity=1.12,
        )
        three_quarter_window = calculate_motion_window(
            t=3.75,
            duration=5.0,
            index=0,
            pan_enabled=True,
            pan_intensity=0.03,
            zoom_intensity=1.12,
        )

        linear_quarter_scale = 1.0 + (1.12 - 1.0) * 0.25
        linear_three_quarter_scale = 1.0 + (1.12 - 1.0) * 0.75

        self.assertLess(quarter_window.scale, linear_quarter_scale)
        self.assertGreater(three_quarter_window.scale, linear_three_quarter_scale)

    def test_calculate_motion_window_uses_subpixel_motion_positions(self) -> None:
        positions = [
            round(
                calculate_motion_window(
                    t=frame_index / 30,
                    duration=3.75,
                    index=0,
                    pan_enabled=True,
                    pan_intensity=0.03,
                    zoom_intensity=1.12,
                ).crop_left,
                4,
            )
            for frame_index in range(24)
        ]

        self.assertGreater(len(set(positions)), 20)
        self.assertTrue(any(position != round(position) for position in positions))

    def test_moviepy_motion_transform_keeps_rendered_clip_filled(self) -> None:
        source_frame = self._build_source_frame()
        clip = ImageClip(source_frame).set_duration(5.0).set_fps(30)
        motion_clip = clip.fl(
            lambda gf, t: render_motion_frame(
                gf(t),
                t=t,
                duration=5.0,
                index=0,
                pan_enabled=True,
                pan_intensity=0.03,
                zoom_intensity=1.12,
            ),
            apply_to=["mask"],
        )

        for t in (0.0, 1.0, 2.5, 5.0):
            actual_frame = motion_clip.get_frame(t)

            self.assertEqual(actual_frame.shape, source_frame.shape)
            self.assertGreaterEqual(int(actual_frame.min()), 50)


if __name__ == "__main__":
    unittest.main()
