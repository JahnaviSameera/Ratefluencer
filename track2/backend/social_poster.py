"""
Ratefluencer — Social Media Poster
=====================================

Direct posting to Instagram and LinkedIn using their official APIs.

Setup (add to .env):
  INSTAGRAM_ACCESS_TOKEN=...    Long-lived Page Access Token from Meta Developer
  INSTAGRAM_USER_ID=...         Your Instagram Business/Creator account ID
  LINKEDIN_ACCESS_TOKEN=...     OAuth 2.0 access token from LinkedIn Developer
  LINKEDIN_PERSON_URN=...       urn:li:person:XXXXXX  (your LinkedIn person ID)
  SERVER_BASE_URL=...           Public URL of this server (for image hosting)
                                e.g. https://yourapp.com or ngrok URL
                                Leave blank on localhost — image will be skipped

How to get tokens:
  Instagram: developers.facebook.com → Create App → Instagram Basic Display
             or use Graph API Explorer to get a long-lived token
  LinkedIn:  developer.linkedin.com → Create App → OAuth 2.0 → r_liteprofile + w_member_social
"""
from __future__ import annotations
import os, json, base64, tempfile, time
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

IG_TOKEN       = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
IG_USER_ID     = os.getenv("INSTAGRAM_USER_ID", "")
LI_TOKEN       = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LI_PERSON_URN  = os.getenv("LINKEDIN_PERSON_URN", "")
SERVER_BASE_URL = os.getenv("SERVER_BASE_URL", "").rstrip("/")

IG_API = "https://graph.facebook.com/v19.0"
LI_API = "https://api.linkedin.com"

OUTPUT_DIR = Path("reels_output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Image hosting helper
# ---------------------------------------------------------------------------
def _save_image_locally(image_url_or_b64: str, filename: str = "post_image.png") -> str | None:
    """
    Save image to reels_output/ and return a public URL using SERVER_BASE_URL.
    Returns None if SERVER_BASE_URL not configured (localhost).
    """
    out_path = OUTPUT_DIR / filename

    if image_url_or_b64.startswith("data:"):
        # Base64 data URL (from Gemini/Imagen)
        header, b64data = image_url_or_b64.split(",", 1)
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(b64data))
    elif image_url_or_b64.startswith("http"):
        # External URL (Pexels etc.) — download it
        r = requests.get(image_url_or_b64, timeout=20)
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(r.content)
        else:
            return None
    else:
        return None

    if SERVER_BASE_URL:
        return f"{SERVER_BASE_URL}/files/{filename}"
    return None   # localhost — can't host image for IG


# ---------------------------------------------------------------------------
# Instagram Graph API
# ---------------------------------------------------------------------------
def post_to_instagram(
    caption:    str,
    hashtags:   list[str],
    image_url:  str | None = None,
) -> dict:
    """
    Post to Instagram Business/Creator account via Graph API.

    Steps:
      1. Create a media container (image or reel)
      2. Publish the container

    Returns: { success, post_id, permalink, error }
    """
    if not IG_TOKEN or not IG_USER_ID:
        return {
            "success": False,
            "error": "INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID not set in .env",
            "setup_url": "https://developers.facebook.com/docs/instagram-api/getting-started",
        }

    # Build full caption with hashtags
    hashtag_str = " ".join(hashtags) if hashtags else ""
    full_caption = f"{caption}\n\n{hashtag_str}".strip()

    # Step 1: Create media container
    container_params: dict = {
        "caption":       full_caption,
        "access_token":  IG_TOKEN,
    }

    # Resolve image URL
    public_image_url = None
    if image_url:
        if image_url.startswith("http") and not image_url.startswith("data:"):
            public_image_url = image_url   # Pexels URL — use directly
        else:
            public_image_url = _save_image_locally(image_url, "ig_post.png")

    if public_image_url:
        container_params["image_url"] = public_image_url
        container_params["media_type"] = "IMAGE"
    else:
        # Text-only post not supported on IG — use a placeholder note
        if not image_url:
            print("[Instagram] No image provided — posting caption only via carousel workaround")
        else:
            print("[Instagram] Image URL not publicly accessible (localhost) — skipping image")
        # Instagram requires an image; without SERVER_BASE_URL we can't post images
        return {
            "success": False,
            "error":   (
                "Instagram requires a publicly accessible image URL. "
                "Set SERVER_BASE_URL in .env to your deployed server or ngrok URL."
            ),
        }

    print(f"[Instagram] Creating media container...")
    r1 = requests.post(f"{IG_API}/{IG_USER_ID}/media",
                       params=container_params, timeout=20)
    if r1.status_code != 200:
        return {"success": False, "error": f"Container creation failed: {r1.text[:200]}"}

    creation_id = r1.json().get("id")
    if not creation_id:
        return {"success": False, "error": "No creation_id in response"}

    print(f"[Instagram] Publishing container {creation_id}...")
    time.sleep(2)   # IG recommends a small delay before publish

    r2 = requests.post(
        f"{IG_API}/{IG_USER_ID}/media_publish",
        params={"creation_id": creation_id, "access_token": IG_TOKEN},
        timeout=20,
    )
    if r2.status_code != 200:
        return {"success": False, "error": f"Publish failed: {r2.text[:200]}"}

    post_id = r2.json().get("id", "")
    permalink = f"https://www.instagram.com/p/{post_id}/" if post_id else ""

    print(f"[Instagram] Posted! ID: {post_id}")
    return {
        "success":   True,
        "post_id":   post_id,
        "permalink": permalink,
        "platform":  "instagram",
    }


