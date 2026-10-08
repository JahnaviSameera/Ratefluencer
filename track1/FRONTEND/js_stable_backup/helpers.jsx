/* Ratefluencer AI — shared formatters + atomic UI components. */
(function () {
  const { useState, useEffect } = React;

  // ── lucide icon factory (vanilla lucide UMD → React components) ──
  function kebabToCamel(k) { return k.replace(/-([a-z])/g, (_, c) => c.toUpperCase()); }
  const _iconCache = {};
  function makeIcon(name) {
    if (_iconCache[name]) return _iconCache[name];
    const Comp = function (props) {
      const { size = 18, className, style, color, ...rest } = props || {};
      const node = (window.lucide && (window.lucide[name] || (window.lucide.icons && window.lucide.icons[name]))) || null;
      const children = node ? node[2] : [];
      const kids = (children || []).map((c, i) => {
        const tag = c[0]; const attrs = {}; const raw = c[1] || {};
        Object.keys(raw).forEach((k) => { attrs[kebabToCamel(k)] = raw[k]; });
        attrs.key = i;
        return React.createElement(tag, attrs);
      });
      return React.createElement("svg", {
        width: size, height: size, viewBox: "0 0 24 24", fill: "none",
        stroke: color || "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round",
        className, style,
      }, kids);
    };
    _iconCache[name] = Comp;
    return Comp;
  }
  const L = new Proxy({}, { get: (_, name) => (typeof name === "string" ? makeIcon(name) : undefined) });

  // ── formatters ──
  function formatFollowers(n) {
    if (n == null) return "—";
    if (n >= 1_000_000) return +(n / 1_000_000).toFixed(n >= 10_000_000 ? 0 : 1) + "M";
    if (n >= 1_000) return +(n / 1_000).toFixed(n >= 100_000 ? 0 : 1) + "K";
    return String(n);
  }
  function formatNum(n) {
    if (n == null) return "—";
    if (n >= 1_000_000) return +(n / 1_000_000).toFixed(1) + "M";
    if (n >= 1_000) return +(n / 1_000).toFixed(1) + "K";
    return n.toLocaleString("en-IN");
  }
  const fmtPct = (n) => (n == null ? "—" : Number(n).toFixed(2) + "%");
  const fmtScore = (n) => (n == null ? "—" : Number(n).toFixed(1));
  function titleCase(s) { return (s || "").replace(/\b\w/g, (c) => c.toUpperCase()); }

  // ── score color ramp ──
  function scoreHex(v) {
    if (v >= 80) return "#ffd700";
    if (v >= 65) return "#16a34a";
    if (v >= 45) return "#d97706";
    return "#dc2626";
  }
  function scoreLabel(v) {
    if (v >= 80) return "Elite"; if (v >= 65) return "Strong";
    if (v >= 45) return "Average"; return "Weak";
  }

  // ── niche colors (20 niches) ──
  const NICHE_HEX = {
    "Fitness":               "#f97316",
    "Health & Wellness":     "#22c55e",
    "Yoga & Meditation":     "#a78bfa",
    "Nutrition & Diet":      "#84cc16",
    "Fashion":               "#ec4899",
    "Beauty & Skincare":     "#f472b6",
    "Lifestyle Vlogging":    "#fb923c",
    "Parenting & Family":    "#facc15",
    "Travel":                "#06b6d4",
    "Food & Cooking":        "#ef4444",
    "Home Decor & Interior": "#8b5cf6",
    "DIY & Crafts":          "#d97706",
    "Technology":            "#2563eb",
    "Gaming":                "#7c3aed",
    "Finance & Investing":   "#16a34a",
    "Entrepreneurship":      "#0891b2",
    "Sports & Athletics":    "#f59e0b",
    "Mental Health":         "#14b8a6",
    "Music & Dance":         "#e879f9",
    "Comedy & Entertainment":"#f43f5e",
  };
  const NICHE_SHORT = {
    "Fitness":               "Fitness",
    "Health & Wellness":     "Health",
    "Yoga & Meditation":     "Yoga",
    "Nutrition & Diet":      "Nutrition",
    "Fashion":               "Fashion",
    "Beauty & Skincare":     "Beauty",
    "Lifestyle Vlogging":    "Lifestyle",
    "Parenting & Family":    "Parenting",
    "Travel":                "Travel",
    "Food & Cooking":        "Food",
    "Home Decor & Interior": "Home",
    "DIY & Crafts":          "DIY",
    "Technology":            "Tech",
    "Gaming":                "Gaming",
    "Finance & Investing":   "Finance",
    "Entrepreneurship":      "Startup",
    "Sports & Athletics":    "Sports",
    "Mental Health":         "Mental",
    "Music & Dance":         "Music",
    "Comedy & Entertainment":"Comedy",
  };
  const nicheHex = (n) => NICHE_HEX[n] || "#6366f1";

  const TIER_HEX = {
    "Nano": "#8b949e", "Micro": "#0891b2", "Mid-Tier": "#2563eb", "Macro": "#7c3aed", "Mega": "#db2777",
  };

  // ── components ──
  function NicheBadge({ niche }) {
    const c = nicheHex(niche);
    return React.createElement("span", {
      className: "rf-badge", style: { color: c, background: c + "22", borderColor: c + "55" },
    }, NICHE_SHORT[niche] || titleCase(niche));
  }

  function TierBadge({ tier }) {
    const c = TIER_HEX[tier] || "#8b949e";
    return React.createElement("span", {
      className: "rf-badge rf-badge-soft", style: { color: c, borderColor: c + "44" },
    }, tier);
  }

  function Avatar({ name, niche, size = 44, username }) {
    const initials = (name || "?").split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();
    const c = nicheHex(niche);
    const seed = encodeURIComponent(username || name || "user");
    const avatarUrl = `https://api.dicebear.com/7.x/avataaars/svg?seed=${seed}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf&backgroundType=gradientLinear`;
    const [imgErr, setImgErr] = React.useState(false);

    return React.createElement("div", {
      className: "rf-avatar",
      style: {
        width: size, height: size, fontSize: size * 0.36,
        background: imgErr ? `linear-gradient(135deg,${c},${c}bb)` : "transparent",
        boxShadow: "0 4px 14px " + c + "44",
        overflow: "hidden", flexShrink: 0,
      },
    },
      !imgErr
        ? React.createElement("img", {
            src: avatarUrl,
            alt: name,
            style: { width: "100%", height: "100%", objectFit: "cover" },
            onError: () => setImgErr(true),
          })
        : initials
    );
  }

  function AuthChip({ score, withText }) {
    let icon = "🚨", cls = "danger", txt = "High risk";
    if (score >= 70) { icon = "✅"; cls = "ok"; txt = "Trusted"; }
    else if (score >= 45) { icon = "⚠️"; cls = "warn"; txt = "Caution"; }
    return React.createElement("span", { className: "rf-authchip rf-auth-" + cls, title: "Authenticity " + score },
      React.createElement("span", null, icon),
      React.createElement("span", { className: "rf-authnum" }, score),
      withText ? React.createElement("span", { className: "rf-authtxt" }, txt) : null,
    );
  }

  // Circular score dial
  function Dial({ value, label, sub, size = 116, color }) {
    const r = size / 2 - 9;
    const circ = 2 * Math.PI * r;
    const pct = Math.max(0, Math.min(100, value)) / 100;
    const c = color || scoreHex(value);
    return React.createElement("div", { className: "rf-dial" },
      React.createElement("svg", { width: size, height: size, viewBox: `0 0 ${size} ${size}` },
        React.createElement("circle", { cx: size / 2, cy: size / 2, r, fill: "none", stroke: "#30363d", strokeWidth: 9 }),
        React.createElement("circle", {
          cx: size / 2, cy: size / 2, r, fill: "none", stroke: c, strokeWidth: 9, strokeLinecap: "round",
          strokeDasharray: circ, strokeDashoffset: circ * (1 - pct),
          transform: `rotate(-90 ${size / 2} ${size / 2})`, style: { transition: "stroke-dashoffset .9s cubic-bezier(.2,.8,.2,1)" },
        }),
        React.createElement("text", { x: "50%", y: "47%", textAnchor: "middle", dominantBaseline: "middle", fontSize: size * 0.26, fontWeight: 700, fill: c }, fmtScore(value)),
        sub ? React.createElement("text", { x: "50%", y: "64%", textAnchor: "middle", fontSize: size * 0.1, fill: "#8b949e" }, sub) : null,
      ),
      label ? React.createElement("div", { className: "rf-dial-label" }, label) : null,
    );
  }

  // Horizontal fill bar
  function FillBar({ value, max = 100, color, height = 8, track = "#21262d" }) {
    const pct = Math.max(0, Math.min(100, (value / max) * 100));
    return React.createElement("div", { className: "rf-fillbar", style: { height, background: track } },
      React.createElement("div", { className: "rf-fillbar-fill", style: { width: pct + "%", background: color || "var(--rf-grad)" } }),
    );
  }

  function Skeleton({ w = "100%", h = 14, r = 6, style }) {
    return React.createElement("div", { className: "rf-skel", style: { width: w, height: h, borderRadius: r, ...style } });
  }

  window.RF = {
    React, L,
    formatFollowers, formatNum, fmtPct, fmtScore, titleCase,
    scoreHex, scoreLabel, nicheHex, NICHE_SHORT, NICHE_HEX, TIER_HEX,
    NicheBadge, TierBadge, Avatar, AuthChip, Dial, FillBar, Skeleton,
  };
})();
