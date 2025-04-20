import os
import subprocess
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime
import tempfile

load_dotenv()

# 必要なライブラリのインポート
try:
    import whisper
except ImportError:
    subprocess.run(["pip", "install", "git+https://github.com/openai/whisper.git"])
    import whisper

try:
    import openai
except ImportError:
    subprocess.run(["pip", "install", "openai==0.28"])  # 古いAPI用に固定
    import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("音声・テキスト要約アプリ")
st.write("音声ファイルまたは文字起こしテキストを使って要約します。")

input_mode = st.radio("入力方法を選んでください：", ["音声ファイルを使用", "文字起こし済テキストを使用"])

text_input = ""
transcription = ""
summary = ""

if input_mode == "文字起こし済テキストを使用":
    text_input = st.text_area("文字起こしされたテキストを入力してください：", height=200)
else:
    audio_file = st.file_uploader("音声ファイルをアップロードしてください（例: .mp3, .m4a, .wav）", type=["mp3", "m4a", "wav"])
    start_time = st.text_input("開始時間（例: 00:00:00）", value="00:00:00")
    end_time = st.text_input("終了時間（例: 00:01:00）", value="00:01:00")
    volume = st.text_input("音声ボリューム倍率（例: 1.5）", value="1")

whisper_model = st.selectbox("Whisperモデルを選択：", ["small", "medium", "large"], index=1)
mode = st.selectbox("要約モードを選んでください：", ["原文の誤字脱字を直して会話ごとに改行表示", "全体の趣旨をまとめる"])

if st.button("実行"):
    st.divider()

    if input_mode == "音声ファイルを使用":
        if not all([audio_file, start_time, end_time, volume]):
            st.error("すべての音声情報を入力してください。")
            st.stop()

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp_input:
            tmp_input.write(audio_file.read())
            input_path = tmp_input.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_output:
            output_path = tmp_output.name

            st.write(f"出力ファイルのパス: {output_path}")  # 出力パスを表示して確認

        command = [
            "ffmpeg", "-ss", start_time, "-to", end_time, "-i", input_path,
            "-filter:a", f"volume={volume}", output_path
        ]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            st.error(f"ffmpegエラー: {result.stderr}")
            st.stop()
        else:
            st.write("音声トリミング成功 ✅")

        st.write("文字起こし中...")
        model = whisper.load_model(whisper_model)
        whisper_result = model.transcribe(output_path, language="ja")
        transcription = whisper_result["text"]

    else:
        transcription = text_input.strip()
        if not transcription:
            st.error("テキストを入力してください。")
            st.stop()

    # GPTによる要約
    system_prompt = "あなたは文書の校正者です。"
    if mode == "原文の誤字脱字を直して会話ごとに改行表示":
        user_prompt = f"以下の文字起こし文を、文脈を考慮して正しい日本語に直してください。誤字脱字、口語表現、不自然な語順を修正し、話者が変わるたびに改行してください。\n\n{transcription}"
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

        st.subheader("🔍 文字起こし結果")
        st.text_area("文字起こし", transcription, height=200)

        st.subheader("✏️ 要約結果")
        st.text_area("生成された要約", summary, height=300)

        file_name = st.text_input("保存ファイル名（例：result.txt）", value="result.txt")
        if st.button("テキストとして保存"):
            combined_text = f"""【文字起こし結果】\n{transcription}\n\n【要約】\n{summary}\n"""
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(combined_text)
            st.success(f"{file_name} に保存しました！")

    except Exception as e:
        st.error(f"要約中にエラーが発生しました: {str(e)}")

