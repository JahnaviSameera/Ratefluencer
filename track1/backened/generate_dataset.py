"""
Generate influencer_dataset.csv + influencer_dataset.xlsx

Expanded dataset: 5000 profiles across 20 niches covering
fitness, health, wellness, lifestyle vlogging and more.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
from faker import Faker
import json, os

fake = Faker("en_IN")
rng  = np.random.default_rng(42)
N    = 5000

# ── 20 niches with realistic distribution weights ──────────────────────────
NICHES = [
    "Fitness", "Health & Wellness", "Yoga & Meditation", "Nutrition & Diet",
    "Fashion", "Beauty & Skincare", "Lifestyle Vlogging", "Parenting & Family",
    "Travel", "Food & Cooking", "Home Decor & Interior", "DIY & Crafts",
    "Technology", "Gaming", "Finance & Investing", "Entrepreneurship",
    "Sports & Athletics", "Mental Health", "Music & Dance", "Comedy & Entertainment",
]

NICHE_WEIGHTS = [
    0.09, 0.07, 0.05, 0.05,   # health cluster
    0.07, 0.06, 0.07, 0.04,   # lifestyle cluster
    0.05, 0.06, 0.03, 0.03,   # home/food cluster
    0.05, 0.04, 0.04, 0.04,   # tech/finance cluster
    0.04, 0.04, 0.04, 0.04,   # entertainment cluster
]

# Realistic engagement rate ranges per niche (higher for smaller/niche content)
NICHE_ER = {
    "Fitness":              (2.5, 9.0),
    "Health & Wellness":    (3.0, 10.0),
    "Yoga & Meditation":    (3.5, 11.0),
    "Nutrition & Diet":     (3.0, 9.5),
    "Fashion":              (1.5, 6.0),
    "Beauty & Skincare":    (2.0, 8.0),
    "Lifestyle Vlogging":   (2.0, 7.5),
    "Parenting & Family":   (3.5, 11.0),
    "Travel":               (2.0, 7.0),
    "Food & Cooking":       (2.5, 8.5),
    "Home Decor & Interior":(2.5, 8.0),
    "DIY & Crafts":         (3.0, 10.0),
    "Technology":           (1.5, 5.5),
    "Gaming":               (2.0, 7.0),
    "Finance & Investing":  (2.0, 7.5),
    "Entrepreneurship":     (2.5, 8.0),
    "Sports & Athletics":   (2.5, 8.5),
    "Mental Health":        (4.0, 12.0),
    "Music & Dance":        (3.0, 10.0),
    "Comedy & Entertainment":(3.5, 12.0),
}

TIERS     = ["nano","micro","mid","macro","mega"]
PLATFORMS = ["Instagram","YouTube","TikTok","LinkedIn","YouTube Shorts"]
COUNTRIES = ["India","USA","UK","UAE","Singapore","Canada","Australia","Germany","France","Brazil"]
TONES     = ["Educational","Inspirational","Humorous","Controversial","Promotional",
             "Storytelling","Motivational","Authentic","Expert","Casual"]

# ── Bio templates (credentialed vs generic) ────────────────────────────────
BIOS = {
    "Fitness":              ["NASM Certified PT | 10yr coaching | Specialising in strength & fat loss",
                             "Fitness journey 🏋️ | sharing workouts | not a trainer just vibing"],
    "Health & Wellness":    ["Functional Medicine Practitioner | Helping you heal naturally | 15K+ clients",
                             "Health enthusiast 🌿 | sharing what works for me | not medical advice"],
    "Yoga & Meditation":    ["500hr RYT Yoga Teacher | Mindfulness coach | Teaching since 2012",
                             "Yoga lover 🧘 | daily practice | beginner friendly content"],
    "Nutrition & Diet":     ["Registered Dietitian | MSc Nutrition | Evidence-based eating for real life",
                             "Foodie trying to eat healthy 🥗 | sharing meal plans | not a nutritionist"],
    "Fashion":              ["Fashion Stylist | Featured in Vogue India | Personal shopping & collab DMs open",
                             "Fashion lover 🌸 | OOTD daily | student budget friendly"],
    "Beauty & Skincare":    ["Licensed Esthetician | 12yr skin experience | Science-backed skincare routines",
                             "Skincare obsessed ✨ | testing products so you don't have to"],
    "Lifestyle Vlogging":   ["Full-time content creator | Life in Mumbai | Documenting the journey",
                             "Just living my life and filming it 📱 | daily vlogs"],
    "Parenting & Family":   ["Child Psychologist | Mom of 3 | Evidence-based parenting without the guilt",
                             "Mom life 👶 | real and unfiltered | no perfect parenting here"],
    "Travel":               ["Professional Travel Photographer | 70+ countries | Award-winning content",
                             "Solo backpacker ✈️ | budget travel tips | always planning next trip"],
    "Food & Cooking":       ["Michelin-trained Chef | 15yr kitchen experience | Recreating restaurant meals at home",
                             "Home cook sharing recipes 🍳 | not a chef just love food"],
    "Home Decor & Interior":["Interior Designer NCIDQ Certified | 200+ projects completed | Luxury to budget",
                             "Home decor obsessed 🏡 | renting and still making it cute"],
    "DIY & Crafts":         ["Professional Woodworker | YouTube Partner | Teaching practical skills",
                             "DIY hobbyist 🔨 | saving money by doing it myself | come learn with me"],
    "Technology":           ["Staff Engineer @Meta | 12yr SWE experience | Making tech accessible",
                             "Tech nerd 💻 | gadget reviews | just sharing what I find cool"],
    "Gaming":               ["Pro Esports Player @TeamVortex | Twitch Partner | 10K hours logged",
                             "Casual gamer 🎮 | variety content | just having fun"],
    "Finance & Investing":  ["CFA Charterholder | Portfolio Manager | Democratising financial literacy for India",
                             "Finance content | not financial advice | just sharing my journey 📈"],
    "Entrepreneurship":     ["3x Founder | Forbes 30U30 | Building in public | Exits & failures shared equally",
                             "Aspiring entrepreneur | startup stories | learning as I go 🚀"],
    "Sports & Athletics":   ["National Level Athlete | Certified S&C Coach | Performance-focused training",
                             "Sports fanatic ⚽ | training videos | amateur but passionate"],
    "Mental Health":        ["Licensed Therapist LMFT | 10yr clinical practice | Destigmatising mental health",
                             "Mental health advocate 🧠 | sharing my own journey | not a therapist"],
    "Music & Dance":        ["Classically trained pianist | Berklee grad | Teaching & performing since 2010",
                             "Music lover 🎵 | covers and originals | learning as I go"],
    "Comedy & Entertainment":["Stand-up comedian | Netflix special | Touring nationally",
                              "Just trying to make people laugh 😂 | relatable content | not professional comedian"],
}

# ── Comment templates ──────────────────────────────────────────────────────
SPAM = ["Nice!", "Great post!", "🔥🔥🔥", "Love this!", "Amazing!", "Follow me back",
        "Check my page", "😍😍", "Keep posting!", "W post", "So true!", "Facts 💯"]

REAL_COMMENTS = {
    "Fitness":              ["This fixed my form, been struggling for months!",
                             "What weights do you start beginners with?",
                             "3 weeks into your program and already seeing results!",
                             "Can you do a video on shoulder mobility? Mine is terrible"],
    "Health & Wellness":    ["Tried this and my energy levels are completely different",
                             "Which brand of supplements do you recommend?",
                             "Finally someone explaining this without selling something",
                             "My doctor said the same thing last week, glad I found this"],
    "Yoga & Meditation":    ["This 10-minute morning routine changed my whole day",
                             "Been trying to meditate for years, this finally clicked",
                             "Can beginners do this? I have zero flexibility",
                             "The way you explain alignment is so much clearer than other instructors"],
    "Nutrition & Diet":     ["Made your meal prep and ate well all week for the first time",
                             "What's a good substitute for someone who's lactose intolerant?",
                             "Finally a dietitian who isn't pushing cleanses or detoxes",
                             "Lost 4kg following your advice over 2 months"],
    "Fashion":              ["Where is that jacket from?? Need it immediately",
                             "This is the first styling video that actually works for my body type",
                             "Budget breakdown please! How much is the full outfit?",
                             "You made me realize I can rewear things I thought were boring"],
    "Beauty & Skincare":    ["My skin has never looked better since following your routine",
                             "Is this fragrance free? I have rosacea",
                             "Dermatologist confirmed what you said in your last video",
                             "The before and after at 3 months is insane"],
    "Lifestyle Vlogging":   ["Your editing style is so calming, I watch before bed",
                             "The way you handle anxiety in this video really resonated",
                             "How do you manage to film every day while working full time?",
                             "This vlog made me want to move to a new city"],
    "Parenting & Family":   ["This approach worked with my 4-year-old within 2 days",
                             "As a first-time dad this content is literally saving me",
                             "Finally parenting advice that doesn't make me feel guilty",
                             "My pediatrician recommended this exact same approach"],
    "Travel":               ["How much did you budget for this entire trip?",
                             "Going here in March, any must-dos that aren't touristy?",
                             "Your photography makes everywhere look magical",
                             "Booked my tickets because of this video, no regrets"],
    "Food & Cooking":       ["Made this last night and my family demanded I make it again",
                             "What can I substitute for heavy cream?",
                             "The technique tip at 2:40 completely changed how I cook",
                             "This recipe is better than the restaurant version honestly"],
    "Home Decor & Interior":["Recreated this on a ₹5K budget and it looks almost identical",
                             "What paint color is that? The undertones are perfect",
                             "Finally someone showing real-size apartments not mansions",
                             "My landlord approved this change and it transformed my space"],
    "DIY & Crafts":         ["Built this with my teenager as a weekend project, perfect",
                             "What wood do you recommend for beginners?",
                             "The jig setup at 8:20 is genius, never thought of that",
                             "Saved ₹15,000 doing this myself instead of hiring someone"],
    "Technology":           ["Saved me 2 hours every day, this is the tool I didn't know I needed",
                             "Does this work on M1 Mac too?",
                             "Your explanation is clearer than the official documentation",
                             "3 years in the industry and I learned something new here"],
    "Gaming":               ["That clutch at 4:30 was actually insane",
                             "What sensitivity settings are you running?",
                             "Been watching since 5K subs, the growth is well deserved",
                             "This strategy got me out of Gold after 3 seasons stuck"],
    "Finance & Investing":  ["Just opened my first index fund because of your videos",
                             "Can you cover NPS vs PPF comparison next?",
                             "The compound interest calculator changed how I think about saving",
                             "Wish I found this at 22 instead of 32"],
    "Entrepreneurship":     ["The failure story in this video is more valuable than most success ones",
                             "What CRM do you recommend for a 2-person team?",
                             "This is the most honest founder content I've found",
                             "Applied your cold outreach template and got 3 responses today"],
    "Sports & Athletics":   ["This drill improved my first touch more than 6 months of normal practice",
                             "What recovery protocol do you follow after match day?",
                             "Club coach shared this with our whole team",
                             "The mental side of performance you cover is underrated"],
    "Mental Health":        ["Cried watching this because I thought I was alone in feeling this",
                             "Showed this to my therapist and we discussed it for the whole session",
                             "The boundary-setting framework you shared literally changed my relationships",
                             "You made it okay to talk about this at work, thank you"],
    "Music & Dance":        ["Learned this song in 3 days using your breakdown method",
                             "What DAW do you use for production?",
                             "Your teaching style finally made music theory make sense",
                             "Been playing 5 years and still picking up new things from you"],
    "Comedy & Entertainment":["Watched this 4 times and laughed every single time",
                              "The callback at the end was so well set up",
                              "Showed this to my whole office, best laugh we've had all week",
                              "You understand my culture better than most creators honestly"],
}

CAPTIONS = {
    "Fitness":              ["The 3 exercises nobody tells you to do for lower back pain 🔥 Save this",
                             "I tracked every workout for 6 months — here's what the data showed 💪"],
    "Health & Wellness":    ["Your gut health affects your mood more than you think. Here's why 🌿",
                             "5 habits I quit that completely changed my energy levels ✨"],
    "Yoga & Meditation":    ["10-minute morning yoga that I do before I even check my phone 🧘",
                             "The breathing technique that stops anxiety in 3 minutes. Try it now 🌸"],
    "Nutrition & Diet":     ["I eat 2800 calories and stay lean — here's how I structure my meals 🥗",
                             "The protein myth that's holding your progress back (with the research) 💪"],
    "Fashion":              ["Styled 7 outfits from 5 pieces. This is the only capsule wardrobe guide you need 👗",
                             "Wore this outfit 3 different ways this week — zero repeat looks 🛍️"],
    "Beauty & Skincare":    ["My dermatologist-approved routine that cleared my acne in 6 weeks ✨",
                             "POV: You finally found the moisturizer that works for your oily skin 💆"],
    "Lifestyle Vlogging":   ["A week in my life as a 26-year-old in Mumbai — real and unfiltered 📱",
                             "I tried to be productive for 30 days straight. Here's what actually happened 🌟"],
    "Parenting & Family":   ["The toddler bedtime routine that actually works (took 3 years to figure out) 👶",
                             "Things I wish someone told me before becoming a parent 💕"],
    "Travel":               ["Hidden spots in Rajasthan that tourists never find 🗺️",
                             "10 days in Japan for ₹80,000 — complete budget breakdown ✈️"],
    "Food & Cooking":       ["Restaurant-quality butter chicken in 30 minutes 🍛 Recipe in comments",
                             "The knife technique that will make you 3x faster in the kitchen 🔪"],
    "Home Decor & Interior":["Transformed my 450sqft rental for ₹8,000 (landlord approved!) 🏡",
                             "The colour palette mistake everyone makes in small spaces 🎨"],
    "DIY & Crafts":         ["Built this floating desk for ₹2,000 instead of paying ₹15,000 🔨",
                             "The beginner woodworking project that teaches every essential skill 🪵"],
    "Technology":           ["The AI tool that saved me 10 hours last week (and it's free) 💻",
                             "Why senior engineers review code differently — the mental model 🧠"],
    "Gaming":               ["Ranked Silver to Diamond in 3 weeks using this one change 🎮",
                             "The settings pro players use that the algorithm won't show you 🏆"],
    "Finance & Investing":  ["How I built a ₹15L emergency fund in 2 years on a ₹40K salary 💰",
                             "The SIP mistake that costs you lakhs (and how to avoid it) 📈"],
    "Entrepreneurship":     ["The B2B cold email that got me 8 paying clients in 30 days 🚀",
                             "Building in public: Month 6 — real revenue, real struggles 📊"],
    "Sports & Athletics":   ["The 15-minute warm-up that cut my injury rate to zero ⚽",
                             "Why most athletes plateau — and the training variable they're missing 🏃"],
    "Mental Health":        ["The CBT technique my therapist taught me that I use every day 🧠",
                             "Boundaries are not walls — here's how I finally learned the difference 💚"],
    "Music & Dance":        ["Learn this chord progression and you can play 80% of pop songs 🎵",
                             "The dance break that went viral — here's the full tutorial 💃"],
    "Comedy & Entertainment":["POV: Monday morning vs Friday evening 😂",
                              "Things only people from Mumbai will understand 🤣"],
}


def tier_followers(tier):
    return {"nano":(1_000,9_999),"micro":(10_000,99_999),"mid":(100_000,499_999),
            "macro":(500_000,4_999_999),"mega":(5_000_000,50_000_000)}[tier]


def _gen_bio(niche, tier, is_fake, rng):
    templates = BIOS.get(niche, BIOS["Lifestyle Vlogging"])
    return templates[1] if (is_fake or tier == "nano") else templates[0]


def _gen_comments(niche, is_fake, rng):
    real = REAL_COMMENTS.get(niche, REAL_COMMENTS["Lifestyle Vlogging"])
    spam = SPAM
    if is_fake:
        return list(rng.choice(spam, 10, replace=True)) + list(rng.choice(real, 2, replace=True))
    return list(rng.choice(real, 8, replace=True)) + list(rng.choice(spam, 2, replace=True))


def _gen_captions(niche, rng):
    caps = CAPTIONS.get(niche, CAPTIONS["Lifestyle Vlogging"])
    return list(rng.choice(caps, 2, replace=True))


# ── Main generation loop ───────────────────────────────────────────────────
rows = []
for i in range(N):
    niche     = rng.choice(NICHES, p=NICHE_WEIGHTS)
    tier      = rng.choice(TIERS, p=[0.22, 0.34, 0.22, 0.13, 0.09])
    lo, hi    = tier_followers(tier)
    followers = int(rng.integers(lo, hi))
    platform  = rng.choice(PLATFORMS)
    is_fake   = rng.random() < 0.18

    er_lo, er_hi = NICHE_ER.get(niche, (2.0, 7.0))
    base_er   = rng.uniform(er_lo * 0.5, er_hi) if tier in ("macro","mega") else rng.uniform(er_lo, er_hi)
    true_er   = base_er * (0.4 if is_fake else 1.0)
    er_vs_exp = true_er - base_er

    # Authenticity signals
    real_pct    = rng.uniform(0.25,0.55) if is_fake else rng.uniform(0.65,0.98)
    susp_pct    = rng.uniform(0.20,0.45) if is_fake else rng.uniform(0.01,0.15)
    bot_pct     = rng.uniform(0.10,0.35) if is_fake else rng.uniform(0.00,0.08)
    spam_ratio  = rng.uniform(0.25,0.65) if is_fake else rng.uniform(0.01,0.12)
    uniq_ratio  = rng.uniform(0.10,0.40) if is_fake else rng.uniform(0.50,0.95)
    spike_ratio = rng.uniform(5,25)       if is_fake else rng.uniform(1,4)
    bio_score   = rng.uniform(0.20,0.60) if is_fake else rng.uniform(0.60,1.0)

    avg_likes    = int(followers * true_er / 100 * rng.uniform(0.8,1.2))
    avg_comments = int(avg_likes * rng.uniform(0.03,0.12))
    avg_saves    = int(avg_likes * rng.uniform(0.02,0.08))
    video_view_r = rng.uniform(0.05,0.40)
    save_r       = avg_saves / max(followers,1)

    # Growth signals
    gr_30d        = rng.uniform(-0.02,0.15) if not is_fake else rng.uniform(0.01,0.40)
    gr_90d        = rng.uniform(-0.01,0.12)
    avg_daily_gr  = followers * gr_30d / 30
    eng_trend_30d = rng.uniform(-0.5,1.5)
    post_std      = rng.uniform(0.1,2.5)
    posts_pw      = rng.uniform(1,14)
    f7d_delta     = int(followers * rng.uniform(-0.01,0.05))
    max_day_gain  = int(followers * rng.uniform(0.001,0.08))

    # Brand/audience
    hashtags  = json.dumps([f"#{niche.lower().replace(' ','').replace('&','')}{k}"
                            for k in rng.integers(1,200,5).tolist()])
    interests = json.dumps(rng.choice(NICHES, 3, replace=False).tolist())
    past_cats = json.dumps(rng.choice(NICHES, 2, replace=False).tolist())
    tone      = rng.choice(TONES)
    age_grp   = rng.choice(["13_17","18_24","25_34","35_44","45_54"])
    country   = rng.choice(COUNTRIES, p=[0.35,0.20,0.10,0.10,0.05,0.08,0.07,0.02,0.02,0.01])

    # Composite scores
    auth_score = float(np.clip(real_pct*60 + (1-bot_pct)*20 + bio_score*20, 0, 100))
    gr_score   = float(np.clip(gr_30d*300 + eng_trend_30d*20 + true_er*5, 0, 100))
    rf_score   = float(np.clip(auth_score*0.35 + gr_score*0.25 + true_er*5*0.20 + bio_score*20*0.20, 0, 100))
    camp_prob  = float(np.clip(rf_score/100 * rng.uniform(0.7,1.0), 0, 1))
    bm_score   = float(rng.uniform(0.3,0.95))

    rows.append({
        "influencer_id":           f"INF{i+1:05d}",
        "username":                fake.user_name(),
        "full_name":               fake.name(),
        "niche":                   niche,
        "tier":                    tier,
        "platform":                platform,
        "followers_count":         followers,
        "following_count":         int(rng.integers(100,5000)),
        "posts_count":             int(rng.integers(50,3000)),
        "engagement_rate":         round(base_er, 3),
        "true_engagement_rate":    round(true_er, 3),
        "avg_likes":               avg_likes,
        "avg_comments":            avg_comments,
        "avg_saves":               avg_saves,
        "video_view_rate":         round(video_view_r, 4),
        "save_rate":               round(save_r, 6),
        "posts_per_week":          round(posts_pw, 1),
        "is_verified":             bool(rng.random() < (0.6 if tier=="mega" else 0.15)),
        "is_fake_account":         bool(is_fake),
        # Authenticity features
        "real_followers_pct":      round(real_pct, 4),
        "suspicious_followers_pct":round(susp_pct, 4),
        "bot_follower_pct":        round(bot_pct, 4),
        "comment_spam_ratio":      round(spam_ratio, 4),
        "unique_commenters_ratio": round(uniq_ratio, 4),
        "spike_ratio":             round(spike_ratio, 3),
        "er_vs_expected":          round(er_vs_exp, 4),
        "bio_completeness_score":  round(bio_score, 4),
        # Growth features
        "growth_rate_30d":         round(gr_30d, 4),
        "growth_rate_90d":         round(gr_90d, 4),
        "avg_daily_growth":        round(avg_daily_gr, 2),
        "engagement_trend_30d":    round(eng_trend_30d, 4),
        "posting_std_dev":         round(post_std, 3),
        "followers_7d_delta":      f7d_delta,
        "max_single_day_gain":     max_day_gain,
        # Brand / audience
        "top_5_hashtags":          hashtags,
        "audience_interests":      interests,
        "past_brand_categories":   past_cats,
        "content_tone":            tone,
        "audience_age_group":      age_grp,
        "audience_country_top1":   country,
        # Extra features for ML models
        "share_rate":              round(float(rng.uniform(0.001,0.05)), 5),
        "comment_like_ratio":      round(avg_comments / max(avg_likes,1), 4),
        "sponsored_er_drop":       round(float(rng.uniform(0.0,0.40)), 4),
        "avg_hashtags_per_post":   round(float(rng.uniform(1,30)), 1),
        "collab_frequency":        round(float(rng.uniform(0,4)), 2),
        # Text fields for Gemini analysis
        "bio":                     _gen_bio(niche, tier, is_fake, rng),
        "sample_comments":         json.dumps(_gen_comments(niche, is_fake, rng)),
        "sample_captions":         json.dumps(_gen_captions(niche, rng)),
        # Composite scores (labels)
        "authenticity_score":      round(auth_score, 1),
        "growth_score":            round(gr_score, 1),
        "ratefluencer_score":      round(rf_score, 1),
        "campaign_success_prob":   round(camp_prob, 4),
        "brand_match_score":       round(bm_score, 4),
    })

df  = pd.DataFrame(rows)
out = os.path.join(os.path.dirname(__file__), "influencer_dataset.csv")
df.to_csv(out, index=False)

# Also export to Excel with per-niche sheets
xl_out = os.path.join(os.path.dirname(__file__), "influencer_dataset.xlsx")
with pd.ExcelWriter(xl_out, engine="openpyxl") as writer:
    # All influencers on first sheet
    df.to_excel(writer, sheet_name="All Influencers", index=False)
    # One sheet per niche
    for niche in NICHES:
        subset = df[df["niche"] == niche]
        safe   = niche[:31]  # Excel sheet name limit
        subset.to_excel(writer, sheet_name=safe, index=False)

print(f"\nDataset: {len(df)} influencers, {len(df.columns)} columns")
print(f"CSV  → {out}")
print(f"Excel → {xl_out}")
print(f"\nNiche breakdown:")
for n, c in df["niche"].value_counts().items():
    print(f"  {n:<28} {c:>4} profiles")
print(f"\nFake accounts: {df['is_fake_account'].sum()} ({df['is_fake_account'].mean()*100:.1f}%)")
print(f"Tiers: {df['tier'].value_counts().to_dict()}")
