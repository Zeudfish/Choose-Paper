# 🚀 Paper Review Agent

拖拽 PDF / 输入 URL，一键生成阅读建议。

> [!NOTE]
> 默认使用 OpenAI 兼容接口，请自行配置 API Key / Base URL。

https://github.com/user-attachments/assets/placeholder-demo.gif

## ✨ 主要特性
🤖 **一键给出阅读建议**：拖拽 PDF/TXT 或粘贴论文 URL，自动提取文本并调用 LLM并给出阅读建议-------经作者实测，gpt5.1效果较好，和我自己的阅读感受较为接近。   
🛠️ **CLI + Web**：命令行和网页双入口，基于 OpenAI 兼容 API。

## 🖥️ Web 端快速开始
```bash
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
# 浏览器打开 http://localhost:8000
```
1) 填写 API Key（及 Base URL 如使用 DeepSeek）  
2) 选择模型/领域/语言，拖拽 PDF 或输入 URL  
3) 点击生成，切到“查看结果”标签页查看阅读建议

## 🛠️ CLI 快速开始
```bash
# 从文件
python review_agent.py \
  --paper examples/paper.txt \
  --domain ML \
  --language zh \
  --model gpt-4o-mini \
  --output review.txt

# 或从 stdin
cat examples/paper.txt | python review_agent.py --paper - --domain CV --language en
```

## 🗺️ 路线图
- 长文分段/摘要后审稿
- 更多模型预设（Anthropic/Google 兼容网关）
- Docker 镜像与一键脚本

## 🤝 贡献 & Star
欢迎 Issue / PR / Star！如需补充徽标、录屏或线上 Demo，欢迎提交 Issue 讨论。
