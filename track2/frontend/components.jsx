/* ============================================================
   AI Generator — shared components & Tabler-style icon set
   ============================================================ */
const { useState, useEffect, useRef } = React;

/* ---------------- Icon set (Tabler outline) ---------------- */
const ICON_PATHS = {
  sparkles:
    "M16 18a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2zm0 -12a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2zm-7 12a6 6 0 0 1 6 -6a6 6 0 0 1 -6 -6a6 6 0 0 1 -6 6a6 6 0 0 1 6 6z",
  trending:
    "M3 17l6 -6l4 4l8 -8 M14 7l7 0l0 7",
  bolt: "M13 3l0 7l6 0l-8 11l0 -7l-6 0l8 -11",
  file:
    "M14 3v4a1 1 0 0 0 1 1h4 M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2z M9 13l6 0 M9 17l4 0",
  gauge:
    "M13.45 11.55l2.05 -2.05 M6.4 20a9 9 0 1 1 11.2 0z",
  package:
    "M12 3l8 4.5v9l-8 4.5l-8 -4.5v-9l8 -4.5 M12 12l8 -4.5 M12 12l0 9 M12 12l-8 -4.5 M16 5.25l-8 4.5",
  key:
    "M16.555 3.843l3.602 3.602a2.877 2.877 0 0 1 0 4.069l-2.643 2.643a2.877 2.877 0 0 1 -4.069 0l-.301 -.301l-6.558 6.558a2 2 0 0 1 -1.239 .578l-.175 .008h-1.172a1 1 0 0 1 -.993 -.883l-.007 -.117v-1.172a2 2 0 0 1 .467 -1.284l.119 -.13l.414 -.414h2v-2h2v-2l2.144 -2.144l-.301 -.301a2.877 2.877 0 0 1 0 -4.069l2.643 -2.643a2.877 2.877 0 0 1 4.069 0z M15 9h.01",
  download:
    "M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2 M7 11l5 5l5 -5 M12 4l0 12",
  chevron: "M6 9l6 6l6 -6",
  check: "M5 12l5 5l10 -10",
  alert:
    "M12 9v4 M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0z M12 16h.01",
  loader: "M12 3a9 9 0 1 0 9 9",
  eye:
    "M10 12a2 2 0 1 0 4 0a2 2 0 0 0 -4 0 M21 12c-2.4 4 -5.4 6 -9 6c-3.6 0 -6.6 -2 -9 -6c2.4 -4 5.4 -6 9 -6c3.6 0 6.6 2 9 6",
  heart:
    "M19.5 12.572l-7.5 7.428l-7.5 -7.428a5 5 0 1 1 7.5 -6.566a5 5 0 1 1 7.5 6.572",
  share:
    "M6 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0 M18 6m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0 M18 18m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0 M8.7 10.7l6.6 -3.4 M8.7 13.3l6.6 3.4",
  bookmark:
    "M9 4h6a2 2 0 0 1 2 2v14l-5 -3l-5 3v-14a2 2 0 0 1 2 -2",
  linkedin:
    "M8 11l0 5 M8 8l0 .01 M12 16l0 -5 M16 16v-3a2 2 0 0 0 -4 0 M4 4m0 2a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2z",
  instagram:
    "M4 4m0 4a4 4 0 0 1 4 -4h8a4 4 0 0 1 4 4v8a4 4 0 0 1 -4 4h-8a4 4 0 0 1 -4 -4z M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0 M16.5 7.5l0 .01",
  photo:
    "M15 8h.01 M3 6a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v12a3 3 0 0 1 -3 3h-12a3 3 0 0 1 -3 -3v-12z M3 16l5 -5c.928 -.893 2.072 -.893 3 0l5 5 M14 14l1 -1c.928 -.893 2.072 -.893 3 0l3 3",
  copy:
    "M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z M4.012 16.737a2 2 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1",
  clock:
    "M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0 M12 7v5l3 3",
  target:
    "M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0 M12 12m-5 0a5 5 0 1 0 10 0a5 5 0 1 0 -10 0 M12 12m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",
  flame:
    "M12 12c2 -2.96 0 -7 -1 -8c0 3.038 -1.773 4.741 -3 6c-1.226 1.26 -2 3.24 -2 5a6 6 0 1 0 12 0c0 -1.532 -1.056 -3.94 -2 -5c-1.786 3 -2.791 3 -4 2z",
  users:
    "M9 7m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0 M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2 M16 3.13a4 4 0 0 1 0 7.75 M21 21v-2a4 4 0 0 0 -3 -3.85",
};

