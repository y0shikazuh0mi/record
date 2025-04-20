import os
import subprocess
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime

# 新しいOpenAI SDK
from openai import OpenAI

# 環境変数の読み込み
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Whisperの準備
try:
    import whisper
except ImportError:
    subprocess.run(["pip", "install", "git+https://github.com/openai/whisper.git"])
    import whisper

# --- UI 構築 ---
st.title("音声・テキスト要約アプリ")
st.write("音声ファイルまたは文字起こしテキストを使って要約します。")

input_mode = st.radio("入力方法を選んでください：", ["音声ファイルを使用", "文字起こし済テキストを使用"])

text_input = ""
audio_path = ""
transcription = ""
summary = ""

if input_mode == "文字起こし済テキストを使用":
    text_input = st.text_area("文字起こしされたテキストを入力してください：", height=200)
else:
    audio_path = st.text_input("音声ファイルのパスを入力してください：")
    start_time = st.text_input("開始時間（例: 00:00:00）", value="00:00:00")
    end_time = st.text_input("終了時間（例: 00:01:00）", value="00:01:00")
    volume = st.text_input("音声ボリューム倍率（例: 1.5）", value="1")

# Whisperモデルの選択
whisper_model = st.selectbox("Whisperモデルを選択：", ["small", "medium", "large"], index=1)

# 要約モードの選択
mode = st.selectbox("要約モードを選んでください：", ["原文の誤字脱字を直して会話ごとに改行表示", "全体の趣旨をまとめる"])

if st.button("実行"):
    st.divider()

    if input_mode == "音声ファイルを使用":
        if not all([audio_path, start_time, end_time, volume]):
            st.error("すべての音声情報を入力してください。")
            st.stop()
        else:
            # 音声トリミング
            output_file = "output.wav"
            if os.path.exists(output_file):
                os.remove(output_file)

            command = [
                "
