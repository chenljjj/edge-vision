from pathlib import Path

from ultralytics import YOLO


MODEL_NAME = "yolo11n.pt"
OUTPUT_PATH = Path("models/yolo11n.onnx")


def main() -> None:
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    model = YOLO(MODEL_NAME)
    model.export(format="onnx", imgsz=640, opset=17, simplify=True)
    exported = Path(MODEL_NAME).with_suffix(".onnx")
    exported.replace(OUTPUT_PATH)
    print(f"已生成 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