# ---------------------------------------------------------------------------
# LinkedIn API
# ---------------------------------------------------------------------------
def post_to_linkedin(
    text:      str,
    hashtags:  list[str] | None = None,
    image_url: str | None = None,
) -> dict:
    """
    Post to LinkedIn using the UGC Posts API.
    Supports text-only and image posts.

    Returns: { success, post_id, post_url, error }
    """
    if not LI_TOKEN or not LI_PERSON_URN:
        return {
            "success": False,
            "error": "LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN not set in .env",
            "setup_url": "https://www.linkedin.com/developers/apps",
        }

    headers = {
        "Authorization":  f"Bearer {LI_TOKEN}",
        "Content-Type":   "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202310",
    }

    # Append hashtags to text
    if hashtags:
        tag_str = " ".join(hashtags)
        full_text = f"{text}\n\n{tag_str}"
    else:
        full_text = text

    # Try to upload image if provided
    media_asset = None
    if image_url:
        try:
            media_asset = _upload_linkedin_image(image_url, headers)
        except Exception as e:
            print(f"[LinkedIn] Image upload failed ({e}) — posting text only")

    # Build post body
    if media_asset:
        body = {
            "author":         LI_PERSON_URN,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary":    {"text": full_text},
                    "shareMediaCategory": "IMAGE",
                    "media": [{
                        "status":      "READY",
                        "description": {"text": ""},
                        "media":       media_asset,
                        "title":       {"text": ""},
                    }],
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }
    else:
        body = {
            "author":         LI_PERSON_URN,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary":    {"text": full_text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

    print(f"[LinkedIn] Posting{'with image' if media_asset else ' (text only)'}...")
    r = requests.post(f"{LI_API}/v2/ugcPosts",
                      headers=headers, json=body, timeout=20)

    if r.status_code not in (200, 201):
        return {"success": False, "error": f"LinkedIn API error {r.status_code}: {r.text[:200]}"}

    post_id = r.headers.get("x-restli-id", r.json().get("id", ""))
    # LinkedIn post URL format
    post_url = f"https://www.linkedin.com/feed/update/{post_id}/" if post_id else \
               "https://www.linkedin.com/feed/"

    print(f"[LinkedIn] Posted! ID: {post_id}")
    return {
        "success":  True,
        "post_id":  post_id,
        "post_url": post_url,
        "platform": "linkedin",
    }


def _upload_linkedin_image(image_url: str, headers: dict) -> str | None:
    """Upload image to LinkedIn and return the asset URN."""
    # Step 1: Register upload
    reg = requests.post(
        f"{LI_API}/v2/assets?action=registerUpload",
        headers=headers,
        json={
            "registerUploadRequest": {
                "recipes":          ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner":            LI_PERSON_URN,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier":       "urn:li:userGeneratedContent",
                }],
            }
        },
        timeout=15,
    )
    if reg.status_code != 200:
        raise Exception(f"Register failed: {reg.status_code}")

    upload_url = reg.json()["value"]["uploadMechanism"] \
                    ["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"] \
                    ["uploadUrl"]
    asset      = reg.json()["value"]["asset"]

    # Step 2: Upload image bytes
    if image_url.startswith("data:"):
        _, b64data = image_url.split(",", 1)
        img_bytes  = base64.b64decode(b64data)
    else:
        r = requests.get(image_url, timeout=20)
        img_bytes = r.content

    up = requests.put(upload_url,
                      headers={"Authorization": headers["Authorization"],
                               "Content-Type": "application/octet-stream"},
                      data=img_bytes, timeout=30)
    if up.status_code not in (200, 201):
        raise Exception(f"Upload failed: {up.status_code}")

    return asset


# ---------------------------------------------------------------------------
# Credential check helpers
# ---------------------------------------------------------------------------
def instagram_configured() -> bool:
    return bool(IG_TOKEN and IG_USER_ID)

def linkedin_configured() -> bool:
    return bool(LI_TOKEN and LI_PERSON_URN)

def get_config_status() -> dict:
    return {
        "instagram": {
            "configured": instagram_configured(),
            "needs":      [] if instagram_configured() else
                          ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID"],
            "setup_url":  "https://developers.facebook.com/docs/instagram-api/getting-started",
        },
        "linkedin": {
            "configured": linkedin_configured(),
            "needs":      [] if linkedin_configured() else
                          ["LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_URN"],
            "setup_url":  "https://www.linkedin.com/developers/apps",
        },
        "image_hosting": {
            "configured": bool(SERVER_BASE_URL),
            "server_url": SERVER_BASE_URL or None,
            "note": "Required for Instagram image posts. Set SERVER_BASE_URL in .env.",
        },
    }
