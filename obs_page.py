OBS_PAGE_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Heart Rate Overlay</title>
<style>
  html, body { margin: 0; height: 100%; background: transparent; overflow: hidden; }
  body { font-family: "Segoe UI", system-ui, sans-serif; }
  #card {
    position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);
    display: inline-flex; align-items: center; gap: 0.3em;
    padding: 0.3em 0.6em; border-radius: 0.5em; white-space: nowrap;
    background: transparent;
  }
  #heart { width: 0.8em; height: 0.8em; flex: none; }
  #heart.beat { animation: beat 0.42s ease-out; }
  @keyframes beat { 0% { transform: scale(1.22); } 100% { transform: scale(1); } }
  #num { font-weight: 700; min-width: 2.2em; font-variant-numeric: tabular-nums; }
  #unit { font-weight: 600; font-size: 0.36em; letter-spacing: 0.06em; opacity: 0.75; }
</style>
</head>
<body>
<div id="card">
  <svg id="heart" viewBox="0 0 24 24" aria-hidden="true">
    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
  </svg>
  <span id="num">--</span>
  <span id="unit">BPM</span>
</div>
<script>
  const POLL_MS = 500;
  let lastBeats = null;

  function render(state) {
    const card = document.getElementById("card");
    const num = document.getElementById("num");
    const unit = document.getElementById("unit");
    const heart = document.getElementById("heart");

    num.textContent = state.bpm == null ? "--" : String(state.bpm);
    num.style.color = state.text_color;
    unit.style.color = state.text_color;
    heart.style.fill = state.heart_color;
    document.body.style.fontSize = (state.font_size * state.scale) + "px";
    card.style.background = state.background ? "rgba(12, 14, 18, 0.7)" : "transparent";
    card.style.borderRadius = "0.5em";
    card.style.opacity = state.opacity;

    if (lastBeats !== null && state.beats !== lastBeats && state.heartbeat && state.bpm != null) {
      heart.classList.remove("beat");
      void heart.getBoundingClientRect();
      heart.classList.add("beat");
    }
    lastBeats = state.beats;
  }

  async function poll() {
    try {
      const response = await fetch("/api/state", { cache: "no-store" });
      if (!response.ok) throw new Error("bad response");
      render(await response.json());
    } catch (error) {
      document.getElementById("num").textContent = "--";
    }
    setTimeout(poll, POLL_MS);
  }

  poll();
</script>
</body>
</html>
"""
