from __future__ import annotations

import argparse
import time
from collections import deque
from pathlib import Path

import cv2

from src.camera import create_frame_source
from src.detector import Detection, YoloOnnxDetector
from src.geometry import parse_rectangle, point_in_rectangle


def parse_source(value: str) -> int | str:
    return int(value) if value.isdigit() else value


def draw_detection(frame, detection: Detection, in_region: bool) -> None:
    x1, y1, x2, y2 = detection.box
    color = (50, 220, 50) if in_region else (80, 170, 255)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    text = f"{detection.label} {detection.confidence:.0%}"
    cv2.putText(frame, text, (x1, max(22, y1 - 7)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)


def format_status(fps: float, object_count: int, region_count: int | None) -> str:
    message = f"status fps={fps:.1f} objects={object_count}"
    if region_count is not None:
        message += f" in_region={region_count}"
    return message


def run(args: argparse.Namespace) -> None:
    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"找不到模型：{model_path}。请先运行 python scripts/export_yolo.py")
    if args.log_interval <= 0:
        raise ValueError("--log-interval 必须大于 0")

    region = parse_rectangle(args.region)
    detector = YoloOnnxDetector(str(model_path), args.confidence, args.iou)
    capture = create_frame_source(
        args.camera_backend, parse_source(args.source), args.camera_width, args.camera_height
    )

    durations: deque[float] = deque(maxlen=30)
    next_log_at = time.monotonic() + args.log_interval
    print("headless mode: use Ctrl+C to exit." if args.headless else "按 q 或 Esc 退出。")
    try:
        while True:
            success, frame = capture.read()
            if not success or frame is None:
                break

            started = time.perf_counter()
            detections = detector.detect(frame)
            durations.append(time.perf_counter() - started)
            tracked = [item for item in detections if item.label in args.classes]
            region_count = 0
            for detection in tracked:
                in_region = region is not None and point_in_rectangle(detection.center, region)
                region_count += int(in_region)
                if not args.headless:
                    draw_detection(frame, detection, in_region)

            fps = len(durations) / sum(durations) if durations else 0
            if args.headless:
                if time.monotonic() >= next_log_at:
                    print(format_status(fps, len(tracked), region_count if region is not None else None), flush=True)
                    next_log_at = time.monotonic() + args.log_interval
                continue

            if region is not None:
                x1, y1, x2, y2 = region
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 200, 0), 2)
            summary = f"FPS: {fps:.1f} | objects: {len(tracked)}"
            if region is not None:
                summary += f" | in region: {region_count}"
            cv2.putText(frame, summary, (15, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 4, cv2.LINE_AA)
            cv2.putText(frame, summary, (15, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow("Edge Vision", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    except KeyboardInterrupt:
        print("stopped", flush=True)
    finally:
        capture.release()
        if not args.headless:
            cv2.destroyAllWindows()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="实时人车检测与区域计数")
    parser.add_argument("--model", default="models/yolo11n.onnx")
    parser.add_argument("--source", default="0", help="摄像头编号、视频文件路径或 RTSP 地址")
    parser.add_argument("--camera-backend", choices=("opencv", "picamera2"), default="opencv")
    parser.add_argument("--camera-width", type=int, default=640)
    parser.add_argument("--camera-height", type=int, default=480)
    parser.add_argument("--headless", action="store_true", help="禁用 OpenCV 窗口，并将运行状态写入标准输出")
    parser.add_argument("--log-interval", type=float, default=5.0, help="无显示器模式的状态日志间隔（秒）")
    parser.add_argument("--confidence", type=float, default=0.45)
    parser.add_argument("--iou", type=float, default=0.45)
    parser.add_argument("--region", help="计数区域：x1,y1,x2,y2，例如 120,80,520,420")
    parser.add_argument("--classes", nargs="+", default=["person", "car", "bus", "truck", "motorcycle"])
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
