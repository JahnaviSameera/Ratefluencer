/* Ratefluencer AI — App shell: nav tabs, screen state, offline banner */
(function () {
  const { useState, useEffect, useCallback } = React;
  const RF = window.RF;
  const { L } = RF;
  const api = window.RFApi;

  function OfflineBanner({ onClose }) {
    return React.createElement("div", { className: "rf-offline" },
      React.createElement(L.WifiOff, { size: 16 }),
      React.createElement("span", null,
        React.createElement("b", null, "Demo mode active — "),
        "showing sample creator profiles. Live search requires a server connection."),
      React.createElement("button", { className: "rf-offline-x", onClick: onClose }, React.createElement(L.X, { size: 15 })),
    );
  }

  function Tab({ id, icon, label, active, disabled, onClick }) {
    const Ico = icon;
    return React.createElement("button", {
      className: "rf-tab" + (active ? " rf-tab-on" : ""), disabled, onClick,
    }, React.createElement(Ico, { size: 17 }), React.createElement("span", null, label));
  }

  function Brand() {
    return React.createElement("div", { className: "rf-brand" },
      React.createElement("div", { className: "rf-brand-mark" }, React.createElement(L.Sparkles, { size: 19 })),
      React.createElement("div", { className: "rf-brand-text" },
        React.createElement("span", { className: "rf-brand-name" }, "Ratefluencer ", React.createElement("span", { className: "rf-grad-text" }, "AI")),
        React.createElement("span", { className: "rf-brand-tag" }, "Influencer intelligence")),
    );
  }

  // ── Trend Alert Bell + Panel ─────────────────────────────────────────────
  function AlertBell({ alerts, onOpen }) {
    const count = alerts.length;
    return React.createElement("button", {
      onClick: onOpen,
      style: {
        position: "relative", background: "none", border: "none",
        cursor: "pointer", padding: "6px 8px", borderRadius: 8,
        color: count > 0 ? "#f97316" : "#64748b",
        transition: "all 0.2s",
      }
    },
      React.createElement(L.Bell, { size: 20 }),
      count > 0 && React.createElement("span", { style: {
        position: "absolute", top: 2, right: 2,
        background: "#f97316", color: "#fff",
        borderRadius: "50%", width: 16, height: 16,
        fontSize: 10, fontWeight: 800,
        display: "flex", alignItems: "center", justifyContent: "center",
        animation: "rf-pulse 2s infinite",
      } }, count > 9 ? "9+" : count),
    );
  }

  function AlertPanel({ alerts, onDismiss, onDismissAll, onLaunch, onClose }) {
    const [scanning, setScanning] = React.useState(false);
    const [scanMsg,  setScanMsg]  = React.useState("");

    const triggerScan = async () => {
      setScanning(true); setScanMsg("Scanning HN + Google News…");
      try {
        await fetch(`${window.RFApi.BASE}/api/alerts/scan`, { method: "POST" });
        setScanMsg("Scan running — alerts appear in ~60s");
        setTimeout(() => setScanMsg(""), 8000);
      } catch(e) { setScanMsg("Scan failed"); }
      setScanning(false);
    };

    if (!alerts.length) return React.createElement("div", { style: {
      position: "fixed", top: 56, right: 16, zIndex: 900,
      background: "#ffffff", border: "1px solid rgba(15,23,42,0.07)",
      borderRadius: 14, padding: 24, width: 340, textAlign: "center",
      boxShadow: "0 16px 48px rgba(15,23,42,0.14)",
    } },
      React.createElement(L.BellOff, { size: 28, style: { color: "#64748b", margin: "0 auto 8px" } }),
      React.createElement("div", { style: { color: "#94a3b8", fontSize: 14, marginBottom: 12 } }, "No active trend alerts"),
      React.createElement("div", { style: { color: "#64748b", fontSize: 12, marginBottom: 14 } }, "Scanner runs every hour"),
      React.createElement("button", { onClick: triggerScan, disabled: scanning, style: {
        padding: "9px 18px", borderRadius: 9, border: "none", cursor: "pointer",
        background: "linear-gradient(135deg,#f97316,#ef4444)",
        color: "#fff", fontSize: 12, fontWeight: 700, width: "100%",
      } }, scanning ? "⟳ Scanning…" : "🔍 Scan Now"),
      scanMsg && React.createElement("div", { style: { color: "#94a3b8", fontSize: 11, marginTop: 8 } }, scanMsg),
    );

    const URGENCY_COLOR = { breaking: "#f97316", rising: "#06b6d4" };

    return React.createElement("div", {
      style: {
        position: "fixed", top: 56, right: 16, zIndex: 900,
        background: "#ffffff", border: "1px solid rgba(15,23,42,0.08)",
        borderRadius: 16, width: 360, maxHeight: "70vh", overflowY: "auto",
        boxShadow: "0 20px 60px rgba(15,23,42,0.16)",
      }
    },
      // Header
      React.createElement("div", { style: {
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "16px 18px 12px", borderBottom: "1px solid rgba(15,23,42,0.06)",
        position: "sticky", top: 0, background: "#ffffff", zIndex: 1,
      } },
        React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 8 } },
          React.createElement(L.TrendingUp, { size: 16, style: { color: "#f97316" } }),
          React.createElement("span", { style: { color: "#0f172a", fontWeight: 700, fontSize: 14 } }, "Trend Alerts"),
          React.createElement("span", { style: {
            background: "#f9731622", color: "#f97316", fontSize: 11, fontWeight: 700,
            padding: "2px 7px", borderRadius: 99,
          } }, alerts.length),
        ),
        React.createElement("div", { style: { display: "flex", gap: 8, alignItems: "center" } },
          React.createElement("button", { onClick: onDismissAll, style: {
            fontSize: 11, color: "#64748b", background: "none", border: "none",
            cursor: "pointer", textDecoration: "underline",
          } }, "Clear all"),
          React.createElement("button", { onClick: onClose, style: {
            background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 18, lineHeight: 1,
          } }, "✕"),
        ),
      ),

      // Alert cards
      React.createElement("div", { style: { padding: "10px 12px 14px" } },
        alerts.map(alert => React.createElement("div", { key: alert.id, style: {
          background: "rgba(15,23,42,0.04)",
          border: `1px solid ${URGENCY_COLOR[alert.urgency] || "#64748b"}22`,
          borderLeft: `3px solid ${URGENCY_COLOR[alert.urgency] || "#64748b"}`,
          borderRadius: 10, padding: "12px 14px", marginBottom: 10,
        } },
          // Top row: urgency badge + score + dismiss
          React.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 } },
            React.createElement("span", { style: {
              fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: 0.5,
              color: URGENCY_COLOR[alert.urgency] || "#64748b",
            } }, alert.urgency === "breaking" ? "🔥 Breaking" : "📈 Rising"),
            React.createElement("div", { style: { display: "flex", gap: 8, alignItems: "center" } },
              React.createElement("span", { style: { color: "#94a3b8", fontSize: 12, fontWeight: 700 } }, alert.score + "/100"),
              React.createElement("button", { onClick: () => onDismiss(alert.id), style: {
                background: "none", border: "none", color: "#475569", cursor: "pointer", fontSize: 14, lineHeight: 1,
              } }, "✕"),
            ),
          ),
          // Phrase
          React.createElement("div", { style: { color: "#0f172a", fontWeight: 700, fontSize: 14, marginBottom: 4 } },
            alert.phrase.charAt(0).toUpperCase() + alert.phrase.slice(1)
          ),
          // Why
          alert.why && React.createElement("div", { style: { color: "#94a3b8", fontSize: 12, lineHeight: 1.5, marginBottom: 10 } },
            alert.why
          ),
          // Launch button
          React.createElement("button", { onClick: () => onLaunch(alert), style: {
            width: "100%", padding: "8px", borderRadius: 8, border: "none",
            background: `linear-gradient(135deg, ${URGENCY_COLOR[alert.urgency] || "#64748b"}33, ${URGENCY_COLOR[alert.urgency] || "#64748b"}22)`,
            color: URGENCY_COLOR[alert.urgency] || "#0f172a",
            fontSize: 12, fontWeight: 700, cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
          } },
            React.createElement(L.Search, { size: 13 }), "Find influencers for this trend →"
          ),
        ))
      ),
    );
  }

  function App() {
    const [screen, setScreen] = useState("search");   // search | discover | profile | campaign | campaigns
    const [selected, setSelected] = useState(null);
    const [results, setResults] = useState(null);
    const [brief, setBrief] = useState(null);
    const [profileFrom, setProfileFrom] = useState("discover");
    const [offline, setOffline] = useState(false);
    const [bannerOpen, setBannerOpen] = useState(true);
    const [alerts, setAlerts] = useState([]);
    const [alertOpen, setAlertOpen] = useState(false);
    const [activeCampaignId, setActiveCampaignId] = useState(function() {
      return localStorage.getItem('rf_active_campaign') || null;
    });

    useEffect(() => api.onOfflineChange((v) => { setOffline(v); if (v) setBannerOpen(true); }), []);
    useEffect(() => {
      function handleGoto(e) { setScreen(e.detail); }
      window.addEventListener('rf-goto', handleGoto);
      return () => window.removeEventListener('rf-goto', handleGoto);
    }, []);
    useEffect(() => { api.getStats().then(() => setOffline(api.isOffline())); }, []);

    // Poll alerts every 30 seconds
    const fetchAlerts = () => {
      fetch(`${window.RFApi.BASE}/api/alerts`)
        .then(r => r.json())
        .then(d => setAlerts(d.alerts || []))
        .catch(() => {});
    };
    useEffect(() => {
      fetchAlerts();
      const t = setInterval(fetchAlerts, 30000);
      return () => clearInterval(t);
    }, []);

    const dismissAlert = (id) => {
      fetch(`${window.RFApi.BASE}/api/alerts/${id}`, { method: "DELETE" })
        .then(() => setAlerts(a => a.filter(x => x.id !== id)));
    };
    const dismissAll = () => {
      fetch(`${window.RFApi.BASE}/api/alerts`, { method: "DELETE" })
        .then(() => { setAlerts([]); setAlertOpen(false); });
    };
    const launchFromAlert = (alert) => {
      const alertBrief = {
        category:    alert.phrase,
        niche:       alert.niche === "artificial intelligence" ? "Technology"
                   : alert.niche === "creator economy"        ? "Lifestyle Vlogging"
                   : alert.niche === "technology"             ? "Technology"
                   : alert.niche === "finance"                ? "Finance & Investing"
                   : alert.niche,
        campaign_goal: "Awareness",
        product_description: `Campaign for trending topic: ${alert.phrase}`,
        keywords:    [alert.phrase],
        min_followers: 1000,
        min_authenticity: 0,
        top_n: 12,
      };
      setBrief(alertBrief);
      setResults(null);
      setAlertOpen(false);
      dismissAlert(alert.id);
      // Auto-search so user sees results immediately
      setScreen("discover");
      api.search(alertBrief).then(res => {
        setResults(res);
      }).catch(() => {});
    };

    const onResults = useCallback((b, res, campId) => {
      setBrief(b); setResults(res);
      if (campId) { setActiveCampaignId(campId); localStorage.setItem('rf_active_campaign', campId); }
      setScreen("discover");
    }, []);
    const onView = useCallback((inf, from) => {
      setSelected(inf); setProfileFrom(from || (results ? "search" : "discover")); setScreen("profile");
    }, [results]);
    const clearResults = useCallback(() => { setResults(null); setBrief(null); }, []);

    return React.createElement("div", { className: "rf-app" },
      React.createElement("header", { className: "rf-topbar" },
        React.createElement(Brand, null),
        React.createElement("nav", { className: "rf-tabs" },
          React.createElement(Tab, { id: "search",    icon: L.Search,      label: "Brand Search",    active: screen === "search",    onClick: () => setScreen("search") }),
          React.createElement(Tab, { id: "discover",  icon: L.LayoutGrid,  label: results ? "Search Results" : "Discover", active: screen === "discover",  onClick: () => setScreen("discover") }),
          React.createElement(Tab, { id: "profile",   icon: L.UserRound,   label: "Profile",         active: screen === "profile",   disabled: !selected, onClick: () => selected && setScreen("profile") }),
          React.createElement(Tab, { id: "campaign",  icon: L.Rocket,      label: "Campaign Planner",active: screen === "campaign",  onClick: () => setScreen("campaign") }),
          React.createElement(Tab, { id: "campaigns", icon: L.Briefcase,   label: "My Campaigns",    active: screen === "campaigns", onClick: () => setScreen("campaigns") }),
        ),
        React.createElement("div", { className: "rf-topbar-right", style: { display: "flex", alignItems: "center", gap: 12 } },
          React.createElement(AlertBell, { alerts, onOpen: () => setAlertOpen(o => !o) }),
          React.createElement("a", {
            href: "/creator",
            target: "_blank",
            rel: "noreferrer",
            style: {
              display: "flex", alignItems: "center", gap: 6,
              padding: "7px 14px", borderRadius: 8, textDecoration: "none",
              background: "linear-gradient(135deg,#7c3aed,#06b6d4)",
              color: "#fff", fontSize: 12, fontWeight: 700, whiteSpace: "nowrap",
            }
          }, "✦ Real Creator Agent"),
          React.createElement("span", { className: "rf-status " + (offline ? "rf-status-off" : "rf-status-on") },
            React.createElement("span", { className: "rf-status-dot" }), offline ? "Demo data" : "Live"),
        ),
      ),
      offline && bannerOpen ? React.createElement(OfflineBanner, { onClose: () => setBannerOpen(false) }) : null,

      // Click-outside to close alert panel
      alertOpen && React.createElement("div", {
        onClick: () => setAlertOpen(false),
        style: { position: "fixed", inset: 0, zIndex: 899 }
      }),
      alertOpen && React.createElement(AlertPanel, {
        alerts, onDismiss: dismissAlert, onDismissAll: dismissAll,
        onLaunch: launchFromAlert, onClose: () => setAlertOpen(false),
      }),

      React.createElement("main", { className: "rf-main" },
        React.createElement("div", { key: screen, className: "rf-screen-fade" },
          screen === "search"    ? React.createElement(window.RFSearch, { onResults, initialBrief: brief, onViewCreator: (inf) => onView(inf, "discover") })
          : screen === "discover"  ? React.createElement(window.RFDiscover, { resultsData: results, brief, onView: (inf) => onView(inf, results ? "search" : "discover"), onClearResults: clearResults, activeCampaignId })
          : screen === "campaign"  ? React.createElement(window.RFCampaign, { onBack: () => setScreen("search") })
          : screen === "campaigns" ? React.createElement(window.RFCampaigns, {
              onRerunSearch: (b) => { setBrief(b); setResults(null); setScreen("search"); },
              onViewCreator: (inf) => onView(inf, "campaigns"),
            })
          : React.createElement(window.RFProfile, { initial: selected, fromSearch: profileFrom === "search",
              activeCampaignId,
              onBack: () => setScreen(profileFrom === "search" ? "discover" : "discover") }),
        ),
      ),
    );
  }

  window.RFApp = App;
})();
