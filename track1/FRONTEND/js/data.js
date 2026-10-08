/* Ratefluencer AI — mock dataset for offline mode.
 * Mirrors the shape of GET /influencers and GET /influencers/{id}.
 * Core fields are authored; everything else is derived deterministically. */
(function () {
  // Tiny seeded PRNG so derived values are stable across reloads.
  function rng(seed) {
    let s = seed % 2147483647;
    if (s <= 0) s += 2147483646;
    return function () { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
  }

  const NICHE_TAGS = {
    "Fitness":               ["#Fitness","#Workout","#GymLife","#Strength","#FitIndia","#Bodybuilding","#Training"],
    "Health & Wellness":     ["#Health","#Wellness","#NaturalHealth","#Immunity","#Holistic","#Healing","#HealthyLife"],
    "Yoga & Meditation":     ["#Yoga","#Meditation","#Mindfulness","#YogaLife","#Breathwork","#Asana","#Peace"],
    "Nutrition & Diet":      ["#Nutrition","#HealthyEating","#MealPrep","#Protein","#Diet","#WeightLoss","#CleanEating"],
    "Fashion":               ["#Fashion","#OOTD","#Style","#Outfits","#Streetwear","#Trending","#FashionIndia"],
    "Beauty & Skincare":     ["#Skincare","#Makeup","#Beauty","#GRWM","#SkincareRoutine","#Glow","#Cosmetics"],
    "Lifestyle Vlogging":    ["#Vlog","#DayInMyLife","#Lifestyle","#MorningRoutine","#Productivity","#LifeStyle"],
    "Parenting & Family":    ["#Parenting","#MomLife","#DadLife","#Baby","#Family","#Kids","#Motherhood"],
    "Travel":                ["#Travel","#Adventure","#Hiking","#Trekking","#Explore","#Wanderlust","#TravelIndia"],
    "Food & Cooking":        ["#Food","#Recipe","#Cooking","#Foodie","#HomeCooked","#Chef","#FoodPhotography"],
    "Home Decor & Interior": ["#HomeDecor","#Interior","#HomeDesign","#RoomTour","#Aesthetic","#DIYHome"],
    "DIY & Crafts":          ["#DIY","#Crafts","#Handmade","#Woodworking","#HowTo","#Tutorial","#Making"],
    "Technology":            ["#Tech","#Gadgets","#Coding","#Developer","#Software","#TechReview","#Innovation"],
    "Gaming":                ["#Gaming","#Gamer","#Twitch","#Esports","#PCGaming","#GameReview","#Stream"],
    "Finance & Investing":   ["#Investing","#StockMarket","#PersonalFinance","#MutualFunds","#Wealth","#FinTech"],
    "Entrepreneurship":      ["#Startup","#Founder","#Entrepreneur","#BuildInPublic","#SaaS","#BusinessGrowth"],
    "Sports & Athletics":    ["#Sports","#Athlete","#Training","#Fitness","#Performance","#Running","#Outdoor"],
    "Mental Health":         ["#MentalHealth","#Anxiety","#SelfCare","#Therapy","#Mindfulness","#Healing"],
    "Music & Dance":         ["#Music","#Dance","#Singer","#Choreography","#Artist","#Cover","#Performance"],
    "Comedy & Entertainment":["#Comedy","#Funny","#Meme","#Entertainment","#Humor","#Relatable","#Viral"],
  };
  const NICHE_BRANDS = {
    "Fitness":               ["Sports Gear","Supplements","Gym Equipment","Activewear","Protein"],
    "Health & Wellness":     ["Supplements","Ayurveda","Organic","Pharma","Wellness Apps"],
    "Yoga & Meditation":     ["Yoga Mats","Wellness Apps","Supplements","Meditation Tools"],
    "Nutrition & Diet":      ["Health Food","Supplements","Meal Kits","Protein","Diet Apps"],
    "Fashion":               ["Clothing","Accessories","Footwear","Luxury","Fast Fashion"],
    "Beauty & Skincare":     ["Skincare","Cosmetics","Haircare","Beauty Devices","Fragrance"],
    "Lifestyle Vlogging":    ["Travel","Home","Productivity","Food Delivery","Lifestyle Apps"],
    "Parenting & Family":    ["Baby Products","EdTech","Toys","Family Apps","Insurance"],
    "Travel":                ["Airlines","Hotels","Trekking Gear","Adventure","Tourism"],
    "Food & Cooking":        ["Food Brands","Kitchen Tools","Delivery Apps","Restaurants","FMCG"],
    "Home Decor & Interior": ["Furniture","Home Brands","Paint","Decor","Smart Home"],
    "DIY & Crafts":          ["Tools","Hardware","Craft Supplies","Home Improvement"],
    "Technology":            ["Consumer Electronics","Apps","SaaS","Telecom","Gaming"],
    "Gaming":                ["Gaming Gear","Games","Streaming","Energy Drinks","Esports"],
    "Finance & Investing":   ["Fintech","Broking","Insurance","Banking","Wealth Management"],
    "Entrepreneurship":      ["SaaS","VC","B2B Tools","HR Tech","Business Services"],
    "Sports & Athletics":    ["Sports Gear","Footwear","Nutrition","Activewear","Equipment"],
    "Mental Health":         ["Wellness Apps","Books","Therapy Platforms","Supplements"],
    "Music & Dance":         ["Music Platforms","Instruments","Events","Apparel","Energy Drinks"],
    "Comedy & Entertainment":["OTT","FMCG","Beverages","Apparel","Events"],
  };

  function tierFor(f) {
    if (f >= 1_000_000) return "Mega";
    if (f >= 500_000) return "Macro";
    if (f >= 100_000) return "Mid-Tier";
    if (f >= 10_000) return "Micro";
    return "Nano";
  }

  // Authored seeds: id, username, full_name, niche, followers, er, verified, scores
  const SEEDS = [
    ["fitpriya",        "Priya Sharma",    "Fitness",               2_940_000, 6.8, true,  91, 88, 84, 89],
    ["yoga.with.asha",  "Asha Mehta",      "Yoga & Meditation",       845_000, 7.2, true,  87, 92, 78, 85],
    ["travelwithrohan", "Rohan Kapoor",    "Travel",                  162_000, 7.9, false, 82, 81, 90, 80],
    ["outdoor.ishaan",  "Ishaan Verma",    "Sports & Athletics",       38_500, 9.1, false, 76, 74, 88, 71],
    ["kavya.cooks",     "Kavya Iyer",      "Food & Cooking",        1_280_000, 5.9, true,  84, 79, 72, 82],
    ["healthytarun",    "Tarun Nair",      "Health & Wellness",       512_000, 6.1, true,  80, 83, 69, 77],
    ["gauri.glows",     "Gauri Deshpande", "Beauty & Skincare",        96_400, 7.8, false, 73, 68, 81, 70],
    ["nutridiaries",    "Aniket Joshi",    "Nutrition & Diet",         21_700, 8.4, false, 69, 71, 85, 66],
    ["moneywithmaya",   "Maya Reddy",      "Finance & Investing",   3_410_000, 4.2, true,  88, 90, 65, 86],
    ["fitlife.pooja",   "Pooja Bansal",    "Fitness",                 690_000, 5.6, true,  81, 85, 71, 79],
    ["mindful.sahil",   "Sahil Grover",    "Mental Health",           134_000, 8.8, false, 78, 76, 83, 74],
    ["hometours",       "Neha Jain",       "Home Decor & Interior",    47_900, 7.1, false, 72, 70, 87, 68],
    ["foundersfuel",    "Vikram Anand",    "Entrepreneurship",      1_050_000, 3.6, true,  83, 82, 74, 84],
    ["buildwithbhavna", "Bhavna Rao",      "Entrepreneurship",        318_000, 5.4, true,  79, 80, 86, 78],
    ["diysneha",        "Sneha Kulkarni",  "DIY & Crafts",             72_300, 7.4, false, 74, 73, 89, 72],
    ["techkaran",       "Karan Malhotra",  "Technology",               14_200, 9.6, false, 66, 64, 91, 63],
    ["vlogwithkunal",   "Kunal Bose",      "Lifestyle Vlogging",    2_100_000, 4.5, true,  86, 84, 70, 83],
    ["meghna.makes",    "Meghna Pillai",   "Lifestyle Vlogging",      430_000, 6.0, true,  80, 87, 82, 79],
    ["parentingnaina",  "Naina Sethi",     "Parenting & Family",       88_700, 7.7, false, 75, 72, 88, 73],
    ["comedyravi",      "Ravi Menon",      "Comedy & Entertainment",    9_800,10.2, false, 63, 60, 90, 61],
    ["fashion.bhushan", "Bhushan Patel",   "Fashion",               1_620_000, 3.4, true,  82, 81, 64, 85],
    ["dancestreet",     "Sara Khan",       "Music & Dance",           276_000, 5.0, true,  78, 79, 75, 80],
    ["gaming.deepak",   "Deepak Shah",     "Gaming",                   58_100, 6.6, false, 71, 47, 80, 69],
    ["traveladitya",    "Aditya Gupta",    "Travel",                   11_500, 8.0, false, 64, 38, 84, 60],
  ];

  // niche benchmark ER (%) for the engagement-rate color comparison
  const NICHE_BENCHMARK = {
    "Fitness": 5.5, "Health & Wellness": 5.2, "Yoga & Meditation": 5.8,
    "Nutrition & Diet": 5.0, "Fashion": 3.5, "Beauty & Skincare": 4.8,
    "Lifestyle Vlogging": 4.5, "Parenting & Family": 5.5, "Travel": 4.2,
    "Food & Cooking": 5.0, "Home Decor & Interior": 4.5, "DIY & Crafts": 5.2,
    "Technology": 3.8, "Gaming": 4.5, "Finance & Investing": 4.0,
    "Entrepreneurship": 4.2, "Sports & Athletics": 5.0, "Mental Health": 6.0,
    "Music & Dance": 5.5, "Comedy & Entertainment": 6.2,
  };

  function enrich(seed, idx) {
    const [username, full_name, niche, followers_count, engagement_rate, is_verified, ratefluencer_score, authenticity_score, growth_score, campaign_success_score] = seed;
    const r = rng((idx + 7) * 9173);
    const tier = tierFor(followers_count);
    const benchmark = NICHE_BENCHMARK[niche];

    const avg_likes = Math.round(followers_count * (engagement_rate / 100) * (0.82 + r() * 0.12));
    const avg_comments = Math.round(avg_likes / (28 + r() * 18));
    const avg_video_views = Math.round(followers_count * (0.25 + r() * 0.4));
    const posts_per_week = +(2 + r() * 7).toFixed(1);
    const true_engagement_rate = +(engagement_rate * (0.74 + r() * 0.16)).toFixed(2);
    const save_rate = +(0.6 + r() * 2.4).toFixed(2);
    const share_rate = +(0.3 + r() * 1.6).toFixed(2);

    // 30d growth delta — scaled to followers, sign mostly positive but a couple negative
    const growthPct = (growth_score - 55) / 1000 + (r() - 0.35) * 0.02; // fraction over 30d
    const followers_30d_delta = Math.round(followers_count * growthPct);
    const engagement_trend_30d = +(((r() - 0.4) * 1.6)).toFixed(3); // slope, %/30d-ish

    // Authenticity factor breakdown (0-100 oriented; some are "lower=better")
    const a = authenticity_score;
    const real_followers_pct = Math.min(99, Math.round(a + r() * 6));
    const bot_followers_pct = Math.max(0, Math.round((100 - a) * (0.5 + r() * 0.3)));
    const suspicious_followers_pct = Math.max(0, Math.round((100 - a) * (0.3 + r() * 0.25)));
    const comment_spam_ratio = +(Math.max(0.5, (100 - a) * (0.12 + r() * 0.1))).toFixed(1);
    const unique_commenters_pct = Math.min(98, Math.round(a + r() * 4 - 2));
    const spike_ratio = +(1 + (100 - a) / 60 + r() * 0.4).toFixed(2);
    const er_vs_benchmark = +((engagement_rate - benchmark)).toFixed(2);
    const profile_completeness = Math.min(100, Math.round(80 + a / 6 + r() * 8));

    let verdict = "Trusted";
    if (a < 45) verdict = "High Risk"; else if (a < 70) verdict = "Caution";

    // Growth predictions
    const d30 = Math.round(followers_count * growthPct);
    const d60 = Math.round(followers_count * growthPct * 1.92);
    const d90 = Math.round(followers_count * growthPct * 2.78);
    const er30 = +(engagement_rate + engagement_trend_30d).toFixed(2);
    const er60 = +(engagement_rate + engagement_trend_30d * 1.8).toFixed(2);
    const growth_drivers = [
      { factor: "Posting consistency", value: posts_per_week >= 5 ? "Strong" : "Moderate" },
      { factor: "Reels velocity", value: (0.4 + r() * 0.5).toFixed(2) + "x niche avg" },
      { factor: "Audience retention", value: Math.round(60 + r() * 30) + "%" },
      { factor: "Hashtag reach", value: Math.round(followers_count * (0.1 + r() * 0.3)).toLocaleString("en-IN") + " / post" },
      { factor: "Collaboration rate", value: Math.round(1 + r() * 5) + " /mo" },
    ];

    // Audience fit
    const ageBase = [25 + r() * 20, 35 + r() * 20, 12 + r() * 10, 5 + r() * 8];
    const ageSum = ageBase.reduce((x, y) => x + y, 0);
    const audience_age = {
      "18-24": Math.round(ageBase[0] / ageSum * 100),
      "25-34": Math.round(ageBase[1] / ageSum * 100),
      "35-44": Math.round(ageBase[2] / ageSum * 100),
      "45+": Math.round(ageBase[3] / ageSum * 100),
    };
    const cBase = [60 + r() * 25, 8 + r() * 10, 4 + r() * 6, 5 + r() * 6];
    const cSum = cBase.reduce((x, y) => x + y, 0);
    const audience_country = {
      "India": Math.round(cBase[0] / cSum * 100),
      "USA": Math.round(cBase[1] / cSum * 100),
      "UAE": Math.round(cBase[2] / cSum * 100),
      "UK": Math.round(cBase[3] / cSum * 100),
    };

    const tags = NICHE_TAGS[niche];
    const top_hashtags = tags.slice(0, 5 + Math.round(r() * 2));
    const past_brand_categories = NICHE_BRANDS[niche].slice(0, 3 + Math.round(r() * 2));

    return {
      id: idx + 1, username, full_name, niche, tier, followers_count, engagement_rate,
      is_verified, ratefluencer_score, authenticity_score, growth_score, campaign_success_score,
      benchmark, avg_likes, avg_comments, avg_video_views, posts_per_week,
      true_engagement_rate, save_rate, share_rate, followers_30d_delta, engagement_trend_30d,
      auth: {
        verdict,
        factors: [
          { key: "Real Followers", value: real_followers_pct, unit: "%", good: real_followers_pct >= 75, higherBetter: true },
          { key: "Bot Followers", value: bot_followers_pct, unit: "%", good: bot_followers_pct <= 15, higherBetter: false },
          { key: "Comment Spam Ratio", value: comment_spam_ratio, unit: "%", good: comment_spam_ratio <= 6, higherBetter: false },
          { key: "Unique Commenters", value: unique_commenters_pct, unit: "%", good: unique_commenters_pct >= 70, higherBetter: true },
          { key: "Spike Ratio", value: spike_ratio, unit: "x", good: spike_ratio <= 1.8, higherBetter: false },
          { key: "ER vs Benchmark", value: er_vs_benchmark, unit: "%", good: er_vs_benchmark >= 0, higherBetter: true, signed: true },
          { key: "Profile Completeness", value: profile_completeness, unit: "%", good: profile_completeness >= 80, higherBetter: true },
          { key: "Suspicious Followers", value: suspicious_followers_pct, unit: "%", good: suspicious_followers_pct <= 12, higherBetter: false },
        ],
      },
      growth: {
        followers: { "30d": d30, "60d": d60, "90d": d90 },
        er: { "30d": er30, "60d": er60 },
        drivers: growth_drivers,
      },
      audience: { age: audience_age, country: audience_country },
      top_hashtags, past_brand_categories,
    };
  }

  const INFLUENCERS = SEEDS.map(enrich);

  // ── Chart simulation helpers (no separate chart API) ──
  function dayLabels(n) {
    const out = []; const now = new Date();
    for (let i = n - 1; i >= 0; i--) {
      const d = new Date(now); d.setDate(now.getDate() - i);
      out.push(d.toLocaleDateString("en-IN", { day: "numeric", month: "short" }));
    }
    return out;
  }
  function simSeries(inf) {
    // Handle both numeric ids (demo) and string ids like "YT00124" / "INF00045"
    const idNum = typeof inf.id === "number" ? inf.id
                : parseInt((inf.id || "1").replace(/\D/g, ""), 10) || 1;
    const r = rng((idNum + 3) * 5501);
    const labels = dayLabels(30);
    const startF = inf.followers_count - inf.followers_30d_delta;
    const followers = [], er = [], likes = [], comments = [];
    for (let i = 0; i < 30; i++) {
      const t = i / 29;
      const f = Math.round(startF + inf.followers_30d_delta * t + (r() - 0.5) * inf.followers_count * 0.004);
      const e = +(inf.engagement_rate - inf.engagement_trend_30d * (1 - t) + (r() - 0.5) * 0.6).toFixed(2);
      const l = Math.round(inf.avg_likes * (1 + (r() - 0.5) * 0.3));
      const c = Math.round(inf.avg_comments * (1 + (r() - 0.5) * 0.3));
      followers.push({ date: labels[i], value: f });
      er.push({ date: labels[i], value: Math.max(0.5, e) });
      likes.push({ date: labels[i], value: Math.max(0, l) });
      comments.push({ date: labels[i], value: Math.max(0, c) });
    }
    return { followers, er, likes, comments };
  }

  // ── Stats summary ──
  function buildStats() {
    const total = INFLUENCERS.length;
    const avgER = INFLUENCERS.reduce((s, i) => s + i.engagement_rate, 0) / total;
    const avgAuth = INFLUENCERS.reduce((s, i) => s + i.authenticity_score, 0) / total;
    const avgScore = INFLUENCERS.reduce((s, i) => s + i.ratefluencer_score, 0) / total;
    const byNiche = {};
    INFLUENCERS.forEach((i) => { byNiche[i.niche] = (byNiche[i.niche] || 0) + 1; });
    const niche_breakdown = Object.entries(byNiche)
      .map(([niche, count]) => ({ niche, count }))
      .sort((a, b) => b.count - a.count);
    return {
      total_influencers: total,
      avg_engagement_rate: +avgER.toFixed(2),
      avg_authenticity: +avgAuth.toFixed(1),
      avg_ratefluencer_score: +avgScore.toFixed(1),
      total_reach: INFLUENCERS.reduce((s, i) => s + i.followers_count, 0),
      niche_breakdown,
    };
  }

  window.RFData = { INFLUENCERS, STATS: buildStats(), simSeries, tierFor, NICHE_BENCHMARK };
})();
