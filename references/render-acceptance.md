# 渲染与验收

## 预览

```bash
python3 build_composition.py
python3 <skill-dir>/scripts/validate_project.py .
npm run check
npx --yes hyperframes@0.8.30 render --fps 30 --quality standard --workers 2 --output renders/<name>-preview.mp4
```

把关键 beat 的进入、中间、稳定、退出帧做成联系表。确认顶部进度持续运动、转场没有前后文字重叠、截图完整、宇航员比例正常、字幕可读、点击声不盖人声。预览必须给用户确认。

## 最终输出

用户确认后优先尝试 HyperFrames 2160×3840/60fps 高质量渲染；先检查临时空间估算。若直渲需要的临时空间或内存不可接受，使用已验证的稳定路径：

1. 渲染 1080×1920 高质量母版。
2. 用 FFmpeg Lanczos 升级到 2160×3840，并封装为 60fps。
3. 明确该文件是高质量母版升级，不冒充原生 4K 动效捕帧。

```bash
ffmpeg -i renders/master.mp4 \
  -vf 'scale=2160:3840:flags=lanczos,fps=60,setsar=1' \
  -c:v libx264 -preset ultrafast -crf 16 -pix_fmt yuv420p -r 60 \
  -c:a copy -movflags +faststart renders/final-4k60.mp4
```

## 必查

- 配音替换后的字幕需听音校准，不能以布局检查、抽帧或按字数分配时间代替同步验收；保留供应商原始时间戳，记录估算和已核验边界。
- 已确认音色无需重复试听授权；视频预览与音色确认分别记录，沿用用户当前任务的明确授权，不因 Skill 切换新增确认步骤。

- ffprobe：2160×3840、60fps、AAC 48kHz 双声道、时长与倍速计算一致。
- `ffmpeg -v error -i final.mp4 -f null -` 无解码错误。
- 音频峰值不削波；点击 cue 与转场误差不超过约 0.1 秒。
- 开场、每个素材边界、章节切换、结尾的最终文件抽帧通过。
- 输出文件版本化，不能覆盖上一版。
