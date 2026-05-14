import anthropic
import json
from pathlib import Path

PATTERNS_FILE = Path("patterns/patterns.json")


def load_summary() -> tuple[str, int]:
    if PATTERNS_FILE.exists():
        with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("summary", ""), data.get("screenshots_analyzed", 0)
    return "", 0


def generate_profile(member_info: dict, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    summary, count = load_summary()

    pattern_section = ""
    if summary:
        pattern_section = f"""【参考プロフィールから学習したパターン（{count}件）】
{summary}

上記のパターンを参考にしながら、以下の会員様の情報をもとにプロフィールを作成してください。

"""

    prompt = f"""{pattern_section}【会員様の基本情報】
年齢: {member_info.get('age', '')}歳
性別: {member_info.get('gender', '')}
職業: {member_info.get('occupation', '')}

【カウンセリングメモ】
＜婚活を始めたきっかけ＞
{member_info.get('reason', '（未記入）')}

＜性格・価値観＞
{member_info.get('personality', '（未記入）')}

＜仕事について＞
{member_info.get('work', '（未記入）')}

＜休日の過ごし方・趣味＞
{member_info.get('hobbies', '（未記入）')}

＜ライフスタイル＞
{member_info.get('lifestyle', '（未記入）')}

＜結婚観＞
{member_info.get('marriage_view', '（未記入）')}

【カウンセラーメモ（紹介文用）】
{member_info.get('counselor_memo', '（未記入）')}

---

以下の2種類の文章を作成してください。

━━━━━━━━━━━━━━━━━━━━━━
【自己PR】
━━━━━━━━━━━━━━━━━━━━━━
会員様自身の言葉として、読んだ方が親しみやすく、温かみを感じられる文章で書いてください。
各項目150〜250文字程度。カウンセリングメモにある情報のみを使い、情報を付け加えないこと。

■ 婚活を始めたきっかけ


■ 性格・価値観


■ 仕事


■ 休日の過ごし方・趣味


■ ライフスタイル


■ 結婚観


━━━━━━━━━━━━━━━━━━━━━━
【カウンセラーより】
━━━━━━━━━━━━━━━━━━━━━━
カウンセラーのみさが書いた信頼感のある紹介文として書いてください。
自己PRと内容が重複しないよう、カウンセリングで聞いた具体的なエピソードや、
直接会って感じた人柄・雰囲気を中心にしてください。

■ カウンセリングでのエピソード
（実際にお話してくださった具体的なエピソード）

■ この方の人柄
（カウンセラーが直接感じた印象・雰囲気・魅力）

■ この方と結婚するメリット
（具体的で魅力的な表現で、お相手が「会ってみたい」と思えるような内容）

【重要なルール】
- 自己PRとカウンセラー紹介文の内容が重複しないこと
- カウンセリングメモにない情報は絶対に追加しないこと
- 自然で読みやすい日本語にすること
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text
