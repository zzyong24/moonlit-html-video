---
name: moonlit-html-video
description: Use when a 月明水清深 project needs a 16:9 (default) pure-HTML, GSAP, or HyperFrames explainer video and the request involves voiceover/SRT timing, adjustable speed, product screenshots, optional astronaut IP visuals, Douyin-safe chapter progress, transition sound, preview iteration, or 4K/60fps delivery.
metadata:
  version: "1.2.0"
  production_mode: "html_explainer"
  updated: "2026-10-14"
---

# 月明纯 AI 信息演示视频

本 Skill 只负责 `production_mode=html_explainer`：纯 AI 编排的 HTML/GSAP/HyperFrames 信息演示，默认 16:9 横版。它可以嵌入真实截图、录屏和少量 AI 场景图，但不负责真人口播 + Remotion B-roll；后者必须使用独立制作 Skill。

## 核心原则

主音频是唯一时钟；每个 beat 只有一个视觉主语；产品机制用真实截图证明，抽象概念优先用本期母意象的 HTML 状态变化，用户本期指定时才用月明宇航员场景图；用户确认预览后才渲染整片 4K/60fps。

实际制作或改片时，使用 `video-editing`。解释机制的配图使用 `moonlit-material-illustration`，品牌场景生成使用 `imagegen`。AI 旁白默认使用 MiniMax 已确认真人复刻音色；生成或更换配音前读取 [voiceover.md](references/voiceover.md)。用户明确选择豆包时才使用 `doubao-tts-voiceover` 与旧 V3 适配器。

## 工作流

盘素材、编排和预览迭代时，按当前激活名称解析 moonlit-talking-head-video 的 references/material-editing-iteration.md，补强现有资产/镜头记录与评审；资源缺失时明确报告并沿用本模式合同。只借素材、运动与迭代方法，不引入人物生成、SeeCut 工作流、剪映交接或强制视频模型评委。

1. Probe 配音、SRT、截图和录屏，记录真实时长、尺寸、帧率与音轨。已授权制作 AI 视频时，生成配音并获取供应商字幕属于制作步骤；优先复用已经确认的音色。配置默认 `voice_provider=MiniMax`、`voice_type=YOUR_AUTHORIZED_VOICE_ID`、`voice_model=speech-2.8-hd`。密钥只从环境变量读取。
2. 从本 Skill 目录创建版本化工程：

   ```bash
   python3 <skill-dir>/scripts/bootstrap_project.py <project-name> --output <dir> --speed 1.0 --aspect 16:9
   ```

3. 依据原始 1.0 倍时间填写 `scenes.json`、`chapters.json`、`motion_direction.md` 和 `timeline_notes.md`。详细顺序见 [workflow.md](references/workflow.md)。
4. 按 [visual-system.md](references/visual-system.md) 选择 HTML 动效、产品截图或 AI 分镜。品牌宇航员没有参考图时暂停生成并索取参考；禁止凭文字猜 IP。
5. Moonlit Creator 中依赖按 maintenance/WORKFLOW.md 管理：package 与锁文件留在工程，安装放工作区外。已有锁文件时从工作区根目录执行 `python3 scripts/moonlit.py deps-prepare <工程目录>`，再进入工程构建；不在共享 node_modules 上运行 npm install。其他工作区按其依赖约定执行。

   ```bash
   python3 build_composition.py
   python3 <skill-dir>/scripts/validate_project.py .
   npm run check
   ```

6. 先渲染 1920×1080/30fps 预览，抽查所有转场边界、章节切换、产品截图和 AI 图。把预览交给用户确认；任何视觉或同步改动都重新走预览门。
7. 用户确认后按 [render-acceptance.md](references/render-acceptance.md) 输出新版本 3840×2160/60fps，并验证解码、时长、音轨和关键帧。
8. 成片确认后调用 `moonlit-video-cover`，以本人固定身份原图和本期具体业务证据制作并确认 3:4、4:3、16:9 三画幅封面；再生成发布交接字段：最终视频绝对路径、标题、简介、关键词/话题、原创状态和封面绝对路径。只交给 `moonlit-video-publisher`，本 Skill 不打开或操作创作者平台。

## 不可破坏的合同

- `playback_speed` 是唯一倍速来源；音频用 `atempo` 保持音高，字幕、场景、章节和 SFX 时间统一除以倍速。
- 产品截图和录屏永远 `contain`，不裁切、不拉伸；UI 必须达到移动端可读尺寸。
- 顶部章节条默认使用 v11 验证过的安全框，但它不是平台官方固定值；每个项目按当前抖音 UI 和参考截图复核。
- 同章内用同一舞台上的变形承接，只有换章才降亮淡出再柔和显现（见 visual-system 的“转场与声音”）；不用绿色/白色全屏刷新，不用贯穿文字的扫描线。
- 点击声默认 `data-volume=0.08`，每个 cue 独立音轨；impact 只给满屏大字（每 30–60 秒最多 1 次），任何音效不能盖住人声。
- AI 场景图不含文字；使用月明宇航员时必须是清晰人形宇航员，禁止虫形、长条躯干、额外肢体。
- 不覆盖历史输出。预览、母版、最终成片和验收帧都要带版本号。
- 工程和交接包必须显式记录 `production_mode=html_explainer`，防止后续把真人口播等不同类型误用本模板。

配置与数据字段见 [project-contract.md](references/project-contract.md)。常见误区及基线回归见 [baseline-tests.md](references/baseline-tests.md)。

用户指定竖版时使用 --aspect 9:16；旧工程保持原画幅，不自动改写历史工程。横版重新排布 stage 与字幕，不把竖屏整体缩进横屏。

横版共用视觉规范（2026-09-09 用户确认）：中文主字幕 + 较小英文辅助行，两者沿用同一 SRT 时间窗；顶部显示带章节名的进度条。数字人分支仅按实际出镜窗及衔接余量生成口型，详见 moonlit-avatar-video。

用户需要手动翻页、截图拖动和现场录屏的 HTML PPT 时，按当前激活名称路由 `moonlit-ppt-html`（`html_presentation`）；这类请求以 HTML 与讲解稿完成。此处仍只负责由音频/SRT 驱动的 `html_explainer` 成片。
