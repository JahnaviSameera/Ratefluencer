/* Ratefluencer AI — trend charts.
 * Uses recharts when its UMD global is present; otherwise falls back to a
 * hand-built SVG area chart with the same look (gradient fill, smooth curve,
 * no gridlines, date axis). */
(function () {
  const { useState } = React;
  const { formatNum } = window.RF;
  const RC = window.Recharts || null;

  // ── recharts path ──
  function RechartsArea({ data, color, valueFmt, height }) {
    const { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, defs } = RC;
    const gid = "g" + Math.random().toString(36).slice(2, 8);
    return React.createElement(ResponsiveContainer, { width: "100%", height },
      React.createElement(AreaChart, { data, margin: { top: 8, right: 10, left: 0, bottom: 0 } },
        React.createElement("defs", null,
          React.createElement("linearGradient", { id: gid, x1: 0, y1: 0, x2: 0, y2: 1 },
            React.createElement("stop", { offset: "0%", stopColor: color, stopOpacity: 0.5 }),
            React.createElement("stop", { offset: "100%", stopColor: color, stopOpacity: 0.02 }),
          ),
        ),
        React.createElement(XAxis, {
          dataKey: "date", tick: { fill: "#8b949e", fontSize: 10 }, axisLine: false, tickLine: false,
          interval: Math.ceil(data.length / 6), minTickGap: 18,
        }),
        React.createElement(YAxis, { hide: true, domain: ["dataMin", "dataMax"] }),
        React.createElement(Tooltip, {
          contentStyle: { background: "#161b22", border: "1px solid #30363d", borderRadius: 10, fontSize: 12, color: "#f0f6fc" },
          labelStyle: { color: "#8b949e" }, formatter: (v) => [valueFmt ? valueFmt(v) : v, ""],
          cursor: { stroke: color, strokeOpacity: 0.3 },
        }),
        React.createElement(Area, {
          type: "monotone", dataKey: "value", stroke: color, strokeWidth: 2.5,
          fill: `url(#${gid})`, dot: false, activeDot: { r: 4, fill: color, stroke: "#ffffff", strokeWidth: 2 },
        }),
      ),
    );
  }

  // ── SVG fallback (monotone cubic) ──
  function monotonePath(pts) {
    if (pts.length < 2) return "";
    const n = pts.length;
    const d = [];
    for (let i = 0; i < n - 1; i++) d.push((pts[i + 1].y - pts[i].y) / (pts[i + 1].x - pts[i].x || 1));
    const m = [d[0]];
    for (let i = 1; i < n - 1; i++) m.push(d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2);
    m.push(d[n - 2]);
    let p = `M ${pts[0].x} ${pts[0].y}`;
    for (let i = 0; i < n - 1; i++) {
      const dx = (pts[i + 1].x - pts[i].x) / 3;
      p += ` C ${pts[i].x + dx} ${pts[i].y + m[i] * dx}, ${pts[i + 1].x - dx} ${pts[i + 1].y - m[i + 1] * dx}, ${pts[i + 1].x} ${pts[i + 1].y}`;
    }
    return p;
  }

  function SvgArea({ data, color, valueFmt, height }) {
    const [hover, setHover] = useState(null);
    const W = 520, H = height, padL = 8, padR = 8, padT = 12, padB = 22;
    const vals = data.map((d) => d.value);
    const min = Math.min(...vals), max = Math.max(...vals);
    const span = max - min || 1;
    const iw = W - padL - padR, ih = H - padT - padB;
    const pts = data.map((d, i) => ({
      x: padL + (i / (data.length - 1)) * iw,
      y: padT + ih - ((d.value - min) / span) * ih,
      raw: d,
    }));
    const gid = "sg" + Math.random().toString(36).slice(2, 8);
    const line = monotonePath(pts);
    const area = line + ` L ${pts[pts.length - 1].x} ${padT + ih} L ${pts[0].x} ${padT + ih} Z`;
    const ticks = [0, Math.floor(data.length / 3), Math.floor((2 * data.length) / 3), data.length - 1];
    return React.createElement("div", { style: { position: "relative", width: "100%" } },
      React.createElement("svg", {
        viewBox: `0 0 ${W} ${H}`, width: "100%", height, preserveAspectRatio: "none",
        onMouseMove: (e) => {
          const r = e.currentTarget.getBoundingClientRect();
          const x = ((e.clientX - r.left) / r.width) * W;
          let best = 0, bd = Infinity;
          pts.forEach((p, i) => { const dd = Math.abs(p.x - x); if (dd < bd) { bd = dd; best = i; } });
          setHover(best);
        },
        onMouseLeave: () => setHover(null),
      },
        React.createElement("defs", null,
          React.createElement("linearGradient", { id: gid, x1: 0, y1: 0, x2: 0, y2: 1 },
            React.createElement("stop", { offset: "0%", stopColor: color, stopOpacity: 0.5 }),
            React.createElement("stop", { offset: "100%", stopColor: color, stopOpacity: 0.02 }),
          ),
        ),
        React.createElement("path", { d: area, fill: `url(#${gid})` }),
        React.createElement("path", { d: line, fill: "none", stroke: color, strokeWidth: 2.5, vectorEffect: "non-scaling-stroke" }),
        hover != null ? React.createElement("circle", { cx: pts[hover].x, cy: pts[hover].y, r: 4, fill: color, stroke: "#ffffff", strokeWidth: 2 }) : null,
        ticks.map((ti, k) => React.createElement("text", {
          key: k, x: padL + (ti / (data.length - 1)) * iw, y: H - 6,
          textAnchor: k === 0 ? "start" : k === ticks.length - 1 ? "end" : "middle",
          fontSize: 10, fill: "#8b949e",
        }, data[ti].date)),
      ),
      hover != null ? React.createElement("div", {
        className: "rf-charttip",
        style: { left: `${(pts[hover].x / W) * 100}%` },
      }, React.createElement("div", { className: "rf-charttip-date" }, data[hover].date),
         React.createElement("div", { className: "rf-charttip-val" }, valueFmt ? valueFmt(data[hover].value) : data[hover].value)) : null,
    );
  }

  function AreaTrend({ data, color = "#7c3aed", label, sub, valueFmt, height = 170, icon }) {
    const Body = RC ? RechartsArea : SvgArea;
    return React.createElement("div", { className: "rf-card rf-chartcard" },
      React.createElement("div", { className: "rf-chart-head" },
        React.createElement("div", null,
          React.createElement("div", { className: "rf-chart-title" }, label),
          sub ? React.createElement("div", { className: "rf-chart-sub" }, sub) : null,
        ),
        React.createElement("span", { className: "rf-chart-dot", style: { background: color } }),
      ),
      React.createElement("div", { style: { height, marginTop: 6 } },
        React.createElement(Body, { data, color, valueFmt, height }),
      ),
    );
  }

  window.RFCharts = { AreaTrend, usingRecharts: !!RC };
})();
