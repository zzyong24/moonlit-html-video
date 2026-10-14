# 项目合同

## 目录

```text
project/
├── config.json
├── scenes.json
├── chapters.json
├── captions.srt
├── build_composition.py
├── motion_direction.md
├── timeline_notes.md
├── project_manifest.md
├── assets/{source,product,ai-broll,reference,sfx}/
├── renders/
└── checks/
```

## config.json

- `production_mode`: 固定为 `html_explainer`；缺失或为其他值时停止，不能把不同视频类型塞入本工程。
- `playback_speed`: 0.5–2.0，唯一倍速来源。
- `original_duration`: 原始配音的 ffprobe 时长。
- `voiceover_file`: 项目相对路径；空值仅用于脚手架演示。
- `voice_provider`: 默认 `MiniMax`；用户选择其他供应商时显式修改。
- `voice_type`: 必须填写使用者本人已授权、当前 MiniMax 账号可用的音色 ID；占位符不能直接调用。
- `voice_model`: 默认 `speech-2.8-hd`。
- `resource_id`: 仅豆包适配器使用，值为 `seed-tts-2.0`；不作为 MiniMax 参数。
- 密钥：MiniMax 从 `MINIMAX_API_KEY` 读取，豆包从 `VOLC_API_KEY` 读取；不得进入配置、Skill、日志、作品或 Git。macOS 登录会话环境需显式传入子进程，不输出变量值。
- `subtitle_timing`: `pending`、`provider_segments`、`estimated` 或 `verified`；按字数细分的时间戳只能标为 `estimated`，校准后才设为 `verified`。
- `srt_file`: SRT 相对路径。
- `ip_reference`: 使用 `type=ai` 时必填且文件必须存在。
- `top_progress_safe_box`: 逻辑画布中的 `x/y/width/height`（16:9 默认 1920×1080；竖版 1080×1920）。
- `transition.out/in/click_volume`: 转场和点击参数。

## scenes.json

所有时间使用原始 1.0 倍秒数，必须从 0 连续覆盖到 `original_duration`。

```json
{
  "start": 12.3,
  "end": 20.8,
  "chapter": "产品证据",
  "eyebrow": "PRODUCT",
  "title": "界面证明什么",
  "accent": "只保留一个结论",
  "type": "product",
  "asset": "assets/product/example.png",
  "items": []
}
```

类型：`statement`、`list`、`product`、`ai`、`html`。`product` 和 `ai` 必须有真实存在的 `asset`；`html` 的内容由编导针对该句设计，不能复用通用卡片阵列。

## chapters.json

章节必须从 0 连续覆盖到 `original_duration`。章节条按章节各自时长推进，不按场景数量均分时间。

## 时间换算

```text
render_time = source_time / playback_speed
render_duration = source_duration / playback_speed
```

禁止单独改语音、字幕、场景、章节或 SFX 中任意一项。

## 发布交接合同

用户确认成片后，另存发布交接清单，不在渲染工程里直接操作平台。至少包含：

```json
{
  "productionMode": "html_explainer",
  "videoPath": "/abs/final.mp4",
  "title": "",
  "description": "",
  "topics": [],
  "originalConfirmed": false,
  "cover3x4": "/abs/cover-3x4.png",
  "cover4x3": "/abs/cover-4x3.png"
}
```

视频、标题、简介或封面发生修改时生成新版本，并让下游发布包重新计算指纹。

双语字幕：`bilingual_captions_file` 指向 [{start,end,zh,en}]，时间为原速秒数，与原 SRT 对应。正文由编导翻译并复核；渲染器不猜翻译。新工程默认双语，历史工程缺该字段时兼容原字幕。
