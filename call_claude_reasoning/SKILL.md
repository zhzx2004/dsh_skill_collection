---
name: call-claude-reasoning
description: 复杂矩阵运算、机器人动力学推导、长文档论文分析、数学逻辑验算时,通过本地 antigravity 网关请求 Claude 严谨推演,返回纯文本分析结果供主 Agent 继续落地。
whenToUse: 任务涉及复杂矩阵运算、机器人运动学/动力学推导、长文档论文深度分析或数学逻辑验算,需要独立模型做严谨推演时使用。
---

# call-claude-reasoning(调用 Claude 严谨推理)

## 触发场景
- 复杂矩阵运算:高维矩阵、特征分解、SVD、雅可比、张量运算等。
- 机器人推导:正/逆运动学、DH 矩阵、拉格朗日 / 牛顿-欧拉动力学方程等。
- 长文档论文分析:结构解析、逐章要点提取、公式推导核对。
- 数学逻辑验算:证明、化简、数值验证思路推演。

## 入参
- `prompt_text`(字符串,必填):需要交给 Claude 处理的问题、文档片段或数学题目。

## 执行步骤
1. 准备 `prompt_text` 文本。
2. 本 skill 的基准目录是本文件所在目录,内含助手脚本 `call_claude_reasoning.py`。
3. 用 pwsh 执行(prompt 较长时建议写入临时变量或用 `--file` 传入文档文本):

   ```powershell
   python "<skill_dir>\call_claude_reasoning.py" "<prompt_text>"
   ```

   长文档场景(仅把文档文本作为入参读取,脚本不写盘、不执行其他操作):

   ```powershell
   python "<skill_dir>\call_claude_reasoning.py" --file "<文档路径>"
   ```

4. 捕获 stdout,即 Claude 返回的纯文本分析结果。
5. 把结果文本交回主对话流,由主 Agent(DeepSeek)继续本地实现;若失败(网关不可达、超时、无 content),如实报告错误,由主 Agent 自行推理兜底。

## 固定系统提示词(脚本内置,调用时无需再传)
> 严谨完成数学推导、动力学分析或者长文档解析,输出完整详细推导过程,只返回分析后的纯文本结果,不要执行任何本地操作,不要生成可直接运行的完整工程代码。

## 网关参数(默认值,可用参数覆盖)
- Base URL:`http://127.0.0.1:8045/v1`(OpenAI 兼容,`/chat/completions`)
- 模型:`claude-3-5-sonnet`,无需 api-key;如代理要求,可用 `--api-key` 或环境变量 `DSH_CLAUDE_API_KEY` 提供。

## 约束
- 本 skill 只负责获取推理文本,不执行任何本地工程操作;Claude 不读写本机文件、不执行 shell(脚本仅发一次 HTTP 请求)。
- 主 Agent 保持 DeepSeek 不变;skill 结果仅作为参考分析文本交回主 Agent 落地实现。
