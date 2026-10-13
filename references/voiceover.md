# 月明真人复刻旁白

## 当前默认值

- 供应商：MiniMax 中国站；音色：`YOUR_AUTHORIZED_VOICE_ID`；模型：`speech-2.8-hd`。
- 2026-09-09 用户已试听确认音色。后续同一音色直接复用，不重复创建、收费或要求重复试听；变更音色或样本时再做短试听。
- 此音色属于创建它的账号；换账号时先查询音色是否可用。鉴权失败或音色不存在时报告原因，不自动重建音色。
- 密钥只读取 `MINIMAX_API_KEY`。本机曾通过 `launchctl setenv` 配置，登录会话结束后可能失效；Skill 不保存密钥。Token Plan Key 与普通按量 Key 分开，复刻使用普通按量账号。价格与套餐以当前官方文档为准。

## 生成与替换

1. 从当前作品 `content/video/` 读取已确认旁白。标题、署名、分镜注释不朗读；保留正文中的英文术语，不机械删掉下划线等有效字符。
2. 使用 `POST https://api.minimax.cn/v1/t2a_v2`，Bearer 环境密钥，`stream=false`、`subtitle_enable=true`，`voice_setting` 指定上述音色、`speed=1`、`vol=1`、`pitch=0`；`audio_setting` 使用 MP3、32000 Hz、128000 bitrate、单声道。以项目显式设置优先。
3. 同时检查 HTTP 状态和 `base_resp.status_code`。将 `data.audio` 从 hex 解码成 MP3，立即下载 `data.subtitle_file` 到当前作品 `production/` 的版本化音频目录。签名下载 URL 不写入日志和清单。保存模型、音色、输入哈希、计费字符数与文件路径。
4. 保留供应商原始字幕 JSON。`time_begin/time_end` 单位为毫秒，实际可能是一整段而非一句。转换 SRT 时先保留原边界；长段可换行。需要细分到短字幕时，通过听音或对齐工具校准；按字数比例拆分属于估算，不能作为精确口型或逐词动画时间源。
5. 换配音后根据新音轨与字幕重排场景、章节、转场和音效；不要整体按时长比例缩放旧时间轴。同步更新 `config.json`、`work.json`、项目说明和脚本实际时长，保留旧版音频与预览。
6. 校验字幕内容覆盖、时间单调、末尾不超音频；听查英文术语、数字、句内拆分、首尾和转场，抽帧只能验证画面。明确区分“结构检查通过”和“音画同步听查通过”。

## 首次复刻或更换样本

用户授权后，上传其本人或已获授权的纯人声样本（10 秒至 5 分钟，MP3/M4A/WAV，20MB 内），`purpose=voice_clone`，再调用 `/v1/voice_clone`。优先使用干净真人录音；需要时降噪和归一化，不能用旧 TTS 通用男声作为真人样本。先试听再采用；已确认音色无需重复此流程。

官方文档：[快速复刻](https://platform.minimaxi.com/docs/api-reference/voice-cloning-clone)、[语音合成](https://platform.minimaxi.com/docs/api-reference/speech-t2a-http)、[计费](https://platform.minimaxi.com/docs/guides/pricing-paygo)。
