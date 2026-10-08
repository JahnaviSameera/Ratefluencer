/* ============================================================
   AI Generator — content sections (class names match styles.css exactly)
   ============================================================ */

/* ---------------- Trends ---------------- */
function urgencyTone(u) {
  u = (u || "").toLowerCase();
  if (u === "breaking") return "urg-breaking";
  if (u === "rising")   return "urg-rising";
  return "urg-established";
}

function TrendCard({ trend, rank }) {
  const score = Math.max(0, Math.min(100, Number(trend.score) || 0));
  return (
    <div className="card trend-card">
      <div className="trend-top">
        <span className="trend-rank">{String(rank).padStart(2, "0")}</span>
        <span className={"badge " + urgencyTone(trend.urgency)}>
          {(trend.urgency || "—").toUpperCase()}
        </span>
      </div>
      <h3 className="trend-phrase">{trend.phrase}</h3>
      <div className="trend-score-row">
        <div className="bar"><div className="bar-fill" style={{ width: score + "%" }} /></div>
        <span className="trend-score-num">{score}</span>
      </div>
      <p className="trend-why">{trend.why_trending}</p>
      <div className="trend-meta">
        <div className="trend-angle"><Icon name="bolt" size={14} /><span>{trend.content_angle}</span></div>
        <div className="trend-aud"><Icon name="users" size={13} /><span>{trend.target_audience}</span></div>
      </div>
      <div className="trend-stats">
        <span>velocity <strong>{Math.round(Number(trend.velocity) || 0)}</strong></span>
        <span className="trend-stat-sep" />
        <span>accel <strong>+{Math.round(Number(trend.acceleration) || 0)}</strong></span>
      </div>
    </div>
  );
}

function TrendsSection({ trends }) {
  if (!trends || !trends.length) return null;
  return (
    <section className="section">
      <SectionHead icon="trending" title="Trending Now" count={trends.length} />
      <div className="trend-grid">
        {trends.map((t, i) => <TrendCard key={i} trend={t} rank={i + 1} />)}
      </div>
    </section>
  );
}

/* ---------------- Scripts (tabbed) ---------------- */
const TABS = [
  { key: "reel",      label: "Reel Script", icon: "file" },
  { key: "linkedin",  label: "LinkedIn",    icon: "linkedin" },
  { key: "instagram", label: "Instagram",   icon: "instagram" },
  { key: "thumb",     label: "Thumbnail",   icon: "photo" },
];

function ReelTab({ script }) {
  return (
    <div className="reel">
      <div className="kv"><span className="kv-key">Hook</span><p className="hook">{script.hook}</p></div>
      <div className="kv"><span className="kv-key">Story</span><p>{script.story}</p></div>
      <div className="kv">
        <span className="kv-key">Key Insights</span>
        <ul className="insights">
          {(script.insights || []).map((x, i) => (
            <li key={i}><span className="insight-n">{i + 1}</span><span>{x}</span></li>
          ))}
        </ul>
      </div>
      <div className="kv"><span className="kv-key">Call to action</span><p className="cta">{script.cta}</p></div>
    </div>
  );
}

function LinkedInTab({ script }) {
  const [show, setShow] = React.useState(false);
  return (
    <div className="social">
      <div className="social-actions">
        <CopyButton getText={() => script.linkedin_post || ""} label="Copy post" />
        <button onClick={() => setShow(s => !s)} style={{
          padding:"6px 12px", borderRadius:7, border:"1px solid rgba(0,119,181,0.4)",
          background:"rgba(0,119,181,0.12)", color:"#67b0e8", fontSize:12,
          fontWeight:700, cursor:"pointer"
        }}>👁 Preview</button>
      </div>
      <p className="social-body">{script.linkedin_post}</p>
      <HashRow tags={script.linkedin_hashtags} />
      {show && (
        <div style={{
          marginTop:14, background:"#1b1f23", border:"1px solid #2d3748",
          borderRadius:12, padding:16, fontSize:13,
        }}>
          <div style={{display:"flex",gap:10,marginBottom:10}}>
            <div style={{width:44,height:44,borderRadius:"50%",background:"linear-gradient(135deg,#0a66c2,#00a0dc)",display:"flex",alignItems:"center",justifyContent:"center",color:"#fff",fontWeight:800,fontSize:16,flexShrink:0}}>
              {(script.trend_phrase||"?")[0].toUpperCase()}
            </div>
            <div>
              <div style={{color:"#e2e8f0",fontWeight:700,fontSize:14}}>Your Name <span style={{fontSize:11,color:"#0a66c2",border:"1px solid #0a66c2",borderRadius:4,padding:"0 4px"}}>1st</span></div>
              <div style={{color:"#94a3b8",fontSize:11}}>Content Creator · just now · 🌐</div>
            </div>
          </div>
          <div style={{color:"#e2e8f0",lineHeight:1.6,whiteSpace:"pre-wrap"}}>{script.linkedin_post}</div>
          <div style={{marginTop:8,color:"#0a66c2",fontSize:12}}>{(script.linkedin_hashtags||[]).join(" ")}</div>
        </div>
      )}
    </div>
  );
}

