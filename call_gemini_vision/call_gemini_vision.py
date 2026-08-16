#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""call_gemini_vision —— 通过本地 antigravity 网关调用 gemini-3.5-flash 解析本地图片/PDF。

本脚本只做一件事:读取本地文件(png/jpg/jpeg/pdf),以 base64 data URL 通过
OpenAI 兼容接口提交给本地 antigravity 网关,由 gemini-3.5-flash 做视觉解析,
并把解析出的纯文本打印到 stdout。

安全边界:
- Gemini 不接触本机文件系统、不执行 shell —— 它只收到一次 HTTP 请求中的文件内容;
- 本脚本不写盘(仅读取入参文件)、不执行任何 shell 命令、不做本地工程操作;
- 所有本地代码修改、程序运行仍由主 Agent(DeepSeek)完成。

用法示例:
    python call_gemini_vision.py ".\\截图.png"
    python call_gemini_vision.py ".\文档.pdf" --timeout 600
    python call_gemini_vision.py ".\报错截图.jpg" --model gemini-3.5-flash --max-tokens 8192
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = os.environ.get("DSH_ANTIGRAVITY_BASE_URL", "http://127.0.0.1:8045/v1")
DEFAULT_MODEL = os.environ.get("DSH_GEMINI_VISION_MODEL", "gemini-3.5-flash")
DEFAULT_TIMEOUT = float(os.environ.get("DSH_GEMINI_VISION_TIMEOUT", "600"))

SYSTEM_PROMPT = (
    "完整解析这份文件，提取全部文字、公式、报错信息、图表数据，"
    "只输出解析后的纯文本，不要总结建议，不要修改代码。"
)

# 支持的文件类型:扩展名(小写) -> MIME
MIME_BY_EXT = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".pdf": "application/pdf",
}


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="call_gemini_vision",
        description="通过本地 antigravity 网关调用 gemini-3.5-flash 解析本地图片/PDF，输出纯文本。",
    )
    parser.add_argument(
        "file_path",
        help="本地图片(.png/.jpg/.jpeg)或 PDF 文件的完整相对路径。",
    )
    parser.add_argument("--system", default=SYSTEM_PROMPT, help="系统提示词（默认内置）。")
    parser.add_argument(
        "--user-text",
        default="请解析附件中的文件，输出完整解析文本。",
        help="随文件一起发送给模型的简短指令文本。",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                        help="网关地址，默认 http://127.0.0.1:8045/v1")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="模型名，默认 gemini-3.5-flash")
    parser.add_argument("--api-key", default=os.environ.get("DSH_GEMINI_VISION_API_KEY", ""),
                        help="可选 API key（本地代理一般无需）。")
    parser.add_argument("--max-tokens", type=int, default=16384, help="最大输出 token，默认 16384。")
    parser.add_argument("--temperature", type=float, default=0.0, help="采样温度，默认 0.0（解析任务）。")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="请求超时秒数，默认 600。")
    return parser.parse_args(argv)


def resolve_mime(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    mime = MIME_BY_EXT.get(ext)
    if mime is None:
        raise ValueError(
            f"不支持的文件类型: {ext or '(无扩展名)'}。仅支持 .png/.jpg/.jpeg/.pdf"
        )
    return mime


def read_file_as_data_url(file_path: str, mime: str) -> str:
    with open(file_path, "rb") as fh:
        raw = fh.read()
    if not raw:
        raise ValueError(f"文件为空: {file_path}")
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def chat_completion(args: argparse.Namespace, data_url: str, mime: str) -> str:
    endpoint = args.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": args.system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": args.user_text},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
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
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "网关响应缺少 choices[0].message.content："
            + json.dumps(data, ensure_ascii=False)[:500]
        ) from exc
    # 个别网关把 content 返回为多段列表，拼成纯文本
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            else:
                parts.append(str(item))
        content = "".join(parts)
    return content


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation):
        pass
    args = parse_args(argv)
    try:
        mime = resolve_mime(args.file_path)
        if not os.path.isfile(args.file_path):
            raise FileNotFoundError(f"文件不存在: {args.file_path}")
        data_url = read_file_as_data_url(args.file_path, mime)
        result = chat_completion(args, data_url, mime)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        print(f"网关 HTTP {exc.code}: {detail}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"入参错误: {exc}", file=sys.stderr)
        return 2
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"网关连接失败: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"入参错误: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
