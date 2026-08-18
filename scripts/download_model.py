from pathlib import Path
from urllib.request import Request, urlopen


MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.onnx"
OUTPUT_PATH = Path("models/yolo11n.onnx")
MODEL_SIZE = 10_930_182


def main() -> None:
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    current_size = OUTPUT_PATH.stat().st_size if OUTPUT_PATH.exists() else 0
    if current_size == MODEL_SIZE:
        print(f"模型已存在：{OUTPUT_PATH}")
        return

    if current_size > MODEL_SIZE:
        raise RuntimeError(f"{OUTPUT_PATH} 大小异常，请将其移走后重试")

    request = Request(MODEL_URL)
    if current_size:
        request.add_header("Range", f"bytes={current_size}-")
        print(f"正在续传官方 YOLO11n ONNX 模型（{current_size:,}/{MODEL_SIZE:,} 字节）...")
        mode = "ab"
    else:
        print("正在下载官方 YOLO11n ONNX 模型...")
        mode = "wb"

    with urlopen(request) as response, OUTPUT_PATH.open(mode) as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)

    if OUTPUT_PATH.stat().st_size != MODEL_SIZE:
        raise RuntimeError("模型下载未完成；重新运行此脚本即可继续下载")
    print(f"已生成 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
