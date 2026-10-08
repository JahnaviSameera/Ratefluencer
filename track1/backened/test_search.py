import sys, requests, json
sys.stdout.reconfigure(encoding="utf-8")

body = {
    "category": "trekking shoes",
    "product_description": "durable trekking shoes for mountain hiking outdoor adventures trail running",
    "campaign_goal": "Awareness",
    "niche": "Travel",
    "min_followers": 10000,
    "top_n": 8
}
r = requests.post("http://localhost:8001/search", json=body, timeout=30)
d = r.json()
print(f"Total results: {d.get('total')}")
for inf in d.get("items", []):
    print(f"  {inf['username'][:25]:25} niche={inf['niche'][:22]:22} match={inf['brand_match']}  followers={inf['followers_count']:,}")
