from flask import Flask, request, Response, stream_with_context
import requests
import os
import urllib.parse

app = Flask(__name__)

HEADERS = {
    "Referer": "https://nxtlive.net/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

BASE_URL = "https://nxtlive.net/sliv/stream.m3u8"

def proxy_request(url):
    """Helper to stream content from the original URL."""
    r = requests.get(url, headers=HEADERS, stream=True)
    r.raise_for_status()
    return r

@app.route("/stream.m3u8")
def master_playlist():
    stream_id = request.args.get("id")
    if not stream_id:
        return "Missing id parameter", 400

    # Fetch the original master playlist
    real_url = f"{BASE_URL}?id={stream_id}"
    r = proxy_request(real_url)
    content = r.text

    # Rewrite all internal playlist URLs to go through this proxy
    # Example: stream.m3u8?live=... -> /playlist?url=...
    import re
    content = re.sub(
        r'(stream\.m3u8\?[^ \n]+)',
        lambda m: f"/playlist?url={urllib.parse.quote(m.group(0))}",
        content
    )

    return Response(content, content_type="application/vnd.apple.mpegurl")


@app.route("/playlist")
def playlist_proxy():
    url = request.args.get("url")
    if not url:
        return "Missing url parameter", 400

    # Decode URL and fetch the real media playlist
    real_url = f"https://nxtlive.net/sliv/{urllib.parse.unquote(url)}"
    r = proxy_request(real_url)
    content = r.text

    # Rewrite TS segments to go through proxy
    import re
    content = re.sub(
        r'([^\n]+\.ts[^\n]*)',
        lambda m: f"/segment?url={urllib.parse.quote(m.group(0))}",
        content
    )

    return Response(content, content_type="application/vnd.apple.mpegurl")


@app.route("/segment")
def segment_proxy():
    url = request.args.get("url")
    if not url:
        return "Missing url parameter", 400

    real_url = f"https://nxtlive.net/sliv/{urllib.parse.unquote(url)}"
    r = proxy_request(real_url)

    # Stream TS segment directly to client
    return Response(stream_with_context(r.iter_content(chunk_size=8192)), content_type="video/MP2T")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
