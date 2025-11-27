#!/usr/bin/env python3
"""
命令行小工具：让 LLM 扮演严格的审稿人，输出纯文本的优缺点与评分（支持 CV/ML/NLP 领域、中文/英文）。
"""
import argparse
import os
import sys
from typing import Dict, List
from urllib.parse import urlparse

import requests
from openai import OpenAI
from pypdf import PdfReader


def read_paper(source: str) -> str:
    """
    读取论文文本：支持文件路径、URL、PDF，或 stdin（source 为 '-'）。
    - http(s) URL：先抓取，按 content-type 判断是否 PDF。
    - .pdf 文件：本地解析 PDF。
    - 其他：按 UTF-8 文本读取。
    """
    if source == "-":
        return sys.stdin.read()

    parsed = urlparse(source)
    if parsed.scheme in ("http", "https"):
        return _read_from_url(source)
    if source.lower().endswith(".pdf"):
        return _read_pdf(source)
    return _read_text_file(source)


def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fp:
        return fp.read()


def _read_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _read_pdf_bytes(data: bytes) -> str:
    from io import BytesIO

    reader = PdfReader(BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def read_pdf_bytes(data: bytes) -> str:
    """从 PDF 二进制内容中提取文本。"""
    return _read_pdf_bytes(data)


def _read_from_url(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "").lower()
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return _read_pdf_bytes(resp.content)
    return resp.text


def build_messages(domain: str, tone: str, paper_text: str, language: str) -> List[Dict[str, str]]:
    """构造提示，支持中文/英文输出和领域（CV/ML/NLP）标签。"""
    lang = language.lower()
    if lang.startswith("zh"):
        template = (
            "请用中文给出审稿意见，语气严格但公正，领域为{domain}。\n"
            "输出采用以下纯文本模板（不要使用 JSON，也不要用代码块）：\n"
            "Summary: ...\n"
            "Strengths:\n- ...\n"
            "Weaknesses:\n- ...\n"
            "Questions:\n- ...\n"
            "Decision (阅读建议: 精读 / 可选浏览 / 可忽略): ...\n"
            "\n论文内容：\n{paper}"
        )
    else:
        template = (
            "Provide the review in English, with a strict but fair tone, domain: {domain}.\n"
            "Use this plain-text template (no JSON, no code fences):\n"
            "Summary: ...\n"
            "Strengths:\n- ...\n"
            "Weaknesses:\n- ...\n"
            "Questions:\n- ...\n"
            "Decision (Reading suggestion: Must Read / Skim Optional / Skip): ...\n"
            "\nPAPER:\n{paper}"
        )
    system_msg = (
        f"You are a seasoned reviewer in {domain}. "
        f"Maintain a strict, skeptical, concise tone: {tone}. "
        "Respond using the requested language."
    )
    user_msg = template.format(domain=domain, paper=paper_text)
    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


def call_model(
    client: OpenAI,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
) -> str:
    """调用模型并返回纯文本内容。"""
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
    )
    return response.choices[0].message.content or ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an LLM-based paper review agent that returns structured text."
    )
    parser.add_argument(
        "--paper",
        required=True,
        help="Path/URL to the paper (txt/pdf/html), or '-' to read from stdin.",
    )
    parser.add_argument(
        "--domain",
        default="ML",
        choices=["CV", "ML", "NLP"],
        help="Research domain persona for the review tone.",
    )
    parser.add_argument(
        "--tone",
        default="mean reviewer who is strict but fair",
        help="Tone reminder injected into the prompt.",
    )
    parser.add_argument(
        "--language",
        default="en",
        choices=["en", "zh"],
        help="Output language for the review.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        help="Model name to call.",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL"),
        help="Optional base URL for OpenAI-compatible APIs (e.g., DeepSeek).",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY"),
        help="API key to use; falls back to OPENAI_API_KEY env var.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for the model.",
    )
    parser.add_argument(
        "--output",
        help="Optional path to save the JSON review. If omitted, prints to stdout.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paper_text = read_paper(args.paper).strip()
    if not paper_text:
        raise SystemExit("Paper text is empty; provide a text file or stdin input.")



    client = OpenAI(api_key=args.api_key, base_url=args.base_url)
    messages = build_messages(args.domain, args.tone, paper_text, args.language)
    review = call_model(client, args.model, messages, args.temperature)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fp:
            fp.write(review)
        print(f"Saved review to {args.output}")
    else:
        print(review)


if __name__ == "__main__":
    main()
