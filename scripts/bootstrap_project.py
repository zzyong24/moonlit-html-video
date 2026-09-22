#!/usr/bin/env python3
import argparse
import json
import shutil
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_project(output: Path, name: str, speed: float, aspect: str = "16:9") -> Path:
    if not 0.5 <= speed <= 2.0:
        raise ValueError("playback_speed 必须在 0.5 到 2.0 之间")
    project = output.expanduser().resolve() / name
    project.mkdir(parents=True, exist_ok=False)
    for relative in (
        "assets/product", "assets/ai-broll", "assets/reference", "assets/sfx",
        "assets/source", "renders", "checks",
    ):
        (project / relative).mkdir(parents=True, exist_ok=True)

    config = {
        "project_name": name,
        "production_mode": "html_explainer",
        "playback_speed": speed,
        "original_duration": 12.0,
        "voiceover_file": "",
        "voice_provider": "MiniMax",
        "voice_type": "",
        "voice_model": "speech-2.8-hd",
        "subtitle_timing": "pending",
        "srt_file": "captions.srt",
        "bilingual_captions_file": "captions-bilingual.json",
        "ip_reference": "",
        "logic_resolution": "1080x1920",
        "preview": {"resolution": "1080x1920", "fps": 30},
        "final": {"resolution": "2160x3840", "fps": 60},
        "top_progress_safe_box": {"x": 54, "y": 88, "width": 972, "height": 92},
        "transition": {"out": 0.22, "in": 0.30, "click_volume": 0.08},
    }
    if aspect == "16:9":
        config.update({"aspect_ratio":"16:9", "logic_resolution":"1920x1080", "preview":{"resolution":"1920x1080","fps":30}, "final":{"resolution":"3840x2160","fps":60}, "top_progress_safe_box":{"x":64,"y":40,"width":1792,"height":64}})
    else:
        config["aspect_ratio"] = "9:16"
    scenes = [
        {"start": 0.0, "end": 6.0, "chapter": "问题", "eyebrow": "WHY",
         "title": "先把问题讲清楚", "accent": "观众才能留下来", "type": "statement",
         "items": ["痛点", "缺口", "代价"], "asset": ""},
        {"start": 6.0, "end": 12.0, "chapter": "答案", "eyebrow": "PROOF",
         "title": "用证据回答", "accent": "再进入结论", "type": "statement",
         "items": ["机制", "证据", "结论"], "asset": ""},
    ]
    chapters = [
        {"start": 0.0, "end": 6.0, "label": "问题"},
        {"start": 6.0, "end": 12.0, "label": "答案"},
    ]
    write_json(project / "config.json", config)
    write_json(project / "captions-bilingual.json", [
        {"start":0,"end":6,"zh":"先把问题讲清楚。","en":"Start by making the problem clear."},
        {"start":6,"end":12,"zh":"用证据回答，再进入结论。","en":"Answer with evidence, then draw the conclusion."},
    ])
    write_json(project / "scenes.json", scenes)
    write_json(project / "chapters.json", chapters)
    write_json(project / "hyperframes.json", {
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
        "media": {"autoProxy": True},
    })
    write_json(project / "package.json", {
        "name": name.lower().replace(" ", "-"), "private": True, "type": "module",
        "scripts": {
            "dev": "npx --yes hyperframes@0.8.30 preview",
            "check": "npx --yes hyperframes@0.8.30 check",
            "render": "npx --yes hyperframes@0.8.30 render",
        },
        "dependencies": {"gsap": "3.14.2"},
    })
    (project / "captions.srt").write_text(
        "1\n00:00:00,000 --> 00:00:06,000\n先把问题讲清楚。\n\n"
        "2\n00:00:06,000 --> 00:00:12,000\n用证据回答，再进入结论。\n",
        encoding="utf-8",
    )
    (project / "motion_direction.md").write_text(
        "# Motion Direction\n\n- Motion thesis：待填写。\n- 连续舞台：待填写。\n- Beat graph：待填写。\n",
        encoding="utf-8",
    )
    (project / "timeline_notes.md").write_text(
        "# Timeline Notes\n\n时间均使用原始 1.0 倍时间；生成器统一按 playback_speed 换算。\n",
        encoding="utf-8",
    )
    (project / "project_manifest.md").write_text(
        f"# Project Manifest\n\n- 项目：{name}\n- production_mode：html_explainer\n- 当前倍速：{speed}\n- 状态：脚手架已创建，等待替换示例输入。\n",
        encoding="utf-8",
    )
    shutil.copy2(SKILL_ROOT / "assets/starter/build_composition.py", project / "build_composition.py")
    shutil.copy2(SKILL_ROOT / "assets/transition-click.wav", project / "assets/sfx/transition-click.wav")
    return project


def main() -> None:
    parser = argparse.ArgumentParser(description="创建月明横版优先 HTML 视频项目")
    parser.add_argument("name")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--aspect", choices=["16:9", "9:16"], default="16:9")
    args = parser.parse_args()
    print(create_project(args.output, args.name, args.speed, args.aspect))


if __name__ == "__main__":
    main()
