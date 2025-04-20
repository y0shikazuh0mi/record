import os
import subprocess
import tempfile
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime

load_dotenv()

# ライブラリの確認・インストール
try:
    import whisper
except ImportError:
    subprocess.run(["pip", "install", "git+https://github.com/openai/whisper.git"])
    import whisper

try:
    import openai
except ImportError:
    subprocess.run(["pip", "install", "openai"])
    import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

# --- UI 構築 ---
st.title("🎙️ 音声・テキスト要約アプリ")
st.write("音声ファイルまたは文字起こしテキストを使って要約します。")

input_mode = st.radio("入力方法を選んでください：", ["音声ファイルを使用", "文字起こし済テキストを使用"])

text_input = ""
transcription = ""
summary = ""

if input_mode == "文字起こし済テキストを使用":
    text_input = st.text_area("文字起こしされたテキストを入力してください：", height=200)
else:
    uploaded_file = st.file_uploader("音声ファイルをアップロードしてください", type=["m4a", "mp3", "wav"])
    start_time = st.text_input("開始時間（例: 00:00:00）", value="00:00:00")
    end_time = st.text_input("終了時間（例: 00:01:00）", value="00:01:00")
    volume = st.text_input("音声ボリューム倍率（例: 1.5）", value="1")

# Whisperモデル選択
whisper_model = st.selectbox("Whisperモデルを選択：", ["small", "medium", "large"], index=1)

# 要約モード選択
mode = st.selectbox("要約モードを選んでください：", ["原文の誤字脱字を直して会話ごとに改行表示", "全体の趣旨をまとめる"])

if st.button("実行"):
    st.divider()

    if input_mode == "音声ファイルを使用":
        if not all([uploaded_file, start_time, end_time, volume]):
            st.error("すべての音声情報を入力してください。")
            st.stop()

        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp:
            tmp.write(uploaded_file.read())
            input_path = tmp.name

        output_file = "output.wav"
        if os.path.exists(output_file):
            os.remove(output_file)

        # ffmpegで音声トリミング＆音量調整
        command = [
            "ffmpeg", "-ss", start_time, "-to", end_time, "-i", input_path,
            "-filter:a", f"volume={volume}", output_file
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            st.error(f"ffmpegエラー: {result.stderr}")
            st.stop()
        else:
            st.success("✅ 音声トリミング成功")

        # Whisperで文字起こし
        st.write("文字起こし中...")
        model = whisper.load_model(whisper_model)
        whisper_result = model.transcribe(output_file, language="ja")
        transcription = whisper_result["text"]

    else:
        transcription = text_input.strip()
        if not transcription:
            st.error("テキストを入力してください。")
            st.stop()

    # 要約プロンプト作成
    system_prompt = "あなたは文書の校正者です。"
    if mode == "原文の誤字脱字を直して会話ごとに改行表示":
        user_prompt = f"以下の文字起こし文を、文脈を考慮して正しい日本語に直してください。誤字脱字、口語表現の整形、不自然な語順を修正し、話者ごとに改行を入れてください。\n\n{transcription}"
    else:
        user_prompt = f"次の内容の全体の趣旨をわかりやすく短くまとめてください。\n\n{transcription}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5
        )
        summary = response['choices'][0]['message']['content']

        # --- 結果表示 ---
        st.subheader("🔍 文字起こし結果")
        st.text_area("文字起こし", transcription, height=200)

        st.subheader("✏️ 要約結果")
        st.text_area("生成された要約", summary, height=300)

        # 保存
        file_name = st.text_input("保存ファイル名（例：result.txt）", value="result.txt")
        if st.button("テキストとして保存"):
            combined_text = f"""【文字起こし結果】\n{transcription}\n\n【要約】\n{summary}\n"""
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(combined_text)
            st.success(f"{file_name} に保存しました！")

    except Exception as e:
        st.error(f"要約中にエラーが発生しました: {str(e)}")
