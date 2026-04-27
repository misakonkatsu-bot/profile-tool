import anthropic
import base64
import json
from pathlib import Path
from datetime import datetime

PATTERNS_FILE = Path("patterns/patterns.json")


def load_patterns():
    if PATTERNS_FILE.exists():
        with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"screenshots_analyzed": 0, "analyses": [], "summary": ""}


def save_patterns(patterns):
    PATTERNS_FILE.parent.mkdir(exist_ok=True)
    with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)


def analyze_screenshot(image_bytes: bytes, filename: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    media_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": """これは結婚相談所の優れたプロフィールのスクリーンショットです。
以下の観点で詳しく分析してください：

1. 文体・トーン（言葉づかい、丁寧さのレベル、温かみ、親しみやすさ）
2. 各項目の構成と長さの特徴
3. 読み手に好印象を与えている具体的な表現・フレーズ
4. 感情やエピソードの使い方
5. 具体性の出し方（数字・固有名詞・エピソードなど）
6. 自己PRとしての訴求ポイント

分析結果を具体的に記述してください。""",
                    },
                ],
            }
        ],
    )

    analysis = response.content[0].text

    patterns = load_patterns()
    patterns["analyses"].append(
        {
            "filename": filename,
            "analysis": analysis,
            "analyzed_at": datetime.now().isoformat(),
        }
    )
    patterns["screenshots_analyzed"] = len(patterns["analyses"])

    # Summarize all accumulated patterns
    all_analyses = "\n---\n".join([a["analysis"] for a in patterns["analyses"]])
    summary_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": f"""以下は結婚相談所の優れたプロフィール{len(patterns['analyses'])}件の分析結果です。
共通する「良いプロフィールのパターン・特徴」をまとめてください。
プロフィール作成の参考になるよう、具体的かつ実践的にまとめてください。

{all_analyses}""",
            }
        ],
    )

    patterns["summary"] = summary_response.content[0].text
    save_patterns(patterns)

    return analysis
