#!/usr/bin/env python3
"""
FastAPI 服务：接受 PDF/URL 上传，调用 LLM 给出结构化审稿意见。
运行示例：
    uvicorn server:app --reload --port 8000
"""
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from review_agent import (
    build_messages,
    call_model,
    read_paper,
    read_pdf_bytes,
)


app = FastAPI(title="Choose Paper")

# 允许前端直接调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    html_path = Path("static/index.html")
    if not html_path.exists():
        raise HTTPException(status_code=500, detail="static/index.html not found")
    return html_path.read_text(encoding="utf-8")


@app.post("/review")
async def review(
    domain: str = Form("ML", description="CV/ML/NLP"),
    language: str = Form("zh", description="zh 或 en"),
    model: str = Form("gpt-4o-mini"),
    base_url: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    tone: str = Form("mean reviewer who is strict but fair"),
    paper_url: Optional[str] = Form(None, description="可选：论文的 URL"),
    temperature: float = Form(0.2),
    file: Optional[UploadFile] = File(None, description="论文 PDF/TXT 上传"),
):
    if not api_key:
        raise HTTPException(status_code=400, detail="缺少 api_key")
    if not (file or paper_url):
        raise HTTPException(status_code=400, detail="需要提供文件或论文 URL")

    paper_text = ""
    paper_source = ""

    if file:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="上传文件为空")
        filename = file.filename or ""
        content_type = (file.content_type or "").lower()
        if filename.lower().endswith(".pdf") or "pdf" in content_type:
            paper_text = read_pdf_bytes(data)
        else:
            paper_text = data.decode("utf-8", errors="ignore")
        paper_source = filename or "uploaded-file"
    elif paper_url:
        paper_text = read_paper(paper_url)
        paper_source = paper_url

    paper_text = paper_text.strip()
    if not paper_text:
        raise HTTPException(status_code=400, detail="论文内容为空，检查文件或 URL 是否有效")

    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = build_messages(domain, tone, paper_text, language)
    review_text = call_model(client, model, messages, temperature)

    return {
        "review_text": review_text,
        "meta": {
            "domain": domain,
            "language": language,
            "model": model,
            "base_url": base_url,
            "paper_source": paper_source,
            "text_chars": len(paper_text),
        },
    }


# 静态文件（CSS/JS）
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
