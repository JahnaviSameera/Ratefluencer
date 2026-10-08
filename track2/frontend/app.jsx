/* ============================================================
   AI Generator — App (state + pipeline orchestration + export)
   ============================================================ */

function App() {
  const [niche, setNiche] = useState(window.NICHES[0]);
  const [apiKey, setApiKey] = useState("");
  const [keyError, setKeyError] = useState(false);

  const [pipeline, setPipeline] = useState({
    trends: "idle",
    scripts: "idle",
    virality: "idle",
    package: "idle",
  });
  const [errors, setErrors] = useState({});
  const [isRunning, setIsRunning] = useState(false);

  const [trends, setTrends] = useState([]);
  const [scripts, setScripts] = useState([]);
  const [virality, setVirality] = useState([]);

  const hasRun =
    trends.length > 0 || scripts.length > 0 || virality.length > 0 || isRunning;

  const setStep = (key, status, err) => {
    setPipeline((p) => ({ ...p, [key]: status }));
    if (err) setErrors((e) => ({ ...e, [key]: err }));
  };

  const reset = () => {
    setPipeline({ trends: "idle", scripts: "idle", virality: "idle", package: "idle" });
    setErrors({});
    setTrends([]);
    setScripts([]);
    setVirality([]);
  };

  const scoreAll = (scriptsArr, trendsArr, nicheVal) =>
    scriptsArr.map((s, i) => {
      const { score, factors } = window.scoreScript(s, trendsArr[i], nicheVal);
      return {
        score,
        factors,
        metrics: window.predictMetrics(score),
        verdict: window.verdictOf(score),
      };
    });

  /* ---- live run via Python backend ---- */
  const generate = async () => {
    reset();
    setIsRunning(true);

    // Stage 1 — Trend Discovery (Python: trend_agent)
    setStep("trends", "running");
    let trendData;
    try {
      trendData = await window.fetchTrends(niche);
      if (!trendData.length) throw new Error("No trends returned");
      setTrends(trendData);
      setStep("trends", "done");
    } catch (e) {
      setStep("trends", "error", shortErr(e));
      setIsRunning(false);
      return;
    }

    // Stage 2 — Script Generation (Python: script_generator + Gemini)
    setStep("scripts", "running");
    const top3 = trendData.slice(0, 3);
    let scriptData;
    try {
      scriptData = await window.fetchScripts(niche, top3);
      if (!scriptData.length) throw new Error("No scripts returned");
      setScripts(scriptData);
      setStep("scripts", "done");
    } catch (e) {
      setStep("scripts", "error", shortErr(e));
      setIsRunning(false);
      return;
    }

    // Stage 3 — Virality Prediction (Python: XGBoost model)
    setStep("virality", "running");
    let viralityData;
    try {
      viralityData = await window.fetchVirality(scriptData);
      setVirality(viralityData);
      setStep("virality", "done");
    } catch (e) {
      // Fallback to JS scoring if backend virality fails
      const scored = scoreAll(scriptData, top3, niche);
      setVirality(scored);
      setStep("virality", "done");
    }

    // Stage 4 — Content Package
    setStep("package", "running");
    await window.delay(350);
    setStep("package", "done");
    setIsRunning(false);
  };

  /* ---- sample run (no API) — simulated pipeline for demos ---- */
  const sampleRun = async () => {
    reset();
    setIsRunning(true);
    setNiche(window.SAMPLE_NICHE);

    setStep("trends", "running");
    await window.delay(650);
    setTrends(window.SAMPLE_TRENDS);
    setStep("trends", "done");

    setStep("scripts", "running");
    await window.delay(800);
    const top3 = window.SAMPLE_TRENDS.slice(0, 3);
    setScripts(window.SAMPLE_SCRIPTS);
    setStep("scripts", "done");

    setStep("virality", "running");
    await window.delay(550);
    setVirality(scoreAll(window.SAMPLE_SCRIPTS, top3, window.SAMPLE_NICHE));
    setStep("virality", "done");

    setStep("package", "running");
    await window.delay(350);
    setStep("package", "done");
    setIsRunning(false);
  };

  /* ---- export ---- */
  const canExport =
    pipeline.package === "done" && trends.length > 0 && !isRunning;

  const exportJson = () => {
    const top3 = trends.slice(0, 3);
    const payload = {
      generated_at: new Date().toISOString(),
      niche,
      model: "gemini-3.1-flash-lite-preview",
      trends,
      content_packages: scripts.map((s, i) => ({
        trend: top3[i] ? top3[i].phrase : null,
        script: s,
        virality: virality[i] || null,
      })),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ai-generator-${niche.toLowerCase().replace(/\s+/g, "-")}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <div className="app">
      <TopBar
        niche={niche}
        setNiche={setNiche}
        apiKey={apiKey}
        setApiKey={setApiKey}
        onGenerate={generate}
        isRunning={isRunning}
        canExport={canExport}
        onExport={exportJson}
        keyError={keyError}
      />

      <div className="page">
        <PipelineBar pipeline={pipeline} errors={errors} />

        {!hasRun ? (
          <EmptyState onSample={sampleRun} isRunning={isRunning} />
        ) : (
          <div className="results">
            <TrendsSection trends={trends} />
            <ScriptsSection
              scripts={scripts} trends={trends} virality={virality}
              onScriptsUpdate={(ranked) => setScripts(ranked)}
            />
            <ViralitySection virality={virality} trends={trends} scripts={scripts} />
          </div>
        )}
      </div>
    </div>
  );
}

function shortErr(e) {
  const m = (e && e.message) || "Something went wrong";
  return m.length > 60 ? m.slice(0, 57) + "…" : m;
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
