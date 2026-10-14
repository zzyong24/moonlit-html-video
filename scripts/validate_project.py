#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"无法读取 {path.name}: {exc}")
        return None


def check_contiguous(items, duration: float, label: str, errors: list[str]) -> None:
    if not items:
        errors.append(f"{label}为空")
        return
    if abs(float(items[0]["start"])) > 0.02 or abs(float(items[-1]["end"]) - duration) > 0.02:
        errors.append(f"{label}时间必须从 0 覆盖到 original_duration")
    for left, right in zip(items, items[1:]):
        if abs(float(left["end"]) - float(right["start"])) > 0.02:
            errors.append(f"{label}时间存在空洞或重叠: {left['end']} → {right['start']}")


def validate_project(project: Path) -> list[str]:
    project = project.expanduser().resolve()
    errors: list[str] = []
    config = load_json(project / "config.json", errors)
    scenes = load_json(project / "scenes.json", errors)
    chapters = load_json(project / "chapters.json", errors)
    if config is None or scenes is None or chapters is None:
        return errors

    if config.get("production_mode") != "html_explainer":
        errors.append("production_mode 必须是 html_explainer")
    speed = float(config.get("playback_speed", 0))
    duration = float(config.get("original_duration", 0))
    if not 0.5 <= speed <= 2.0:
        errors.append("playback_speed 必须在 0.5 到 2.0 之间")
    if duration <= 0:
        errors.append("original_duration 必须大于 0")
    check_contiguous(chapters, duration, "章节时间", errors)
    check_contiguous(scenes, duration, "场景时间", errors)

    for scene in scenes:
        if scene.get("type") not in {"statement", "list", "product", "ai", "html"}:
            errors.append(f"未知场景类型: {scene.get('type')}")
        asset = str(scene.get("asset", "")).strip()
        if scene.get("type") in {"product", "ai"}:
            if not asset or not (project / asset).is_file():
                errors.append(f"素材不存在: {asset or '[空路径]'}")
        if scene.get("type") == "ai":
            ref = str(config.get("ip_reference", "")).strip()
            if not ref or not (project / ref).is_file():
                errors.append("AI 场景必须配置存在的 ip_reference，禁止无参考图生成品牌 IP")

    safe = config.get("top_progress_safe_box", {})
    try:
        x, y = float(safe["x"]), float(safe["y"])
        width, height = float(safe["width"]), float(safe["height"])
        canvas_w, canvas_h = map(int, config.get("logic_resolution", "1080x1920").split("x"))
        if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > canvas_w or y + height > canvas_h:
            errors.append("top_progress_safe_box 必须位于配置的逻辑画布内")
    except Exception:
        errors.append("top_progress_safe_box 缺少 x/y/width/height")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="验证月明 HTML 视频项目（默认 16:9）")
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    errors = validate_project(args.project)
    if errors:
        for item in errors:
            print(f"ERROR: {item}")
        raise SystemExit(1)
    print("OK: project contract passed")


if __name__ == "__main__":
    main()
