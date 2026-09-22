#!/usr/bin/env python3
"""Generate a Volcengine Seed-TTS V3 voiceover and timing SRT.

The API key is read only from VOLC_API_KEY. It is never accepted as a command
line argument or written to the output manifest.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


DEFAULT_ENDPOINT = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
DEFAULT_VOICE = "zh_male_liufei_uranus_bigtts"
DEFAULT_RESOURCE_ID = "seed-tts-2.0"
DEFAULT_MODEL = "seed-tts-2.0-standard"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="UTF-8 Markdown or plain-text voiceover")
    parser.add_argument("--output", required=True, type=Path, help="Final MP3 path")
    parser.add_argument("--srt", required=True, type=Path, help="Generated SRT path")
    parser.add_argument("--voice-type", default=DEFAULT_VOICE)
    parser.add_argument("--resource-id", default=DEFAULT_RESOURCE_ID)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--sample-rate", type=int, default=24000)
    parser.add_argument("--max-chars", type=int, default=180)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def clean_script(markdown: str) -> str:
    lines: list[str] = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line or line.startswith("<!--"):
            continue
        if line.startswith("#"):
            continue
        if re.fullmatch(r"[-—]+\s*月明水清深", line):
            continue
        line = re.sub(r"[*_`]+", "", line)
        line = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", line)
        if line:
            lines.append(line)
    return "\n".join(lines)


def split_segments(text: str, max_chars: int) -> list[str]:
    pieces = re.split(r"(?<=[。！？!?；;])\s*|\n+", text)
    segments: list[str] = []
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        while len(piece) > max_chars:
            cut = max(piece.rfind(mark, 0, max_chars + 1) for mark in "，、：,")
            if cut < max_chars // 2:
                cut = max_chars
            else:
                cut += 1
            segments.append(piece[:cut].strip())
            piece = piece[cut:].strip()
        if piece:
            segments.append(piece)
    return segments


def request_audio(
    *, text: str, api_key: str, endpoint: str, voice: str,
    resource_id: str, model: str, speed: float, sample_rate: int,
) -> bytes:
    payload = {
        "user": {"uid": "moonlit-html-video"},
        "req_params": {
            "text": text,
            "speaker": voice,
            "model": model,
            "audio_params": {
                "format": "mp3",
                "sample_rate": sample_rate,
                "speed_ratio": speed,
            },
            "additions": json.dumps(
                {
                    "disable_markdown_filter": True,
                    "enable_language_detector": True,
                    "enable_latex_tn": True,
                    "disable_default_bit_rate": True,
                    "max_length_to_filter_parenthesis": 0,
                },
                ensure_ascii=False,
            ),
        },
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
            "X-Api-Resource-Id": resource_id,
            "X-Api-Request-Id": str(uuid.uuid4()),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"TTS HTTP {error.code}: {detail}") from error

    chunks: list[bytes] = []
    last_error = ""
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("data:"):
            line = line[5:].strip()
        frame = json.loads(line)
        header = frame.get("header") or {}
        code = frame.get("code", header.get("code"))
        if code not in (0, 20000000, None):
            last_error = frame.get("message") or header.get("message") or str(code)
        if frame.get("data"):
            chunks.append(base64.b64decode(frame["data"]))
    audio = b"".join(chunks)
    if not audio:
        raise RuntimeError(f"TTS returned no audio: {last_error or 'unknown response'}")
    return audio


def duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def srt_time(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def main() -> int:
    args = parse_args()
    api_key = os.environ.get("VOLC_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("VOLC_API_KEY is not set")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")
    for target in (args.output, args.srt, args.output.with_suffix(".json")):
        if target.exists() and not args.force:
            raise SystemExit(f"Refusing to overwrite existing file: {target}")

    source = args.input.read_text(encoding="utf-8")
    spoken = clean_script(source)
    segments = split_segments(spoken, args.max_chars)
    if not segments:
        raise SystemExit("No speakable text found")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.srt.parent.mkdir(parents=True, exist_ok=True)
    segment_durations: list[float] = []

    with tempfile.TemporaryDirectory(prefix="moonlit-tts-") as temp_name:
        temp_dir = Path(temp_name)
        chunk_paths: list[Path] = []
        for index, segment in enumerate(segments, start=1):
            audio = None
            for attempt in range(3):
                try:
                    audio = request_audio(
                        text=segment,
                        api_key=api_key,
                        endpoint=args.endpoint,
                        voice=args.voice_type,
                        resource_id=args.resource_id,
                        model=args.model,
                        speed=args.speed,
                        sample_rate=args.sample_rate,
                    )
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(1.5 * (attempt + 1))
            chunk = temp_dir / f"{index:03d}.mp3"
            chunk.write_bytes(audio or b"")
            chunk_paths.append(chunk)
            segment_durations.append(duration(chunk))
            print(f"[{index}/{len(segments)}] {segment[:36]}")

        concat_file = temp_dir / "concat.txt"
        concat_file.write_text(
            "".join(f"file '{path.as_posix()}'\n" for path in chunk_paths),
            encoding="utf-8",
        )
        temp_output = temp_dir / "voiceover.mp3"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-c:a", "libmp3lame", "-b:a", "128k", str(temp_output),
            ],
            check=True,
        )
        shutil.copy2(temp_output, args.output)

    cursor = 0.0
    blocks: list[str] = []
    for index, (segment, seconds) in enumerate(zip(segments, segment_durations), start=1):
        start = cursor
        cursor += seconds
        blocks.append(f"{index}\n{srt_time(start)} --> {srt_time(cursor)}\n{segment}\n")
    args.srt.write_text("\n".join(blocks), encoding="utf-8")

    final_duration = duration(args.output)
    manifest = {
        "source": str(args.input.resolve()),
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "voice_type": args.voice_type,
        "resource_id": args.resource_id,
        "model": args.model,
        "speed": args.speed,
        "sample_rate": args.sample_rate,
        "segment_count": len(segments),
        "duration_seconds": round(final_duration, 3),
        "audio": str(args.output.resolve()),
        "srt": str(args.srt.resolve()),
    }
    args.output.with_suffix(".json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