function Icon({ name, size = 18, className = "", style = {} }) {
  const d = ICON_PATHS[name];
  return (
    <svg
      className={"ic " + className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={style}
      aria-hidden="true"
    >
      {d
        .trim()
        .split(/\s(?=M)/)
        .map((seg, i) => (
          <path key={i} d={seg} />
        ))}
    </svg>
  );
}

/* ---------------- Top bar ---------------- */
function TopBar({
  niche,
  setNiche,
  apiKey,
  setApiKey,
  onGenerate,
  isRunning,
  canExport,
  onExport,
  keyError,
}) {
  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-mark">
          <Icon name="sparkles" size={20} />
        </div>
        <div className="brand-text">
          <div className="brand-name">AI Generator</div>
          <div className="brand-sub">Viral Content Intelligence</div>
        </div>
      </div>

      <div className="controls">
        <label className="field niche-field">
          <select
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            disabled={isRunning}
          >
            {window.NICHES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          <Icon name="chevron" size={16} className="select-chevron" />
        </label>

        <label className={"field key-field" + (keyError ? " field-error" : "")}>
          <Icon name="key" size={16} className="field-icon" />
          <input
            type="password"
            value={apiKey}
            placeholder="Gemini key (optional — server uses .env)"
            onChange={(e) => setApiKey(e.target.value)}
            disabled={isRunning}
            spellCheck={false}
          />
        </label>

        <button
          className="btn btn-secondary"
          onClick={onExport}
          disabled={!canExport}
          title="Download full JSON package"
        >
          <Icon name="download" size={16} />
          <span>Export</span>
        </button>

        <button className="btn btn-primary" onClick={onGenerate} disabled={isRunning}>
          {isRunning ? (
            <Icon name="loader" size={16} className="spin" />
          ) : (
            <Icon name="bolt" size={16} />
          )}
          <span>{isRunning ? "Generating…" : "Generate"}</span>
        </button>
      </div>
    </header>
  );
}

/* ---------------- Pipeline status bar ---------------- */
const PIPELINE_META = [
  { key: "trends", label: "Trend Discovery", icon: "trending", hint: "Scraping HN + Google News… (~40s)" },
  { key: "scripts", label: "Script Generation", icon: "file",   hint: "Gemini writing scripts…" },
  { key: "virality", label: "Virality Prediction", icon: "gauge", hint: "Scoring with XGBoost…" },
  { key: "package", label: "Content Package", icon: "package", hint: "Packaging output…" },
];

function StepDot({ status }) {
  if (status === "running")
    return <Icon name="loader" size={14} className="spin" />;
  if (status === "done") return <Icon name="check" size={14} />;
  if (status === "error") return <Icon name="alert" size={14} />;
  return <span className="dot-idle" />;
}

function PipelineBar({ pipeline, errors }) {
  return (
    <div className="pipeline">
      {PIPELINE_META.map((s, i) => {
        const status = pipeline[s.key] || "idle";
        return (
          <React.Fragment key={s.key}>
            <div className={"pstep pstep-" + status}>
              <div className="pstep-icon">
                <Icon name={s.icon} size={18} />
              </div>
              <div className="pstep-body">
                <div className="pstep-label">{s.label}</div>
                <div className="pstep-status">
                  <StepDot status={status} />
                  <span>
                    {status === "error"
                      ? errors[s.key] || "Error"
                      : status === "running"
                      ? (s.hint || "Running…")
                      : status[0].toUpperCase() + status.slice(1)}
                  </span>
                </div>
              </div>
              <div className="pstep-num">{String(i + 1).padStart(2, "0")}</div>
            </div>
            {i < PIPELINE_META.length - 1 && (
              <div
                className={
                  "pconn " +
                  (pipeline[s.key] === "done" ? "pconn-done" : "")
                }
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

/* ---------------- Empty state ---------------- */
function EmptyState({ onSample, isRunning }) {
  return (
    <div className="empty">
      <div className="empty-glow" />
      <div className="empty-mark">
        <Icon name="sparkles" size={34} />
      </div>
      <h1 className="empty-title">Turn any niche into viral-ready content</h1>
      <p className="empty-sub">
        Pick a niche and hit <strong>Generate</strong>. The pipeline discovers
        live trends, writes reel scripts plus social copy, and predicts a
        virality score for each — all in one run.
      </p>
      <div className="empty-steps">
        {PIPELINE_META.map((s, i) => (
          <div className="empty-step" key={s.key}>
            <Icon name={s.icon} size={16} />
            <span>{s.label}</span>
            {i < PIPELINE_META.length - 1 && <span className="empty-arrow">→</span>}
          </div>
        ))}
      </div>
      <div style={{display:"flex",alignItems:"center",gap:8,marginTop:8,padding:"12px 18px",borderRadius:10,background:"rgba(124,108,255,0.1)",border:"1px solid rgba(124,108,255,0.25)",color:"#a78bfa",fontSize:13,fontWeight:600}}>
        <span>👆</span>
        <span>Select a niche from the dropdown above, then click <strong>Generate</strong></span>
      </div>
    </div>
  );
}

/* ---------------- Small shared bits ---------------- */
function SectionHead({ icon, title, count, children }) {
  return (
    <div className="section-head">
      <div className="section-head-l">
        <Icon name={icon} size={18} className="section-icon" />
        <h2 className="section-title">{title}</h2>
        {count != null && <span className="section-count">{count}</span>}
      </div>
      {children}
    </div>
  );
}

function CopyButton({ getText, label = "Copy" }) {
  const [done, setDone] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(getText());
    } catch (_) {
      const ta = document.createElement("textarea");
      ta.value = getText();
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setDone(true);
    setTimeout(() => setDone(false), 1400);
  };
  return (
    <button className="copy-btn" onClick={copy}>
      <Icon name={done ? "check" : "copy"} size={14} />
      <span>{done ? "Copied" : label}</span>
    </button>
  );
}

function HashRow({ tags }) {
  const arr = Array.isArray(tags) ? tags : [];
  return (
    <div className="hash-row">
      {arr.map((t, i) => (
        <span className="hash" key={i}>
          {("" + t).startsWith("#") ? t : "#" + t}
        </span>
      ))}
    </div>
  );
}

Object.assign(window, {
  Icon,
  TopBar,
  PipelineBar,
  PIPELINE_META,
  EmptyState,
  SectionHead,
  CopyButton,
  HashRow,
});
