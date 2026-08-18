# Edge Vision: 从笔记本到树莓派

这个项目在摄像头画面中实时检测人车，显示 FPS，并统计矩形区域内的目标数量。
推理过程只依赖 `ONNX Runtime + OpenCV`，因此 Windows 验证完成后可以直接迁移到 Raspberry Pi OS。

## 第一阶段：Windows 笔记本

在 PowerShell 中执行：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-desktop.txt
python scripts/download_model.py
python -m src.main --source 0 --region 120,80,520,420
```

`--source 0` 是默认摄像头。摄像头不是编号 0 时，依次尝试 `1` 或 `2`。也可将其替换为视频路径或 RTSP 地址。

窗口中绿色框代表其中心点位于区域内。按 `q` 或 `Esc` 退出。

## 可验证结果

- 窗口能显示摄像头画面与检测框；
- 画面左上角有实时 FPS；
- 调整 `--region x1,y1,x2,y2` 后，`in region` 数字随目标进入或离开矩形而变化；
- `python -m unittest discover -s tests` 通过。

## 第二阶段：迁移到树莓派

建议 Raspberry Pi 5 + 64-bit Raspberry Pi OS。复制整个项目目录，但不要复制 `.venv`。
CSI 摄像头使用 Raspberry Pi OS 的 Picamera2/libcamera 链路。

```bash
sudo apt update
sudo apt install -y python3-venv python3-opencv python3-picamera2 libatlas-base-dev
rpicam-hello --timeout 3000
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-pi.txt
python -m src.main --camera-backend picamera2 --camera-width 640 --camera-height 480 --model models/yolo11n.onnx --region 120,80,520,420
```

`rpicam-hello` 可先验证 CSI 排线、摄像头和系统驱动；较旧系统可使用 `libcamera-hello`。必须在树莓派的本地桌面或已配置图形显示的会话中运行，因为程序会创建 OpenCV 窗口。

性能不足时，先将 CSI 输出降低到 `--camera-width 640 --camera-height 480`，然后再考虑将模型输入尺寸改为 `imgsz=416` 并重新导出；下一步再做 INT8 量化。程序没有使用 Windows 专属接口。

## 结构

```text
scripts/export_yolo.py   # 将 YOLO 权重导出到 ONNX，仅在模型构建时需要 Ultralytics
scripts/download_model.py # 下载可直接部署的官方 ONNX 模型，支持断点续传
src/detector.py         # 预处理、ONNX Runtime 推理、NMS 和坐标还原
src/camera.py           # OpenCV 与 Raspberry Pi CSI/Picamera2 采集后端
src/main.py             # 视频流、检测绘制、区域计数与 FPS
tests/                  # 无摄像头也能运行的基础测试
```

## 常见问题

- PowerShell 阻止激活脚本时，在当前终端执行：`Set-ExecutionPolicy -Scope Process Bypass`。
- 导出模型后首次在树莓派运行前，确认 `models/yolo11n.onnx` 已随项目一并复制。
- CSI 摄像头无法打开时，先执行 `rpicam-hello --timeout 3000` 验证硬件与系统；程序启动时使用 `--camera-backend picamera2`。

## 自训模型（可选）

默认模型已经是可部署的 ONNX 文件，无需安装训练框架。之后你训练或替换模型时，再执行：

```powershell
pip install -r requirements-export.txt
python scripts/export_yolo.py
```
