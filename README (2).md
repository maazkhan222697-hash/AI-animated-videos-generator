# AI Video-to-Animation Converter

A Streamlit interface for real AI video-to-video restyling using `fal-ai/wan/v2.7/edit-video`.

## Features
- Upload MP4 or MOV videos.
- Choose Anime, 3D Cartoon, Disney-inspired cartoon aesthetic, Comic Book, Pencil Sketch, Watercolor or Clay Animation.
- Add custom instructions, choose 720p/1080p, and preserve original audio.
- Preview and download the generated MP4.
- Validate duration, file size, and video metadata.

## Model requirements and cost
The model documentation lists MP4/MOV input, 2–10 seconds, maximum 100 MB, and 720p/1080p output. Pricing may change; check the model page and your fal.ai dashboard before every use. Each generation may incur a charge.

Model/API documentation: https://fal.ai/models/fal-ai/wan/v2.7/edit-video/api

## 1. Get your API key
Create an account at https://fal.ai/ and generate a key at https://fal.ai/dashboard/keys. Keep it secret; never commit it to GitHub.

## 2. Run locally
Install Python 3.10+ and run:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

Set the key and launch:

```bash
# Windows PowerShell
$env:FAL_KEY="your_api_key"
streamlit run app.py
```

```bash
# macOS/Linux
export FAL_KEY="your_api_key"
streamlit run app.py
```

## 3. Develop in Google Colab
Upload `app.py` and `requirements.txt` to Colab, then install dependencies:

```python
!pip install -r requirements.txt
```

Enter your key without hardcoding it in a shared notebook:

```python
import os
from getpass import getpass
os.environ["FAL_KEY"] = getpass("Enter fal.ai API key: ")
```

For a temporary Streamlit preview, install Cloudflare Tunnel and start Streamlit:

```bash
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
!chmod +x cloudflared
!streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
!./cloudflared tunnel --url http://localhost:8501
```

Keep the Colab runtime active. This tunnel is temporary, not permanent hosting. AI inference runs on fal.ai, not on the Colab GPU.

## 4. Upload to GitHub
Create a repository and upload `app.py`, `requirements.txt`, and `README.md`. Never upload API keys, `.env` files, private videos, or generated videos.

## 5. Deploy on Streamlit Community Cloud
1. Visit https://share.streamlit.io/ and sign in with GitHub.
2. Select your repository and set the main file to `app.py`.
3. Open app Settings → Secrets.
4. Add this TOML secret:

```toml
FAL_KEY = "your_api_key"
```

5. Save and wait for deployment.

## Important limitations
- Clips must be 2–10 seconds and no larger than 100 MB.
- The AI model may change fine details; identity, movement, and background preservation are best-effort, not guaranteed.
- Streamlit hosts the interface. fal.ai performs the paid AI generation.
- OpenCV reads video metadata; `ffprobe` checks duration if installed. If ffprobe is unavailable, OpenCV's duration estimate is used.
- The temporary uploaded source file is deleted from the app after processing, but it is uploaded to fal.ai for inference and is subject to that provider's terms and retention policies.
- Upload only footage you own or have permission to process.
