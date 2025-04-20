import streamlit as st
import tempfile
import os
import subprocess

st.title("🎵 音声トリミングテストアプリ")

audio_file = st.file_uploader("音声ファイルをアップロード", type=["mp3", "m4a", "wav"])
start_time = st.text_input("開始時間 (例: 00:00:00)")
end_time = st.text_input("終了時間 (例: 00:00:05)")

if st.button("トリミング開始"):

    if not all([audio_file, start_time, end_time]):
        st.error("すべての情報を入力してください。")
        st.stop()

    # 入力ファイルをテンポラリに保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp_input:
        tmp_input.write(audio_file.read())
        input_path = tmp_input.name

    # 出力ファイルパスを作成
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_output:
        output_path = tmp_output.name

    command = [
        "ffmpeg", "-y", "-ss", start_time, "-to", end_time,
        "-i", input_path, "-filter:a", "volume=1", output_path
    ]

    try:
        st.write("🔧 ffmpeg 実行中...")
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            st.error("❌ ffmpeg エラー発生")
            st.text(result.stderr)
        else:
            st.success("✅ トリミング成功！")
            st.audio(output_path, format="audio/wav")

    except subprocess.TimeoutExpired:
        st.error("⚠️ ffmpeg の実行がタイムアウトしました（60秒以上）")
