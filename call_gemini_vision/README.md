# call-gemini-vision

DSH 自定义 skill:通过本地 antigravity 反重力网关(OpenAI 兼容接口)调用
`gemini-3.5-flash` 解析本地图片(`.png`/`.jpg`/`.jpeg`)或 PDF 文件,
仅取回解析出的纯文本,交回主 Agent(DeepSeek)继续落地实现。

## 文件结构
```
call_gemini_vision/
├── SKILL.md                  # DSH skill 定义(frontmatter + 指令正文)
├── call_gemini_vision.py     # python 实现:读取文件、组装 OpenAI 视觉请求、取回文本
├── test_vision.png           # 本地测试图片(可用它验证 skill)
└── README.md                 # 本说明
```

## 环境
- 网关:`http://127.0.0.1:8045/v1`(OpenAI 兼容,`/chat/completions`)
- 模型:`gemini-3.5-flash`,无需 api-key(本地代理转发)
- 依赖:仅 Python 3 标准库(urllib),无需 pip 安装

## 用法
```powershell
# 1) 解析本地图片
python call_gemini_vision.py ".\\截图.png"

# 2) 解析 PDF
python call_gemini_vision.py ".\文档.pdf"

# 3) 自定义参数(网关、模型、超时等)
python call_gemini_vision.py ".\报错截图.jpg" --model gemini-3.5-flash --timeout 600
```

返回:stdout 为 Gemini 解析出的纯文本;失败时 stderr 输出错误、退出码非 0。

## 测试调用示例
```powershell
# 用本目录自带的测试图片验证(需先启动本地 antigravity 网关)
python call_gemini_vision.py ".\test_vision.png"
```

## 说明
- 本 skill **只做文件解析**:不写代码、不运行 shell、不操作本地工程;
  Gemini 不接触本机文件系统,所有本地修改仍由 DeepSeek 主 Agent 完成。
- DSH skill 名只允许 kebab-case,故 frontmatter `name` 为 `call-gemini-vision`
  (目录名按用户约定保留 `call_gemini_vision`)。
- 若要在 DSH 目录中发现本 skill,可把它放在项目的 `.dsh/skills/` 或
  `~/.dsh/skills/` 下;本仓库同时提供了项目级发现副本 `.dsh/skills/call_gemini_vision/`。
