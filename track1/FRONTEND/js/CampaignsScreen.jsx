/* Ratefluencer AI — Screen 5: My Campaigns & Collaborations */
(function () {
  const { useState } = React;
  const RF = window.RF;
  const { L, formatFollowers, scoreHex, NicheBadge, Avatar } = RF;

  // ── localStorage helpers (shared) ──────────────────────────────────────────
  function getCampaigns() {
    try { return JSON.parse(localStorage.getItem('rf_campaigns') || '[]'); } catch(e) { return []; }
  }
  function getCollabs() {
    try { return JSON.parse(localStorage.getItem('rf_collabs') || '[]'); } catch(e) { return []; }
  }
  function saveCampaigns(list) { localStorage.setItem('rf_campaigns', JSON.stringify(list)); }
  function saveCollabs(list)   { localStorage.setItem('rf_collabs',   JSON.stringify(list)); }

  window.RFStore = { getCampaigns, getCollabs, saveCampaigns, saveCollabs };

  // ── Status colour maps ─────────────────────────────────────────────────────
  const CAMP_COLORS = {
    Planning:  { bg: "#eff6ff", color: "#2563eb", border: "#bfdbfe" },
    Active:    { bg: "#f0fdf4", color: "#16a34a", border: "#bbf7d0" },
    Completed: { bg: "#f5f3ff", color: "#7c3aed", border: "#ddd6fe" },
  };
  const COLLAB_COLORS = {
    Shortlisted: { bg: "#f8fafc", color: "#64748b", border: "#e2e8f0" },
    Contacted:   { bg: "#eff6ff", color: "#2563eb", border: "#bfdbfe" },
    Negotiating: { bg: "#fffbeb", color: "#d97706", border: "#fde68a" },
    Confirmed:   { bg: "#f0fdf4", color: "#16a34a", border: "#bbf7d0" },
    Declined:    { bg: "#fef2f2", color: "#dc2626", border: "#fecaca" },
  };
  window.RF_COLLAB_COLORS = COLLAB_COLORS;

  function StatusPill({ status, colors }) {
    const c = colors[status] || colors[Object.keys(colors)[0]];
    return React.createElement("span", { style: {
      display: "inline-flex", alignItems: "center",
      padding: "3px 10px", borderRadius: 99, fontSize: 11, fontWeight: 700,
      background: c.bg, color: c.color, border: "1px solid " + c.border,
    }}, status);
  }

  // ── Creators modal (View Shortlisted) ──────────────────────────────────────
  function CreatorsModal({ campaignId, onClose, onViewCreator }) {
    const collabs  = getCollabs().filter(c => c.campaignId === campaignId);
    const campaign = getCampaigns().find(c => c.id === campaignId);
    return React.createElement(React.Fragment, null,
      React.createElement("div", { onClick: onClose, style: {
        position: "fixed", inset: 0, zIndex: 1000,
        background: "rgba(15,23,42,0.4)", backdropFilter: "blur(3px)",
      }}),
      React.createElement("div", { style: {
        position: "fixed", top: "50%", left: "50%", zIndex: 1001,
        transform: "translate(-50%,-50%)",
        background: "#ffffff", borderRadius: 16,
        width: "min(500px,95vw)", maxHeight: "75vh", overflowY: "auto",
        boxShadow: "0 24px 64px rgba(15,23,42,0.18)",
      }},
        // sticky header
        React.createElement("div", { style: {
          padding: "18px 20px 14px", borderBottom: "1px solid #f0f2f8",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          position: "sticky", top: 0, background: "#ffffff", zIndex: 1,
        }},
          React.createElement("div", null,
            React.createElement("div", { style: { fontSize: 15, fontWeight: 700, color: "#0f172a" }}, "Shortlisted creators"),
            React.createElement("div", { style: { fontSize: 12, color: "#64748b", marginTop: 2 }}, campaign ? campaign.name : ""),
          ),
          React.createElement("button", { onClick: onClose, style: {
            background: "none", border: "none", color: "#64748b",
            cursor: "pointer", fontSize: 20, lineHeight: 1, padding: 4,
          }}, "✕"),
        ),
        collabs.length === 0
          ? React.createElement("div", { style: { padding: "32px 24px", textAlign: "center", color: "#94a3b8", fontSize: 14 }},
              "No creators shortlisted yet for this campaign.")
          : collabs.map(function(collab) {
              const inf = collab.creator || {};
              const sc  = scoreHex(inf.ratefluencer_score);
              const cc  = COLLAB_COLORS[collab.status] || COLLAB_COLORS.Shortlisted;
              return React.createElement("div", { key: collab.id, style: {
                display: "flex", alignItems: "center", gap: 12,
                padding: "12px 20px", borderBottom: "1px solid #f0f2f8",
              }},
                React.createElement(Avatar, { name: inf.full_name, niche: inf.niche, size: 44, username: inf.username }),
                React.createElement("div", { style: { flex: 1 }},
                  React.createElement("div", { style: { fontSize: 13, fontWeight: 700, color: "#0f172a" }}, "@" + inf.username),
                  React.createElement("div", { style: { fontSize: 11, color: "#64748b", marginTop: 2 }},
                    (inf.niche || "") + " · " + formatFollowers(inf.followers_count)),
                ),
                React.createElement("span", { style: { fontSize: 16, fontWeight: 800, color: sc, marginRight: 8 }},
                  Math.round(inf.ratefluencer_score || 0)),
                React.createElement("span", { style: {
                  padding: "3px 10px", borderRadius: 99, fontSize: 11, fontWeight: 700,
                  background: cc.bg, color: cc.color, border: "1px solid " + cc.border, marginRight: 8,
                }}, collab.status),
                React.createElement("button", {
                  onClick: function() { onViewCreator(inf); onClose(); },
                  style: {
                    padding: "6px 12px", borderRadius: 7, border: "none",
                    background: "linear-gradient(135deg,#6d28d9,#4f46e5)",
                    color: "#fff", fontSize: 11, fontWeight: 700, cursor: "pointer",
                  }
                }, "View"),
              );
            }),
      ),
    );
  }

  // ── Single campaign card ───────────────────────────────────────────────────
  function CampaignCard({ campaign, onRerunSearch, onViewCreators, onStatusChange }) {
    const brief   = campaign.brief || {};
    const collabs = getCollabs().filter(function(c) { return c.campaignId === campaign.id; });
    const cc      = CAMP_COLORS[campaign.status] || CAMP_COLORS.Planning;

    return React.createElement("div", { style: {
      background: "#ffffff", borderRadius: 14, padding: "18px 20px",
      border: "1px solid #e8ecf5", marginBottom: 12,
      boxShadow: "0 1px 4px rgba(15,23,42,0.06)",
    }},
      // top row
      React.createElement("div", { style: {
        display: "flex", alignItems: "flex-start",
        justifyContent: "space-between", marginBottom: 10,
      }},
        React.createElement("div", null,
          React.createElement("div", { style: { fontSize: 15, fontWeight: 700, color: "#0f172a", marginBottom: 4 }},
            campaign.name || "Untitled Campaign"),
          React.createElement("div", { style: { fontSize: 12, color: "#64748b", display: "flex", gap: 10, flexWrap: "wrap" }},
            React.createElement("span", null,
              new Date(campaign.date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })),
            brief.niche        ? React.createElement("span", null, "· " + brief.niche)        : null,
            brief.campaign_goal? React.createElement("span", null, "· " + brief.campaign_goal): null,
          ),
        ),
        React.createElement("span", { style: {
          padding: "3px 10px", borderRadius: 99, fontSize: 11, fontWeight: 700,
          background: cc.bg, color: cc.color, border: "1px solid " + cc.border,
        }}, campaign.status),
      ),
      // metrics
      React.createElement("div", { style: { display: "flex", gap: 24, marginBottom: 14 }},
        React.createElement("div", { style: { fontSize: 12, color: "#64748b" }},
          React.createElement("span", { style: { fontWeight: 700, color: "#0f172a", fontSize: 15 }},
            campaign.matchedCount || 0), " creators matched"),
        React.createElement("div", { style: { fontSize: 12, color: "#64748b" }},
          React.createElement("span", { style: { fontWeight: 700, color: "#7c3aed", fontSize: 15 }},
            collabs.length), " shortlisted"),
      ),
      // action row
      React.createElement("div", { style: { display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }},
        React.createElement("button", {
          onClick: function() { onRerunSearch(brief); },
          style: {
            display: "flex", alignItems: "center", gap: 6,
            padding: "8px 14px", borderRadius: 8, border: "none", cursor: "pointer",
            background: "linear-gradient(135deg,#6d28d9,#4f46e5)",
            color: "#fff", fontSize: 12, fontWeight: 700,
          }
        }, React.createElement(L.Search, { size: 13 }), "Re-run Search"),
        collabs.length > 0 ? React.createElement("button", {
          onClick: function() { onViewCreators(campaign.id); },
          style: {
            display: "flex", alignItems: "center", gap: 6,
            padding: "8px 14px", borderRadius: 8, cursor: "pointer",
            background: "#f8f9ff", border: "1px solid #e0d9ff",
            color: "#7c3aed", fontSize: 12, fontWeight: 700,
          }
        }, React.createElement(L.Users, { size: 13 }), "View Shortlisted (" + collabs.length + ")") : null,
        React.createElement("select", {
          value: campaign.status,
          onChange: function(e) { onStatusChange(campaign.id, e.target.value); },
          style: {
            marginLeft: "auto", padding: "7px 12px", borderRadius: 8,
            border: "1px solid #e8ecf5", background: "#f8f9ff",
            color: "#64748b", fontSize: 12, fontWeight: 600, cursor: "pointer",
          }
        },
          ["Planning","Active","Completed"].map(function(s) {
            return React.createElement("option", { key: s, value: s }, s);
          }),
        ),
      ),
    );
  }

  // ── Collaboration row ──────────────────────────────────────────────────────
  function CollabRow({ collab, onViewCreator, onStatusChange }) {
    const inf = collab.creator || {};
    const sc  = scoreHex(inf.ratefluencer_score);
    const cc  = COLLAB_COLORS[collab.status] || COLLAB_COLORS.Shortlisted;
    return React.createElement("div", { style: {
      display: "flex", alignItems: "center", gap: 12,
      padding: "12px 16px", borderBottom: "1px solid #f0f2f8",
    }},
      React.createElement(Avatar, { name: inf.full_name, niche: inf.niche, size: 44, username: inf.username }),
      React.createElement("div", { style: { flex: 1, minWidth: 0 }},
        React.createElement("div", { style: { fontSize: 13, fontWeight: 700, color: "#0f172a" }},
          "@" + inf.username),
        React.createElement("div", { style: { fontSize: 11, color: "#64748b", marginTop: 2 }},
          (inf.niche || "") + " · " + (collab.campaignName || "No campaign")),
      ),
      React.createElement("div", { style: { textAlign: "right", marginRight: 10 }},
        React.createElement("div", { style: { fontSize: 16, fontWeight: 800, color: sc }},
          Math.round(inf.ratefluencer_score || 0)),
        React.createElement("div", { style: { fontSize: 10, color: "#94a3b8", fontWeight: 700, textTransform: "uppercase" }},
          "score"),
      ),
      React.createElement("select", {
        value: collab.status,
        onChange: function(e) { onStatusChange(collab.id, e.target.value); },
        onClick: function(e) { e.stopPropagation(); },
        style: {
          padding: "6px 10px", borderRadius: 7, fontSize: 11, fontWeight: 700,
          border: "1px solid " + cc.border, background: cc.bg, color: cc.color,
          cursor: "pointer", marginRight: 8,
        }
      },
        ["Shortlisted","Contacted","Negotiating","Confirmed","Declined"].map(function(s) {
          return React.createElement("option", { key: s, value: s }, s);
        }),
      ),
      React.createElement("button", {
        onClick: function() { onViewCreator(inf); },
        style: {
          display: "flex", alignItems: "center", gap: 4,
          padding: "6px 12px", borderRadius: 7,
          border: "1px solid #e8ecf5", background: "#f8f9ff",
          color: "#7c3aed", fontSize: 11, fontWeight: 700,
          cursor: "pointer", whiteSpace: "nowrap",
        }
      }, React.createElement(L.User, { size: 12 }), "View Profile"),
    );
  }

  // ── Main screen ────────────────────────────────────────────────────────────
  function CampaignsScreen({ onRerunSearch, onViewCreator }) {
    const [campaigns,      setCampaigns]      = useState(getCampaigns);
    const [collabs,        setCollabs]        = useState(getCollabs);
    const [activeTab,      setActiveTab]      = useState("campaigns");
    const [viewCreatorsFor,setViewCreatorsFor]= useState(null);

    function updateCampaignStatus(id, status) {
      const list = getCampaigns();
      const idx  = list.findIndex(function(c) { return c.id === id; });
      if (idx >= 0) { list[idx].status = status; saveCampaigns(list); }
      setCampaigns([...list]);
    }
    function updateCollabStatus(id, status) {
      const list = getCollabs();
      const idx  = list.findIndex(function(c) { return c.id === id; });
      if (idx >= 0) { list[idx].status = status; saveCollabs(list); }
      setCollabs([...list]);
    }

    const isEmpty = campaigns.length === 0 && collabs.length === 0;

    return React.createElement("div", { style: { maxWidth: 820, margin: "0 auto", padding: "24px 16px" }},
      // page header
      React.createElement("div", { style: { marginBottom: 24 }},
        React.createElement("div", { style: {
          display: "inline-flex", alignItems: "center", gap: 6,
          fontSize: 11, fontWeight: 700, color: "#7c3aed",
          textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8,
        }}, React.createElement(L.Briefcase, { size: 13 }), "Campaign Manager"),
        React.createElement("h1", { style: { fontSize: 26, fontWeight: 800, color: "#0f172a", margin: 0 }},
          "My Campaigns"),
        React.createElement("p", { style: { fontSize: 14, color: "#64748b", marginTop: 6 }},
          "Every search you run creates a campaign. Shortlist creators from results and track your collaborations here."),
      ),

      // tabs
      React.createElement("div", { style: {
        display: "flex", gap: 4, marginBottom: 20,
        background: "#f0f2f8", borderRadius: 10, padding: 4,
      }},
        [
          ["campaigns", L.FolderOpen, "Campaigns (" + campaigns.length + ")"],
          ["collabs",   L.Users,      "Collaborations (" + collabs.length + ")"],
        ].map(function(item) {
          var id = item[0], Icon = item[1], label = item[2];
          return React.createElement("button", {
            key: id, onClick: function() { setActiveTab(id); },
            style: {
              flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
              padding: "8px 16px", borderRadius: 8, border: "none", cursor: "pointer",
              fontSize: 13, fontWeight: 700,
              background: activeTab === id ? "#ffffff" : "transparent",
              color:      activeTab === id ? "#0f172a"  : "#64748b",
              boxShadow:  activeTab === id ? "0 1px 4px rgba(15,23,42,0.08)" : "none",
              transition: "all 0.15s",
            }
          }, React.createElement(Icon, { size: 15 }), label);
        }),
      ),

      // empty state
      isEmpty ? React.createElement("div", { style: {
        textAlign: "center", padding: "60px 24px",
        background: "#ffffff", borderRadius: 16, border: "1px solid #e8ecf5",
      }},
        React.createElement("div", { style: { fontSize: 48, marginBottom: 16 }}, "📋"),
        React.createElement("div", { style: { fontSize: 17, fontWeight: 700, color: "#0f172a", marginBottom: 8 }},
          "No campaigns yet"),
        React.createElement("div", { style: { fontSize: 14, color: "#64748b", marginBottom: 20 }},
          "Go to Brand Search, fill your brief, and click Find Influencers — your first campaign appears here automatically."),
        React.createElement("button", {
          onClick: function() { onRerunSearch({}); },
          style: {
            padding: "12px 24px", borderRadius: 10, border: "none", cursor: "pointer",
            background: "linear-gradient(135deg,#6d28d9,#4f46e5)",
            color: "#fff", fontSize: 14, fontWeight: 700,
            display: "inline-flex", alignItems: "center", gap: 8,
          }
        }, React.createElement(L.Search, { size: 15 }), "Start a Campaign"),
      ) : null,

      // Campaigns tab
      activeTab === "campaigns" && !isEmpty && (
        campaigns.length === 0
          ? React.createElement("div", { style: { textAlign: "center", padding: 40, color: "#94a3b8" }},
              "No campaigns found. Run a Brand Search to create one.")
          : campaigns.map(function(c) {
              return React.createElement(CampaignCard, {
                key: c.id, campaign: c,
                onRerunSearch: onRerunSearch,
                onViewCreators: function(id) { setViewCreatorsFor(id); },
                onStatusChange: updateCampaignStatus,
              });
            })
      ),

      // Collabs tab
      activeTab === "collabs" && !isEmpty && (
        collabs.length === 0
          ? React.createElement("div", { style: { textAlign: "center", padding: 40, color: "#94a3b8" }},
              "No collaborations yet. Add creators using the + button on any creator card.")
          : React.createElement("div", { style: {
              background: "#ffffff", borderRadius: 14,
              border: "1px solid #e8ecf5", overflow: "hidden",
              boxShadow: "0 1px 4px rgba(15,23,42,0.06)",
            }},
              collabs.map(function(collab) {
                return React.createElement(CollabRow, {
                  key: collab.id, collab,
                  onViewCreator: onViewCreator,
                  onStatusChange: updateCollabStatus,
                });
              }),
            )
      ),

      // View creators modal
      viewCreatorsFor ? React.createElement(CreatorsModal, {
        campaignId: viewCreatorsFor,
        onClose:       function() { setViewCreatorsFor(null); },
        onViewCreator: onViewCreator,
      }) : null,
    );
  }

  window.RFCampaigns = CampaignsScreen;
})();
