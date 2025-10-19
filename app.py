from flask import Flask, request, Response
import requests

app = Flask(__name__)

BASE_URL = "https://nxtlive.net/sliv/stream.m3u8"

@app.route("/stream.m3u8")
def proxy_hls():
    # Get the stream ID from query parameters
    stream_id = request.args.get("id")
    if not stream_id:
        return "Missing id parameter", 400

    # Build the real HLS URL
    real_url = f"{BASE_URL}?id={stream_id}"

    # Headers including Referer
    headers = {
        "Referer": "https://nxtlive.net/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    # Relay the content to client
    def generate():
        with requests.get(real_url, headers=headers, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

    return Response(generate(), content_type="application/vnd.apple.mpegurl")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
