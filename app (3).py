import os
import tempfile
import subprocess
from pathlib import Path

import cv2
import requests
import streamlit as st
import fal_client

MODEL_ID = "fal-ai/wan/v2.7/edit-video"
MAX_MB = 100
STYLES = {
    "Anime": "Restyle the entire video as polished 2D Japanese anime with expressive line art, cel shading and illustrated backgrounds.",
    "3D Cartoon": "Restyle the entire video as polished 3D cartoon animation with expressive stylized characters and cinematic lighting.",
    "Disney-inspired cartoon aesthetic": "Restyle the video as a charming family animated-film aesthetic with expressive characters and rich colors. Do not copy specific existing characters.",
    "Comic Book": "Restyle the video as a dynamic comic-book animation with bold ink outlines, halftone texture and graphic shadows.",
    "Pencil Sketch": "Restyle the video as an animated graphite pencil drawing with visible strokes, cross-hatching and paper texture.",
    "Watercolor": "Restyle the video as a moving watercolor painting with soft brushstrokes, flowing pigment and paper texture.",
    "Clay Animation": "Restyle the video as stop-motion clay animation with tactile clay textures and handcrafted miniature-set lighting.",
}

st.set_page_config(page_title="AI Video-to-Animation", page_icon="🎬", layout="wide")
st.title("🎬 AI Video-to-Animation Converter")
st.write("Upload a short real video, select a style, and transform it with a genuine AI video model.")

with st.sidebar:
    st.header("Animation settings")
    style = st.selectbox("Animation style", list(STYLES))
    resolution = st.selectbox("Output resolution", ["720p", "1080p"])
    audio = st.selectbox("Audio", ["origin", "auto"],
                         format_func=lambda x: "Keep original audio" if x == "origin" else "Let model decide")
    custom = st.text_area("Extra instructions (optional)", max_chars=500)

st.info("Model limits: MP4/MOV, 2–10 seconds, maximum 100 MB. Generation may incur fal.ai charges.")
uploaded = st.file_uploader("Upload video", type=["mp4", "mov"])

if uploaded:
    data = uploaded.getvalue()
    size_mb = len(data) / (1024 * 1024)
    if size_mb > MAX_MB:
        st.error("Video exceeds the 100 MB model limit.")
        st.stop()

    suffix = Path(uploaded.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(data)
        input_path = f.name

    try:
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        duration = frames / fps if fps and fps > 0 else 0

        # Prefer ffprobe's duration when available.
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", input_path],
                capture_output=True, text=True, check=True, timeout=20)
            duration = float(probe.stdout.strip())
        except (FileNotFoundError, subprocess.SubprocessError, ValueError):
            pass

        if duration <= 0 or width <= 0 or height <= 0:
            st.error("Could not read this video. Please upload a valid MP4 or MOV.")
            st.stop()

        a, b, c = st.columns(3)
        a.metric("Duration", f"{duration:.1f} sec")
        b.metric("Resolution", f"{width} × {height}")
        c.metric("File size", f"{size_mb:.1f} MB")
        st.subheader("Original video")
        st.video(data)

        if not 2 <= duration <= 10:
            st.warning("This model accepts videos between 2 and 10 seconds.")
        elif st.button("✨ Convert to animation", type="primary", use_container_width=True):
            key = None
            try:
                key = st.secrets.get("FAL_KEY")
            except Exception:
                pass
            key = key or os.getenv("FAL_KEY")
            if not key:
                st.error("Missing FAL_KEY. Add it to Streamlit Secrets or your environment variables.")
                st.stop()

            os.environ["FAL_KEY"] = str(key)
            prompt = (
                STYLES[style] +
                " Preserve the original person's recognizable appearance, facial expressions, "
                "body movements, gestures, actions, timing, scene composition, background and camera "
                "movement as much as possible. Avoid adding extra people or objects. "
                + custom.strip()
            )
            bar = st.progress(5, text="Uploading source video to fal.ai...")
            try:
                video_url = fal_client.upload_file(input_path)
                bar.progress(25, text="Video uploaded. AI transformation is running...")
                result = fal_client.subscribe(
                    MODEL_ID,
                    arguments={
                        "prompt": prompt,
                        "video_url": video_url,
                        "resolution": resolution,
                        "audio_setting": audio,
                        "enable_safety_checker": True,
                    },
                    with_logs=True,
                )
                output_url = result.get("video", {}).get("url")
                if not output_url:
                    raise RuntimeError(f"No output video URL was returned: {result}")

                bar.progress(75, text="Downloading generated video...")
                response = requests.get(output_url, timeout=180)
                response.raise_for_status()
                output = response.content
                if not output:
                    raise RuntimeError("The generated video download was empty.")

                bar.progress(100, text="Animation complete!")
                st.success("Your animated video is ready.")
                st.subheader("Animated result")
                st.video(output)
                st.download_button("⬇️ Download animated MP4", output,
                                   file_name="animated_video.mp4", mime="video/mp4",
                                   use_container_width=True)
                st.caption("Check your fal.ai dashboard for the exact generation charge.")
            except Exception as e:
                st.error("Conversion failed. Check your API key, account credits, video limits and model availability.")
                st.exception(e)
    finally:
        try:
            os.remove(input_path)
        except OSError:
            pass

st.divider()
st.caption("Your clip is sent to fal.ai for processing. Upload only videos you own or have permission to use.")