function InstagramTab({ script }) {
  const words = window.countWords(script.instagram_caption);
  const tags  = window.countHashtags(script.instagram_hashtags);
  const [imgUrl, setImgUrl]       = React.useState(null);
  const [imgLoading, setImgLoading] = React.useState(false);
  const [showPreview, setShowPreview] = React.useState(false);

  async function generateImage() {
    setImgLoading(true);
    const phrase = (script.trend_phrase || "trending topic").toLowerCase();
    const niche  = script.niche || "technology";
    const prompt = `${phrase}. Cinematic portrait, dark moody, professional, no text. Theme: ${niche}`;
    try {
      const res = await fetch(`${window.API_BASE}/api/generate-image`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ prompt, query: phrase, aspect_ratio: "1:1" }),
      });
      const d = await res.json();
      setImgUrl(d.image_url);
    } catch(e) {}
    setImgLoading(false);
  }

  return (
    <div className="social">
      <div className="social-actions">
        <span className="social-meta">{words} words · {tags} tags</span>
        <CopyButton getText={() => script.instagram_caption || ""} label="Copy caption" />
        <button onClick={() => setShowPreview(s => !s)} style={{
          padding:"6px 12px", borderRadius:7, border:"1px solid rgba(225,48,108,0.4)",
          background:"rgba(225,48,108,0.12)", color:"#f472b6", fontSize:12,
          fontWeight:700, cursor:"pointer"
        }}>👁 Preview</button>
      </div>
      <p className="social-body">{script.instagram_caption}</p>
      <HashRow tags={script.instagram_hashtags} />

      <div style={{marginTop:14,display:"flex",gap:10,flexWrap:"wrap"}}>
        <button onClick={generateImage} disabled={imgLoading} style={{
          padding:"7px 14px", borderRadius:8, border:"none",
          background:"linear-gradient(135deg,#7c3aed,#a855f7)",
          color:"#fff", fontSize:12, fontWeight:700, cursor:"pointer"
        }}>
          {imgLoading ? "⟳ Generating…" : imgUrl ? "↺ Regenerate Image" : "✦ Generate Post Image"}
        </button>
      </div>

      {imgUrl && (
        <div style={{marginTop:10,borderRadius:10,overflow:"hidden",maxWidth:280}}>
          <img src={imgUrl} alt="post" style={{width:"100%",display:"block",borderRadius:10}} />
          <a href={imgUrl} download="ig-post.png" style={{display:"block",textAlign:"center",marginTop:6,fontSize:12,color:"#7c3aed",textDecoration:"underline"}}>↓ Download</a>
        </div>
      )}

      {showPreview && (
        <div style={{
          marginTop:14, background:"#000", borderRadius:16, overflow:"hidden",
          maxWidth:300, border:"1px solid #222", fontFamily:"-apple-system,sans-serif",
        }}>
          <div style={{padding:"10px 14px",display:"flex",alignItems:"center",gap:10,borderBottom:"1px solid #222"}}>
            <div style={{width:32,height:32,borderRadius:"50%",background:"linear-gradient(135deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888)",display:"flex",alignItems:"center",justifyContent:"center",color:"#fff",fontWeight:700,fontSize:13}}>
              {(script.trend_phrase||"?")[0].toUpperCase()}
            </div>
            <span style={{color:"#fff",fontWeight:600,fontSize:13}}>yourhandle</span>
          </div>
          {imgUrl
            ? <img src={imgUrl} alt="" style={{width:"100%",aspectRatio:"1/1",objectFit:"cover"}} />
            : <div style={{width:"100%",aspectRatio:"1/1",background:"linear-gradient(135deg,#1a1a2e,#16213e)",display:"flex",alignItems:"center",justifyContent:"center",color:"#4a5568",fontSize:12}}>Generate image above</div>
          }
          <div style={{padding:"10px 14px"}}>
            <div style={{fontSize:13,color:"#fff",marginBottom:6}}>{script.instagram_caption}</div>
            <div style={{fontSize:12,color:"#3b82f6"}}>{(script.instagram_hashtags||[]).slice(0,5).join(" ")}</div>
          </div>
        </div>
      )}
    </div>
  );
}

function ThumbTab({ script }) {
  return (
    <div className="thumb">
      <div className="thumb-preview">
        <div className="thumb-grain" />
        <div className="thumb-text">
          <div className="thumb-title">{script.thumbnail_title}</div>
          <div className="thumb-sub">{script.thumbnail_subtitle}</div>
        </div>
        <div className="thumb-badge"><Icon name="photo" size={14} /> 1280×720</div>
      </div>
      <div className="thumb-fields">
        <div className="kv"><span className="kv-key">Title</span><p>{script.thumbnail_title}</p></div>
        <div className="kv"><span className="kv-key">Subtitle</span><p>{script.thumbnail_subtitle}</p></div>
      </div>
    </div>
  );
}

