from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
import onnxruntime as ort

from src.labels import COCO_LABELS


@dataclass(frozen=True)
class Detection:
    class_id: int
    label: str
    confidence: float
    box: tuple[int, int, int, int]

    @property
    def center(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.box
        return ((x1 + x2) // 2, (y1 + y2) // 2)


class YoloOnnxDetector:
    """Run a standard non-end-to-end Ultralytics YOLO ONNX export."""

    def __init__(self, model_path: str, confidence_threshold: float = 0.45, iou_threshold: float = 0.45) -> None:
        providers = ort.get_available_providers()
        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name
        input_shape = self.session.get_inputs()[0].shape
        self.input_size = int(input_shape[2]) if isinstance(input_shape[2], int) else 640
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold

    def detect(self, frame: np.ndarray) -> list[Detection]:
        image, ratio, padding = self._letterbox(frame)
        tensor = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)
        tensor = np.ascontiguousarray(tensor, dtype=np.float32) / 255.0
        prediction = self.session.run(None, {self.input_name: tensor[None]})[0]
        return self._postprocess(prediction, frame.shape[:2], ratio, padding)

    def _letterbox(self, frame: np.ndarray) -> tuple[np.ndarray, float, tuple[float, float]]:
        height, width = frame.shape[:2]
        ratio = min(self.input_size / width, self.input_size / height)
        resized_size = (round(width * ratio), round(height * ratio))
        resized = cv2.resize(frame, resized_size, interpolation=cv2.INTER_LINEAR)
        pad_x = (self.input_size - resized_size[0]) / 2
        pad_y = (self.input_size - resized_size[1]) / 2
        bordered = cv2.copyMakeBorder(
            resized,
            int(np.floor(pad_y)),
            int(np.ceil(pad_y)),
            int(np.floor(pad_x)),
            int(np.ceil(pad_x)),
            cv2.BORDER_CONSTANT,
            value=(114, 114, 114),
        )
        return bordered, ratio, (pad_x, pad_y)

    def _postprocess(
        self,
        prediction: np.ndarray,
        original_shape: tuple[int, int],
        ratio: float,
        padding: tuple[float, float],
    ) -> list[Detection]:
        candidates = np.squeeze(prediction)
        if candidates.ndim != 2:
            raise ValueError(f"不支持的模型输出形状: {prediction.shape}")
        if candidates.shape[0] < candidates.shape[1]:
            candidates = candidates.T
        if candidates.shape[1] < 6:
            raise ValueError("模型输出不包含 YOLO 类别分数；请使用 scripts/export_yolo.py 导出的模型")

        class_scores = candidates[:, 4:]
        class_ids = class_scores.argmax(axis=1)
        confidences = class_scores[np.arange(len(candidates)), class_ids]
        selected = confidences >= self.confidence_threshold
        candidates, class_ids, confidences = candidates[selected], class_ids[selected], confidences[selected]

        boxes: list[list[int]] = []
        for center_x, center_y, width, height in candidates[:, :4]:
            boxes.append([
                int(center_x - width / 2),
                int(center_y - height / 2),
                int(width),
                int(height),
            ])
        indices = cv2.dnn.NMSBoxes(boxes, confidences.tolist(), self.confidence_threshold, self.iou_threshold)
        if len(indices) == 0:
            return []

        original_height, original_width = original_shape
        pad_x, pad_y = padding
        detections: list[Detection] = []
        for index in np.array(indices).reshape(-1):
            x, y, width, height = boxes[int(index)]
            x1 = max(0, min(original_width - 1, round((x - pad_x) / ratio)))
            y1 = max(0, min(original_height - 1, round((y - pad_y) / ratio)))
            x2 = max(0, min(original_width - 1, round((x + width - pad_x) / ratio)))
            y2 = max(0, min(original_height - 1, round((y + height - pad_y) / ratio)))
            class_id = int(class_ids[int(index)])
            label = COCO_LABELS[class_id] if class_id < len(COCO_LABELS) else f"class_{class_id}"
            detections.append(Detection(class_id, label, float(confidences[int(index)]), (x1, y1, x2, y2)))
        return detections
