"""
Real Influencer Scraper — YouTube Data API v3
==============================================

Fetches REAL influencer data from YouTube:
  - Channel name, description, subscriber count
  - Recent video titles (= what they actually post)
  - Engagement metrics (likes, comments, views)
  - Tags (= their hashtags)

This replaces synthetic profiles with real creator data so the
brand match uses actual posted content for semantic matching.

Setup:
  1. Go to https://console.cloud.google.com
  2. Create project → Enable "YouTube Data API v3"
  3. Create API key → add to .env as YOUTUBE_API_KEY=...
  4. Run: python scrape_real_influencers.py

The scraped profiles are merged with the existing synthetic dataset,
giving you a mix of real + synthetic influencers.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import os, json, time, math
import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()
YT_KEY = os.getenv("YOUTUBE_API_KEY", "")
YT_API = "https://www.googleapis.com/youtube/v3"

# ── Search queries per niche ───────────────────────────────────────────────

# 2 queries per niche × 3 results = 20×2×100 = 4000 units for search
# + ~20×3×3 = 180 units for channel/video details
# Total ≈ 4,200 units (well under 10,000/day limit)
NICHE_QUERIES = {
    "Fitness":               ["fitness workout gym training", "bodybuilding strength coach"],
    "Health & Wellness":     ["health wellness lifestyle channel", "natural holistic health"],
    "Yoga & Meditation":     ["yoga meditation mindfulness", "yoga teacher channel"],
    "Nutrition & Diet":      ["nutrition diet healthy eating", "meal prep dietitian"],
    "Fashion":               ["fashion style OOTD channel", "fashion influencer lookbook"],
    "Beauty & Skincare":     ["skincare makeup tutorial", "beauty influencer GRWM"],
    "Lifestyle Vlogging":    ["lifestyle vlog day in my life", "lifestyle creator routine"],
    "Parenting & Family":    ["parenting family channel", "mom vlog kids family"],
    "Travel":                ["travel vlog adventure", "budget travel channel"],
    "Food & Cooking":        ["cooking recipe channel", "food vlog restaurant review"],
    "Home Decor & Interior": ["home decor interior design", "home renovation DIY"],
    "DIY & Crafts":          ["DIY crafts tutorial channel", "woodworking handmade projects"],
    "Technology":            ["tech review gadget channel", "software coding tutorial"],
    "Gaming":                ["gaming channel commentary", "esports game review"],
    "Finance & Investing":   ["personal finance investing channel", "stock market financial literacy"],
    "Entrepreneurship":      ["entrepreneur startup channel", "business founder advice"],
    "Sports & Athletics":    ["sports training performance", "athlete fitness sports"],
    "Mental Health":         ["mental health awareness channel", "therapy anxiety wellness"],
    "Music & Dance":         ["music dance tutorial channel", "singer dancer performance"],
    "Comedy & Entertainment":["comedy funny entertainment", "stand up comedy vlog"],
}


def search_channels(query: str, max_results: int = 10) -> list[dict]:
    """Search YouTube for channels matching a query."""
    r = requests.get(f"{YT_API}/search", params={
        "key":        YT_KEY,
        "q":          query,
        "type":       "channel",
        "part":       "snippet",
        "maxResults": max_results,
        "order":      "relevance",
    }, timeout=15)
    if r.status_code != 200:
        print(f"  Search error {r.status_code}: {r.text[:100]}")
        return []
    return r.json().get("items", [])


def get_channel_details(channel_ids: list[str]) -> list[dict]:
    """Get subscriber count, view count, description for channel IDs."""
    if not channel_ids:
        return []
    r = requests.get(f"{YT_API}/channels", params={
        "key":  YT_KEY,
        "id":   ",".join(channel_ids),
        "part": "snippet,statistics,brandingSettings",
    }, timeout=15)
    if r.status_code != 200:
        return []
    return r.json().get("items", [])


def get_recent_videos_with_stats(channel_id: str, max_results: int = 10) -> list[dict]:
    """
    Get recent videos WITH actual like/comment/view counts.
    Two API calls:
      1. playlistItems → video IDs + titles
      2. videos.list   → per-video statistics (views, likes, comments)
    """
    # Step 1: get uploads playlist ID
    r = requests.get(f"{YT_API}/channels", params={
        "key":  YT_KEY,
        "id":   channel_id,
        "part": "contentDetails",
    }, timeout=15)
    if r.status_code != 200:
        return []
    items = r.json().get("items", [])
    if not items:
        return []
    playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Step 2: get video IDs + titles from playlist
    r2 = requests.get(f"{YT_API}/playlistItems", params={
        "key":        YT_KEY,
        "playlistId": playlist_id,
        "part":       "snippet",
        "maxResults": max_results,
    }, timeout=15)
    if r2.status_code != 200:
        return []
    playlist_items = r2.json().get("items", [])
    video_ids = [v["snippet"]["resourceId"]["videoId"]
                 for v in playlist_items
                 if v.get("snippet", {}).get("resourceId", {}).get("videoId")]

    if not video_ids:
        return playlist_items  # fallback: return items without stats

    # Step 3: get actual stats per video
    r3 = requests.get(f"{YT_API}/videos", params={
        "key":  YT_KEY,
        "id":   ",".join(video_ids),
        "part": "snippet,statistics",
    }, timeout=15)
    if r3.status_code != 200:
        return playlist_items  # fallback

    # Merge stats into the items
    stats_map = {v["id"]: v.get("statistics", {}) for v in r3.json().get("items", [])}
    enriched  = []
    for item in playlist_items:
        vid_id = item.get("snippet", {}).get("resourceId", {}).get("videoId", "")
        item["_stats"] = stats_map.get(vid_id, {})
        enriched.append(item)
    return enriched


def scrape_niche(niche: str, queries: list[str],
                 n_per_query: int = 3) -> list[dict]:
    """Scrape real influencer profiles for a niche."""
    print(f"\n[{niche}] Scraping...")
    channel_ids_seen = set()
    profiles = []

    for query in queries:
        results = search_channels(query, max_results=n_per_query)
        ids = [r["id"]["channelId"] for r in results if "channelId" in r.get("id", {})]
        ids = [i for i in ids if i not in channel_ids_seen]
        channel_ids_seen.update(ids)

        details = get_channel_details(ids)
        for ch in details:
            stats   = ch.get("statistics", {})
            snippet = ch.get("snippet", {})
            subs    = int(stats.get("subscriberCount", 0))
            views   = int(stats.get("viewCount", 0))
            vid_cnt = int(stats.get("videoCount", 1))

            if subs < 1000:  # skip tiny channels
                continue

            # Get recent videos WITH actual likes/comments/views
            channel_id = ch["id"]
            videos     = get_recent_videos_with_stats(channel_id, max_results=10)

            titles, tags = [], []
            v_views, v_likes, v_comments = [], [], []

            for v in videos:
                s = v.get("snippet", {})
                if s.get("title"):
                    titles.append(s["title"])
                tags.extend(s.get("tags", [])[:3])

                # Real per-video stats
                st = v.get("_stats", {})
                if st.get("viewCount"):    v_views.append(int(st["viewCount"]))
                if st.get("likeCount"):    v_likes.append(int(st["likeCount"]))
                if st.get("commentCount"): v_comments.append(int(st["commentCount"]))

            # Real engagement rate from actual video data
            avg_vid_views   = int(np.mean(v_views))   if v_views   else int(views / max(vid_cnt,1))
            avg_vid_likes   = int(np.mean(v_likes))   if v_likes   else 0
            avg_vid_comments= int(np.mean(v_comments))if v_comments else 0

            if avg_vid_views > 0:
                real_er = min(((avg_vid_likes + avg_vid_comments) / avg_vid_views) * 100, 20.0)
            else:
                real_er = min((views / max(vid_cnt,1) / max(subs,1)) * 100, 15.0)

            # Tier
            if   subs >= 5_000_000:  tier = "mega"
            elif subs >= 500_000:    tier = "macro"
            elif subs >= 100_000:    tier = "mid"
            elif subs >= 10_000:     tier = "micro"
            else:                    tier = "nano"

            country = snippet.get("country", "")

            profile = {
                "source":              "youtube",
                "platform":            "YouTube",
                "niche":               niche,
                "tier":                tier,
                "channel_id":          channel_id,
                "channel_url":         f"https://youtube.com/@{snippet.get('customUrl','').lstrip('@') or channel_id}",
                "username":            snippet.get("customUrl", channel_id).lstrip("@"),
                "full_name":           snippet.get("title", ""),
                "bio":                 snippet.get("description", "")[:400],
                "country":             country,
                "followers_count":     subs,
                "total_views":         views,
                "video_count":         vid_cnt,
                "engagement_rate":     round(real_er, 3),
                "avg_video_views":     avg_vid_views,
                "avg_likes":           avg_vid_likes,
                "avg_comments":        avg_vid_comments,
                "sample_captions":     json.dumps(titles[:5]),
                "top_hashtags":        json.dumps(list(dict.fromkeys(tags))[:8]),
            }
            profiles.append(profile)
            print(f"  ✓ {profile['full_name'][:38]:38} {subs:>10,} subs  "
                  f"avg_views={avg_vid_views:>8,}  likes={avg_vid_likes:>6,}  ER={real_er:.1f}%")
        time.sleep(0.5)

    return profiles


def profiles_to_dataset_rows(profiles: list[dict]) -> pd.DataFrame:
    """
    Convert scraped YouTube profiles to influencer_dataset.csv schema.
    Uses REAL stats wherever available; synthetic proxies only for missing fields.
    """
    rng = np.random.default_rng(99)
    rows = []

    for i, p in enumerate(profiles):
        subs     = p.get("followers_count", 10000)
        er       = p.get("engagement_rate", 3.0)
        true_er  = er * rng.uniform(0.90, 1.0)
        # Use real stats if available, fallback to estimates
        likes    = p.get("avg_likes",    int(subs * true_er / 100))
        comments = p.get("avg_comments", int(likes * 0.06))
        avg_views= p.get("avg_video_views", int(subs * 0.10))

        rows.append({
            "influencer_id":           f"YT{i+1:05d}",
            "username":                p.get("username", f"creator_{i}"),
            "full_name":               p.get("full_name", ""),
            "niche":                   p.get("niche", ""),
            "tier":                    p.get("tier", "micro"),
            "platform":                "YouTube",
            "followers_count":         subs,
            "following_count":         int(rng.integers(50, 500)),
            "posts_count":             p.get("video_count", 100),
            "engagement_rate":         round(er, 3),
            "true_engagement_rate":    round(true_er, 3),
            "avg_likes":               likes,
            "avg_comments":            comments,
            "avg_saves":               int(likes * 0.05),
            "video_view_rate":         round(float(rng.uniform(0.1, 0.4)), 4),
            "save_rate":               round(likes * 0.05 / max(subs,1), 6),
            "posts_per_week":          round(float(rng.uniform(1, 5)), 1),
            "is_verified":             subs >= 1_000_000,
            "is_fake_account":         False,  # real scraped accounts
            "real_followers_pct":      round(float(rng.uniform(0.75, 0.97)), 4),
            "suspicious_followers_pct":round(float(rng.uniform(0.01, 0.10)), 4),
            "bot_follower_pct":        round(float(rng.uniform(0.00, 0.05)), 4),
            "comment_spam_ratio":      round(float(rng.uniform(0.02, 0.12)), 4),
            "unique_commenters_ratio": round(float(rng.uniform(0.60, 0.95)), 4),
            "spike_ratio":             round(float(rng.uniform(1, 3)), 3),
            "er_vs_expected":          round(true_er - er, 4),
            "bio_completeness_score":  round(min(len(p.get("bio","")) / 200, 1.0), 4),
            "growth_rate_30d":         round(float(rng.uniform(0.01, 0.08)), 4),
            "growth_rate_90d":         round(float(rng.uniform(0.01, 0.06)), 4),
            "avg_daily_growth":        round(subs * 0.002, 2),
            "engagement_trend_30d":    round(float(rng.uniform(-0.2, 1.0)), 4),
            "posting_std_dev":         round(float(rng.uniform(0.5, 2.0)), 3),
            "followers_7d_delta":      int(subs * rng.uniform(0.001, 0.01)),
            "max_single_day_gain":     int(subs * rng.uniform(0.002, 0.02)),
            "top_5_hashtags":          p.get("top_hashtags", "[]"),
            "audience_interests":      json.dumps([p.get("niche","")]),
            "past_brand_categories":   "[]",
            "content_tone":            "Educational",
            "audience_age_group":      "25_34",
            "audience_country_top1":   "USA",
            "share_rate":              round(float(rng.uniform(0.002, 0.04)), 5),
            "comment_like_ratio":      round(comments / max(likes,1), 4),
            "sponsored_er_drop":       round(float(rng.uniform(0.0, 0.20)), 4),
            "avg_hashtags_per_post":   round(float(rng.uniform(3, 15)), 1),
            "collab_frequency":        round(float(rng.uniform(0, 2)), 2),
            "bio":                     p.get("bio", ""),
            "sample_captions":         p.get("sample_captions", "[]"),
            "sample_comments":         "[]",
            "authenticity_score":      round(float(rng.uniform(75, 95)), 1),
            "growth_score":            round(float(rng.uniform(40, 80)), 1),
            "ratefluencer_score":      round(float(rng.uniform(50, 85)), 1),
            "campaign_success_prob":   round(float(rng.uniform(0.55, 0.90)), 4),
            "brand_match_score":       round(float(rng.uniform(0.50, 0.90)), 4),
        })

    return pd.DataFrame(rows)


def main():
    if not YT_KEY:
        print("ERROR: YOUTUBE_API_KEY not set in .env")
        print("Get a free key at: https://console.cloud.google.com")
        print("  1. Create project")
        print("  2. Enable 'YouTube Data API v3'")
        print("  3. Create API key")
        print("  4. Add to .env: YOUTUBE_API_KEY=your_key_here")
        return

    dataset_path = os.path.join(os.path.dirname(__file__), "influencer_dataset.csv")
    all_profiles = []

    for niche, queries in NICHE_QUERIES.items():
        profiles = scrape_niche(niche, queries, n_per_query=5)
        all_profiles.extend(profiles)
        time.sleep(1)

    if not all_profiles:
        print("No profiles scraped.")
        return

    print(f"\nTotal real profiles scraped: {len(all_profiles)}")

    # Convert to dataset schema
    df_real = profiles_to_dataset_rows(all_profiles)

    # Merge with existing synthetic dataset
    if os.path.exists(dataset_path):
        df_existing = pd.read_csv(dataset_path)
        df_merged   = pd.concat([df_real, df_existing], ignore_index=True)
        print(f"Merged: {len(df_real)} real + {len(df_existing)} synthetic = {len(df_merged)} total")
    else:
        df_merged = df_real
        print(f"New dataset: {len(df_merged)} real profiles")

    df_merged.to_csv(dataset_path, index=False)
    print(f"Saved → {dataset_path}")

    # Update Excel
    xl = dataset_path.replace(".csv", ".xlsx")
    with pd.ExcelWriter(xl, engine="openpyxl") as writer:
        df_merged.to_excel(writer, sheet_name="All Influencers", index=False)
        df_real.to_excel(writer, sheet_name="Real (YouTube)", index=False)
        for niche in sorted(df_merged["niche"].unique()):
            df_merged[df_merged["niche"]==niche].to_excel(
                writer, sheet_name=niche[:31], index=False)
    print(f"Excel → {xl}")

    print("\nNext steps:")
    print("  python train_models.py   ← retrain on real data")
    print("  python -m uvicorn main:app --reload --port 8001")


if __name__ == "__main__":
    main()
