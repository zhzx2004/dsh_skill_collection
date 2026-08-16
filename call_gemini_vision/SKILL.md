---
name: call-gemini-vision
description: 任务遇到本地图片(.png/.jpg/.jpeg)或 PDF 文件、DSH 不擅长读图时，通过本地 antigravity 网关调用 gemini-3.5-flash 做视觉解析，返回提取出的纯文本（全部文字、公式、报错信息、图表数据）供主 Agent 继续处理。
whenToUse: 需要读取本地图片或 PDF 中的内容（文字、公式、报错信息、图表数据），而 DSH 本身无法直接看图时使用；Gemini 只负责解析输出文本，不操作本机文件、不执行 shell，本地代码修改与程序运行仍由 DeepSeek 主 Agent 完成。
---

# call-gemini-vision(调用 Gemini 视觉解析)

## 触发场景
- 任务涉及本地图片(`.png`/`.jpg`/`.jpeg`)或 PDF 文件，需要读取其中的文字、公式、报错信息、图表数据。
- DSH(DeepSeek)不擅长直接读图，需要独立视觉模型解析后把文本交回。

## 入参
- `file_path`(字符串,必填):本地机器上图片或 PDF 的完整相对路径。

## 执行步骤
1. 确认 `file_path` 指向的文件存在，扩展名为 `.png`/`.jpg`/`.jpeg`/`.pdf`。
2. 本 skill 的基准目录是本文件所在目录，内含助手脚本 `call_gemini_vision.py`。
3. 用 pwsh 执行(脚本只读取文件并把 base64 发给网关，不写盘、不执行其他命令):

   ```powershell
   python "<skill_dir>\call_gemini_vision.py" "<file_path>"
   ```

4. 捕获 stdout，即 Gemini 解析出的纯文本(全部文字、公式、报错信息、图表数据)。
5. 把解析文本交回主对话流，由主 Agent(DeepSeek)继续本地实现;若失败(网关不可达、超时、无 content、文件类型不支持)，如实报告错误，由主 Agent 自行兜底。

## 固定系统提示词(脚本内置,调用时无需再传)
> 完整解析这份文件，提取全部文字、公式、报错信息、图表数据，只输出解析后的纯文本，不要总结建议，不要修改代码。

## 网关参数(默认值,可用参数覆盖)
- Base URL:`http://127.0.0.1:8045/v1`(OpenAI 兼容,`/chat/completions`)
- 模型:`gemini-3.5-flash`,无需 api-key;如代理要求,可用 `--api-key` 或环境变量 `DSH_GEMINI_VISION_API_KEY` 提供。
- 超时默认 600 秒(大文件/长 PDF 解析较慢),可用 `--timeout` 调整。

## 约束
- 本 skill **只做文件解析**:读取本地文件并提交给 Gemini,返回解析文本;不写代码、不运行 shell、不做任何本地工程操作(Gemini 不接触本机文件系统、不执行命令)。
- 主 Agent 保持 DeepSeek 不变,只把解析结果作为文本交回主 Agent 落地实现;不要用 Gemini 替换主模型。