function ScriptCard({ script, trend, virality }) {
  const [tab, setTab] = React.useState("reel");
  const v = virality || {};
  const verdict = v.verdict || window.verdictOf(v.score || 0);
  const sc = v.score != null ? v.score : null;

  return (
    <div className="card script-card">
      <div className="script-head">
        <div className="script-head-l">
          <div className="script-phrase">{script.trend_phrase || (trend && trend.phrase)}</div>
          {sc != null && (
            <span className={"badge " + (verdict.tone === "high" ? "urg-breaking" : verdict.tone === "mid" ? "urg-rising" : "urg-established")}>
              {verdict.emoji} {sc}/100
            </span>
          )}
        </div>
      </div>
      <div className="tabs" style={{ marginBottom: 14 }}>
        {TABS.map((t) => (
          <button key={t.key} className={"tab" + (tab === t.key ? " tab-active" : "")} onClick={() => setTab(t.key)}>
            <Icon name={t.icon} size={14} />
            <span>{t.label}</span>
          </button>
        ))}
      </div>
      <div className="tab-body">
        {tab === "reel"      && <ReelTab      script={script} />}
        {tab === "linkedin"  && <LinkedInTab  script={script} />}
        {tab === "instagram" && <InstagramTab script={script} />}
        {tab === "thumb"     && <ThumbTab     script={script} />}
      </div>
    </div>
  );
}

function ScriptsSection({ scripts, trends, virality }) {
  if (!scripts || !scripts.length) return null;
  return (
    <section className="section">
      <SectionHead icon="file" title="Script Generation" count={scripts.length} />
      <div className="script-grid">
        {scripts.map((s, i) => (
          <ScriptCard key={i} script={s} trend={trends && trends[i]} virality={virality && virality[i]} />
        ))}
      </div>
    </section>
  );
}

/* ---------------- Virality ---------------- */
function CircularScore({ score, tone }) {
  const r = 52, c = 2 * Math.PI * r;
  const pct   = Math.max(0, Math.min(100, Number(score) || 0));
  const dash  = (pct / 100) * c;
  const color = tone === "high" ? "#16a34a" : tone === "mid" ? "#d97706" : "#dc2626";
  return (
    <div className="dial">
      <svg width="130" height="130" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="65" cy="65" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="11" />
        <circle cx="65" cy="65" r={r} fill="none" stroke={color} strokeWidth="11"
          strokeDasharray={`${dash} ${c}`} strokeLinecap="round"
          style={{ transition: "stroke-dasharray 1s cubic-bezier(.2,.8,.2,1)" }} />
      </svg>
      <div className="dial-center">
        <div className="dial-num" style={{ color }}>{Math.round(pct)}</div>
        <div className="dial-of">/ 100</div>
      </div>
    </div>
  );
}

const METRIC_META = [
  { key: "views",  label: "Views",  icon: "eye" },
  { key: "likes",  label: "Likes",  icon: "heart" },
  { key: "shares", label: "Shares", icon: "share" },
  { key: "saves",  label: "Saves",  icon: "bookmark" },
];

function ViralityCard({ result, trend }) {
  const verdict = result.verdict || window.verdictOf(result.score);
  const top     = window.topFactors(result.factors || [], 5);
  return (
    <div className="card virality-card">
      <div className="vc-l">
        <CircularScore score={result.score} tone={verdict.tone} />
        <div className={"verdict tone-" + (verdict.tone || "mid")}>
          <span className="verdict-emoji">{verdict.emoji}</span>
          <span>{verdict.label}</span>
        </div>
        <div className="vc-phrase">{trend ? trend.phrase : ""}</div>
      </div>
      <div className="vc-r">
        <div className="metrics">
          {METRIC_META.map((m) => (
            <div className="metric" key={m.key}>
              <Icon name={m.icon} size={15} className="metric-icon" />
              <span className="metric-val">{window.fmtNum((result.metrics || {})[m.key])}</span>
              <span className="metric-label">{m.label}</span>
            </div>
          ))}
        </div>
        <div className="factors">
          <div className="factors-head">Top factors</div>
          {top.map((f) => (
            <div className="factor" key={f.key}>
              <span className="factor-label">{f.key}</span>
              <div className="bar bar-sm">
                <div className="bar-fill" style={{ width: Math.round(f.value * 100) + "%" }} />
              </div>
              <span className="factor-val">{Math.round(f.value * 100)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ViralitySection({ virality, trends }) {
  if (!virality || !virality.length) return null;
  return (
    <section className="section">
      <SectionHead icon="gauge" title="Virality Prediction" count={virality.length} />
      <div className="virality-grid">
        {virality.map((v, i) => <ViralityCard key={i} result={v} trend={trends && trends[i]} />)}
      </div>
    </section>
  );
}

Object.assign(window, {
  TrendsSection,
  ScriptsSection,
  ViralitySection,
});
