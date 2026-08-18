from __future__ import annotations

from typing import Protocol

import cv2
import numpy as np


class FrameSource(Protocol):
    def read(self) -> tuple[bool, np.ndarray | None]: ...

    def release(self) -> None: ...


class OpenCvFrameSource:
    def __init__(self, source: int | str) -> None:
        self.capture = cv2.VideoCapture(source)
        if not self.capture.isOpened():
            raise RuntimeError(f"无法打开视频源：{source}")

    def read(self) -> tuple[bool, np.ndarray | None]:
        return self.capture.read()

    def release(self) -> None:
        self.capture.release()


class Picamera2FrameSource:
    """Read frames from a Raspberry Pi CSI camera through libcamera."""

    def __init__(self, width: int, height: int) -> None:
        try:
            from picamera2 import Picamera2
        except ImportError as error:
            raise RuntimeError(
                "未安装 Picamera2。请执行 sudo apt install python3-picamera2，并使用 "
                "python3 -m venv --system-site-packages 创建虚拟环境。"
            ) from error

        self.camera = Picamera2()
        configuration = self.camera.create_video_configuration(
            main={"size": (width, height), "format": "RGB888"}
        )
        self.camera.configure(configuration)
        self.camera.start()

    def read(self) -> tuple[bool, np.ndarray | None]:
        rgb_frame = self.camera.capture_array("main")
        if rgb_frame is None:
            return False, None
        return True, cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

    def release(self) -> None:
        self.camera.stop()
        self.camera.close()


def create_frame_source(
    backend: str, source: int | str, width: int, height: int
) -> FrameSource:
    if backend == "picamera2":
        return Picamera2FrameSource(width, height)
    return OpenCvFrameSource(source)
