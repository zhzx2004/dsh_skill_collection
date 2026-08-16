#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""call_claude_reasoning —— 通过本地 antigravity 网关调用 Claude 严谨推理。

本脚本只负责"取回推理文本":把 prompt_text 组装成 OpenAI 兼容请求发送到
本地网关,并将 Claude 返回的纯文本分析结果打印到 stdout。

安全边界:
- Claude 不读写本机文件、不执行 shell —— 本脚本仅发起一次 HTTP 请求;
- 本脚本不做任何本地工程操作,不落盘(仅 --file 场景读取入参文本);
- 主 Agent(DeepSeek)负责本地代码编写、调试、文件操作。

用法示例:
    python call_claude_reasoning.py "推导2自由度机械臂正运动学DH矩阵"
    python call_claude_reasoning.py --file "paper.md"
    python call_claude_reasoning.py "..." --model claude-3-5-sonnet --max-tokens 8192
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = os.environ.get("DSH_ANTIGRAVITY_BASE_URL", "http://127.0.0.1:8045/v1")
DEFAULT_MODEL = os.environ.get("DSH_ANTIGRAVITY_MODEL", "claude-3-5-sonnet")
DEFAULT_TIMEOUT = float(os.environ.get("DSH_ANTIGRAVITY_TIMEOUT", "300"))

SYSTEM_PROMPT = (
    "严谨完成数学推导、动力学分析或者长文档解析，输出完整详细推导过程，"
    "只返回分析后的纯文本结果，不要执行任何本地操作，"
    "不要生成可直接运行的完整工程代码。"
)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="call_claude_reasoning",
        description="通过本地 antigravity 网关请求 Claude 严谨推理，返回纯文本结果。",
    )
    parser.add_argument(
        "prompt_text",
        nargs="?",
        default=None,
        help="需要交给 Claude 处理的问题、文档片段或数学题目（与 --file 二选一；缺省时从 stdin 读取）。",
    )
    parser.add_argument(
        "--file", "-f",
        default=None,
        help="从本地文本文件读取 prompt（仅读取为入参，脚本不写盘、不执行其他操作）。",
    )
    parser.add_argument("--system", default=SYSTEM_PROMPT, help="自定义系统提示词（默认内置）。")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                        help="网关地址，默认 http://127.0.0.1:8045/v1")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="模型名，默认 claude-3-5-sonnet")
    parser.add_argument("--api-key", default=os.environ.get("DSH_CLAUDE_API_KEY", ""),
                        help="可选 API key（本地代理一般无需）。")
    parser.add_argument("--max-tokens", type=int, default=8192, help="最大输出 token，默认 8192。")
    parser.add_argument("--temperature", type=float, default=0.2, help="采样温度，默认 0.2。")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="请求超时秒数，默认 300。")
    return parser.parse_args(argv)


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt_text is not None:
        return args.prompt_text
    if args.file:
        with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    data = sys.stdin.read()
    if not data.strip():
        raise SystemExit("错误：请提供 prompt_text 参数、--file 文件路径或 stdin 输入。")
    return data


def chat_completion(args: argparse.Namespace, prompt: str) -> str:
    endpoint = args.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": args.system},
            {"role": "user", "content": prompt},
        ],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if args.api_key:
        headers["Authorization"] = "Bearer " + args.api_key
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=args.timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "网关响应缺少 choices[0].message.content："
            + json.dumps(data, ensure_ascii=False)[:500]
        ) from exc


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation):
        pass
    args = parse_args(argv)
    try:
        prompt = load_prompt(args)
        result = chat_completion(args, prompt)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        print(f"网关 HTTP {exc.code}: {detail}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"网关连接失败: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
