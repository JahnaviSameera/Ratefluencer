/* Ratefluencer AI — Screen 2: Discovery Dashboard + shared InfluencerRow */
(function () {
  const { useState, useEffect, useCallback } = React;
  const RF = window.RF;
  const { L, formatFollowers, fmtPct, fmtScore, scoreHex, scoreLabel, titleCase, NicheBadge, TierBadge, Avatar, AuthChip, Skeleton } = RF;
  const api = window.RFApi;

  const NICHES = [
    "Fitness", "Health & Wellness", "Yoga & Meditation", "Nutrition & Diet",
    "Fashion", "Beauty & Skincare", "Lifestyle Vlogging", "Parenting & Family",
    "Travel", "Food & Cooking", "Home Decor & Interior", "DIY & Crafts",
    "Technology", "Gaming", "Finance & Investing", "Entrepreneurship",
    "Sports & Athletics", "Mental Health", "Music & Dance", "Comedy & Entertainment",
  ];
  const TIERS = ["Nano", "Micro", "Mid-Tier", "Macro", "Mega"];
  const SORTS = [
    { v: "ratefluencer_score", l: "Creator Score" }, { v: "followers", l: "Followers" },
    { v: "engagement_rate", l: "Engagement Rate" }, { v: "authenticity", l: "Audience Quality" }, { v: "growth", l: "Growth" },
  ];

  // ── localStorage collab helper ────────────────────────────────────────────
  function addToCollab(inf, activeCampaignId) {
    if (!activeCampaignId) return false;
    var campaigns = [];
    try { campaigns = JSON.parse(localStorage.getItem('rf_campaigns') || '[]'); } catch(e) {}
    var camp = campaigns.find(function(c) { return c.id === activeCampaignId; });
    if (!camp) return false;
    var collabs = [];
    try { collabs = JSON.parse(localStorage.getItem('rf_collabs') || '[]'); } catch(e) {}
    var key = String(inf.id) + '_' + activeCampaignId;
    if (collabs.find(function(c) { return c.id === key; })) return false; // already added
    collabs.unshift({
      id: key,
      creatorId: String(inf.id),
      creator: {
        id: inf.id, username: inf.username, full_name: inf.full_name,
        niche: inf.niche, followers_count: inf.followers_count,
        ratefluencer_score: inf.ratefluencer_score, tier: inf.tier, is_verified: inf.is_verified,
      },
      campaignId: activeCampaignId,
      campaignName: camp.name,
      status: 'Shortlisted',
      date: new Date().toISOString(),
    });
    localStorage.setItem('rf_collabs', JSON.stringify(collabs));
    return true;
  }

  // ── shared row used by Discovery + Search results ──
  function InfluencerRow({ inf, rank, onView, showMatch, inCompare, onToggleCompare, activeCampaignId }) {
    const [added, setAdded] = React.useState(false);
    const erUp = inf.engagement_rate >= inf.benchmark;
    const sc = scoreHex(inf.ratefluencer_score);
    return React.createElement("div", { className: "rf-row", onClick: () => onView(inf), style: { position: "relative" } },
      // Compare checkbox — absolute positioned top-left, doesn't affect row layout
      onToggleCompare && React.createElement("div", {
        onClick: (e) => { e.stopPropagation(); onToggleCompare(inf); },
        style: {
          position: "absolute", top: 8, left: 6, zIndex: 2,
          width: 18, height: 18, borderRadius: 4, cursor: "pointer",
          border: "2px solid " + (inCompare ? "#7c3aed" : "rgba(255,255,255,0.2)"),
          background: inCompare ? "#7c3aed" : "rgba(15,23,42,0.10)",
          display: "flex", alignItems: "center", justifyContent: "center",
        }
      }, inCompare ? React.createElement(L.Check, { size: 11, color: "#fff" }) : null),
      React.createElement("div", { className: "rf-row-rank" }, "#" + rank),
      React.createElement(Avatar, { name: inf.full_name, niche: inf.niche, size: 50, username: inf.username }),
      React.createElement("div", { className: "rf-row-id" },
        React.createElement("div", { className: "rf-row-user" }, "@" + inf.username,
          inf.is_verified ? React.createElement(L.BadgeCheck, { size: 15, className: "rf-verified" }) : null),
        React.createElement("div", { className: "rf-row-name" }, inf.full_name),
        React.createElement("div", { className: "rf-row-badges" },
          React.createElement(NicheBadge, { niche: inf.niche }), React.createElement(TierBadge, { tier: inf.tier })),
      ),
      React.createElement("div", { className: "rf-row-metric" },
        React.createElement("div", { className: "rf-metric-value" }, formatFollowers(inf.followers_count)),
        React.createElement("div", { className: "rf-metric-label" }, "Followers")),
      React.createElement("div", { className: "rf-row-metric" },
        React.createElement("div", { className: "rf-metric-value", style: { color: erUp ? "#16a34a" : "#dc2626" } },
          fmtPct(inf.engagement_rate), React.createElement(erUp ? L.TrendingUp : L.TrendingDown, { size: 14, style: { marginLeft: 3 } })),
        React.createElement("div", { className: "rf-metric-label" }, "Engagement")),
      React.createElement("div", { className: "rf-row-metric" },
        React.createElement("div", { className: "rf-metric-value rf-grow" }, fmtScore(inf.growth_score)),
        React.createElement("div", { className: "rf-metric-label" }, "Growth")),
      React.createElement("div", { className: "rf-row-auth" }, React.createElement(AuthChip, { score: inf.authenticity_score })),
      React.createElement("div", { className: "rf-row-score" },
        React.createElement("div", { className: "rf-bigscore", style: { color: sc } }, fmtScore(inf.ratefluencer_score)),
        React.createElement("div", { className: "rf-bigscore-label", style: { color: sc } }, scoreLabel(inf.ratefluencer_score)),
      ),
      showMatch && inf.brand_match != null ? React.createElement("div", { className: "rf-row-match" },
        React.createElement("div", { className: "rf-match-head" },
          React.createElement("span", null, "Brand match"), React.createElement("b", null, inf.brand_match + "%")),
        React.createElement("div", { className: "rf-match-track" },
          React.createElement("div", { className: "rf-match-fill", style: { width: inf.brand_match + "%" } })),
      ) : null,
      activeCampaignId ? React.createElement("button", {
        className: "rf-btn rf-row-cta",
        onClick: (e) => {
          e.stopPropagation();
          var ok = addToCollab(inf, activeCampaignId);
          if (ok || !added) setAdded(true);
          setTimeout(function() { setAdded(false); }, 2000);
        },
        style: {
          background: added ? "#f0fdf4" : "rgba(22,163,74,0.10)",
          color:  added ? "#16a34a" : "#16a34a",
          border: "1px solid " + (added ? "#bbf7d0" : "rgba(22,163,74,0.25)"),
          display: "flex", alignItems: "center", gap: 5,
          padding: "6px 11px", borderRadius: 8, fontSize: 12, fontWeight: 700,
          cursor: "pointer", whiteSpace: "nowrap", transition: "all 0.2s",
        }
      }, added ? React.createElement(L.Check, { size: 13 }) : React.createElement(L.Plus, { size: 13 }),
         added ? "Added!" : "Add") : null,
      React.createElement("button", { className: "rf-btn rf-btn-soft rf-row-cta", onClick: (e) => { e.stopPropagation(); onView(inf); } },
        "View profile", React.createElement(L.ArrowRight, { size: 15 })),
    );
  }

  function RowSkeleton() {
    return React.createElement("div", { className: "rf-row rf-row-skel" },
      React.createElement(Skeleton, { w: 28, h: 16 }),
      React.createElement(Skeleton, { w: 50, h: 50, r: 50 }),
      React.createElement("div", { style: { flex: 1 } }, React.createElement(Skeleton, { w: "55%", h: 16 }), React.createElement(Skeleton, { w: "35%", h: 11, style: { marginTop: 8 } })),
      React.createElement(Skeleton, { w: 60, h: 30 }), React.createElement(Skeleton, { w: 60, h: 30 }),
      React.createElement(Skeleton, { w: 48, h: 40 }), React.createElement(Skeleton, { w: 96, h: 36, r: 10 }),
    );
  }

  function Pill({ active, onClick, children, color }) {
    return React.createElement("button", {
      className: "rf-pill" + (active ? " rf-pill-on" : ""), onClick,
      style: active && color ? { background: color + "22", borderColor: color + "66", color } : null,
    }, children);
  }

  function DiscoverScreen({ resultsData, brief, onView, onClearResults, activeCampaignId }) {
    const isResults = !!resultsData;
    const [niche, setNiche] = useState("");
    const [tier, setTier] = useState("");
    const [sortBy, setSortBy] = useState("ratefluencer_score");
    const [q, setQ] = useState("");
    const [page, setPage] = useState(0);
    const [loading, setLoading] = useState(!isResults);
    const [error, setError] = useState(null);
    const [data, setData] = useState({ items: [], total: 0 });

    // ── Compare state ──
    const [compareList, setCompareList] = useState([]);  // max 3
    const [showCompare, setShowCompare] = useState(false);
    const toggleCompare = (inf) => {
      setCompareList(prev => {
        const exists = prev.find(i => i.id === inf.id);
        if (exists) return prev.filter(i => i.id !== inf.id);
        if (prev.length >= 3) return prev; // max 3
        return [...prev, inf];
      });
    };
    const PER = 20;

    const fetchList = useCallback(() => {
      setLoading(true); setError(null);
      api.getInfluencers({ niche, tier, sort_by: sortBy, q, limit: PER, offset: page * PER })
        .then((res) => { setData(res); setLoading(false); })
        .catch(() => { setError("Couldn’t load influencers."); setLoading(false); });
    }, [niche, tier, sortBy, q, page]);

    useEffect(() => { if (!isResults) fetchList(); }, [fetchList, isResults]);
    useEffect(() => { setPage(0); }, [niche, tier, sortBy, q]);

    // results mode: filter/sort client-side
    let items, total;
    if (isResults) {
      let list = resultsData.items.slice();
      if (niche) list = list.filter((i) => i.niche === niche);
      if (tier) list = list.filter((i) => i.tier === tier);
      if (q) { const s = q.toLowerCase(); list = list.filter((i) => i.username.toLowerCase().includes(s) || i.full_name.toLowerCase().includes(s)); }
      // results keep brand_match order unless a different sort chosen
      if (sortBy !== "ratefluencer_score") {
        const key = { followers: "followers_count", engagement_rate: "engagement_rate", authenticity: "authenticity_score", growth: "growth_score" }[sortBy];
        if (key) list.sort((a, b) => b[key] - a[key]);
      } else { list.sort((a, b) => b.brand_match - a.brand_match); }
      total = list.length; items = list.slice(page * PER, page * PER + PER);
    } else { items = data.items; total = data.total; }

    const start = total === 0 ? 0 : page * PER + 1;
    const end = Math.min(total, page * PER + items.length);
    const maxPage = Math.max(0, Math.ceil(total / PER) - 1);

    return React.createElement("div", { className: "rf-discover" },
      // header
      React.createElement("div", { className: "rf-disc-head" },
        React.createElement("div", null,
          React.createElement("h1", { className: "rf-page-title" }, isResults ? "Ranked for your brief" : "Discover creators"),
          React.createElement("p", { className: "rf-page-sub" }, isResults
            ? "Scored on brand fit, authenticity & engagement against your campaign."
            : "Browse every creator in the index. Filter, sort and open a profile to go deep."),
        ),
        isResults ? React.createElement("button", { className: "rf-btn rf-btn-ghost", onClick: onClearResults },
          React.createElement(L.X, { size: 15 }), "Clear search") : null,
      ),
      isResults && brief ? React.createElement("div", { className: "rf-brief-chip" },
        React.createElement(L.Target, { size: 14 }),
        React.createElement("span", null, brief.category || "Campaign"),
        brief.niche ? React.createElement("span", { className: "rf-brief-sep" }, titleCase(brief.niche)) : null,
        brief.campaign_goal ? React.createElement("span", { className: "rf-brief-sep" }, brief.campaign_goal) : null,
        (brief.min_authenticity ? React.createElement("span", { className: "rf-brief-sep" }, "Auth ≥ " + brief.min_authenticity) : null),
      ) : null,

      // Budget & ROI panel — always visible
      React.createElement(BudgetPanel, { brief }),

      // filter bar
      React.createElement("div", { className: "rf-filterbar" },
        React.createElement("div", { className: "rf-searchbox" },
          React.createElement(L.Search, { size: 16, className: "rf-searchbox-icon" }),
          React.createElement("input", { className: "rf-input rf-searchinput", placeholder: "Search by username or name", value: q, onChange: (e) => setQ(e.target.value) }),
          q ? React.createElement("button", { className: "rf-searchbox-clear", onClick: () => setQ("") }, React.createElement(L.X, { size: 14 })) : null,
        ),
        React.createElement("div", { className: "rf-filtergroup" },
          React.createElement("span", { className: "rf-filter-label" }, React.createElement(L.SlidersHorizontal, { size: 14 }), "Niche"),
          React.createElement(Pill, { active: !niche, onClick: () => setNiche("") }, "All"),
          NICHES.map((n) => React.createElement(Pill, { key: n, active: niche === n, onClick: () => setNiche(niche === n ? "" : n), color: RF.nicheHex(n) }, RF.NICHE_SHORT[n])),
        ),
        React.createElement("div", { className: "rf-filtergroup" },
          React.createElement("span", { className: "rf-filter-label" }, "Tier"),
          React.createElement(Pill, { active: !tier, onClick: () => setTier("") }, "All"),
          TIERS.map((t) => React.createElement(Pill, { key: t, active: tier === t, onClick: () => setTier(tier === t ? "" : t) }, t)),
        ),
        React.createElement("div", { className: "rf-sortwrap" },
          React.createElement("span", { className: "rf-filter-label" }, React.createElement(L.ArrowDownWideNarrow, { size: 14 }), "Sort"),
          React.createElement("div", { className: "rf-selectwrap" },
            React.createElement("select", { className: "rf-input rf-select rf-select-sm", value: sortBy, onChange: (e) => setSortBy(e.target.value) },
              SORTS.map((s) => React.createElement("option", { key: s.v, value: s.v }, s.l))),
            React.createElement(L.ChevronDown, { size: 15, className: "rf-select-caret" })),
        ),
      ),

      // list
      error ? React.createElement("div", { className: "rf-errorcard rf-errorcard-wide" },
          React.createElement(L.WifiOff, { size: 22 }),
          React.createElement("div", { className: "rf-errorcard-title" }, error),
          React.createElement("button", { className: "rf-btn rf-btn-ghost", onClick: fetchList }, React.createElement(L.RotateCcw, { size: 15 }), "Retry"))
        : loading ? React.createElement("div", { className: "rf-rowlist" }, [0, 1, 2, 3, 4, 5].map((i) => React.createElement(RowSkeleton, { key: i })))
        : items.length === 0 ? React.createElement("div", { className: "rf-empty" },
            React.createElement("div", { className: "rf-empty-art" }, React.createElement(L.SearchX, { size: 30 })),
            React.createElement("div", { className: "rf-empty-title" }, "No creators match these filters"),
            React.createElement("p", { className: "rf-empty-sub" }, "Try widening the niche or clearing the search box."),
            React.createElement("button", { className: "rf-btn rf-btn-soft", onClick: () => { setNiche(""); setTier(""); setQ(""); } }, "Reset filters"))
        : React.createElement("div", { className: "rf-rowlist" },
            items.map((inf, idx) => React.createElement(InfluencerRow, {
              key: inf.id, inf, rank: page * PER + idx + 1, onView, showMatch: isResults,
              inCompare: compareList.some(c => c.id === inf.id),
              onToggleCompare: toggleCompare,
              activeCampaignId,
            })),
          ),

      // ── floating compare bar ──
      compareList.length > 0 && React.createElement("div", { style: {
        position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)",
        background: "#ffffff", border: "1px solid rgba(124,108,255,0.4)",
        borderRadius: 14, padding: "14px 20px", zIndex: 999,
        display: "flex", alignItems: "center", gap: 16,
        boxShadow: "0 8px 32px rgba(15,23,42,0.14)", backdropFilter: "blur(12px)",
      } },
        React.createElement("span", { style: { color: "#a78bfa", fontSize: 13, fontWeight: 700 } },
          compareList.length === 1 ? "Select 1 more to compare" : `${compareList.length} selected`),
        React.createElement("div", { style: { display: "flex", gap: 8 } },
          compareList.map(inf => React.createElement("div", { key: inf.id, style: {
            padding: "4px 10px", borderRadius: 6, background: "rgba(124,108,255,0.2)",
            color: "#c4b5fd", fontSize: 12,
          } }, "@" + inf.username)),
        ),
        compareList.length >= 2 && React.createElement("button", {
          onClick: () => setShowCompare(true),
          style: {
            padding: "9px 18px", borderRadius: 8, border: "none",
            background: "linear-gradient(135deg,#7c3aed,#06b6d4)",
            color: "#fff", fontSize: 13, fontWeight: 700, cursor: "pointer",
          }
        }, "⚡ Compare Now"),
        React.createElement("button", {
          onClick: () => setCompareList([]),
          style: { background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 18 }
        }, "✕"),
      ),

      // ── comparison modal ──
      showCompare && React.createElement(CompareModal, {
        influencers: compareList,
        brief: brief || {},
        onClose: () => setShowCompare(false),
      }),

      // pagination
      !loading && !error && items.length > 0 ? React.createElement("div", { className: "rf-pagination" },
        React.createElement("span", { className: "rf-page-count" }, "Showing ", React.createElement("b", null, start + "–" + end), " of ", React.createElement("b", null, total)),
        React.createElement("div", { className: "rf-page-btns" },
          React.createElement("button", { className: "rf-btn rf-btn-soft", disabled: page === 0, onClick: () => setPage((p) => Math.max(0, p - 1)) },
            React.createElement(L.ChevronLeft, { size: 16 }), "Prev"),
          React.createElement("span", { className: "rf-page-num" }, (page + 1) + " / " + (maxPage + 1)),
          React.createElement("button", { className: "rf-btn rf-btn-soft", disabled: page >= maxPage, onClick: () => setPage((p) => Math.min(maxPage, p + 1)) },
            "Next", React.createElement(L.ChevronRight, { size: 16 })),
        ),
      ) : null,
    );
  }

  // ── Compare Modal ────────────────────────────────────────────────────────
  function CompareModal({ influencers, brief, onClose }) {
    const [result, setResult] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [category, setCategory] = React.useState(brief?.category || "");

    async function runCompare() {
      setLoading(true);
      try {
        const res = await fetch(`${window.RFApi.BASE}/api/compare`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            influencer_ids: influencers.map(i => i.id),
            category: category || brief?.category || "",
            product_description: brief?.product_description || "",
            campaign_goal: brief?.campaign_goal || "Awareness",
          }),
        });
        const data = await res.json();
        setResult(data);
      } catch(e) { setResult(null); }
      setLoading(false);
    }

    React.useEffect(() => { if (category || brief?.category) runCompare(); }, []);

    return React.createElement("div", {
      onClick: onClose,
      style: { position:"fixed", inset:0, zIndex:1000, background:"rgba(0,0,0,0.75)",
               display:"flex", alignItems:"center", justifyContent:"center", padding:24 }
    },
      React.createElement("div", { onClick: e => e.stopPropagation(), style: {
        background:"#ffffff", borderRadius:16, padding:24, width:"100%", maxWidth:720,
        maxHeight:"85vh", overflowY:"auto", border:"1px solid rgba(124,108,255,0.3)",
      } },
        React.createElement("div", { style:{ display:"flex", justifyContent:"space-between", marginBottom:16 } },
          React.createElement("h2", { style:{ color:"#0f172a", fontSize:18, fontWeight:700 } }, "⚡ Influencer Comparison"),
          React.createElement("button", { onClick: onClose, style:{ background:"none", border:"none", color:"#64748b", cursor:"pointer", fontSize:20 } }, "✕"),
        ),

        // Campaign input
        !result && React.createElement("div", { style:{ display:"flex", gap:10, marginBottom:16 } },
          React.createElement("input", { className:"rf-input", placeholder:"Your product/campaign (e.g. yoga mats)",
            value: category, onChange: e => setCategory(e.target.value), style:{ flex:1 } }),
          React.createElement("button", { onClick: runCompare, style:{
            padding:"8px 16px", borderRadius:8, background:"linear-gradient(135deg,#7c3aed,#06b6d4)",
            color:"#fff", border:"none", cursor:"pointer", fontWeight:700,
          } }, "Compare"),
        ),

        // Influencer stats side-by-side
        React.createElement("div", { style:{ display:"grid", gridTemplateColumns: `repeat(${influencers.length}, 1fr)`, gap:12, marginBottom:16 } },
          influencers.map(inf => React.createElement("div", { key: inf.id, style:{
            background: result?.winner?.id === inf.id ? "rgba(124,108,255,0.12)" : "rgba(15,23,42,0.04)",
            border: result?.winner?.id === inf.id ? "1px solid rgba(124,108,255,0.4)" : "1px solid rgba(15,23,42,0.06)",
            borderRadius:10, padding:14,
          } },
            result?.winner?.id === inf.id && React.createElement("div", { style:{ fontSize:11, color:"#a78bfa", fontWeight:700, marginBottom:6 } }, "🏆 WINNER"),
            React.createElement("div", { style:{ color:"#0f172a", fontWeight:700, marginBottom:4 } }, "@" + inf.username),
            React.createElement("div", { style:{ fontSize:12, color:"#94a3b8", marginBottom:10 } }, inf.niche),
            [["Followers", inf.followers_count?.toLocaleString()],
             ["Engagement", (inf.engagement_rate||0) + "%"],
             ["Quality", (inf.authenticity_score||0) + "/100"],
             ["Score", (inf.ratefluencer_score||0) + "/100"]].map(([k,v]) =>
              React.createElement("div", { key:k, style:{ display:"flex", justifyContent:"space-between", fontSize:12, marginBottom:4 } },
                React.createElement("span", { style:{ color:"#64748b" } }, k),
                React.createElement("span", { style:{ color:"#0f172a", fontWeight:600 } }, v),
              )
            ),
          ))
        ),

        loading ? React.createElement("div", { style:{ textAlign:"center", color:"#94a3b8", padding:20 } },
          React.createElement("div", { className:"rf-spinner", style:{ margin:"0 auto 8px" } }),
          "Analyzing your shortlist…")
        : result && React.createElement("div", null,
            // Winner reason
            result.winner?.reason && React.createElement("div", { style:{
              background:"rgba(124,108,255,0.1)", border:"1px solid rgba(124,108,255,0.2)",
              borderRadius:10, padding:14, marginBottom:12,
            } },
              React.createElement("div", { style:{ fontSize:11, color:"#7c6cff", fontWeight:700, marginBottom:6 } }, "WHY @" + result.winner?.username?.toUpperCase() + " WINS"),
              React.createElement("div", { style:{ color:"#c4b5fd", fontSize:13, lineHeight:1.6 } }, result.winner?.reason),
            ),
            // Comparison breakdown
            result.comparison && React.createElement("div", { style:{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:10, marginBottom:12 } },
              Object.entries(result.comparison).map(([k,v]) =>
                React.createElement("div", { key:k, style:{
                  background:"rgba(15,23,42,0.04)", borderRadius:8, padding:10
                } },
                  React.createElement("div", { style:{ fontSize:10, color:"#64748b", fontWeight:700, textTransform:"uppercase", marginBottom:4 } }, k),
                  React.createElement("div", { style:{ fontSize:12, color:"#334155", lineHeight:1.5 } }, v),
                )
              )
            ),
            result.recommendation && React.createElement("div", { style:{
              background:"rgba(22,163,74,0.1)", border:"1px solid rgba(22,163,74,0.2)",
              borderRadius:8, padding:12, fontSize:13, color:"#86efac"
            } }, "💡 ", result.recommendation),
          ),
      )
    );
  }


  // ── Budget & ROI Panel ────────────────────────────────────────────────────
  function BudgetPanel({ brief }) {
    const [open,    setOpen]    = React.useState(false);
    const [budget,  setBudget]  = React.useState("");
    const [loading, setLoading] = React.useState(false);
    const [result,  setResult]  = React.useState(null);
    const [err,     setErr]     = React.useState("");

    async function estimate() {
      if (!budget || parseInt(budget) <= 0) { setErr("Enter a valid budget"); return; }
      setLoading(true); setErr(""); setResult(null);
      try {
        const res = await fetch(`${window.RFApi.BASE}/api/budget-estimate`, {
          method:"POST", headers:{"Content-Type":"application/json"},
          body: JSON.stringify({
            budget_inr:          parseInt(budget),
            category:            brief?.category || "",
            product_description: brief?.product_description || "",
            campaign_goal:       brief?.campaign_goal || "Awareness",
            niche:               brief?.niche || "",
            top_n:               20,
          }),
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Request failed"); }
        const data = await res.json();
        setResult(data);
      } catch(e) { setErr(e.message || "Estimation failed — check server"); }
      setLoading(false);
    }

    const fmt = n => n >= 1e7 ? (n/1e7).toFixed(1)+"Cr" : n >= 1e5 ? (n/1e5).toFixed(1)+"L" : n >= 1e3 ? (n/1e3).toFixed(0)+"K" : String(n);

    return React.createElement("div", { style:{ margin:"16px 0" } },
      !open
        ? React.createElement("button", { onClick:()=>setOpen(true), style:{
            display:"flex", alignItems:"center", gap:8, padding:"10px 18px",
            borderRadius:10, border:"1px solid rgba(6,182,212,0.3)",
            background:"rgba(6,182,212,0.08)", color:"#67e8f9",
            fontSize:13, fontWeight:700, cursor:"pointer",
          } }, "💰 Estimate Budget & ROI")
        : React.createElement("div", { style:{
            background:"#ffffff", border:"1px solid rgba(6,182,212,0.3)",
            borderRadius:14, padding:20,
          } },
            React.createElement("div", { style:{ display:"flex", justifyContent:"space-between", marginBottom:14 } },
              React.createElement("h3", { style:{ color:"#67e8f9", fontSize:15, fontWeight:700 } }, "💰 Budget & ROI Estimator"),
              React.createElement("button", { onClick:()=>setOpen(false), style:{ background:"none", border:"none", color:"#64748b", cursor:"pointer" } }, "✕"),
            ),
            React.createElement("div", { style:{ display:"flex", gap:10, marginBottom:16 } },
              React.createElement("input", { className:"rf-input", type:"number", placeholder:"Budget in ₹ (e.g. 200000)",
                value: budget, onChange: e => setBudget(e.target.value), style:{ flex:1 } }),
              React.createElement("button", { onClick:estimate, disabled:!budget||loading, style:{
                padding:"10px 20px", borderRadius:9, border:"none",
                background:"linear-gradient(135deg,#0891b2,#06b6d4)",
                color:"#fff", fontSize:13, fontWeight:700, cursor: loading?"wait":"pointer",
                opacity: !budget ? 0.5 : 1,
              } }, loading ? "⟳ Estimating…" : "Calculate"),
            ),
            err && React.createElement("div", { style:{ color:"#f87171", fontSize:12, marginBottom:10 } }, "⚠ " + err),
            result && React.createElement("div", null,
              // Key metrics
              React.createElement("div", { style:{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:10, marginBottom:14 } },
                [["Total Reach", fmt(result.total_reach||0)],
                 ["Impressions", fmt(result.estimated_impressions||0)],
                 ["Est. Conversions", (result.estimated_conversions||0).toLocaleString()],
                 ["ROI Estimate", (result.roi_multiplier||0) + "x"]].map(([k,v]) =>
                  React.createElement("div", { key:k, style:{
                    background:"rgba(15,23,42,0.04)", borderRadius:8, padding:12, textAlign:"center"
                  } },
                    React.createElement("div", { style:{ color:"#67e8f9", fontSize:18, fontWeight:800 } }, v),
                    React.createElement("div", { style:{ color:"#64748b", fontSize:11, marginTop:3 } }, k),
                  )
                )
              ),
              // Recommended mix
              result.recommended_mix?.length > 0 && React.createElement("div", { style:{ marginBottom:12 } },
                React.createElement("div", { style:{ fontSize:11, color:"#94a3b8", fontWeight:700, textTransform:"uppercase", marginBottom:8 } }, "Recommended influencer mix"),
                result.recommended_mix.map((item, i) => React.createElement("div", { key:i, style:{
                  display:"flex", justifyContent:"space-between", alignItems:"center",
                  padding:"8px 12px", borderRadius:7, background:"rgba(15,23,42,0.04)",
                  marginBottom:6, fontSize:13,
                } },
                  React.createElement("span", { style:{ color:"#0f172a" } }, "@" + item.influencer?.username),
                  React.createElement("span", { style:{ color:"#94a3b8" } }, item.influencer?.tier + " · " + item.posts + " post(s)"),
                  React.createElement("span", { style:{ color:"#67e8f9", fontWeight:700 } }, "₹" + (item.allocation||0).toLocaleString()),
                ))
              ),
              // Gemini strategy
              result.gemini_strategy && React.createElement("div", { style:{
                background:"rgba(6,182,212,0.08)", border:"1px solid rgba(6,182,212,0.2)",
                borderRadius:8, padding:12, fontSize:13, color:"#a5f3fc", lineHeight:1.6,
              } }, "✦ ", result.gemini_strategy,
                result.gemini_tip && React.createElement("div", { style:{ marginTop:8, color:"#67e8f9" } }, "💡 Tip: ", result.gemini_tip)
              ),
            ),
          ),
    );
  }


  window.RFDiscover = DiscoverScreen;
  window.RFRow = InfluencerRow;
  window.RFBudgetPanel = BudgetPanel;
})();
