#!/usr/bin/env python3
import argparse
import html
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def parse_time(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def parse_srt(path: Path, speed: float):
    if not path.is_file():
        return []
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8").strip())
    captions = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        start, end = [part.strip() for part in lines[1].split("-->")]
        captions.append({
            "start": parse_time(start) / speed,
            "end": parse_time(end) / speed,
            "text": html.escape("".join(lines[2:])),
        })
    return captions


def stage_html(scene: dict) -> str:
    kind = scene["type"]
    if kind in {"product", "ai"}:
        label = "PRODUCT PROOF" if kind == "product" else "MOONLIT VISUAL"
        return (
            f'<div class="visual surface {kind}"><img src="{html.escape(scene["asset"])}" '
            f'alt="{label}"><div class="visual-label">{label}<i></i></div></div>'
        )
    if kind == "html":
        return f'<div class="custom-stage">{scene.get("html", "")}</div>'
    items = scene.get("items", [])
    rows = "".join(
        f'<div class="rail-row" data-step><b>{index:02d}</b><span>{html.escape(str(item))}</span></div>'
        for index, item in enumerate(items, 1)
    )
    return f'<div class="statement-stage surface"><div class="statement-core">{html.escape(scene.get("title", ""))}</div>{rows}</div>'


def scene_html(scene: dict, index: int, speed: float) -> str:
    return f'''<section id="scene-{index}" class="scene scene-{html.escape(scene["type"])}">
      <div class="scene-chapter">{html.escape(scene.get("chapter", ""))}</div>
      <div class="eyebrow">{html.escape(scene.get("eyebrow", ""))} / MOONLIT FIELD NOTE</div>
      <h1>{html.escape(scene.get("title", ""))}<br><em>{html.escape(scene.get("accent", ""))}</em></h1>
      <div class="stage">{stage_html(scene)}</div>
    </section>'''


def media_html(config: dict, speed: float, scenes: list[dict]) -> str:
    tag = str(speed).replace(".", "p")
    duration = float(config["original_duration"]) / speed
    parts = []
    if config.get("voiceover_file"):
        parts.append(
            f'<audio id="voiceover" src="assets/voiceover-speed-{tag}.mp3" data-start="0" '
            f'data-duration="{duration:.6f}" data-track-index="100" data-volume="1" preload="auto"></audio>'
        )
    click_volume = float(config.get("transition", {}).get("click_volume", 0.08))
    for index, scene in enumerate(scenes[1:], 1):
        cue = max(0, float(scene["start"]) / speed - 0.04)
        parts.append(
            f'<audio id="transition-click-{index}" src="assets/sfx/transition-click.wav" '
            f'data-start="{cue:.6f}" data-duration="0.199" data-track-index="{200 + index}" '
            f'data-volume="{click_volume:.3f}" preload="auto"></audio>'
        )
    return "\n".join(parts)


def build_html(config: dict, scenes: list[dict], chapters: list[dict], captions: list[dict]) -> str:
    speed = float(config["playback_speed"])
    duration = float(config["original_duration"]) / speed
    safe = config["top_progress_safe_box"]
    transition = config.get("transition", {})
    scene_data = [{"id": f"scene-{i + 1}", "start": s["start"] / speed, "end": s["end"] / speed, "type": s["type"]} for i, s in enumerate(scenes)]
    chapter_data = [{"start": c["start"] / speed, "end": c["end"] / speed, "label": c["label"]} for c in chapters]
    chapter_markup = "".join(
        f'<div class="macro-phase" id="macro-{i + 1}"><i class="macro-fill"></i><span>{html.escape(c["label"])}</span><b class="phase-pulse"></b></div>'
        for i, c in enumerate(chapters)
    )
    scene_markup = "\n".join(scene_html(scene, i + 1, speed) for i, scene in enumerate(scenes))
    total_label = f"{int(duration // 60):02d}:{int(duration % 60):02d}"
    replacements = {
        "__DURATION__": f"{duration:.6f}",
        "__TOTAL_LABEL__": total_label,
        "__SAFE_X__": str(safe["x"]), "__SAFE_Y__": str(safe["y"]),
        "__SAFE_W__": str(safe["width"]), "__SAFE_H__": str(safe["height"]),
        "__CHAPTER_COLUMNS__": str(len(chapters)),
        "__CHAPTERS_HTML__": chapter_markup,
        "__SCENES_HTML__": scene_markup,
        "__MEDIA_HTML__": media_html(config, speed, scenes),
        "__CAPTIONS_JSON__": json.dumps(captions, ensure_ascii=False),
        "__SCENES_JSON__": json.dumps(scene_data, ensure_ascii=False),
        "__CHAPTERS_JSON__": json.dumps(chapter_data, ensure_ascii=False),
        "__TRANSITION_OUT__": str(float(transition.get("out", 0.22))),
        "__TRANSITION_IN__": str(float(transition.get("in", 0.30))),
    }
    result = TEMPLATE
    for key, value in replacements.items():
        result = result.replace(key, value)
    if config.get("logic_resolution") == "1920x1080":
        result = result.replace('data-resolution="portrait"', 'data-resolution="landscape"').replace('data-width="1080" data-height="1920"', 'data-width="1920" data-height="1080"')
        css = """<style>html,body,#moonlit-video{width:1920px;height:1080px}.scene{padding:175px 72px 160px}.scene h1{width:1640px;font-size:62px}.eyebrow{margin-bottom:12px}.scene-chapter{top:130px}.clock{top:122px}.stage{top:365px;left:72px;right:72px;height:495px}.visual{height:495px}.statement-stage{padding:24px 48px}.statement-core{font-size:42px;margin-bottom:16px}.rail-row{height:90px}.caption-zone{bottom:35px;height:120px}.caption{max-width:1740px;font-size:34px}</style>"""
        result = result.replace('</head>',css+'</head>')
    return result


def run_media(config: dict, speed: float) -> None:
    source = str(config.get("voiceover_file", "")).strip()
    if not source:
        return
    source_path = ROOT / source
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("找不到 ffmpeg")
    tag = str(speed).replace(".", "p")
    output = ROOT / f"assets/voiceover-speed-{tag}.mp3"
    subprocess.run([
        ffmpeg, "-y", "-i", str(source_path), "-filter:a", f"atempo={speed}",
        "-ar", "48000", "-ac", "2", "-b:a", "192k", str(output),
    ], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-media", action="store_true")
    args = parser.parse_args()
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    scenes = json.loads((ROOT / "scenes.json").read_text(encoding="utf-8"))
    chapters = json.loads((ROOT / "chapters.json").read_text(encoding="utf-8"))
    speed = float(config["playback_speed"])
    if not 0.5 <= speed <= 2.0:
        raise ValueError("playback_speed 必须在 0.5 到 2.0 之间")
    if not args.skip_media:
        run_media(config, speed)
    captions = parse_srt(ROOT / config.get("srt_file", "captions.srt"), speed)
    if config.get("bilingual_captions_file"):
        bilingual = json.loads((ROOT / config["bilingual_captions_file"]).read_text(encoding="utf-8"))
        captions = [{"start": c["start"] / speed, "end": c["end"] / speed,
                     "text": '<div class="caption-zh">' + html.escape(c["zh"]) + '</div><div class="caption-en">' + html.escape(c["en"]) + '</div>'} for c in bilingual]
    (ROOT / "index.html").write_text(build_html(config, scenes, chapters, captions), encoding="utf-8")
    print(json.dumps({"duration": config["original_duration"] / speed, "scenes": len(scenes), "captions": len(captions)}, ensure_ascii=False))


TEMPLATE = r'''<!doctype html><html lang="zh-CN" data-resolution="portrait"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<script src="node_modules/gsap/dist/gsap.min.js"></script><style>
:root{--ink:#0e1a28;--paper:#f3f0e8;--muted:#8c99aa;--accent:#e0894f;--line:rgba(243,240,232,.16)}
*{box-sizing:border-box}html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:var(--ink);color:var(--paper);font-family:Inter,sans-serif}
#moonlit-video{position:relative;width:1080px;height:1920px;overflow:hidden;background:var(--ink)}
.scene{position:absolute;inset:0;padding:330px 72px 330px;visibility:hidden;opacity:0;background:radial-gradient(circle at 86% 12%,rgba(224,137,79,.10),transparent 30%),linear-gradient(180deg,#122135,#0e1a28);transform-origin:center}.scene:after{content:"";position:absolute;inset:0;opacity:.18;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:72px 72px}.scene>*{position:relative;z-index:2}
.macro-progress{position:absolute;left:__SAFE_X__px;top:__SAFE_Y__px;width:__SAFE_W__px;height:__SAFE_H__px;z-index:150;display:grid;grid-template-columns:repeat(__CHAPTER_COLUMNS__,1fr);gap:3px;padding:5px;border:1px solid var(--line);border-radius:18px;background:#13223a}.macro-phase{position:relative;display:grid;place-items:center;overflow:hidden;background:#182a40;color:#c9cfd8}.macro-phase span{position:relative;z-index:3;font-size:20px;font-weight:760;white-space:nowrap}.macro-fill{position:absolute;inset:0;z-index:1;background:linear-gradient(90deg,#7a3f22,#9b4f2c 72%,#b8653a);transform-origin:left}.phase-pulse{position:absolute;left:50%;bottom:6px;z-index:4;width:8px;height:8px;border:1px solid #fff;border-radius:50%;opacity:0}.clock{position:absolute;right:62px;top:187px;z-index:151;color:var(--muted);font:17px monospace}.clock strong{color:var(--paper)}
.scene-chapter{position:absolute;top:255px;right:72px;color:var(--accent);font:19px monospace}.eyebrow{color:var(--muted);font:21px monospace;margin-bottom:25px}.scene h1{margin:0;width:920px;font-size:70px;line-height:1.08;letter-spacing:-.045em}.scene h1 em{color:var(--accent);font-style:normal}.stage{position:absolute;left:72px;right:72px;top:690px;height:665px}.surface{border:1px solid var(--line);border-radius:30px;background:#16263a;overflow:hidden;box-shadow:0 42px 100px rgba(0,0,0,.42)}
.visual{position:relative;height:624px;background:#0b1622}.visual img{display:block;width:100%;height:100%;object-fit:contain}.visual-label{position:absolute;left:28px;right:28px;bottom:24px;display:flex;justify-content:space-between;font:16px monospace}.visual-label i{width:98px;height:3px;background:var(--accent)}
.statement-stage{height:100%;padding:54px}.statement-core{font-size:48px;font-weight:820;margin-bottom:42px}.rail-row{height:112px;display:grid;grid-template-columns:90px 1fr;align-items:center;border-top:1px solid var(--line);visibility:hidden}.rail-row b{color:var(--accent);font:20px monospace}.rail-row span{font-size:30px}.custom-stage{height:100%}
.caption-zone{position:absolute;left:64px;right:64px;bottom:128px;height:180px;z-index:180;display:grid;place-items:center}.caption{position:absolute;max-width:930px;padding:21px 30px;border:1px solid var(--line);border-radius:18px;background:rgba(10,20,32,.94);font-size:38px;font-weight:650;line-height:1.36;text-align:center;visibility:hidden;opacity:0}
</style><style>.caption-en{font-size:.65em;line-height:1.35;color:#8c99aa;margin-top:8px}.caption-zh{line-height:1.3}</style></head><body><main id="moonlit-video" data-composition-id="moonlit-video" data-width="1080" data-height="1920" data-start="0" data-duration="__DURATION__" data-fps="30">
<div class="macro-progress">__CHAPTERS_HTML__</div><div class="clock"><strong id="time-now">00:00</strong> / __TOTAL_LABEL__</div>
__SCENES_HTML__<div class="caption-zone" id="caption-zone"></div><script>(function(){
const DURATION=__DURATION__,OUT=__TRANSITION_OUT__,IN=__TRANSITION_IN__,CAPTIONS=__CAPTIONS_JSON__,SCENES=__SCENES_JSON__,CHAPTERS=__CHAPTERS_JSON__;
const zone=document.getElementById('caption-zone');CAPTIONS.forEach((c,i)=>{const n=document.createElement('div');n.id=`cap-${i}`;n.className='caption';n.innerHTML=c.text;zone.appendChild(n)});
const tl=gsap.timeline({paused:true});gsap.set('.scene',{autoAlpha:0,scale:1});gsap.set('.macro-fill',{scaleX:0});
CHAPTERS.forEach((c,i)=>{const phase=`#macro-${i+1}`;tl.to(`${phase} .macro-fill`,{scaleX:1,duration:c.end-c.start,ease:'none'},c.start);tl.fromTo(`${phase} .phase-pulse`,{autoAlpha:1,scale:.55},{autoAlpha:0,scale:3,duration:.38},c.start)});
const clock={v:0};tl.to(clock,{v:DURATION,duration:DURATION,ease:'none',onUpdate:()=>{const s=Math.floor(clock.v);document.getElementById('time-now').textContent=`${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`}},0);
CAPTIONS.forEach((c,i)=>{tl.set(`#cap-${i}`,{autoAlpha:1},c.start);tl.set(`#cap-${i}`,{autoAlpha:0},c.end)});
tl.set('#scene-1',{autoAlpha:1},0);SCENES.forEach((s,i)=>{const at=s.start,sel=`#${s.id}`;if(i>0){const prev=`#${SCENES[i-1].id}`,handoff=Math.max(0,at-OUT);tl.set(sel,{autoAlpha:0,scale:1.01,filter:'brightness(.82)'},handoff);tl.to(prev,{autoAlpha:0,scale:.994,filter:'brightness(.74)',duration:OUT,ease:'power2.in'},handoff);tl.set(prev,{autoAlpha:0,scale:1,filter:'brightness(1)'},at);tl.to(sel,{autoAlpha:1,scale:1,filter:'brightness(1)',duration:IN,ease:'power3.out'},at)}
tl.from(`${sel} h1`,{y:42,duration:.48,ease:'power4.out'},at+.05);tl.from(`${sel} .stage`,{y:48,duration:.52,ease:'power4.out'},at+.16);document.getElementById(s.id).querySelectorAll('[data-step]').forEach((el,j)=>{tl.set(el,{visibility:'visible'},at+.55+j*.55);tl.from(el,{y:18,duration:.28},at+.55+j*.55)})});
window.__timelines=window.__timelines||{};window.__timelines['moonlit-video']=tl;})();</script></main>
__MEDIA_HTML__</body></html>'''


if __name__ == "__main__":
    main()
