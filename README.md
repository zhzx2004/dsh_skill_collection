# dsh_skill_collection
DSH 自定义Skill集合，包含2个机器人技能模块。

## 🎯 Skill介绍
- Skill 1：**call‑claude‑reasoning**（调用 Claude 严谨推理）——复杂矩阵运算、机器人运动学/动力学推导、长文档论文深度分析、数学逻辑验算时，通过本地 antigravity 网关请求 Claude 严谨推演，返回纯文本分析结果供主 Agent 继续落地。
- Skill 2：**call‑gemini‑vision**（调用 Gemini 视觉解析）——需要读取本地图片（`.png`/`.jpg`/`.jpeg`）或 PDF 中的文字、公式、报错信息、图表数据，而 DSH 不擅长直接读图时，通过本地 antigravity 网关调用 gemini‑3.5‑flash 做视觉解析，返回提取出的纯文本供主 Agent 继续处理。

## 📋 环境要求
- DSH 版本：支持 `skills/` 目录自动加载的 DSH 版本
- Python3（运行两个技能内置的调用脚本）
- 本地 antigravity 网关：`http://127.0.0.1:8045/v1`（OpenAI 兼容接口），两个技能均通过该网关转发请求；默认无需 api‑key

## 📂 安装部署
1. 将本仓库内 `skills/call_claude_reasoning` 与 `skills/call_gemini_vision` 两个技能文件夹复制到 DSH 项目的 `skills/` 目录下
2. 重启 DSH 服务，即可加载这两项技能

## 📌 使用提示
- 调用方式：主 Agent 在遇到复杂推理或读图任务时自动触发对应技能；也可直接通过技能名 `call‑claude‑reasoning` / `call‑gemini‑vision` 调用
- 注意事项：
  - 两个技能仅负责「推理 / 解析」，不执行任何本地文件写入与 shell 操作，落地实现仍由主 Agent（DeepSeek）完成
  - 依赖本地 antigravity 网关可达；网关不可达、超时或返回为空时技能会如实报错，由主 Agent 自行兜底
  - call‑gemini‑vision 仅支持 `.png`/`.jpg`/`.jpeg`/`.pdf` 文件，默认超时 600 秒（大文件/长 PDF 解析较慢），可用 `--timeout` 调整

## License
MIT
