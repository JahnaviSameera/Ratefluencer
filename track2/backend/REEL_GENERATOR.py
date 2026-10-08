"""
Ratefluencer — Reel Production Engine
=======================================

Takes a GeneratedContent script dict and produces a ready-to-post MP4:
  1. Voiceover   — edge-tts neural TTS (free, no signup)
  2. Images      — Imagen 4 via Gemini API (scene-specific AI images)
  3. Subtitles   — auto word-timed captions burned into video
  4. Thumbnail   — Pillow-generated title card (first frame)
  5. Assembly    — MoviePy stitches image clips + audio + captions → MP4

Output: reel_<phrase>.mp4  +  thumbnail_<phrase>.jpg
"""
from __future__ import annotations
import asyncio, base64, json, math, os, re, shutil, tempfile, textwrap, time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
IMAGEN_URL = "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-fast-generate-001:predict"
PEXELS_KEY = os.getenv("PEXELS_API_KEY", "")
OUTPUT_DIR = Path("reels_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Reel dimensions (vertical 9:16)
W, H = 1080, 1920

# ---------------------------------------------------------------------------
# 1. Voiceover via edge-tts
# ---------------------------------------------------------------------------
# Human-sounding voices ranked best to fallback
VOICES = [
    "en-US-JennyNeural",      # warm, conversational, most human
    "en-US-AriaNeural",       # energetic, clear
    "en-US-SaraNeural",       # friendly, upbeat
]
VOICE = VOICES[0]

def build_voiceover_script(script: dict) -> str:
    """Build spoken script with natural pause markers for human feel."""
    reel     = script.get("reel_script", {})
    hook     = reel.get("hook", "").strip()
    story    = reel.get("story", "").strip()
    insights = reel.get("insights", [])[:2]
    cta      = reel.get("cta", "").strip()

    # Add natural pauses between sections — comma pauses feel human
    parts = []
    if hook:
        parts.append(hook)
    if story:
        parts.append(story)
    for ins in insights:
        ins = ins.strip()
        if ins:
            # Prefix insight with natural transition
            parts.append(f"Here's what you need to know. {ins}")
    if cta:
        parts.append(f"So, {cta}")

    return "  ".join(parts)


async def _synthesize(text: str, out_path: str) -> None:
    import edge_tts, ssl, aiohttp
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    # JennyNeural at slightly slower rate sounds most natural
    communicate = edge_tts.Communicate(text, VOICE, rate="+5%", volume="+10%", pitch="+2Hz")
    communicate._connector = connector
    await communicate.save(out_path)


def generate_voiceover(text: str, out_path: str) -> str:
    print(f"[ReelProducer] Generating voiceover ({len(text)} chars)...")
    asyncio.run(_synthesize(text, out_path))
    print(f"[ReelProducer] Voiceover saved → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# 2. Scene images via Imagen 4 (Gemini)
# ---------------------------------------------------------------------------

def _build_scene_prompts(script: dict) -> list[str]:
    """Build 4 scene-specific image prompts from the script content."""
    reel     = script.get("reel_script", {})
    hook     = reel.get("hook", script.get("hook", ""))
    insights = reel.get("insights", script.get("insights", []))
    phrase   = script.get("trend_phrase", script.get("phrase", "technology"))
    niche    = script.get("niche", "technology")

    style = (
        "cinematic vertical 9:16 portrait photo, ultra-sharp, dramatic lighting, "
        "dark moody background, photorealistic, professional stock photo style, "
        "no text, no watermark"
    )
    return [
        f"{hook}. {style}. Theme: {phrase}",
        f"A professional showing {phrase} on a futuristic screen, {style}",
        f"{insights[0] if insights else phrase} visualised as a concept, {style}",
        f"Close-up of {niche} technology with glowing elements, {style}",
    ]


def generate_images_gemini(script: dict, tmp_dir: str, n: int = 4) -> list[str]:
    """
    Generate n scene images using Imagen 4 via Gemini API.
    Returns list of local PNG paths.
    Falls back to Pexels if Imagen is unavailable.
    """
    if not GEMINI_KEY:
        print("[ReelProducer] No GEMINI_KEY — falling back to Pexels")
        return _pexels_fallback(script, tmp_dir, n)

    prompts = _build_scene_prompts(script)[:n]
    paths   = []

    for i, prompt in enumerate(prompts):
        print(f"[ReelProducer] Imagen generating scene {i+1}/{n}...")
        try:
            r = requests.post(
                f"{IMAGEN_URL}?key={GEMINI_KEY}",
                json={
                    "instances":  [{"prompt": prompt}],
                    "parameters": {"sampleCount": 1, "aspectRatio": "9:16"},
                },
                timeout=30,
            )
            if r.status_code != 200:
                print(f"[ReelProducer] Imagen error {r.status_code}: {r.text[:120]}")
                continue
            predictions = r.json().get("predictions", [])
            if not predictions:
                continue
            img_b64 = predictions[0].get("bytesBase64Encoded", "")
            if not img_b64:
                continue
            out = os.path.join(tmp_dir, f"scene_{i}.png")
            with open(out, "wb") as f:
                f.write(base64.b64decode(img_b64))
            paths.append(out)
            time.sleep(0.5)   # gentle rate limit
        except Exception as e:
            print(f"[ReelProducer] Scene {i+1} failed: {e}")

    if not paths:
        print("[ReelProducer] Imagen returned no images — falling back to Pexels")
        return _pexels_fallback(script, tmp_dir, n)

    print(f"[ReelProducer] Imagen generated {len(paths)} scene images")
    return paths


def _pexels_fallback(script: dict, tmp_dir: str, n: int) -> list[str]:
    """Fall back to Pexels video clips if Imagen fails."""
    phrase = script.get("trend_phrase", script.get("phrase", "technology"))
    niche  = script.get("niche", "technology")
    query  = f"{phrase} {niche}"
    return fetch_broll_pexels(query, tmp_dir, n)


# Keep Pexels as fallback
def fetch_broll_pexels(query: str, tmp_dir: str, n_clips: int = 4) -> list[str]:
    url    = "https://api.pexels.com/videos/search"
    params = {"query": query, "per_page": n_clips + 2, "orientation": "portrait"}
    try:
        r = requests.get(url, headers={"Authorization": PEXELS_KEY}, params=params, timeout=15)
        if r.status_code != 200:
            return []
        videos = r.json().get("videos", [])
    except Exception:
        return []

    paths = []
    for i, v in enumerate(videos):
        if len(paths) >= n_clips:
            break
        files = v.get("video_files", [])
        link  = next(
            (f["link"] for q in ["hd","sd"] for f in files
             if f.get("quality") == q and f.get("height",0) >= 720),
            files[0]["link"] if files else None
        )
        if not link:
            continue
        out = os.path.join(tmp_dir, f"clip_{i}.mp4")
        try:
            resp = requests.get(link, stream=True, timeout=30)
            if resp.status_code == 200:
                with open(out, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                paths.append(out)
        except Exception:
            pass
    print(f"[ReelProducer] Pexels fallback: {len(paths)} clips")
    return paths


# ---------------------------------------------------------------------------
# 3. Thumbnail generation (Pillow)
# ---------------------------------------------------------------------------
GRADIENT_COLORS = [
    ((15, 15, 35), (60, 20, 80)),    # deep purple
    ((10, 30, 60), (20, 80, 120)),   # ocean blue
    ((40, 10, 10), (100, 30, 20)),   # deep red
    ((10, 40, 20), (20, 90, 50)),    # forest green
]

def _draw_gradient(img: Image.Image, top: tuple, bottom: tuple) -> None:
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(top[0] + t * (bottom[0] - top[0]))
        g = int(top[1] + t * (bottom[1] - top[1]))
        b = int(top[2] + t * (bottom[2] - top[2]))
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def _get_font(size: int) -> ImageFont.ImageFont:
    # Try system fonts in order
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_text_centered(draw, text, font, y, fill=(255,255,255), shadow=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw   = bbox[2] - bbox[0]
    x    = (W - tw) // 2
    if shadow:
        draw.text((x+6, y+6), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]


def generate_thumbnail(script: dict, out_path: str, color_idx: int = 0) -> str:
    thumbnail = script.get("thumbnail", {})
    title     = thumbnail.get("title", script.get("trend_phrase", "").title())
    subtitle  = thumbnail.get("subtitle", "")
    urgency   = script.get("urgency", "rising").upper()

    img  = Image.new("RGB", (W, H))
    top, bot = GRADIENT_COLORS[color_idx % len(GRADIENT_COLORS)]
    _draw_gradient(img, top, bot)
    draw = ImageDraw.Draw(img)

    # Urgency badge — top left, large enough to read
    badge_font  = _get_font(52)
    badge_color = (255, 80, 80) if urgency == "BREAKING" else (80, 220, 130)
    draw.text((80, 160), f"● {urgency}", font=badge_font, fill=badge_color)

    # Main title — very large, word-wrapped, centered vertically
    title_font = _get_font(160)
    words      = title.upper().split()
    # Split into lines of max 2 words for impact
    lines = []
    for i in range(0, len(words), 2):
        lines.append(" ".join(words[i:i+2]))

    line_h   = 190
    total_h  = len(lines) * line_h
    y_start  = (H - total_h) // 2 - 100

    for line in lines:
        _draw_text_centered(draw, line, title_font, y_start, fill=(255, 255, 255))
        y_start += line_h

    # Subtitle — medium, centered, below title
    if subtitle:
        sub_font = _get_font(72)
        sub_lines = textwrap.wrap(subtitle.upper(), width=18)
        y_sub = y_start + 60
        for line in sub_lines:
            _draw_text_centered(draw, line, sub_font, y_sub, fill=(200, 200, 200), shadow=False)
            y_sub += 90

    # Bottom branding strip
    brand_font = _get_font(52)
    draw.rectangle([(0, H - 140), (W, H)], fill=(0, 0, 0))
    _draw_text_centered(draw, "RATEFLUENCER", brand_font, H - 110, fill=(180, 180, 180), shadow=False)

    img.save(out_path, "JPEG", quality=95)
    print(f"[ReelProducer] Thumbnail saved → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# 4. Caption overlay helper
# ---------------------------------------------------------------------------
def _estimate_word_times(text: str, total_duration: float) -> list[tuple[str, float, float]]:
    """Rough word-level timing: distribute evenly weighted by word length."""
    words      = text.split()
    total_chars = sum(len(w) for w in words) or 1
    times, cursor = [], 0.0
    for w in words:
        duration = (len(w) / total_chars) * total_duration
        times.append((w, cursor, cursor + duration))
        cursor += duration
    return times


SUBTITLE_FONT    = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
SUBTITLE_FONT_SZ = 68       # big enough to read on phone
SUBTITLE_Y_POS   = 0.78     # 78% down the frame (above safe area)
SUBTITLE_MAX_W   = 900       # max pixels wide before wrapping
SUBTITLE_WORDS   = 4         # words per subtitle chunk


def _render_subtitle_frame(text: str, w: int, h: int) -> "np.ndarray":
    """Render a single subtitle as a transparent RGBA numpy frame."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    img  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(SUBTITLE_FONT, SUBTITLE_FONT_SZ)
    except Exception:
        font = ImageFont.load_default()

    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    tw   = bbox[2] - bbox[0]
    th   = bbox[3] - bbox[1]
    x    = (w - tw) // 2
    y    = int(h * SUBTITLE_Y_POS)

    # Semi-transparent pill background
    pad   = 20
    bg_x0 = x - pad
    bg_y0 = y - pad // 2
    bg_x1 = x + tw + pad
    bg_y1 = y + th + pad // 2
    draw.rounded_rectangle([bg_x0, bg_y0, bg_x1, bg_y1], radius=12,
                            fill=(0, 0, 0, 175))

    # White text with black stroke for contrast
    for ox, oy in [(-2,-2),(2,-2),(-2,2),(2,2)]:
        draw.text((x+ox, y+oy), text, font=font, fill=(0, 0, 0, 255))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    return np.array(img)


def _make_caption_clip(text: str, duration: float, w: int, h: int):
    """Burn subtitles as Pillow-rendered ImageClips — always visible, no font deps."""
    import numpy as np
    from moviepy.editor import ImageClip

    words     = text.split()
    chunks    = [" ".join(words[i:i+SUBTITLE_WORDS])
                 for i in range(0, len(words), SUBTITLE_WORDS)]
    chunk_dur = duration / max(len(chunks), 1)

    clips = []
    for i, chunk in enumerate(chunks):
        try:
            frame = _render_subtitle_frame(chunk, w, h)
            clip  = (ImageClip(frame, ismask=False)
                     .set_start(i * chunk_dur)
                     .set_duration(chunk_dur)
                     .set_position(("center", "center")))
            clips.append(clip)
        except Exception as e:
            print(f"[ReelProducer] Subtitle frame failed: {e}")
    return clips


# ---------------------------------------------------------------------------
# 4b. Animated background generator (fallback when no B-roll)
# ---------------------------------------------------------------------------
def _make_animated_bg(duration: float, color_idx: int = 0, fps: int = 10):
    """Generate a slow animated gradient background as ImageSequenceClip."""
    import numpy as np
    from moviepy.editor import ImageSequenceClip

    PALETTES = [
        [(15, 15, 35), (80, 20, 100)],   # purple
        [(10, 30, 60), (20, 90, 140)],   # blue
        [(40, 10, 10), (110, 35, 20)],   # red
        [(10, 40, 20), (20, 100, 55)],   # green
    ]
    top_rgb, bot_rgb = PALETTES[color_idx % len(PALETTES)]

    n_frames = max(int(duration * fps), 1)
    frames   = []

    for i in range(n_frames):
        t      = i / n_frames
        # Slow pulse: brightness oscillates ±15%
        pulse  = 0.85 + 0.15 * math.sin(2 * math.pi * t)
        frame  = np.zeros((H, W, 3), dtype=np.uint8)
        for y in range(H):
            blend = y / H
            r = int((top_rgb[0] + blend * (bot_rgb[0] - top_rgb[0])) * pulse)
            g = int((top_rgb[1] + blend * (bot_rgb[1] - top_rgb[1])) * pulse)
            b = int((top_rgb[2] + blend * (bot_rgb[2] - top_rgb[2])) * pulse)
            frame[y, :] = [min(r,255), min(g,255), min(b,255)]
        frames.append(frame)

    clip = ImageSequenceClip(frames, fps=fps)
    # Loop to fill full duration
    loops = math.ceil(duration / clip.duration)
    from moviepy.editor import concatenate_videoclips
    looped = concatenate_videoclips([clip] * loops).subclip(0, duration)
    return looped


# ---------------------------------------------------------------------------
# 5. MP4 Assembly via MoviePy
# ---------------------------------------------------------------------------
def assemble_reel(
    clip_paths:      list[str],
    audio_path:      str,
    caption_text:    str,
    out_path:        str,
    target_duration: int = 55,
) -> str:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip,
        concatenate_videoclips, ColorClip,
    )

    print(f"[ReelProducer] Assembling reel ({target_duration}s target)...")

    audio = AudioFileClip(audio_path)
    actual_duration = min(audio.duration, target_duration)

    CROSSFADE = 0.4   # seconds of crossfade between clips

    # Build video timeline with crossfade transitions
    video_clips = []
    total = 0.0
    for path in clip_paths:
        if total >= actual_duration:
            break
        try:
            vc      = VideoFileClip(path, audio=False)
            need    = actual_duration - total
            use_dur = min(vc.duration, need, 12)   # max 12s per clip
            segment = vc.subclip(0, use_dur).resize((W, H))
            # Crossfade in/out on every clip except the first
            if video_clips:
                segment = segment.crossfadein(CROSSFADE)
            video_clips.append(segment)
            total += use_dur - (CROSSFADE if video_clips else 0)
        except Exception as e:
            print(f"[ReelProducer] Skipping clip {path}: {e}")

    # Pad with animated background if not enough footage
    if total < actual_duration:
        pad = _make_animated_bg(actual_duration - total, color_idx=0)
        if video_clips:
            pad = pad.crossfadein(CROSSFADE)
        video_clips.append(pad)

    # Guard: never concatenate an empty list
    if not video_clips:
        print("[ReelProducer] No video clips — using animated background")
        video_clips = [_make_animated_bg(actual_duration, color_idx=0)]

    # Images don't support crossfade — plain concat
    has_images = any(Path(p).suffix.lower() in (".png",".jpg",".jpeg",".webp")
                     for p in clip_paths)
    if has_images:
        base = concatenate_videoclips(video_clips, method="compose")
    else:
        base = concatenate_videoclips(video_clips, method="compose", padding=-CROSSFADE)
    base = base.set_duration(actual_duration)

    # Captions
    caption_clips = _make_caption_clip(caption_text, actual_duration, W, H)
    layers = [base] + caption_clips

    final = CompositeVideoClip(layers, size=(W, H))
    final = final.set_audio(audio.subclip(0, actual_duration))

    final.write_videofile(
        out_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="4000k",
        preset="ultrafast",
        temp_audiofile=out_path.replace(".mp4", "_tmp_audio.m4a"),
        remove_temp=True,
        write_logfile=False,
        logger=None,
    )
    print(f"[ReelProducer] Reel saved → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def produce_reel(script: dict, color_idx: int = 0) -> dict:
    """
    Full pipeline: voiceover → B-roll → thumbnail → MP4.
    Returns dict with paths to all produced files.
    """
    phrase   = re.sub(r"[^a-z0-9]+", "_", script.get("trend_phrase", "reel").lower())
    tmp_dir  = tempfile.mkdtemp(prefix="reel_")

    try:
        # Paths
        audio_path     = os.path.join(tmp_dir, "voiceover.mp3")
        reel_path      = str(OUTPUT_DIR / f"reel_{phrase}.mp4")
        thumbnail_path = str(OUTPUT_DIR / f"thumbnail_{phrase}.jpg")

        # 1. Voiceover
        spoken_text = build_voiceover_script(script)
        generate_voiceover(spoken_text, audio_path)

        # 2. Scene images via Imagen 4 (falls back to Pexels if needed)
        clip_paths = generate_images_gemini(script, tmp_dir, n=4)

        # 3. Thumbnail
        generate_thumbnail(script, thumbnail_path, color_idx=color_idx)

        # 4. Assembly
        caption_text = build_voiceover_script(script)
        assemble_reel(
            clip_paths      = clip_paths,
            audio_path      = audio_path,
            caption_text    = caption_text,
            out_path        = reel_path,
            target_duration = script.get("reel_script", {}).get("estimated_duration_seconds", 55),
        )

        return {
            "trend_phrase":    script.get("trend_phrase"),
            "reel_path":       reel_path,
            "thumbnail_path":  thumbnail_path,
            "spoken_text":     spoken_text,
            "status":          "success",
        }

    except Exception as e:
        print(f"[ReelProducer] ERROR: {e}")
        return {
            "trend_phrase": script.get("trend_phrase"),
            "status":       "failed",
            "error":        str(e),
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def produce_all(scripts: list[dict]) -> list[dict]:
    results = []
    for i, s in enumerate(scripts):
        print(f"\n[ReelProducer] === Producing reel {i+1}/{len(scripts)}: {s.get('trend_phrase')} ===")
        r = produce_reel(s, color_idx=i)
        results.append(r)
    return results


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    scripts_file = "scripts_output.json"
    if os.path.exists(scripts_file):
        with open(scripts_file) as f:
            scripts = json.load(f)
        print(f"[ReelProducer] Loaded {len(scripts)} scripts from {scripts_file}")
    else:
        print("[ReelProducer] No scripts_output.json — using test stub")
        scripts = [
            {
                "trend_phrase": "ai agents",
                "trend_score":  87.4,
                "niche":        "artificial intelligence",
                "urgency":      "breaking",
                "content_angle": "Show exactly what an AI agent can do that a chatbot cannot.",
                "reel_script": {
                    "hook":     "AI agents just made 90% of SaaS tools obsolete. Here's why.",
                    "story":    "Last week OpenAI's Operator agent completed a full insurance claim without human input. That's not a demo, it's production. Agents don't just answer questions, they take actions: browse, click, fill forms, send emails. The shift from chatbot to agent is as big as mobile was to desktop.",
                    "insights": [
                        "Agents act autonomously — chatbots only respond",
                        "OpenAI Operator handled real insurance claims this week",
                        "By 2026 every enterprise workflow will have an agent layer",
                    ],
                    "cta": "Follow for daily AI breakdowns you won't find on the news.",
                    "estimated_duration_seconds": 50,
                },
                "instagram": {
                    "caption":  "AI agents just made chatbots look ancient. They don't just talk — they act. What job do you think agents will replace first?",
                    "hashtags": ["#AI", "#AIagents", "#futureofwork"],
                },
                "linkedin": {
                    "post":     "The chatbot era is over. AI agents are here.",
                    "hashtags": ["#AI", "#FutureOfWork"],
                },
                "thumbnail": {
                    "title":    "AI Agents Killed Chatbots",
                    "subtitle": "Here's What's Next",
                },
            }
        ]

    results = produce_all(scripts[:1])   # produce first reel by default

    print("\n[ReelProducer] === RESULTS ===")
    for r in results:
        print(f"  {r['trend_phrase']}: {r['status']}")
        if r["status"] == "success":
            print(f"    Reel:      {r['reel_path']}")
            print(f"    Thumbnail: {r['thumbnail_path']}")
        else:
            print(f"    Error: {r.get('error')}")

    with open("reels_output.json", "w") as f:
        json.dump(results, f, indent=2)
