from __future__ import annotations


def point_in_rectangle(point: tuple[int, int], rectangle: tuple[int, int, int, int]) -> bool:
    """Return whether a pixel point is inside an inclusive x1,y1,x2,y2 rectangle."""
    x, y = point
    x1, y1, x2, y2 = rectangle
    return x1 <= x <= x2 and y1 <= y <= y2


def parse_rectangle(value: str | None) -> tuple[int, int, int, int] | None:
    if value is None:
        return None

    try:
        coordinates = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as error:
        raise ValueError("区域必须为 x1,y1,x2,y2，例如 120,80,520,420") from error

    if len(coordinates) != 4:
        raise ValueError("区域必须包含 4 个整数：x1,y1,x2,y2")

    x1, y1, x2, y2 = coordinates
    if x2 <= x1 or y2 <= y1:
        raise ValueError("区域右下角必须位于左上角的右下方")
    return coordinates
