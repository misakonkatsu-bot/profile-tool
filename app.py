import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from analyzer import analyze_screenshot, load_patterns
from generator import generate_profile
from google_docs import extract_folder_id, is_configured, save_to_google_docs

load_dotenv()

Path("screenshots").mkdir(exist_ok=True)
Path("patterns").mkdir(exist_ok=True)

st.set_page_config(
    page_title="婚活プロフィール作成ツール",
    page_icon="💒",
    layout="wide",
)

st.title("💒 婚活プロフィール作成ツール")

with st.sidebar:
    st.header("⚙️ 設定")
    folder_url = st.text_input(
        "Googleドライブの保存先フォルダURL",
        placeholder="https://drive.google.com/drive/folders/xxx",
        help="フォルダを開いてブラウザのURLをそのまま貼り付けてください",
    )
    if folder_url:
        st.success("保存先フォルダが設定されています")

api_key = os.getenv("ANTHROPIC_API_KEY", "")
if not api_key:
    st.error("⚠️ APIキーが設定されていません。`.env` ファイルに `ANTHROPIC_API_KEY` を設定してください。")

tab1, tab2 = st.tabs(["📸 スクショ分析・蓄積", "✍️ プロフィール作成"])

# ── タブ1：スクショ分析 ──────────────────────────────────────────
with tab1:
    st.header("参考プロフィールを学習させる")
    st.caption("IBJの良いプロフィールのスクショをアップロードすると、AIがパターンを学習して次のプロフィール作成に活かします。")

    patterns = load_patterns()
    count = patterns["screenshots_analyzed"]

    if count == 0:
        st.info("📂 まだ学習データがありません。スクショをアップロードしてください。")
    else:
        st.success(f"✅ **{count}件** のプロフィールから学習済み")
        if patterns.get("summary"):
            with st.expander("学習済みパターンのまとめを見る"):
                st.write(patterns["summary"])

    st.divider()

    uploaded_files = st.file_uploader(
        "スクショをここにドロップ（複数まとめてOK）",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="screenshot_uploader",
    )

    if uploaded_files:
        if not api_key:
            st.warning("APIキーを設定してから分析できます。")
        else:
            if st.button("分析して学習させる", type="primary"):
                for f in uploaded_files:
                    with st.spinner(f"{f.name} を分析中..."):
                        try:
                            analysis = analyze_screenshot(f.read(), f.name, api_key)
                            st.success(f"✅ {f.name} 完了")
                            with st.expander(f"{f.name} の分析結果"):
                                st.write(analysis)
                        except Exception as e:
                            st.error(f"{f.name} でエラー: {e}")
                st.rerun()

# ── タブ2：プロフィール作成 ──────────────────────────────────────
with tab2:
    st.header("プロフィールを作成する")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("基本情報")
        name = st.text_input("名前（ニックネームでもOK）", placeholder="例：みさき様")
        age = st.number_input("年齢", min_value=18, max_value=80, value=30, step=1)
        gender = st.selectbox("性別", ["女性", "男性"])
        occupation = st.text_input("職業・勤務先", placeholder="例：看護師（総合病院勤務）")

    with col_right:
        st.subheader("カウンセリングメモ（自己PR用）")
        reason = st.text_area(
            "婚活を始めたきっかけ",
            height=90,
            placeholder="カウンセリング中にメモしながら入力してください",
        )
        personality = st.text_area("性格・価値観", height=90)
        work = st.text_area("仕事について", height=90)
        hobbies = st.text_area("休日の過ごし方・趣味", height=90)
        lifestyle = st.text_area("ライフスタイル", height=90)
        marriage_view = st.text_area("結婚観", height=90)

    st.subheader("カウンセラーメモ（紹介文用）")
    counselor_memo = st.text_area(
        "エピソード・人柄・印象など（自己PRに入れない内容を書く）",
        height=130,
        placeholder='例：「将来は家庭菜園がしたい」とおっしゃっていた。笑顔が多く、初対面でもとても話しやすい雰囲気。聞き上手で相手を気遣う言葉が自然に出てくる方。',
    )

    st.divider()

    generate_disabled = not api_key or not name
    if st.button("プロフィールを生成する", type="primary", disabled=generate_disabled):
        member_info = {
            "name": name,
            "age": age,
            "gender": gender,
            "occupation": occupation,
            "reason": reason,
            "personality": personality,
            "work": work,
            "hobbies": hobbies,
            "lifestyle": lifestyle,
            "marriage_view": marriage_view,
            "counselor_memo": counselor_memo,
        }
        with st.spinner("プロフィールを生成中です...（30秒〜1分ほどかかります）"):
            try:
                result = generate_profile(member_info, api_key)
                title_line = f"【{name}様　プロフィール】\n\n"
                st.session_state["generated"] = title_line + result
                st.session_state["doc_title"] = f"{name} プロフィール"
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

    if not name and api_key:
        st.caption("※ 名前を入力するとボタンが有効になります")

    if "generated" in st.session_state:
        st.divider()
        st.subheader("生成されたプロフィール")
        st.text_area(
            "内容を確認・修正してから保存してください",
            value=st.session_state["generated"],
            height=550,
            key="profile_output",
        )

        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            st.download_button(
                label="📥 テキストで保存",
                data=st.session_state["generated"],
                file_name=f"{st.session_state['doc_title']}.txt",
                mime="text/plain",
            )
        with col_btn2:
            if is_configured():
                if st.button("📄 Googleドキュメントに保存", type="secondary"):
                    with st.spinner("Googleドキュメントに保存中..."):
                        try:
                            fid = extract_folder_id(folder_url) if folder_url else ""
                            url = save_to_google_docs(
                                st.session_state["doc_title"],
                                st.session_state["generated"],
                                folder_id=fid,
                            )
                            st.success("保存しました！")
                            st.markdown(f"[📄 Googleドキュメントを開く]({url})")
                        except Exception as e:
                            st.error(f"エラー: {e}")
            else:
                st.info("💡 Googleドキュメント保存を使うには `credentials.json` の設定が必要です。")
