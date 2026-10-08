/* Ratefluencer AI — API wrapper.
 * Tries the real backend at http://localhost:8000; on any network failure
 * it transparently serves the mock dataset and flips an "offline" flag that
 * the UI uses to show the backend-offline banner. */
(function () {
  const BASE = "http://localhost:8000";
  const state = { offline: false, probed: false };
  const listeners = [];
  function setOffline(v) {
    if (state.offline !== v) { state.offline = v; listeners.forEach((fn) => fn(v)); }
  }

  async function tryFetch(path, opts) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 8000);
    try {
      const res = await fetch(BASE + path, { ...opts, signal: ctrl.signal });
      clearTimeout(t);
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      setOffline(false);
      return data;
    } catch (e) {
      clearTimeout(t);
      setOffline(true);
      return null; // signal: use mock
    }
  }

  function delay(ms) { return new Promise((r) => setTimeout(r, ms)); }

  // ── mock implementations ──
  const D = () => window.RFData;

  function applyFilters(list, p = {}) {
    let out = list.slice();
    if (p.niche) out = out.filter((i) => i.niche === p.niche);
    if (p.tier) out = out.filter((i) => i.tier === p.tier);
    if (p.min_followers) out = out.filter((i) => i.followers_count >= p.min_followers);
    if (p.max_followers) out = out.filter((i) => i.followers_count <= p.max_followers);
    if (p.min_score) out = out.filter((i) => i.ratefluencer_score >= p.min_score);
    if (p.q) {
      const q = p.q.toLowerCase();
      out = out.filter((i) => i.username.toLowerCase().includes(q) || i.full_name.toLowerCase().includes(q));
    }
    const sort = p.sort_by || "ratefluencer_score";
    const key = {
      "ratefluencer_score": "ratefluencer_score", "followers": "followers_count",
      "engagement_rate": "engagement_rate", "authenticity": "authenticity_score",
      "growth": "growth_score",
    }[sort] || "ratefluencer_score";
    out.sort((a, b) => b[key] - a[key]);
    return out;
  }

  function scoreMatch(inf, brief) {
    let score = 0; const reasons = []; const warns = [];
    // niche (35)
    if (brief.niche && inf.niche === brief.niche) {
      score += 35; reasons.push("Exact niche match — " + titleCase(inf.niche));
    } else if (brief.niche) {
      score += 12; warns.push("Adjacent niche (" + titleCase(inf.niche) + ")");
    } else { score += 22; }
    // authenticity (25)
    const authPts = Math.round((inf.authenticity_score / 100) * 25);
    score += authPts;
    if (inf.authenticity_score >= 80) reasons.push("High authenticity (" + inf.authenticity_score + "/100)");
    else if (inf.authenticity_score < 60) warns.push("Authenticity below target (" + inf.authenticity_score + "/100)");
    // ratefluencer score (20)
    score += Math.round((inf.ratefluencer_score / 100) * 20);
    if (inf.ratefluencer_score >= 80) reasons.push("Top-tier Ratefluencer Score (" + inf.ratefluencer_score + ")");
    // engagement vs benchmark (10)
    if (inf.engagement_rate >= inf.benchmark) { score += 10; reasons.push("Engagement above niche benchmark"); }
    else { score += 4; warns.push("Engagement below niche benchmark"); }
    // keyword overlap (10)
    if (brief.keywords && brief.keywords.length) {
      const hay = (inf.top_hashtags.join(" ") + " " + inf.past_brand_categories.join(" ") + " " + inf.niche).toLowerCase();
      const hits = brief.keywords.filter((k) => k && hay.includes(k.toLowerCase()));
      if (hits.length) { score += Math.min(10, hits.length * 4); reasons.push("Matches keywords: " + hits.join(", ")); }
    } else { score += 5; }
    // audience age/country fit
    if (brief.target_age_group && inf.audience.age[brief.target_age_group] >= 25)
      reasons.push((inf.audience.age[brief.target_age_group]) + "% of audience is " + brief.target_age_group);
    if (brief.target_country && inf.audience.country[brief.target_country] >= 40)
      reasons.push("Strong " + brief.target_country + " audience (" + inf.audience.country[brief.target_country] + "%)");
    // follower window
    if (brief.min_followers && inf.followers_count < brief.min_followers) { warns.push("Below min follower target"); score -= 15; }
    if (brief.max_followers && inf.followers_count > brief.max_followers) { warns.push("Above max follower target"); score -= 8; }
    if (brief.min_authenticity && inf.authenticity_score < brief.min_authenticity) { warns.push("Below authenticity floor"); score -= 12; }

    score = Math.max(0, Math.min(100, Math.round(score + (inf.id % 5))));
    return { brand_match: score, match_reasons: reasons.slice(0, 5), match_warnings: warns.slice(0, 3) };
  }

  function titleCase(s) { return s.replace(/\b\w/g, (c) => c.toUpperCase()); }

  // ── public API ──
  const api = {
    BASE,
    onOfflineChange(fn) { listeners.push(fn); return () => { const i = listeners.indexOf(fn); if (i >= 0) listeners.splice(i, 1); }; },
    isOffline() { return state.offline; },

    async getStats() {
      const real = await tryFetch("/stats");
      if (real) return real;
      await delay(350);
      return D().STATS;
    },

    async getInfluencers(params = {}) {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => { if (v !== "" && v != null) qs.set(k, v); });
      const real = await tryFetch("/influencers?" + qs.toString());
      if (real) return real;
      await delay(300);
      const all = applyFilters(D().INFLUENCERS, params);
      const offset = params.offset || 0;
      const limit = params.limit || 20;
      return { total: all.length, items: all.slice(offset, offset + limit) };
    },

    async getInfluencer(id) {
      const real = await tryFetch("/influencers/" + id);
      if (real) return real;
      await delay(300);
      return D().INFLUENCERS.find((i) => i.id === Number(id)) || null;
    },

    async getGrowth(id) {
      const real = await tryFetch("/influencers/" + id + "/growth");
      if (real) return real;
      const inf = D().INFLUENCERS.find((i) => i.id === Number(id));
      return inf ? inf.growth : null;
    },

    async getAuth(id) {
      const real = await tryFetch("/influencers/" + id + "/auth");
      if (real) return real;
      const inf = D().INFLUENCERS.find((i) => i.id === Number(id));
      return inf ? inf.auth : null;
    },

    async search(brief) {
      const real = await tryFetch("/search", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(brief),
      });
      if (real) return real;
      await delay(700);
      let list = D().INFLUENCERS.slice();
      if (brief.niche) {
        // keep niche-matching first but include all for ranking
      }
      const ranked = list
        .map((inf) => ({ ...inf, ...scoreMatch(inf, brief) }))
        .sort((a, b) => b.brand_match - a.brand_match)
        .slice(0, brief.top_n || 12);
      return { brief, total: ranked.length, items: ranked };
    },

    simSeries(inf) { return D().simSeries(inf); },
  };

  window.RFApi = api;
})();
