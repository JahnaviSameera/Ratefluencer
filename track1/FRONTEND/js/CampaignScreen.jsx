/* Ratefluencer — Campaign Planner Screen
   Full autonomous pipeline: Brief → Optimize → Search → Compare → Budget → Email */
(function () {
  const { useState } = React;
  const { L, formatFollowers, fmtScore, titleCase, NicheBadge, TierBadge } = window.RF;
  const BASE = window.RFApi.BASE;

  const STEP_LABELS = [
    { key:"s1", icon:"✦", label:"Optimize Brief",        desc:"Gemini refines your campaign" },
    { key:"s2", icon:"🔍", label:"Find Influencers",      desc:"ML ranks 5,364 profiles" },
    { key:"s3", icon:"⚡", label:"Compare & Pick Winner", desc:"AI compares top 3" },
    { key:"s4", icon:"💰", label:"Budget & ROI",          desc:"ML estimates campaign ROI" },
    { key:"s5", icon:"✉", label:"Outreach Email",         desc:"Gemini drafts personalised pitch" },
  ];

  function StepIndicator({ steps, currentStep, result }) {
    return React.createElement("div", { style:{
      display:"flex", gap:0, marginBottom:32, position:"relative",
    } },
      // connector line
      React.createElement("div", { style:{
        position:"absolute", top:18, left:24, right:24, height:2,
        background:"rgba(15,23,42,0.07)", zIndex:0,
      } }),
      React.createElement("div", { style:{
        position:"absolute", top:18, left:24, height:2, zIndex:1,
        background:"linear-gradient(90deg,#7c3aed,#06b6d4)",
        width: currentStep >= steps.length ? "calc(100% - 48px)"
             : `calc(${(currentStep / (steps.length-1)) * 100}% - 48px)`,
        transition:"width 0.8s ease",
      } }),
      steps.map((s, i) => {
        const done    = result && Object.keys(result).some(k => k.startsWith(`step${i+1}`));
        const active  = i === currentStep && !done;
        const pending = i > currentStep;
        return React.createElement("div", { key:s.key, style:{
          flex:1, display:"flex", flexDirection:"column", alignItems:"center", zIndex:2,
        } },
          React.createElement("div", { style:{
            width:36, height:36, borderRadius:"50%", fontSize:15,
            display:"flex", alignItems:"center", justifyContent:"center",
            background: done    ? "linear-gradient(135deg,#7c3aed,#06b6d4)"
                       : active  ? "rgba(124,108,255,0.3)"
                       : "rgba(15,23,42,0.05)",
            border: active ? "2px solid #7c3aed" : done ? "none" : "2px solid rgba(15,23,42,0.08)",
            boxShadow: active ? "0 0 16px rgba(124,108,255,0.5)" : "none",
            animation: active ? "rf-pulse 1.5s infinite" : "none",
            transition:"all 0.5s",
          } }, done ? "✓" : s.icon),
          React.createElement("div", { style:{
            fontSize:10, fontWeight:700, color: done ? "#0f172a" : pending ? "#475569" : "#a78bfa",
            marginTop:6, textAlign:"center", lineHeight:1.4,
          } }, s.label),
        );
      })
    );
  }

  function CampaignScreen({ onBack }) {
    const [category,  setCategory]  = useState("");
    const [desc,      setDesc]       = useState("");
    const [goal,      setGoal]       = useState("Awareness");
    const [budget,    setBudget]     = useState("");
    const [niche,     setNiche]      = useState("");
    const [running,   setRunning]    = useState(false);
    const [step,      setStep]       = useState(-1);
    const [result,    setResult]     = useState(null);
    const [error,     setError]      = useState("");
    const [copied,    setCopied]     = useState(false);

    const GOALS   = ["Awareness","Conversions","Engagement","Reach"];
    const NICHES  = ["Fitness","Health & Wellness","Yoga & Meditation","Nutrition & Diet",
                     "Fashion","Beauty & Skincare","Lifestyle Vlogging","Travel","Food & Cooking",
                     "Technology","Gaming","Finance & Investing","Entrepreneurship","Sports & Athletics",
                     "Mental Health","Music & Dance","Comedy & Entertainment","Parenting & Family"];

    async function runCampaign() {
      if (!category.trim()) { setError("Enter a campaign category"); return; }
      if (!budget || parseInt(budget) <= 0) { setError("Enter your budget"); return; }
      setError(""); setRunning(true); setResult(null); setStep(0);

      try {
        const timer = (n) => new Promise(r => setTimeout(r, n));

        // Step 1 — create campaign in My Campaigns
        setStep(0); await timer(800);
        var campId = Date.now().toString();
        var brief  = { category, product_description: desc, campaign_goal: goal, niche };
        var campaigns = [];
        try { campaigns = JSON.parse(localStorage.getItem('rf_campaigns') || '[]'); } catch(e) {}
        campaigns.unshift({
          id: campId, name: category, brief: brief,
          status: 'Planning', date: new Date().toISOString(), matchedCount: 0,
        });
        localStorage.setItem('rf_campaigns', JSON.stringify(campaigns.slice(0, 30)));
        localStorage.setItem('rf_active_campaign', campId);

        setStep(1); await timer(600);
        setStep(2); await timer(500);
        setStep(3); await timer(400);
        setStep(4);

        const res = await fetch(`${BASE}/api/run-campaign`, {
          method:"POST", headers:{"Content-Type":"application/json"},
          body: JSON.stringify({
            category, product_description: desc,
            campaign_goal: goal, niche,
            budget_inr: parseInt(budget), top_n: 3,
          }),
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Pipeline failed"); }
        const data = await res.json();

        // Step 3 complete — winner found → add to collaborations as Shortlisted
        if (data.step3_winner) {
          var winner = data.step3_winner;
          var collabs = [];
          try { collabs = JSON.parse(localStorage.getItem('rf_collabs') || '[]'); } catch(e) {}
          var key = String(winner.id || winner.username) + '_' + campId;
          if (!collabs.find(function(c) { return c.id === key; })) {
            collabs.unshift({
              id: key,
              creatorId: String(winner.id || winner.username),
              creator: {
                id: winner.id || winner.username,
                username: winner.username, full_name: winner.full_name || winner.username,
                niche: winner.niche, followers_count: winner.followers,
                ratefluencer_score: winner.ratefluencer || 0,
                tier: winner.tier || "Micro", is_verified: false,
              },
              campaignId: campId, campaignName: category,
              status: 'Shortlisted', date: new Date().toISOString(),
            });
            localStorage.setItem('rf_collabs', JSON.stringify(collabs));
          }
          // Update campaign matchedCount
          var campList = JSON.parse(localStorage.getItem('rf_campaigns') || '[]');
          var ci = campList.findIndex(function(c) { return c.id === campId; });
          if (ci >= 0) { campList[ci].matchedCount = 3; campList[ci].status = 'Active'; }
          localStorage.setItem('rf_campaigns', JSON.stringify(campList));
        }

        // Step 5 complete — email ready → update collab to Contacted
        if (data.step5_outreach_email && data.step3_winner) {
          var winner = data.step3_winner;
          var collabs2 = JSON.parse(localStorage.getItem('rf_collabs') || '[]');
          var key2 = String(winner.id || winner.username) + '_' + campId;
          var ci2 = collabs2.findIndex(function(c) { return c.id === key2; });
          if (ci2 >= 0) { collabs2[ci2].status = 'Contacted'; }
          localStorage.setItem('rf_collabs', JSON.stringify(collabs2));
        }

        setResult(data);
        setStep(5);
      } catch(e) { setError(e.message || "Pipeline failed"); }
      setRunning(false);
    }

    function copyEmail() {
      if (!result?.step5_outreach_email) return;
      const e = result.step5_outreach_email;
      navigator.clipboard.writeText(`Subject: ${e.subject}\n\n${e.body}`);
      setCopied(true); setTimeout(() => setCopied(false), 2000);
    }

    const fmt = n => n >= 1e7 ? (n/1e7).toFixed(1)+"Cr"
                   : n >= 1e5 ? (n/1e5).toFixed(1)+"L"
                   : n >= 1e3 ? (n/1e3).toFixed(0)+"K"
                   : String(n||0);

    return React.createElement("div", { className:"rf-discover" },
      // Header
      React.createElement("div", { style:{ display:"flex", alignItems:"center", gap:14, marginBottom:24 } },
        React.createElement("button", { className:"rf-backbtn", onClick:onBack, style:{ marginBottom:0 } },
          React.createElement(L.ArrowLeft, { size:16 }), "Back"),
        React.createElement("div", null,
          React.createElement("h1", { className:"rf-page-title", style:{ margin:0 } },
            "🚀 Full Campaign Planner"),
          React.createElement("p", { style:{ color:"#64748b", fontSize:13, margin:0 } },
            "One brief → complete campaign: influencer + budget + outreach email"),
        ),
      ),

      // Input form (only show when not running/done)
      !running && !result && React.createElement("div", { style:{
        background:"#ffffff", border:"1px solid rgba(124,108,255,0.2)",
        borderRadius:16, padding:24, marginBottom:24,
      } },
        React.createElement("div", { style:{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, marginBottom:16 } },
          React.createElement("div", null,
            React.createElement("div", { style:{ fontSize:11, color:"#64748b", fontWeight:700, textTransform:"uppercase", marginBottom:6 } }, "Campaign Category *"),
            React.createElement("input", { className:"rf-input",
              placeholder:"e.g. yoga mats, protein powder, fitness app",
              value: category, onChange: e => setCategory(e.target.value),
            }),
          ),
          React.createElement("div", null,
            React.createElement("div", { style:{ fontSize:11, color:"#64748b", fontWeight:700, textTransform:"uppercase", marginBottom:6 } }, "Budget (₹) *"),
            React.createElement("input", { className:"rf-input", type:"number",
              placeholder:"e.g. 100000",
              value: budget, onChange: e => setBudget(e.target.value),
            }),
          ),
        ),
        React.createElement("div", { style:{ marginBottom:16 } },
          React.createElement("div", { style:{ fontSize:11, color:"#64748b", fontWeight:700, textTransform:"uppercase", marginBottom:6 } }, "Product Description"),
          React.createElement("textarea", { className:"rf-input rf-textarea", rows:2,
            placeholder:"What are you promoting? What makes it special?",
            value: desc, onChange: e => setDesc(e.target.value),
          }),
        ),
        React.createElement("div", { style:{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, marginBottom:20 } },
          React.createElement("div", null,
            React.createElement("div", { style:{ fontSize:11, color:"#64748b", fontWeight:700, textTransform:"uppercase", marginBottom:6 } }, "Campaign Goal"),
            React.createElement("select", { className:"rf-input rf-select", value:goal, onChange:e=>setGoal(e.target.value) },
              GOALS.map(g => React.createElement("option", { key:g, value:g }, g))
            ),
          ),
          React.createElement("div", null,
            React.createElement("div", { style:{ fontSize:11, color:"#64748b", fontWeight:700, textTransform:"uppercase", marginBottom:6 } }, "Niche (optional)"),
            React.createElement("select", { className:"rf-input rf-select", value:niche, onChange:e=>setNiche(e.target.value) },
              React.createElement("option", { value:"" }, "Any niche (AI decides)"),
              NICHES.map(n => React.createElement("option", { key:n, value:n }, n))
            ),
          ),
        ),
        error && React.createElement("div", { style:{ color:"#f87171", fontSize:13, marginBottom:12 } }, "⚠ " + error),
        React.createElement("button", { onClick:runCampaign, disabled:!category||!budget, style:{
          width:"100%", padding:"14px", borderRadius:12, border:"none",
          background:"linear-gradient(135deg,#7c3aed,#06b6d4)",
          color:"#fff", fontSize:15, fontWeight:800, cursor:"pointer",
          opacity: (!category||!budget) ? 0.5 : 1,
          display:"flex", alignItems:"center", justifyContent:"center", gap:10,
        } },
          React.createElement(L.Rocket, { size:18 }), "Run Full Campaign Pipeline"
        ),
      ),

      // Step progress (shown while running or done)
      (running || result) && React.createElement("div", { style:{ marginBottom:28 } },
        React.createElement(StepIndicator, { steps:STEP_LABELS, currentStep:step, result }),
        running && React.createElement("div", { style:{ textAlign:"center", color:"#a78bfa", fontSize:13, marginTop:8 } },
          STEP_LABELS[Math.min(step, 4)]?.desc + "…"
        ),
      ),

      // Results
      result && React.createElement("div", { style:{ display:"flex", flexDirection:"column", gap:16 } },

        // Step 1: Optimized Brief
        result.step1_optimized_brief && React.createElement("div", { style:{
          background:"rgba(124,108,255,0.08)", border:"1px solid rgba(124,108,255,0.2)",
          borderRadius:12, padding:18,
        } },
          React.createElement("div", { style:{ fontSize:12, color:"#7c6cff", fontWeight:700, marginBottom:10 } }, "✦ STEP 1 — Brief Optimized by Gemini"),
          React.createElement("div", { style:{ display:"flex", gap:8, flexWrap:"wrap", marginBottom:8 } },
            (result.step1_optimized_brief.target_niches || []).map(n =>
              React.createElement("span", { key:n, style:{
                padding:"3px 10px", borderRadius:99, fontSize:12, fontWeight:600,
                background:"rgba(124,108,255,0.2)", color:"#a78bfa",
              } }, n)
            )
          ),
          result.step1_optimized_brief.ideal_persona && React.createElement("div", { style:{ color:"#94a3b8", fontSize:13, lineHeight:1.6 } },
            result.step1_optimized_brief.ideal_persona.slice(0, 150) + "…"
          ),
        ),

        // Step 2+3: Winner
        result.step3_winner && React.createElement("div", { style:{
          background:"rgba(6,182,212,0.08)", border:"2px solid rgba(6,182,212,0.3)",
          borderRadius:12, padding:18,
        } },
          React.createElement("div", { style:{ fontSize:12, color:"#67e8f9", fontWeight:700, marginBottom:10 } }, "🏆 STEP 2+3 — Best Influencer Selected"),
          React.createElement("div", { style:{ display:"flex", alignItems:"center", gap:16, marginBottom:10 } },
            React.createElement("div", { style:{
              width:52, height:52, borderRadius:"50%", flexShrink:0,
              background:`url(https://api.dicebear.com/7.x/avataaars/svg?seed=${result.step3_winner.username}&backgroundColor=b6e3f4&backgroundType=gradientLinear)`,
              backgroundSize:"cover",
            } }),
            React.createElement("div", null,
              React.createElement("div", { style:{ color:"#0f172a", fontWeight:800, fontSize:16 } }, "@" + result.step3_winner.username),
              React.createElement("div", { style:{ color:"#64748b", fontSize:12 } }, result.step3_winner.niche),
              React.createElement("div", { style:{ display:"flex", gap:12, marginTop:4 } },
                [["👥", formatFollowers(result.step3_winner.followers)],
                 ["🛡", (result.step3_winner.authenticity||0) + "/100"],
                 ["⭐", (result.step3_winner.ratefluencer||0) + "/100"]].map(([ico, val]) =>
                  React.createElement("span", { key:ico, style:{ color:"#94a3b8", fontSize:12 } }, ico + " " + val)
                ),
              ),
            ),
          ),
          result.step3_winner.why && React.createElement("div", { style:{
            background:"rgba(6,182,212,0.1)", borderRadius:8, padding:10,
            color:"#a5f3fc", fontSize:13, lineHeight:1.6,
          } }, "💡 " + result.step3_winner.why),
        ),

        // Step 4: Budget
        result.step4_budget && React.createElement("div", { style:{
          background:"rgba(249,115,22,0.08)", border:"1px solid rgba(249,115,22,0.2)",
          borderRadius:12, padding:18,
        } },
          React.createElement("div", { style:{ fontSize:12, color:"#f97316", fontWeight:700, marginBottom:12 } }, "💰 STEP 4 — Budget & ROI Estimate"),
          React.createElement("div", { style:{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:10, marginBottom:12 } },
            [["Reach",       fmt(result.step4_budget.total_reach)],
             ["Impressions", fmt(result.step4_budget.estimated_impressions)],
             ["Conversions", (result.step4_budget.estimated_conversions||0).toLocaleString()],
             ["ROI",         (result.step4_budget.roi_multiplier||0) + "x"]].map(([k,v]) =>
              React.createElement("div", { key:k, style:{
                background:"rgba(15,23,42,0.04)", borderRadius:8, padding:10, textAlign:"center",
              } },
                React.createElement("div", { style:{ color:"#f97316", fontSize:18, fontWeight:800 } }, v),
                React.createElement("div", { style:{ color:"#64748b", fontSize:10, marginTop:2 } }, k),
              )
            )
          ),
          result.step4_budget.strategy && React.createElement("div", { style:{ color:"#94a3b8", fontSize:13, lineHeight:1.6 } },
            "🤖 " + result.step4_budget.strategy
          ),
        ),

        // Step 5: Email
        result.step5_outreach_email && React.createElement("div", { style:{
          background:"rgba(16,185,129,0.08)", border:"2px solid rgba(16,185,129,0.3)",
          borderRadius:12, padding:18,
        } },
          React.createElement("div", { style:{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12 } },
            React.createElement("div", { style:{ fontSize:12, color:"#34d399", fontWeight:700 } }, "✉ STEP 5 — Outreach Email Ready"),
            React.createElement("button", { onClick:copyEmail, style:{
              padding:"8px 16px", borderRadius:8, border:"none", cursor:"pointer",
              background: copied ? "rgba(34,197,94,0.2)" : "rgba(16,185,129,0.2)",
              color: copied ? "#4ade80" : "#34d399", fontSize:12, fontWeight:700,
              display:"flex", alignItems:"center", gap:6,
            } },
              React.createElement(L.Copy, { size:13 }), copied ? "Copied!" : "Copy Email"
            ),
          ),
          React.createElement("div", { style:{
            background:"rgba(15,23,42,0.04)", borderRadius:8, padding:14, marginBottom:10,
          } },
            React.createElement("div", { style:{ fontSize:11, color:"#64748b", fontWeight:700, textTransform:"uppercase", marginBottom:4 } }, "Subject"),
            React.createElement("div", { style:{ color:"#0f172a", fontWeight:600, marginBottom:12 } },
              result.step5_outreach_email.subject
            ),
            React.createElement("div", { style:{ fontSize:11, color:"#64748b", fontWeight:700, textTransform:"uppercase", marginBottom:4 } }, "Body"),
            React.createElement("div", { style:{ color:"#334155", fontSize:13, lineHeight:1.8, whiteSpace:"pre-wrap" } },
              result.step5_outreach_email.body
            ),
          ),
          result.step5_outreach_email.cta && React.createElement("div", { style:{
            background:"rgba(16,185,129,0.1)", borderRadius:7, padding:"8px 12px",
            fontSize:12, color:"#6ee7b7",
          } }, "CTA: ", React.createElement("b", null, result.step5_outreach_email.cta)),
        ),

        // Jump to My Campaigns
        React.createElement("div", { style:{ display:"flex", gap:10 } },
          React.createElement("button", { onClick: function() {
              // navigate to campaigns tab
              var ev = new CustomEvent('rf-goto', { detail: 'campaigns' });
              window.dispatchEvent(ev);
            }, style:{
              flex:1, padding:"12px", borderRadius:10, border:"none",
              background:"linear-gradient(135deg,#6d28d9,#4f46e5)",
              color:"#fff", fontSize:13, fontWeight:700, cursor:"pointer",
              display:"flex", alignItems:"center", justifyContent:"center", gap:8,
            }},
            React.createElement(L.Briefcase, { size:15 }), "View in My Campaigns →"
          ),
          React.createElement("button", { onClick:()=>{ setResult(null); setStep(-1); }, style:{
            padding:"12px 20px", borderRadius:10, border:"1px solid rgba(15,23,42,0.08)",
            background:"transparent", color:"#94a3b8", fontSize:13, cursor:"pointer",
          }}, "↺ Run another"),
        ),
      ),
    );
  }

  window.RFCampaign = CampaignScreen;
})();
