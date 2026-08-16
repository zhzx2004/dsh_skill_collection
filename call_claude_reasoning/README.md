# call-claude-reasoning

DSH 自定义 skill:通过本地 antigravity 反重力网关(OpenAI 兼容接口)请求 Claude
做严谨推演分析,仅取回纯文本结果,交回主 Agent(DeepSeek)继续落地实现。

## 文件结构
```
call_claude_reasoning/
├── SKILL.md                  # DSH skill 定义(frontmatter + 指令正文)
├── call_claude_reasoning.py  # python 实现:组装 OpenAI 请求、取回文本
└── README.md                 # 本说明
```

## 环境
- 网关:`http://127.0.0.1:8045/v1`(OpenAI 兼容,`/chat/completions`)
- 模型:`claude-3-5-sonnet`,无需 api-key(本地代理转发)
- 依赖:仅 Python 3 标准库(urllib),无需 pip 安装

## 用法
```powershell
# 1) 直接传 prompt
python call_claude_reasoning.py "推导2自由度机械臂正运动学DH矩阵"

# 2) 长文档:从文件读取入参(脚本只读文本,不写盘)
python call_claude_reasoning.py --file "论文.txt"

# 3) 自定义参数
python call_claude_reasoning.py "..." --model claude-3-5-sonnet --max-tokens 8192 --timeout 600

# 4) 从 stdin 读取
Get-Content 题目.txt -Raw | python call_claude_reasoning.py
```

返回:stdout 为 Claude 的纯文本分析结果;失败时 stderr 输出错误、退出码非 0。

## 测试调用示例
```powershell
python call_claude_reasoning.py "推导2自由度机械臂正运动学DH矩阵"
```

## 说明
- DSH skill 名只允许 kebab-case,故 frontmatter `name` 为 `call-claude-reasoning`
  (目录名按约定保留 `call_claude_reasoning`)。
- 若要在 DSH 目录中发现本 skill,可把它放在项目的 `.dsh/skills/` 或
  `~/.dsh/skills/` 下,或在 DSH 配置的 custom skill 目录中;本仓库同时提供了
  项目级发现副本 `.dsh/skills/call_claude_reasoning/`。
