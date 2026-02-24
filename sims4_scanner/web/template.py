# -*- coding: utf-8 -*-
"""Komplettes HTML/CSS/JS Template fuer die Web-UI."""


def build_html_page() -> str:
    """Gibt das komplette HTML-Template als String zurueck.
    Platzhalter __TOKEN__ und __LOGFILE__ muessen vom Server ersetzt werden."""
    return r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sims4 Duplicate Scanner – Web UI</title>
<style>
  body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background:#0f1115; color:#e7e7e7; margin:16px; }
  h1 { margin:0 0 8px 0; }
  .muted { color:#b6b6b6; }
  .box { background:#151926; border:1px solid #232a3a; border-radius:14px; padding:14px; margin:12px 0; }
  code { color:#d7d7ff; }
  .topgrid { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
  @media (max-width: 900px) { .topgrid { grid-template-columns: 1fr; } }
  .pill { display:inline-block; padding:2px 8px; border-radius:999px; background:#232a3a; margin-left:8px; font-size:12px; }
  .search { width:100%; padding:10px 12px; border-radius:10px; border:1px solid #232a3a; background:#0f1422; color:#e7e7e7; }
  details.grp { border:1px solid #232a3a; border-radius:14px; padding:10px 12px; margin:10px 0; }
  details.grp.color-0 { background:#141a28; border-left:4px solid #4a7fff; }
  details.grp.color-1 { background:#1a1428; border-left:4px solid #a855f7; }
  details.grp.color-2 { background:#14281a; border-left:4px solid #22c55e; }
  details.grp.color-3 { background:#281a14; border-left:4px solid #f97316; }
  details.grp.color-4 { background:#28141a; border-left:4px solid #ef4444; }
  details.grp.color-5 { background:#142828; border-left:4px solid #06b6d4; }
  details.grp.grp-ignored { opacity:0.55; }
  details.grp.grp-ignored > summary { font-style:italic; }
  #import-dropzone:hover { border-color:#2563eb !important; background:#1e293b !important; }
  #import-dropzone.drag-active { border-color:#22c55e !important; background:#0f2a1a !important; }
  summary { cursor:pointer; }
  summary::-webkit-details-marker { display:none; }
  .files { margin-top:10px; display:flex; flex-direction:column; gap:10px; }
  .file { background:#0f1422; border:1px solid #1f2738; border-radius:12px; padding:10px; }
  .row1 { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
  .tag { display:inline-block; padding:2px 8px; border-radius:999px; background:#2d3a55; font-size:12px; }
  .size { color:#cfd6ff; font-size:12px; }
  .date { color:#a8ffcf; font-size:12px; }
  .btn { border:1px solid #2a3350; background:#11182b; color:#e7e7e7; padding:6px 10px; border-radius:10px; cursor:pointer; font-size:13px; }
  .btn:hover { filter:brightness(1.1); }
  .btn-danger { border-color:#6b2b2b; background:#2b1111; }
  .btn-ok { border-color:#2b6b3b; background:#112b1a; }
  .btn-ghost { border-color:#2a3350; background:transparent; }
  .flex { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
  .hr { height:1px; background:#232a3a; margin:10px 0; }
  .notice { background:#1a2238; border:1px solid #2b3553; padding:10px; border-radius:12px; }
  .subhead { margin-top:8px; padding:8px 10px; border-radius:10px; background:#101729; border:1px dashed #2a3350; color:#cfd6ff; }
  .pathline { word-break: break-all; }
  .small { font-size:12px; }
  #last { padding:10px 12px; border-radius:12px; background:#101729; border:1px solid #232a3a; }
  #log { width:100%; min-height:120px; max-height:260px; overflow:auto; padding:10px; border-radius:12px; background:#0f1422; border:1px solid #232a3a; color:#e7e7e7; white-space:pre; }
  #batchbar { position:sticky; top:0; z-index:5; }
  #section-nav { position:sticky; top:0; z-index:10; background:#0f172a; border-bottom:2px solid #334155; padding:0 16px; display:flex; gap:0; flex-wrap:wrap; align-items:stretch; margin:0 -20px; padding-left:20px; padding-right:20px; }
  #section-nav .nav-tab { background:transparent; border:none; border-bottom:3px solid transparent; color:#94a3b8; padding:6px 12px 5px; font-size:13px; cursor:pointer; transition:all 0.15s; display:inline-flex; flex-direction:column; align-items:center; white-space:nowrap; font-weight:600; position:relative; text-align:center; line-height:1.3; }
  #section-nav .nav-tab:hover { color:#e2e8f0; background:rgba(99,102,241,0.08); }
  #section-nav .nav-tab.active { color:#a5b4fc; border-bottom-color:#6366f1; background:rgba(99,102,241,0.12); }
  #section-nav .nav-tab .nav-badge { background:#6366f1; color:#fff; font-size:10px; padding:1px 6px; border-radius:10px; font-weight:bold; min-width:14px; text-align:center; }
  #section-nav .nav-tab .nav-badge.badge-warn { background:#f59e0b; }
  #section-nav .nav-tab .nav-badge.badge-danger { background:#ef4444; }
  #section-nav .nav-tab .nav-badge.badge-zero { display:none; }
  .nav-tab-sep { width:1px; background:#334155; margin:8px 2px; flex-shrink:0; }
  .nav-sub { display:block; font-size:10px; font-weight:400; color:#64748b; margin-top:1px; letter-spacing:0.2px; }
  .nav-tab.active .nav-sub { color:#818cf8; }
  .help-toggle { background:#1e293b; border:1px solid #334155; color:#94a3b8; padding:6px 14px; border-radius:8px; cursor:pointer; font-size:13px; transition:all 0.2s; }
  .help-toggle:hover { background:#334155; color:#e2e8f0; }
  .help-panel { display:none; background:#0f172a; border:1px solid #334155; border-radius:12px; padding:20px; margin-top:10px; }
  .help-panel.open { display:block; }
  .help-step { display:flex; gap:12px; margin-bottom:14px; align-items:flex-start; }
  .help-num { background:#6366f1; color:#fff; min-width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:13px; flex-shrink:0; }
  .help-text { color:#cbd5e1; font-size:13px; line-height:1.5; }
  .help-text b { color:#e2e8f0; }
  .legend-grid { display:grid; grid-template-columns:auto 1fr; gap:6px 14px; font-size:12px; margin-top:10px; }
  .legend-icon { text-align:center; min-width:80px; }
  .info-hint { background:#172554; border:1px solid #1e40af; border-radius:8px; padding:10px 14px; margin-bottom:12px; font-size:12px; color:#93c5fd; }

  /* ---- Spotlight Tutorial ---- */
  #tutorial-overlay { display:none; position:fixed; inset:0; z-index:10000; }
  #tutorial-overlay.active { display:block; }
  #tutorial-backdrop { position:fixed; inset:0; z-index:10000; cursor:default; }
  #tutorial-spotlight { position:fixed; border-radius:12px; box-shadow:0 0 0 99999px rgba(0,0,0,0.72); z-index:10001; pointer-events:none; display:none; transition:top 0.45s cubic-bezier(.4,0,.2,1),left 0.45s cubic-bezier(.4,0,.2,1),width 0.45s cubic-bezier(.4,0,.2,1),height 0.45s cubic-bezier(.4,0,.2,1); }
  #tutorial-spotlight.visible { display:block; }
  #tutorial-spotlight::after { content:''; position:absolute; inset:-4px; border-radius:14px; border:2px solid rgba(99,102,241,0.5); animation:spotPulse 2s ease-in-out infinite; pointer-events:none; }
  @keyframes spotPulse { 0%,100%{border-color:rgba(99,102,241,0.3);box-shadow:inset 0 0 8px rgba(99,102,241,0.1)} 50%{border-color:rgba(99,102,241,0.8);box-shadow:inset 0 0 24px rgba(99,102,241,0.3)} }
  @keyframes tutorialIn { from { opacity:0; transform:translateY(30px) scale(0.95); } to { opacity:1; transform:translateY(0) scale(1); } }
  #tutorial-tooltip { position:fixed; z-index:10002; background:linear-gradient(145deg,#0f172a 60%,#1e1b4b); border:1px solid #4f46e5; border-radius:16px; padding:28px 30px 20px; max-width:440px; min-width:280px; box-shadow:0 14px 44px rgba(0,0,0,0.55),0 0 0 1px rgba(99,102,241,0.15); pointer-events:auto; }
  #tutorial-tooltip.center-mode { top:50%!important; left:50%!important; transform:translate(-50%,-50%); max-width:560px; width:90vw; animation:tutCenterIn 0.4s ease-out; }
  @keyframes tutCenterIn { from{opacity:0;transform:translate(-50%,-50%) translateY(30px) scale(0.95)} to{opacity:1;transform:translate(-50%,-50%) translateY(0) scale(1)} }
  #tutorial-tooltip.pos-mode { animation:tutTipIn 0.3s ease-out; }
  @keyframes tutTipIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
  #tutorial-tooltip .tut-header { text-align:center; margin-bottom:14px; }
  #tutorial-tooltip .tut-icon { font-size:40px; display:block; margin-bottom:6px; }
  #tutorial-tooltip .tut-title { font-size:19px; font-weight:bold; color:#e2e8f0; }
  #tutorial-tooltip .tut-body { color:#cbd5e1; font-size:13px; line-height:1.7; max-height:40vh; overflow-y:auto; }
  #tutorial-tooltip .tut-body b { color:#a5b4fc; }
  #tutorial-tooltip .tut-body ul { margin:8px 0 0 18px; padding:0; }
  #tutorial-tooltip .tut-body li { margin-bottom:3px; }
  .tut-progress { display:flex; align-items:center; gap:10px; margin:16px 0 12px; }
  .tut-progress-bar { flex:1; height:4px; background:#1e293b; border-radius:4px; overflow:hidden; }
  .tut-progress-fill { height:100%; background:linear-gradient(90deg,#6366f1,#818cf8); border-radius:4px; transition:width 0.4s ease; }
  .tut-progress-text { font-size:11px; color:#64748b; white-space:nowrap; min-width:40px; text-align:right; }
  .tut-footer { display:flex; justify-content:space-between; align-items:center; gap:12px; }
  .tut-btn { border:1px solid #4f46e5; background:#1e1b4b; color:#c7d2fe; padding:8px 20px; border-radius:10px; cursor:pointer; font-size:13px; transition:all 0.15s; white-space:nowrap; }
  .tut-btn:hover { background:#312e81; color:#e0e7ff; }
  .tut-btn-primary { background:#6366f1; color:#fff; border-color:#6366f1; font-weight:bold; }
  .tut-btn-primary:hover { background:#818cf8; }
  .tut-btn-skip { background:transparent; border-color:#334155; color:#64748b; font-size:12px; }
  .tut-btn-skip:hover { color:#94a3b8; border-color:#475569; }
  .tut-check { display:flex; align-items:center; gap:8px; margin-top:14px; justify-content:center; }
  .tut-check label { color:#64748b; font-size:12px; cursor:pointer; }
  .tut-check input { accent-color:#6366f1; }

  /* Plumbob CSS Animation */
  .plumbob-container { position:relative; width:54px; height:70px; margin:0 auto 12px; }
  .plumbob { width:54px; height:70px; animation: plumbobFloat 3s ease-in-out infinite, plumbobGlow 2s ease-in-out infinite alternate; filter: drop-shadow(0 0 12px rgba(99,230,130,0.5)); }
  @keyframes plumbobFloat {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    25% { transform: translateY(-8px) rotate(2deg); }
    50% { transform: translateY(-4px) rotate(0deg); }
    75% { transform: translateY(-10px) rotate(-2deg); }
  }
  @keyframes plumbobGlow {
    0% { filter: drop-shadow(0 0 8px rgba(99,230,130,0.3)); }
    100% { filter: drop-shadow(0 0 20px rgba(99,230,130,0.7)); }
  }
  .nav-btn-tutorial { background:linear-gradient(135deg,#312e81,#1e1b4b) !important; border-color:#6366f1 !important; color:#c7d2fe !important; }
  .nav-btn-tutorial:hover { background:linear-gradient(135deg,#3730a3,#312e81) !important; color:#e0e7ff !important; }
  .nav-btn-bug { background:linear-gradient(135deg,#7f1d1d,#1e1b4b) !important; border-color:#dc2626 !important; color:#fca5a5 !important; }
  .nav-btn-bug:hover { background:linear-gradient(135deg,#991b1b,#312e81) !important; color:#fecaca !important; }
  .nav-btn-coffee { background:linear-gradient(135deg,#78350f,#451a03) !important; border-color:#f59e0b !important; color:#fde68a !important; text-decoration:none !important; }
  .nav-btn-coffee:hover { background:linear-gradient(135deg,#92400e,#78350f) !important; color:#fef3c7 !important; transform:scale(1.05); }
  .nav-btn-discord { background:linear-gradient(135deg,#5865F2,#4752C4) !important; border-color:#7289da !important; color:#fff !important; text-decoration:none !important; font-size:0.95em !important; padding:7px 18px !important; }
  .nav-btn-discord:hover { background:linear-gradient(135deg,#7289da,#5865F2) !important; transform:scale(1.08); }
  @keyframes discord-glow { 0%,100%{box-shadow:0 0 8px rgba(88,101,242,0.4)} 50%{box-shadow:0 0 18px rgba(88,101,242,0.7)} }
  #discord-float { position:fixed; bottom:70px; right:24px; z-index:9999; display:flex; align-items:center; gap:10px; background:linear-gradient(135deg,#5865F2,#4752C4); color:#fff; text-decoration:none; padding:14px 22px; border-radius:50px; font-size:1.05em; font-weight:bold; box-shadow:0 4px 20px rgba(88,101,242,0.6); animation:discord-glow 2s ease-in-out infinite; transition:all 0.3s ease; cursor:pointer; border:2px solid #7289da; }
  #discord-float:hover { transform:scale(1.08) translateY(-2px); box-shadow:0 6px 28px rgba(88,101,242,0.8); background:linear-gradient(135deg,#7289da,#5865F2); }
  #discord-float .discord-icon { font-size:1.4em; }
  @media(max-width:600px) { #discord-float span { display:none; } #discord-float { padding:14px 16px; border-radius:50%; } }

  /* Bug Report Modal */
  #bugreport-overlay { display:none; position:fixed; inset:0; z-index:10000; background:rgba(0,0,0,0.75); backdrop-filter:blur(4px); justify-content:center; align-items:center; }
  #bugreport-overlay.active { display:flex; }
  #bugreport-card { background:linear-gradient(145deg,#0f172a,#1c1017); border:1px solid #dc2626; border-radius:20px; padding:32px 36px 24px; max-width:620px; width:94vw; box-shadow:0 20px 60px rgba(0,0,0,0.6); animation:tutorialIn 0.35s ease-out; max-height:90vh; overflow-y:auto; }
  #bugreport-card h2 { margin:0 0 6px; font-size:20px; color:#fca5a5; }
  #bugreport-card .bug-sub { color:#94a3b8; font-size:13px; margin-bottom:16px; }
  #bugreport-card textarea { width:100%; min-height:80px; background:#0f1422; border:1px solid #334155; border-radius:10px; color:#e7e7e7; padding:12px; font-size:13px; resize:vertical; font-family:inherit; }
  #bugreport-card textarea:focus { outline:none; border-color:#dc2626; }
  #bugreport-card .bug-info { background:#172554; border:1px solid #1e40af; border-radius:8px; padding:10px 14px; margin:12px 0; font-size:12px; color:#93c5fd; }
  #bugreport-card .bug-footer { display:flex; justify-content:flex-end; gap:10px; margin-top:16px; }
  #bugreport-card .bug-status { margin-top:12px; padding:10px; border-radius:8px; font-size:13px; display:none; }
  #bugreport-card .bug-status.success { display:block; background:#052e16; border:1px solid #16a34a; color:#86efac; }
  #bugreport-card .bug-status.error { display:block; background:#2b1111; border:1px solid #dc2626; color:#fca5a5; }
  #bugreport-card label { color:#cbd5e1; font-size:13px; font-weight:bold; display:block; margin-bottom:4px; }
  #bugreport-card select { width:100%; background:#0f1422; border:1px solid #334155; border-radius:10px; color:#e7e7e7; padding:10px 12px; font-size:13px; font-family:inherit; appearance:auto; }
  #bugreport-card select:focus { outline:none; border-color:#dc2626; }
  .bug-field { margin-bottom:14px; }
  .bug-checks { display:grid; grid-template-columns:1fr 1fr; gap:6px 16px; margin-top:6px; }
  .bug-checks label { font-weight:normal; display:flex; align-items:center; gap:6px; cursor:pointer; font-size:12px; color:#94a3b8; }
  .bug-checks input { accent-color:#dc2626; }

  #back-to-top { position:fixed; bottom:24px; right:24px; z-index:99; background:#6366f1; color:#fff; border:none; border-radius:50%; width:44px; height:44px; font-size:20px; cursor:pointer; box-shadow:0 4px 12px rgba(0,0,0,0.4); transition:opacity 0.2s, transform 0.2s; opacity:0; pointer-events:none; transform:translateY(10px); }
  #back-to-top.visible { opacity:1; pointer-events:auto; transform:translateY(0); }
  #back-to-top:hover { background:#818cf8; transform:translateY(-2px); }
  @keyframes pulse { 0% { margin-left:0; } 100% { margin-left:70%; } }
  .selbox { transform: scale(1.15); margin-right:8px; }
  .busy { opacity:0.65; pointer-events:none; }
  .err-card { border-radius:12px; padding:12px; margin:8px 0; }
  .err-card.hoch { background:#2b1111; border:1px solid #6b2b2b; border-left:4px solid #ef4444; }
  .err-card.mittel { background:#2b2211; border:1px solid #6b5b2b; border-left:4px solid #f59e0b; }
  .err-card.niedrig { background:#112b1a; border:1px solid #2b6b3b; border-left:4px solid #22c55e; }
  .err-card.harmlos { background:#151926; border:1px solid #2a3348; border-left:4px solid #64748b; }
  .err-card.unbekannt { background:#151926; border:1px solid #232a3a; border-left:4px solid #64748b; }
  .err-title { font-weight:bold; font-size:15px; }
  .err-schwere { display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:bold; text-transform:uppercase; }
  .err-schwere.hoch { background:#7f1d1d; color:#fca5a5; }
  .err-schwere.mittel { background:#78350f; color:#fde68a; }
  .err-schwere.niedrig { background:#14532d; color:#86efac; }
  .err-schwere.harmlos { background:#334155; color:#cbd5e1; }
  .err-schwere.unbekannt { background:#334155; color:#cbd5e1; }
  .err-explain { margin:6px 0; color:#d1d5db; }
  .corrupt-card { border-radius:10px; padding:10px 14px; margin:6px 0; background:#2b1111; border:1px solid #6b2b2b; border-left:4px solid #ef4444; display:flex; justify-content:space-between; align-items:center; }
  .corrupt-card.warn { background:#2b2211; border-color:#6b5b2b; border-left-color:#f59e0b; }
  .corrupt-status { display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:bold; }
  .corrupt-status.empty { background:#7f1d1d; color:#fca5a5; }
  .corrupt-status.too_small { background:#7f1d1d; color:#fca5a5; }
  .corrupt-status.no_dbpf { background:#7f1d1d; color:#fca5a5; }
  .corrupt-status.wrong_version { background:#78350f; color:#fde68a; }
  .corrupt-status.unreadable { background:#334155; color:#cbd5e1; }
  .conflict-card { border-radius:10px; padding:12px 14px; margin:8px 0; background:#1a1a2e; border:1px solid #3a3a5e; border-left:4px solid #8b5cf6; }
  .conflict-badge { display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:bold; background:#4c1d95; color:#c4b5fd; }
  .conflict-types { margin-top:6px; display:flex; flex-wrap:wrap; gap:4px; }
  .conflict-type-pill { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; background:#1e293b; color:#94a3b8; }
  .skin-card { border-radius:10px; padding:14px 16px; margin:8px 0; background:#1a1215; border:1px solid #7f1d1d; border-left:4px solid #ef4444; }
  .skin-card.skin-warn { border-left-color:#fbbf24; border-color:#78350f; background:#1a1810; }
  .skin-card.skin-info { border-left-color:#60a5fa; border-color:#1e3a5f; background:#0f1422; }
  .skin-badge { display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:bold; }
  .skin-badge-hoch { background:#7f1d1d; color:#fca5a5; }
  .skin-badge-mittel { background:#78350f; color:#fde68a; }
  .skin-badge-niedrig { background:#1e3a5f; color:#93c5fd; }
  .skin-reason { display:inline-block; padding:1px 8px; border-radius:6px; background:#1e293b; color:#f0abfc; font-size:11px; margin:2px; }
  .addon-badge { display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:bold; background:#065f46; color:#6ee7b7; }
  .addon-ok { display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:bold; background:#14532d; color:#86efac; }
  .err-solution { margin:6px 0; padding:8px 10px; background:#0f1422; border-radius:8px; border-left:3px solid #4a7fff; }
  .err-meta { display:flex; gap:12px; flex-wrap:wrap; font-size:12px; color:#9ca3af; margin-top:6px; }
  .err-mods { margin-top:6px; }
  .err-mod-tag { display:inline-block; padding:1px 8px; border-radius:6px; background:#1e293b; color:#93c5fd; font-size:11px; margin:2px; }
  .err-raw { margin-top:8px; }
  .err-raw summary { cursor:pointer; color:#6b7280; font-size:12px; }
  .err-raw pre { font-size:11px; color:#9ca3af; white-space:pre-wrap; word-break:break-all; max-height:200px; overflow:auto; background:#0a0e17; padding:8px; border-radius:8px; margin-top:4px; }

  /* Status-Badges NEU/BEKANNT */
  .err-status { display:inline-block; padding:1px 8px; border-radius:999px; font-size:10px; font-weight:bold; text-transform:uppercase; margin-left:8px; }
  .err-status.neu { background:#1e3a5f; color:#60a5fa; }
  .err-status.bekannt { background:#334155; color:#94a3b8; }

  /* History-Tabelle */
  .hist-table { width:100%; border-collapse:collapse; font-size:13px; margin-top:8px; }
  .hist-table th { text-align:left; padding:8px 10px; border-bottom:2px solid #334155; color:#94a3b8; font-weight:600; }
  .hist-table td { padding:6px 10px; border-bottom:1px solid #1e293b; }
  .hist-table tr:hover { background:#111827; }

  /* Mod-Inventar Stats */
  .mod-stats { display:flex; gap:16px; flex-wrap:wrap; margin:8px 0; }
  .mod-stat { padding:10px 16px; border-radius:10px; background:#111827; border:1px solid #1e293b; text-align:center; min-width:120px; }
  .mod-stat .val { font-size:22px; font-weight:bold; color:#e2e8f0; }
  .mod-stat .lbl { font-size:11px; color:#94a3b8; margin-top:2px; }

  /* Änderungs-Tags */
  .change-tag { display:inline-block; padding:2px 8px; border-radius:6px; font-size:11px; margin:2px; }
  .change-tag.neu { background:#14532d; color:#86efac; }
  .change-tag.entfernt { background:#7f1d1d; color:#fca5a5; }
  .change-tag.geaendert { background:#78350f; color:#fde68a; }

  /* Per-File Ansicht */
  .view-toggle { display:flex; gap:4px; background:#151926; border-radius:10px; padding:3px; border:1px solid #232a3a; }
  .view-toggle button { padding:6px 14px; border-radius:8px; border:none; background:transparent; color:#b6b6b6; cursor:pointer; font-size:13px; font-weight:600; transition:all 0.15s; }
  .view-toggle button.active { background:#2d3a55; color:#e7e7e7; }
  .view-toggle button:hover:not(.active) { color:#e7e7e7; }
  .pf-card { background:#151926; border:1px solid #232a3a; border-radius:14px; padding:14px; margin:10px 0; }
  .pf-card .pf-header { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }
  .pf-card .pf-name { font-weight:bold; font-size:15px; word-break:break-all; }
  .pf-card .pf-meta { display:flex; gap:8px; flex-wrap:wrap; align-items:center; font-size:12px; }
  .pf-section { margin-top:10px; padding:10px 12px; border-radius:10px; border-left:4px solid; }
  .pf-section.pf-name-dupe { background:#141a28; border-color:#4a7fff; }
  .pf-section.pf-content-dupe { background:#1a1428; border-color:#a855f7; }
  .pf-section.pf-similar-dupe { background:#142828; border-color:#06b6d4; }
  .pf-section.pf-corrupt { background:#2b1111; border-color:#ef4444; }
  .pf-section.pf-addon { background:#0f2922; border-color:#22c55e; }
  .pf-section.pf-conflict { background:#1a1a2e; border-color:#8b5cf6; }
  .pf-section.pf-skin { background:#2b1115; border-color:#ef4444; }
  .pf-section-title { font-weight:bold; font-size:13px; margin-bottom:6px; }
  .pf-partner { font-size:12px; color:#94a3b8; margin:2px 0; }
  .pf-partner code { font-size:11px; }
  #perfile-view { display:none; }

  /* Mod-Notizen */
  .note-area { margin-top:8px; }
  .note-display { display:flex; align-items:flex-start; gap:8px; padding:6px 10px; background:#0f172a; border:1px solid #1e293b; border-radius:8px; font-size:12px; color:#fde68a; cursor:pointer; }
  .note-display:hover { background:#111827; }
  .note-input { width:100%; padding:8px 10px; background:#0f1115; border:1px solid #334155; border-radius:8px; color:#e7e7e7; font-size:12px; resize:vertical; min-height:36px; box-sizing:border-box; font-family:inherit; }
  .note-btn { font-size:11px; padding:3px 10px; border-radius:6px; cursor:pointer; border:1px solid #334155; background:#1e293b; color:#94a3b8; }
  .note-btn:hover { background:#334155; color:#e2e8f0; }
  .note-btn-save { background:#112b1a; border-color:#2b6b3b; color:#86efac; }

  /* Mod-Tags */
  .mod-tags-area { display:flex; flex-wrap:wrap; gap:4px; margin-top:6px; align-items:center; }
  .mod-tag-pill { display:inline-flex; align-items:center; gap:3px; padding:2px 8px; border-radius:999px; font-size:11px; font-weight:600; cursor:default; }
  .mod-tag-pill .tag-remove { cursor:pointer; opacity:0.6; margin-left:2px; font-size:10px; }
  .mod-tag-pill .tag-remove:hover { opacity:1; }
  .tag-add-btn { display:inline-flex; align-items:center; padding:2px 6px; border-radius:999px; font-size:11px; background:#1e293b; border:1px dashed #334155; color:#94a3b8; cursor:pointer; }
  .tag-add-btn:hover { background:#334155; color:#e2e8f0; }
  .tag-menu { position:absolute; background:#1e293b; border:1px solid #334155; border-radius:8px; padding:6px; z-index:20; display:flex; flex-wrap:wrap; gap:4px; max-width:260px; box-shadow:0 8px 24px rgba(0,0,0,0.4); }
  .tag-menu-item { padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600; cursor:pointer; border:none; }
  .tag-menu-item:hover { filter:brightness(1.3); }

  /* Verlaufs-Diagramm */
  .chart-container { position:relative; width:100%; height:220px; margin-top:12px; background:#0f172a; border:1px solid #1e293b; border-radius:10px; padding:12px; box-sizing:border-box; }
  .chart-container canvas { width:100% !important; height:100% !important; }

  /* Dashboard / Ampel */
  .dashboard { display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:12px; margin:12px 0; }
  .dash-card { border-radius:14px; padding:16px; border:1px solid; cursor:pointer; transition:all 0.2s; position:relative; overflow:hidden; }
  .dash-card:hover { transform:translateY(-2px); filter:brightness(1.15); }
  .dash-card .dash-icon { font-size:28px; margin-bottom:6px; }
  .dash-card .dash-count { font-size:32px; font-weight:800; margin-bottom:2px; }
  .dash-card .dash-label { font-size:14px; font-weight:600; margin-bottom:4px; }
  .dash-card .dash-desc { font-size:12px; opacity:0.8; line-height:1.4; }
  .dash-card .dash-action { display:inline-block; margin-top:8px; padding:4px 12px; border-radius:6px; font-size:11px; font-weight:600; background:rgba(255,255,255,0.1); }
  .dash-card.dash-critical { background:linear-gradient(135deg,#1a0505,#2b1111); border-color:#6b2b2b; }
  .dash-card.dash-critical .dash-count { color:#f87171; }
  .dash-card.dash-warn { background:linear-gradient(135deg,#1a1005,#2b2211); border-color:#6b5b2b; }
  .dash-card.dash-warn .dash-count { color:#fbbf24; }
  .dash-card.dash-info { background:linear-gradient(135deg,#050d1a,#111a2b); border-color:#2b3a6b; }
  .dash-card.dash-info .dash-count { color:#60a5fa; }
  .dash-card.dash-ok { background:linear-gradient(135deg,#051a0d,#112b1a); border-color:#2b6b3b; }
  .dash-card.dash-ok .dash-count { color:#4ade80; }
  .dash-card.dash-hidden { display:none; }
  .dash-header { margin:16px 0 8px; }
  .dash-header h2 { margin:0 0 4px; font-size:20px; }
  .dash-header p { margin:0; }
  #section-nav .nav-sep { width:1px; height:20px; background:#334155; margin:0 4px; flex-shrink:0; }

  /* ---- Lightbox / Bildvorschau ---- */
  #lightbox-overlay {
    display:none; position:fixed; inset:0; z-index:10000;
    background:rgba(0,0,0,0.92); backdrop-filter:blur(8px);
    justify-content:center; align-items:center; cursor:zoom-out;
    flex-direction:column; padding:20px;
  }
  #lightbox-overlay.active { display:flex; }
  #lightbox-overlay .lb-single {
    max-width:90vw; max-height:90vh; border-radius:12px;
    border:2px solid #475569; box-shadow:0 0 60px rgba(0,0,0,0.7);
    object-fit:contain; cursor:default;
    animation: lbFadeIn 0.2s ease;
  }
  @keyframes lbFadeIn { from{opacity:0;transform:scale(0.85)} to{opacity:1;transform:scale(1)} }
  #lightbox-close {
    position:fixed; top:18px; right:24px; z-index:10001;
    font-size:32px; color:#fff; background:rgba(0,0,0,0.5); border:none;
    border-radius:50%; width:44px; height:44px; cursor:pointer;
    display:none; align-items:center; justify-content:center; line-height:1;
  }
  #lightbox-close:hover { background:rgba(255,255,255,0.15); }
  #lightbox-overlay.active ~ #lightbox-close { display:flex; }
  .thumb-clickable { cursor:zoom-in; transition:transform 0.15s, box-shadow 0.15s; }
  .thumb-clickable:hover { transform:scale(1.12); box-shadow:0 0 12px rgba(96,165,250,0.5); }
  .gallery-card:hover { transform:translateY(-3px); box-shadow:0 4px 16px rgba(96,165,250,0.3); border-color:#3b82f6 !important; }

  /* Gallery / Vergleichsansicht */
  #lightbox-overlay .lb-gallery {
    display:flex; flex-wrap:wrap; gap:18px; justify-content:center;
    align-items:flex-start; max-width:95vw; max-height:88vh;
    overflow-y:auto; padding:10px; cursor:default;
  }
  #lightbox-overlay .lb-gallery::-webkit-scrollbar { width:6px; }
  #lightbox-overlay .lb-gallery::-webkit-scrollbar-thumb { background:#475569; border-radius:3px; }
  .lb-gallery-card {
    background:#1e293b; border:2px solid #334155; border-radius:12px;
    padding:12px; text-align:center; min-width:180px; max-width:320px;
    flex:1 1 220px; animation: lbFadeIn 0.25s ease;
    transition: border-color 0.2s;
  }
  .lb-gallery-card:hover { border-color:#60a5fa; }
  .lb-gallery-card img {
    max-width:280px; max-height:280px; border-radius:8px;
    object-fit:contain; background:#0f172a;
    border:1px solid #475569; margin-bottom:8px;
  }
  .lb-gallery-card .lb-label {
    color:#e2e8f0; font-size:12px; word-break:break-all;
    margin-top:6px; line-height:1.3;
  }
  .lb-gallery-card .lb-meta {
    color:#94a3b8; font-size:11px; margin-top:4px;
  }
  .lb-gallery-title {
    color:#e2e8f0; font-size:18px; font-weight:600;
    margin-bottom:12px; text-align:center; width:100%;
  }
  .lb-gallery-hint {
    color:#64748b; font-size:12px; text-align:center;
    width:100%; margin-top:8px;
  }

  /* ---- Tray-Analyse ---- */
  .tray-summary-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:10px; margin:12px 0; }
  .tray-stat { background:linear-gradient(135deg,#0f172a,#1e1b4b); border:1px solid #312e81; border-radius:12px; padding:14px; text-align:center; }
  .tray-stat .tray-stat-num { font-size:28px; font-weight:800; color:#a78bfa; }
  .tray-stat .tray-stat-label { font-size:11px; color:#94a3b8; margin-top:4px; }
  .tray-items-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(340px, 1fr)); gap:12px; margin-top:12px; }
  .tray-card { background:linear-gradient(135deg,#1e1b4b,#0f172a); border:1px solid #312e81; border-radius:14px; padding:0; transition:all 0.2s; cursor:pointer; overflow:hidden; }
  .tray-card:hover { border-color:#6366f1; transform:translateY(-2px); box-shadow:0 4px 24px rgba(99,102,241,0.2); }
  .tray-card-header { display:flex; align-items:center; gap:12px; padding:14px 14px 10px; }
  .tray-card-icon { font-size:36px; flex-shrink:0; width:56px; height:56px; display:flex; align-items:center; justify-content:center; border-radius:14px; }
  .tray-card-icon.type-household { background:linear-gradient(135deg,#7c3aed33,#6366f122); border:1px solid #7c3aed44; }
  .tray-card-icon.type-lot { background:linear-gradient(135deg,#05966933,#10b98122); border:1px solid #05966944; }
  .tray-card-icon.type-room { background:linear-gradient(135deg,#d9770633,#f59e0b22); border:1px solid #d9770644; }
  .tray-card-name { font-size:15px; font-weight:700; color:#e2e8f0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .tray-card-creator { font-size:11px; color:#94a3b8; margin-top:2px; }
  .tray-card-body { padding:0 14px 12px; }
  .tray-card-badges { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:8px; }
  .tray-badge { font-size:10px; padding:3px 10px; border-radius:8px; font-weight:600; }
  .tray-badge-cc { background:#7c3aed33; color:#c4b5fd; border:1px solid #7c3aed55; }
  .tray-badge-type { background:#6366f133; color:#a5b4fc; border:1px solid #6366f155; }
  .tray-badge-nocc { background:#16a34a22; color:#86efac; border:1px solid #16a34a44; }
  .tray-card-mods { max-height:0; overflow:hidden; transition:max-height 0.3s ease; }
  .tray-card.expanded .tray-card-mods { max-height:600px; overflow-y:auto; }
  .tray-card.expanded .tray-expand-hint { display:none; }
  .tray-mod-item { display:flex; align-items:center; gap:8px; padding:5px 0; border-top:1px solid #312e8133; font-size:11px; color:#cbd5e1; }
  .tray-mod-item:first-child { border-top:none; }
  .tray-mod-dot { width:6px; height:6px; border-radius:50%; background:#818cf8; flex-shrink:0; }
  .tray-mod-name { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:1; }
  .tray-mod-matches { color:#6366f1; font-size:10px; flex-shrink:0; }
  .tray-expand-hint { font-size:10px; color:#64748b; text-align:center; padding:6px 0 2px; border-top:1px solid #312e8133; }
  /* ═══ SIM-CARDS (Pokémon-Style) ═══ */
  .sim-card { background:linear-gradient(180deg,#1a1744 0%,#0f172a 100%); border:3px solid #312e81; border-radius:16px; padding:0; transition:all 0.25s; overflow:hidden; position:relative; }
  .sim-card::before { content:''; position:absolute; inset:0; border-radius:13px; background:linear-gradient(180deg,rgba(255,255,255,0.04) 0%,transparent 40%); pointer-events:none; z-index:1; }
  .sim-card:hover { transform:translateY(-4px) scale(1.02); box-shadow:0 8px 32px rgba(99,102,241,0.3); }
  .sim-card.male { border-color:#3b82f680; background:linear-gradient(180deg,#172554 0%,#0f172a 100%); }
  .sim-card.male:hover { border-color:#60a5fa; box-shadow:0 8px 32px rgba(59,130,246,0.35); }
  .sim-card.female { border-color:#ec489980; background:linear-gradient(180deg,#4a1942 0%,#0f172a 100%); }
  .sim-card.female:hover { border-color:#f472b6; box-shadow:0 8px 32px rgba(236,72,153,0.35); }
  .sim-card.lib-only-card { border-color:#8b5cf680; background:linear-gradient(180deg,#2e1065 0%,#0f172a 100%); }
  .sim-card.lib-only-card:hover { border-color:#a78bfa; box-shadow:0 8px 32px rgba(139,92,246,0.35); }
  .sim-card.lib-only-card .sim-portrait-frame { border-color:rgba(139,92,246,0.25); }
  /* ── Karten-Kopf: Name + Typ ── */
  .sim-card-topbar { display:flex; flex-direction:column; padding:10px 14px 6px; position:relative; z-index:2; gap:4px; }
  .sim-card-topbar .sim-name { font-size:15px; font-weight:800; color:#f1f5f9; letter-spacing:0.02em; white-space:nowrap; }
  .sim-card-topbar .sim-badges-row { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
  .sim-card-topbar .sim-type-badge { font-size:10px; font-weight:700; padding:3px 10px; border-radius:10px; text-transform:uppercase; letter-spacing:0.06em; flex-shrink:0; }
  .sim-type-badge.male { background:#3b82f633; color:#93c5fd; border:1px solid #3b82f655; }
  .sim-type-badge.female { background:#ec489933; color:#f9a8d4; border:1px solid #ec489955; }
  .sim-type-badge.unknown { background:#64748b33; color:#94a3b8; border:1px solid #64748b55; }
  /* ── Portrait-Bereich (großes Bild) ── */
  .sim-portrait-frame { margin:0 10px; border-radius:10px; overflow:hidden; position:relative; z-index:2; aspect-ratio:4/3; background:#0c0a2a; border:2px solid rgba(99,102,241,0.2); }
  .sim-card.male .sim-portrait-frame { border-color:rgba(59,130,246,0.25); }
  .sim-card.female .sim-portrait-frame { border-color:rgba(236,72,153,0.25); }
  .sim-portrait-frame img { width:100%; height:100%; object-fit:cover; display:block; }
  .sim-portrait-frame .sim-emoji-holder { width:100%; height:100%; display:flex; align-items:center; justify-content:center; font-size:64px; background:linear-gradient(135deg,#1e1b4b 0%,#0f172a 100%); }
  .sim-portrait-frame .sim-emoji-holder.male { background:linear-gradient(135deg,#1e3a5f,#172554); }
  .sim-portrait-frame .sim-emoji-holder.female { background:linear-gradient(135deg,#4a1942,#2d1230); }
  .sim-portrait-frame .sim-emoji-holder.unknown { background:linear-gradient(135deg,#334155,#1e293b); }
  /* ── Info-Bereich unter dem Bild ── */
  .sim-card-info { padding:10px 14px 6px; position:relative; z-index:2; }
  .sim-card-info .sim-subtitle { font-size:11px; color:#94a3b8; display:flex; align-items:center; gap:6px; }
  .sim-card-info .sim-subtitle .gender-dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
  .sim-card-info .sim-subtitle .gender-dot.male { background:#60a5fa; box-shadow:0 0 6px #60a5fa88; }
  .sim-card-info .sim-subtitle .gender-dot.female { background:#f472b6; box-shadow:0 0 6px #f472b688; }
  .sim-card-info .sim-subtitle .gender-dot.unknown { background:#94a3b8; }
  .sim-world-tag { font-size:10px; color:#86efac; background:#064e3b44; border:1px solid #06b6d433; border-radius:8px; padding:1px 8px; margin-top:2px; display:inline-block; }
  /* ── Stats-Zeile ── */
  .sim-card-stats { display:flex; gap:0; padding:0 10px 8px; position:relative; z-index:2; }
  .sim-stat { flex:1; text-align:center; padding:6px 2px; }
  .sim-stat + .sim-stat { border-left:1px solid #ffffff08; }
  .sim-stat-val { font-size:13px; font-weight:700; color:#e2e8f0; }
  .sim-stat-label { font-size:9px; color:#64748b; text-transform:uppercase; letter-spacing:0.05em; margin-top:1px; }
  /* ── Badges & Footer ── */
  .sim-card-body { padding:0 12px 10px; position:relative; z-index:2; }
  .sim-badges { display:flex; gap:4px; flex-wrap:wrap; }
  .sim-badge { font-size:10px; padding:3px 9px; border-radius:8px; font-weight:600; }
  .sim-badge-hh { background:#6366f118; color:#a5b4fc; border:1px solid #6366f133; }
  .sim-badge-age { background:#14b8a618; color:#5eead4; border:1px solid #14b8a633; }
  .sim-badge-species { background:#7c3aed18; color:#c4b5fd; border:1px solid #7c3aed33; }
  .sim-badge-skin { background:#f59e0b18; color:#fcd34d; border:1px solid #f59e0b33; }
  .sim-badge-basegame { background:#10b98118; color:#6ee7b7; border:1px solid #10b98133; font-weight:700; }
  .sim-badge-townie { background:#f59e0b18; color:#fbbf24; border:1px solid #f59e0b33; font-weight:700; }
  .sim-badge-dupe { background:#ef444418; color:#f87171; border:1px solid #ef444433; font-weight:700; animation: dupe-pulse 2s ease-in-out infinite; }
  @keyframes dupe-pulse { 0%,100%{opacity:1} 50%{opacity:.6} }
  .sim-badge-traits { background:#06b6d418; color:#67e8f9; border:1px solid #06b6d433; }
  .sim-badge-active { background:#22c55e18; color:#86efac; border:1px solid #22c55e33; font-weight:700; }
  .sim-badge-libonly { background:#8b5cf618; color:#c4b5fd; border:1px solid #8b5cf633; font-weight:700; }
  .sim-badge-creator { background:#3b82f618; color:#93c5fd; border:1px solid #3b82f633; }
  .sim-partner-line { font-size:11px; color:#f472b6; padding:4px 14px 0; display:flex; align-items:center; gap:4px; position:relative; z-index:2; }
  .sim-extra-line { font-size:10px; color:#64748b; padding:2px 14px 0; position:relative; z-index:2; }
  /* ── Outfit-Sektion ── */
  .sim-outfit-section { padding:6px 12px 8px; position:relative; z-index:2; border-top:1px solid #ffffff08; margin-top:4px; }
  .sim-outfit-title { font-size:10px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px; }
  .sim-outfit-detail { max-height:0; overflow:hidden; transition:max-height 0.3s ease; }
  .sim-outfit-detail.open { max-height:800px; }
  .outfit-cat-row { padding:4px 0; border-bottom:1px solid #1e293b; }
  .outfit-cat-name { font-size:11px; font-weight:700; color:#e2e8f0; }
  .outfit-cat-count { font-size:10px; color:#94a3b8; margin-left:8px; }
  .outfit-bt-tags { display:flex; flex-wrap:wrap; gap:3px; margin-top:3px; }
  .outfit-bt-tag { font-size:9px; background:#1e293b; color:#94a3b8; padding:1px 6px; border-radius:4px; border:1px solid #334155; }
  /* ── Familien-Rollen ── */
  .sim-family-section { padding:6px 12px 8px; position:relative; z-index:2; border-top:1px solid #ffffff08; margin-top:4px; }
  .sim-family-title { font-size:10px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px; }
  .sim-family-member { font-size:11px; color:#cbd5e1; padding:2px 0; display:flex; align-items:center; gap:5px; }
  .sim-family-role { font-size:9px; color:#94a3b8; background:#1e293b; padding:1px 6px; border-radius:4px; }
  .sim-role-badge { font-size:10px; padding:2px 8px; border-radius:6px; font-weight:700; }
  .sim-role-badge.elternteil { background:#8b5cf618; color:#c4b5fd; border:1px solid #8b5cf633; }
  .sim-role-badge.kind { background:#38bdf818; color:#7dd3fc; border:1px solid #38bdf833; }
  .sim-role-badge.partner { background:#ec489918; color:#f9a8d4; border:1px solid #ec489933; }
  .sim-role-badge.geschwister { background:#f59e0b18; color:#fcd34d; border:1px solid #f59e0b33; }
  .sim-role-badge.mitbewohner { background:#64748b18; color:#94a3b8; border:1px solid #64748b33; }
  .sim-rel-bar { height:4px; border-radius:2px; background:#1e293b; margin-top:4px; overflow:hidden; }
  .sim-rel-bar-fill { height:100%; border-radius:2px; transition:width 0.4s; }
  .sim-rel-bar-fill.wenige { width:15%; background:#64748b; }
  .sim-rel-bar-fill.einige { width:40%; background:#3b82f6; }
  .sim-rel-bar-fill.viele { width:70%; background:#8b5cf6; }
  .sim-rel-bar-fill.sehr-viele { width:100%; background:linear-gradient(90deg,#8b5cf6,#ec4899); }
  .sim-hh-detail { margin-top:8px; padding:10px 14px; background:linear-gradient(135deg,rgba(99,102,241,0.06),rgba(99,102,241,0.02)); border:1px solid #6366f122; border-radius:10px; }
  .sim-hh-detail .hh-member-row { display:flex; align-items:center; gap:8px; padding:3px 0; font-size:12px; color:#cbd5e1; }
  .sim-hh-detail .hh-member-row .hh-m-role { font-size:10px; color:#94a3b8; margin-left:auto; }
  /* Sim Skills */
  .sim-skills-section { padding:4px 12px 2px; }
  .sim-skill-row { display:flex; align-items:center; gap:6px; padding:2px 0; font-size:11px; color:#cbd5e1; }
  .sim-skill-name { flex:1; min-width:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .sim-skill-name.mod-skill { color:#64748b; font-style:italic; }
  .sim-skill-stars { color:#fbbf24; font-size:10px; letter-spacing:-1px; white-space:nowrap; }
  .sim-skill-stars .off { color:#334155; }
  /* Sim Needs */
  .sim-needs-section { padding:4px 12px 6px; }
  .sim-needs-title { font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px; font-weight:600; }
  .sim-need-row { display:flex; align-items:center; gap:6px; padding:2px 0; font-size:11px; color:#cbd5e1; }
  .sim-need-emoji { width:16px; text-align:center; font-size:12px; flex-shrink:0; }
  .sim-need-name { width:52px; flex-shrink:0; font-size:10px; color:#94a3b8; }
  .sim-need-bar { flex:1; height:6px; border-radius:3px; background:#1e293b; overflow:hidden; position:relative; }
  .sim-need-bar-fill { height:100%; border-radius:3px; transition:width 0.4s; }
  .sim-need-bar-fill.critical { background:linear-gradient(90deg,#dc2626,#ef4444); }
  .sim-need-bar-fill.low { background:linear-gradient(90deg,#f59e0b,#fbbf24); }
  .sim-need-bar-fill.medium { background:linear-gradient(90deg,#3b82f6,#60a5fa); }
  .sim-need-bar-fill.high { background:linear-gradient(90deg,#22c55e,#4ade80); }
  .sim-need-val { width:32px; text-align:right; font-size:10px; color:#64748b; flex-shrink:0; }
  /* Sim Mood Bar */
  .sim-mood-bar { height:4px; border-radius:2px; background:#1e293b; margin-top:2px; overflow:hidden; }
  .sim-mood-bar-fill { height:100%; border-radius:2px; transition:width 0.4s; }
  .sim-mood-bar-fill.very-happy { width:100%; background:linear-gradient(90deg,#22c55e,#4ade80); }
  .sim-mood-bar-fill.happy { width:75%; background:#22c55e; }
  .sim-mood-bar-fill.neutral { width:50%; background:#64748b; }
  .sim-mood-bar-fill.sad { width:30%; background:#f59e0b; }
  .sim-mood-bar-fill.very-sad { width:15%; background:#ef4444; }
  /* Sim Detail Row */
  .sim-detail-row { display:flex; align-items:center; gap:6px; padding:1px 12px; font-size:11px; color:#94a3b8; }
  .sim-detail-row .detail-icon { font-size:12px; }
  .sim-detail-row .detail-label { color:#64748b; }
  .sim-detail-row .detail-val { color:#cbd5e1; }

  /* ═══ MMO CHARACTER SHEET MODAL ═══ */
  .cs-overlay { position:fixed; inset:0; z-index:9999; background:rgba(0,0,0,0.85); backdrop-filter:blur(8px); display:none; overflow-y:auto; animation:cs-fadeIn 0.25s ease; }
  .cs-overlay.open { display:flex; justify-content:center; align-items:flex-start; padding:24px; }
  @keyframes cs-fadeIn { from{opacity:0} to{opacity:1} }
  .cs-sheet { width:100%; max-width:900px; background:linear-gradient(180deg,#12101f 0%,#0a0914 100%); border:2px solid #2a2755; border-radius:16px; box-shadow:0 0 60px rgba(99,102,241,0.15),0 0 120px rgba(99,102,241,0.05); position:relative; overflow:hidden; margin:auto; }
  .cs-sheet::before { content:''; position:absolute; inset:0; background:url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 30h60M30 0v60' stroke='%23ffffff' stroke-width='0.3' opacity='0.03'/%3E%3C/svg%3E"); pointer-events:none; }
  .cs-close { position:absolute; top:14px; right:18px; z-index:10; background:none; border:1px solid #ffffff22; color:#94a3b8; font-size:20px; width:36px; height:36px; border-radius:50%; cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; }
  .cs-close:hover { background:#ef444433; border-color:#ef4444; color:#f87171; }
  /* Header */
  .cs-header { display:flex; align-items:center; gap:20px; padding:24px 28px 16px; border-bottom:1px solid #ffffff0a; position:relative; z-index:1; }
  .cs-portrait { width:100px; height:100px; border-radius:14px; overflow:hidden; border:3px solid #312e81; flex-shrink:0; background:#0c0a2a; }
  .cs-portrait img { width:100%; height:100%; object-fit:cover; }
  .cs-portrait .cs-emoji { width:100%; height:100%; display:flex; align-items:center; justify-content:center; font-size:48px; background:linear-gradient(135deg,#1e1b4b 0%,#0f172a 100%); }
  .cs-header-info { flex:1; min-width:0; }
  .cs-name { font-size:22px; font-weight:800; color:#f1f5f9; letter-spacing:0.01em; }
  .cs-subtitle { font-size:12px; color:#64748b; margin-top:2px; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
  .cs-subtitle .cs-tag { font-size:10px; padding:2px 8px; border-radius:6px; font-weight:600; }
  .cs-subtitle .cs-tag-species { background:#7c3aed22; color:#c4b5fd; border:1px solid #7c3aed44; }
  .cs-subtitle .cs-tag-age { background:#3b82f622; color:#93c5fd; border:1px solid #3b82f644; }
  .cs-subtitle .cs-tag-gender { background:#ec489922; color:#f9a8d4; border:1px solid #ec489944; }
  .cs-subtitle .cs-tag-gender.male { background:#3b82f622; color:#93c5fd; border-color:#3b82f644; }
  .cs-subtitle .cs-tag-career { background:#f59e0b22; color:#fcd34d; border:1px solid #f59e0b44; }
  .cs-subtitle .cs-tag-mood { border-radius:6px; padding:2px 8px; font-size:10px; font-weight:600; }
  .cs-gold { position:absolute; right:28px; top:50%; transform:translateY(-50%); display:flex; align-items:center; gap:6px; }
  .cs-gold-icon { font-size:20px; }
  .cs-gold-val { font-size:18px; font-weight:800; color:#fbbf24; text-shadow:0 0 12px rgba(251,191,36,0.3); }
  /* Two-column layout */
  .cs-body { display:grid; grid-template-columns:1fr 1fr; gap:0; position:relative; z-index:1; }
  .cs-col { padding:16px 24px; }
  .cs-col:first-child { border-right:1px solid #ffffff06; }
  .cs-section-title { font-size:10px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px; display:flex; align-items:center; gap:6px; }
  .cs-section-title .cs-st-icon { font-size:13px; }
  /* Skill bars */
  .cs-skill { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
  .cs-skill-name { font-size:11px; color:#cbd5e1; width:100px; flex-shrink:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .cs-skill-bar { flex:1; height:8px; border-radius:4px; background:#1a1744; overflow:hidden; position:relative; border:1px solid #2a2755; }
  .cs-skill-fill { height:100%; border-radius:3px; transition:width 0.6s ease; background:linear-gradient(90deg,#6366f1,#8b5cf6); box-shadow:inset 0 1px 0 rgba(255,255,255,0.15); }
  .cs-skill-lvl { font-size:10px; font-weight:700; color:#a78bfa; width:28px; text-align:right; flex-shrink:0; }
  /* Trait chips */
  .cs-traits { display:flex; flex-wrap:wrap; gap:5px; margin-bottom:8px; }
  .cs-trait { font-size:10px; padding:3px 9px; border-radius:8px; font-weight:600; background:#1e1b4b; color:#c4b5fd; border:1px solid #312e81; }
  .cs-trait-person { background:#3b82f615; color:#93c5fd; border-color:#3b82f633; }
  .cs-trait-bonus { background:#f59e0b15; color:#fcd34d; border-color:#f59e0b33; }
  .cs-trait-aspir { background:#ec489915; color:#f9a8d4; border-color:#ec489933; }
  .cs-trait-like { background:#ef444415; color:#fca5a5; border-color:#ef444433; }
  .cs-trait-dislike { background:#64748b15; color:#94a3b8; border-color:#64748b33; text-decoration:line-through; }
  .cs-trait-life { background:#22c55e15; color:#86efac; border-color:#22c55e33; }
  /* Preference rows */
  .cs-pref-row { display:flex; flex-wrap:wrap; align-items:center; gap:4px; margin-bottom:4px; }
  .cs-pref-cat { font-size:10px; color:#94a3b8; font-weight:600; min-width:90px; flex-shrink:0; }
  /* Needs vitals */
  .cs-need { display:flex; align-items:center; gap:6px; margin-bottom:5px; }
  .cs-need-icon { font-size:14px; width:20px; text-align:center; flex-shrink:0; }
  .cs-need-name { font-size:10px; color:#94a3b8; width:48px; flex-shrink:0; }
  .cs-need-bar { flex:1; height:10px; border-radius:5px; background:#1a1744; overflow:hidden; border:1px solid #2a2755; position:relative; }
  .cs-need-fill { height:100%; border-radius:4px; transition:width 0.6s; }
  .cs-need-fill.crit { background:linear-gradient(90deg,#dc2626,#ef4444); box-shadow:0 0 8px rgba(239,68,68,0.4); }
  .cs-need-fill.low { background:linear-gradient(90deg,#f59e0b,#fbbf24); }
  .cs-need-fill.med { background:linear-gradient(90deg,#3b82f6,#60a5fa); }
  .cs-need-fill.high { background:linear-gradient(90deg,#22c55e,#4ade80); }
  .cs-need-pct { font-size:10px; font-weight:600; color:#94a3b8; width:30px; text-align:right; flex-shrink:0; }
  /* Equipment / outfit */
  .cs-equip-grid { display:grid; grid-template-columns:1fr 1fr; gap:6px; }
  .cs-equip-slot { background:#0f0d1e; border:1px solid #1e1b4b; border-radius:8px; padding:8px 10px; display:flex; align-items:center; gap:8px; transition:all 0.2s; }
  .cs-equip-slot:hover { border-color:#6366f144; background:#12101f; }
  .cs-equip-icon { font-size:18px; width:28px; height:28px; display:flex; align-items:center; justify-content:center; background:#1a1744; border-radius:6px; border:1px solid #2a2755; flex-shrink:0; }
  .cs-equip-info { flex:1; min-width:0; }
  .cs-equip-label { font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:0.05em; }
  .cs-equip-val { font-size:11px; color:#cbd5e1; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .cs-equip-empty .cs-equip-icon { opacity:0.3; }
  .cs-equip-empty .cs-equip-val { color:#334155; }
  /* Info rows */
  .cs-info-row { display:flex; align-items:center; gap:8px; padding:4px 0; font-size:11px; }
  .cs-info-icon { font-size:13px; width:20px; text-align:center; flex-shrink:0; }
  .cs-info-label { color:#64748b; }
  .cs-info-val { color:#cbd5e1; font-weight:600; margin-left:auto; }
  /* CC Mods section */
  .cs-cc-list { max-height:120px; overflow-y:auto; }
  .cs-cc-item { display:flex; align-items:center; gap:6px; padding:3px 0; font-size:10px; }
  .cs-cc-name { color:#fbbf24; flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .cs-cc-count { color:#64748b; font-weight:600; }
  /* Family */
  .cs-family-member { display:flex; align-items:center; gap:8px; padding:3px 0; font-size:11px; color:#cbd5e1; }
  .cs-family-member .cs-fm-role { font-size:9px; color:#94a3b8; margin-left:auto; }
  /* Relationship detail rows */
  .cs-rel-scroll { max-height:260px; overflow-y:auto; padding-right:4px; scrollbar-width:thin; scrollbar-color:#334155 transparent; }
  .cs-rel-scroll::-webkit-scrollbar { width:5px; }
  .cs-rel-scroll::-webkit-scrollbar-track { background:transparent; }
  .cs-rel-scroll::-webkit-scrollbar-thumb { background:#334155; border-radius:4px; }
  .cs-rel-row { display:flex; align-items:center; gap:6px; padding:2px 0; font-size:11px; }
  .cs-rel-name { color:#cbd5e1; min-width:90px; flex-shrink:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .cs-rel-tags { display:flex; flex-wrap:wrap; gap:3px; }
  .cs-rel-tag { font-size:9px; padding:1px 6px; border-radius:6px; font-weight:600; background:#1e1b4b; color:#c4b5fd; border:1px solid #312e81; }
  .cs-rel-fam { background:#7c3aed15; color:#c4b5fd; border-color:#7c3aed33; }
  .cs-rel-rom { background:#ec489915; color:#f9a8d4; border-color:#ec489933; }
  .cs-rel-fri { background:#3b82f615; color:#93c5fd; border-color:#3b82f633; }
  .cs-rel-comp { background:#f59e0b15; color:#fcd34d; border-color:#f59e0b33; }

  /* ── Cheat-Konsole v2 ── */
  .cheat-toolbar { display:flex; gap:12px; align-items:stretch; margin-bottom:18px; }
  .cheat-search-wrap { position:relative; flex:1; }
  .cheat-search-wrap::before { content:'🔍'; position:absolute; left:14px; top:50%; transform:translateY(-50%); font-size:15px; pointer-events:none; z-index:1; }
  .cheat-search { width:100%; padding:11px 16px 11px 42px; background:#0d1117; border:1px solid #30363d; border-radius:12px; color:#e6edf3; font-size:14px; outline:none; transition:border-color 0.2s, box-shadow 0.2s; box-sizing:border-box; }
  .cheat-search:focus { border-color:#6366f1; box-shadow:0 0 0 3px rgba(99,102,241,0.18); }
  .cheat-fav-toggle { display:flex; align-items:center; gap:6px; padding:8px 18px; background:#0d1117; border:1px solid #30363d; border-radius:12px; color:#94a3b8; cursor:pointer; font-size:13px; font-weight:600; white-space:nowrap; transition:all 0.2s; user-select:none; }
  .cheat-fav-toggle:hover { border-color:#eab308; color:#fbbf24; }
  .cheat-fav-toggle.active { background:#eab30812; border-color:#eab308; color:#fbbf24; box-shadow:0 0 12px rgba(234,179,8,0.12); }
  .cheat-fav-toggle .fav-star { font-size:16px; }
  .cheat-fav-count { font-size:11px; background:#eab30822; color:#fbbf24; padding:1px 7px; border-radius:8px; margin-left:2px; }
  .cheat-cats { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:20px; padding:0 2px; }
  .cheat-cat-btn { background:#161b22; border:1px solid #21262d; color:#8b949e; padding:7px 16px; border-radius:99px; cursor:pointer; font-size:12px; font-weight:600; transition:all 0.2s; user-select:none; }
  .cheat-cat-btn:hover { background:#1c2333; border-color:#388bfd44; color:#c9d1d9; }
  .cheat-cat-btn.active { background:linear-gradient(135deg,#4f46e5,#6366f1); color:#fff; border-color:transparent; box-shadow:0 2px 12px rgba(99,102,241,0.35); }
  .cheat-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(420px, 1fr)); gap:16px; }
  .cheat-card { background:#0d1117; border:1px solid #21262d; border-radius:16px; overflow:hidden; transition:all 0.25s; }
  .cheat-card:hover { border-color:#30363d; box-shadow:0 8px 32px rgba(0,0,0,0.4); }
  .cheat-card-head { padding:16px 20px 10px; display:flex; align-items:center; gap:14px; border-bottom:1px solid #21262d; }
  .cheat-card-icon { font-size:28px; width:46px; height:46px; display:flex; align-items:center; justify-content:center; border-radius:12px; flex-shrink:0; }
  .cheat-card-title { font-size:15px; font-weight:700; color:#e6edf3; letter-spacing:-0.01em; }
  .cheat-card-desc { font-size:11px; color:#8b949e; margin-top:3px; }
  .cheat-card-body { padding:8px 8px 12px; }
  .cheat-row { display:grid; grid-template-columns:1fr auto auto auto; align-items:center; gap:8px; padding:9px 14px; margin:2px 0; border-radius:10px; cursor:pointer; transition:all 0.15s; position:relative; }
  .cheat-row:hover { background:#161b22; }
  .cheat-row-code { font-family:'Cascadia Code','Fira Code','JetBrains Mono',monospace; font-size:12.5px; color:#79c0ff; word-break:break-all; line-height:1.4; }
  .cheat-row-desc { font-size:11px; color:#8b949e; text-align:right; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:200px; }
  .cheat-row-fav { font-size:14px; opacity:0.3; cursor:pointer; transition:all 0.2s; padding:2px 4px; flex-shrink:0; user-select:none; }
  .cheat-row-fav:hover { opacity:1; transform:scale(1.3); }
  .cheat-row-fav.is-fav { opacity:1; filter:drop-shadow(0 0 4px rgba(234,179,8,0.5)); }
  .cheat-row-copy { font-size:13px; opacity:0; transition:opacity 0.15s; flex-shrink:0; color:#8b949e; }
  .cheat-row:hover .cheat-row-copy { opacity:0.7; }
  .cheat-row:hover .cheat-row-copy:hover { opacity:1; color:#6366f1; }
  .cheat-copied { background:#22c55e12 !important; }
  .cheat-copied .cheat-row-copy { opacity:1 !important; color:#22c55e !important; }
  .cheat-card.cheat-hidden { display:none; }
  .cheat-row.cheat-hidden { display:none; }
  .cheat-count { font-size:12px; color:#8b949e; font-weight:500; }
  .cheat-req { display:inline-block; font-size:9px; padding:2px 7px; border-radius:6px; background:#f59e0b12; color:#f59e0b; border:1px solid #f59e0b28; font-weight:600; letter-spacing:0.02em; }
  .cheat-note { font-size:11px; color:#8b949e; padding:6px 14px; font-style:italic; border-left:2px solid #30363d; margin:4px 12px; }
  .cheat-card-fav { background:linear-gradient(135deg,#1a1500 0%,#0d1117 100%); }
  .cheat-card-fav .cheat-card-body { max-height:300px; overflow-y:auto; }

  /* Footer */
  .cs-footer { padding:12px 24px; border-top:1px solid #ffffff06; text-align:center; font-size:10px; color:#334155; position:relative; z-index:1; }
  /* Responsive */
  @media (max-width:700px) { .cs-body { grid-template-columns:1fr; } .cs-col:first-child { border-right:none; border-bottom:1px solid #ffffff06; } .cs-header { flex-direction:column; text-align:center; } .cs-gold { position:static; transform:none; justify-content:center; margin-top:8px; } }

  /* Library household cards */
  .lib-hh-card { background:linear-gradient(135deg,#1a1d2e 0%,#0f1115 100%); border:1px solid #334155; border-radius:14px; padding:16px; transition:all 0.2s; }
  .lib-hh-card:hover { border-color:#6366f155; box-shadow:0 0 20px rgba(99,102,241,0.08); transform:translateY(-1px); }
  .lib-hh-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
  .lib-hh-name { font-size:15px; font-weight:700; color:#e2e8f0; }
  .lib-hh-creator { font-size:11px; color:#94a3b8; }
  .lib-hh-sims { display:flex; flex-wrap:wrap; gap:8px; }
  .lib-sim-mini { display:flex; align-items:center; gap:6px; background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:4px 10px 4px 4px; font-size:12px; color:#cbd5e1; transition:all 0.2s; }
  .lib-sim-mini:hover { border-color:#6366f144; }
  .lib-sim-mini img { width:36px; height:36px; border-radius:6px; object-fit:cover; }
  .lib-sim-mini .lib-sim-avatar { width:36px; height:36px; border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:18px; background:#1e1b4b; }
  .lib-sim-mini.in-game { border-color:#22c55e44; background:#22c55e08; }
  .lib-sim-mini.lib-only { border-color:#8b5cf644; background:#8b5cf608; }
  .lib-sim-dot { width:6px; height:6px; border-radius:50%; flex-shrink:0; }
  .lib-sim-dot.active { background:#4ade80; }
  .lib-sim-dot.inactive { background:#8b5cf6; }
  /* CC-Info auf Haushaltskarten */
  .lib-cc-badge { display:inline-flex; align-items:center; gap:3px; background:#f59e0b22; color:#fbbf24; border:1px solid #f59e0b44; padding:2px 8px; border-radius:6px; font-size:10px; font-weight:600; cursor:pointer; transition:all 0.2s; }
  .lib-cc-badge:hover { background:#f59e0b33; border-color:#f59e0b66; }
  .lib-cc-badge.no-cc { background:#22c55e11; color:#86efac; border-color:#22c55e33; cursor:default; }
  .lib-cc-list { display:none; margin-top:8px; padding:8px 10px; background:#0f172a; border:1px solid #1e293b; border-radius:8px; font-size:11px; color:#94a3b8; }
  .lib-cc-list.open { display:block; }
  .lib-cc-item { display:flex; justify-content:space-between; align-items:center; padding:3px 0; border-bottom:1px solid #1e293b; }
  .lib-cc-item:last-child { border-bottom:none; }
  .lib-cc-item-name { color:#cbd5e1; word-break:break-all; }
  .lib-cc-item-count { color:#f59e0b; font-weight:600; font-size:10px; flex-shrink:0; margin-left:8px; }
  /* ── Card-Glanz-Effekt bei Hover ── */
  .sim-card::after { content:''; position:absolute; top:-50%; left:-50%; width:200%; height:200%; background:radial-gradient(circle at 30% 30%, rgba(255,255,255,0.05), transparent 60%); opacity:0; transition:opacity 0.3s; pointer-events:none; z-index:0; }
  .sim-card:hover::after { opacity:1; }
  /* ── Neue Badges: Spezies, Simoleons, Karriere, Lot, Username ── */
  .sim-badge-simoleons { background:#22c55e18; color:#86efac; border:1px solid #22c55e33; font-weight:700; }
  .sim-badge-career { background:#3b82f618; color:#93c5fd; border:1px solid #3b82f633; }
  .sim-badge-lot { background:#a855f718; color:#d8b4fe; border:1px solid #a855f733; font-style:italic; }
  .sim-badge-username { background:#06b6d418; color:#67e8f9; border:1px solid #06b6d433; }
  /* Spezies-spezifische Karten-Farben */
  .sim-card.pet { border-color:#a855f780; background:linear-gradient(180deg,#3b1d5e 0%,#0f172a 100%); }
  .sim-card.pet:hover { border-color:#c084fc; box-shadow:0 8px 32px rgba(168,85,247,0.35); }
  .sim-card.horse { border-color:#92400e80; background:linear-gradient(180deg,#451a03 0%,#0f172a 100%); }
  .sim-card.horse:hover { border-color:#d97706; box-shadow:0 8px 32px rgba(217,119,6,0.35); }
  .sim-card.werewolf { border-color:#65a30d80; background:linear-gradient(180deg,#1a2e05 0%,#0f172a 100%); }
  .sim-card.werewolf:hover { border-color:#84cc16; box-shadow:0 8px 32px rgba(132,204,22,0.35); }
  .sim-card.spellcaster { border-color:#7c3aed80; background:linear-gradient(180deg,#2e1065 0%,#0f172a 100%); }
  .sim-card.spellcaster:hover { border-color:#a78bfa; box-shadow:0 8px 32px rgba(139,92,246,0.35); }
  .sim-card.fairy { border-color:#10b98180; background:linear-gradient(180deg,#064e3b 0%,#0f172a 100%); }
  .sim-card.fairy:hover { border-color:#34d399; box-shadow:0 8px 32px rgba(52,211,153,0.35); }
  .sim-card.vampire { border-color:#dc262680; background:linear-gradient(180deg,#450a0a 0%,#0f172a 100%); }
  .sim-card.vampire:hover { border-color:#f87171; box-shadow:0 8px 32px rgba(248,113,113,0.35); }
  .sim-card.mermaid { border-color:#06b6d480; background:linear-gradient(180deg,#083344 0%,#0f172a 100%); }
  .sim-card.mermaid:hover { border-color:#22d3ee; box-shadow:0 8px 32px rgba(34,211,238,0.35); }
  .sim-card.alien { border-color:#84cc1680; background:linear-gradient(180deg,#1a2e05 0%,#0f172a 100%); }
  .sim-card.alien:hover { border-color:#a3e635; box-shadow:0 8px 32px rgba(163,230,53,0.35); }
  /* ── Trait-Details Tooltip/Aufklapper ── */
  .sim-trait-details { display:none; font-size:10px; color:#94a3b8; padding:2px 12px; margin-top:2px; }
  .sim-badge-traits:hover + .sim-trait-details, .sim-trait-details:hover { display:flex; gap:6px; flex-wrap:wrap; }
  .sim-trait-detail-item { background:#1e293b; padding:1px 6px; border-radius:4px; border:1px solid #334155; white-space:nowrap; }
  /* ── Spieleinstellungen-Panel ── */
  .game-settings-panel { background:linear-gradient(135deg,#1a1d2e 0%,#0f1115 100%); border:1px solid #334155; border-radius:14px; padding:16px; margin-bottom:16px; }
  .game-settings-panel h3 { font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:12px; display:flex; align-items:center; gap:8px; }
  .game-settings-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:8px; }
  .game-setting-item { display:flex; align-items:center; gap:8px; padding:6px 10px; background:#0f172a; border:1px solid #1e293b; border-radius:8px; font-size:12px; }
  .game-setting-icon { font-size:14px; flex-shrink:0; }
  .game-setting-label { color:#64748b; font-size:10px; text-transform:uppercase; letter-spacing:0.05em; }
  .game-setting-val { color:#e2e8f0; font-weight:600; }
  .game-version-badge { font-size:11px; background:#6366f122; color:#a5b4fc; border:1px solid #6366f144; padding:3px 10px; border-radius:8px; font-weight:600; }
  .sim-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:14px; }
  .tray-most-used-table { width:100%; border-collapse:collapse; margin-top:10px; }
  .tray-most-used-table th { text-align:left; font-size:11px; color:#64748b; padding:6px 10px; border-bottom:1px solid #334155; }
  .tray-most-used-table td { font-size:12px; color:#cbd5e1; padding:8px 10px; border-bottom:1px solid #1e293b; }
  .tray-most-used-table tr:hover { background:#1e293b; }
  .tray-used-count { background:#6366f133; color:#a5b4fc; padding:2px 8px; border-radius:6px; font-size:11px; font-weight:600; }
  .tray-progress { background:#1e293b; border-radius:8px; height:8px; margin:10px 0; overflow:hidden; }
  .tray-progress-bar { height:100%; background:linear-gradient(90deg,#6366f1,#a78bfa); border-radius:8px; transition:width 0.3s; }

  /* ═══ MINI SIMS-LOADER (einheitlich für alle Tabs) ═══ */
  .sims-mini-loader { text-align:center; padding:30px 20px; }
  .sims-mini-loader .mini-plumbob { width:40px; height:52px; margin:0 auto 12px; animation: miniPlumbobFloat 2s ease-in-out infinite; }
  @keyframes miniPlumbobFloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
  .sims-mini-loader .mini-loader-bar-wrap { max-width:280px; margin:0 auto 14px; height:4px; background:rgba(255,255,255,0.08); border-radius:4px; overflow:hidden; }
  .sims-mini-loader .mini-loader-bar { height:100%; background:linear-gradient(90deg,#3bc455,#4cda64,#7be89a); border-radius:4px; transition:width 0.3s ease; box-shadow:0 0 8px rgba(76,218,100,0.4); }
  .sims-mini-loader .mini-loader-text { font-size:14px; font-weight:300; color:rgba(255,255,255,0.5); letter-spacing:2px; text-transform:uppercase; margin-bottom:8px; }
  .sims-mini-loader .mini-loader-tip { font-size:12px; color:rgba(255,255,255,0.35); letter-spacing:1px; min-height:18px; transition:opacity 0.4s ease; }
  .tray-warning-badge { display:inline-flex; align-items:center; gap:4px; background:#f59e0b22; color:#fbbf24; border:1px solid #f59e0b44; padding:2px 8px; border-radius:6px; font-size:10px; font-weight:600; cursor:help; }

  /* Toast-Benachrichtigungen */
  #toast-container { position:fixed; top:18px; right:18px; z-index:99999; display:flex; flex-direction:column; gap:8px; pointer-events:none; }
  .toast { pointer-events:auto; display:flex; align-items:center; gap:10px; padding:12px 18px; border-radius:10px; font-size:13px; font-weight:500; color:#e2e8f0; box-shadow:0 8px 24px #0008; backdrop-filter:blur(8px); animation: toastIn .3s ease-out, toastOut .3s ease-in forwards; animation-delay: 0s, var(--toast-duration, 4s); max-width:420px; }
  .toast-success { background:#065f4680; border:1px solid #10b98155; }
  .toast-error   { background:#7f1d1d80; border:1px solid #ef444455; }
  .toast-warning { background:#78350f80; border:1px solid #f59e0b55; }
  .toast-info    { background:#1e3a5f80; border:1px solid #3b82f655; }
  .toast-icon { font-size:18px; flex-shrink:0; }
  .toast-close { cursor:pointer; opacity:.6; margin-left:auto; font-size:16px; flex-shrink:0; }
  .toast-close:hover { opacity:1; }
  @keyframes toastIn { from { transform:translateX(120%); opacity:0; } to { transform:translateX(0); opacity:1; } }
  @keyframes toastOut { from { opacity:1; } to { opacity:0; transform:translateY(-10px); } }

  /* ═══ LADESCREEN ═══ */
  #sims-loader {
    position:fixed; inset:0; z-index:100000;
    background:linear-gradient(135deg, #0a1628 0%, #1a3a5c 30%, #1e5a8a 50%, #1a3a5c 70%, #0a1628 100%);
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    font-family:'Segoe UI', system-ui, sans-serif;
    color:#fff;
    transition:opacity 0.8s ease, visibility 0.8s ease;
    overflow:hidden;
  }
  #sims-loader.hidden { opacity:0; visibility:hidden; pointer-events:none; }
  #sims-loader::before {
    content:''; position:absolute; inset:0;
    background-image:
      radial-gradient(1px 1px at 10% 20%, rgba(255,255,255,0.4) 50%, transparent 100%),
      radial-gradient(1px 1px at 30% 60%, rgba(255,255,255,0.3) 50%, transparent 100%),
      radial-gradient(1.5px 1.5px at 50% 10%, rgba(255,255,255,0.5) 50%, transparent 100%),
      radial-gradient(1px 1px at 70% 40%, rgba(255,255,255,0.3) 50%, transparent 100%),
      radial-gradient(1px 1px at 90% 80%, rgba(255,255,255,0.4) 50%, transparent 100%),
      radial-gradient(1.5px 1.5px at 15% 85%, rgba(255,255,255,0.35) 50%, transparent 100%),
      radial-gradient(1px 1px at 55% 75%, rgba(255,255,255,0.3) 50%, transparent 100%),
      radial-gradient(1px 1px at 85% 15%, rgba(255,255,255,0.4) 50%, transparent 100%);
    animation:twinkle 4s ease-in-out infinite alternate;
  }
  @keyframes twinkle { 0%{opacity:0.5;} 100%{opacity:1;} }
  #plumbob-canvas { position:relative; z-index:2; margin-bottom:20px; }
  .loader-title { font-size:28px; font-weight:300; letter-spacing:6px; text-transform:uppercase; margin-bottom:8px; text-shadow:0 0 20px rgba(76,218,100,0.4); z-index:2; }
  .loader-version { font-size:13px; font-weight:300; letter-spacing:3px; color:rgba(255,255,255,0.5); margin-bottom:50px; z-index:2; }
  .loader-bar-wrap { width:380px; max-width:80vw; height:4px; background:rgba(255,255,255,0.1); border-radius:4px; overflow:hidden; margin-bottom:20px; z-index:2; }
  .loader-bar { height:100%; width:0%; background:linear-gradient(90deg,#3bc455,#4cda64,#7be89a); border-radius:4px; transition:width 0.4s ease; box-shadow:0 0 12px rgba(76,218,100,0.5); }
  .loader-tip { font-size:14px; font-weight:300; color:rgba(255,255,255,0.7); letter-spacing:1px; min-height:22px; z-index:2; transition:opacity 0.4s ease; }
  .loader-stage { font-size:11px; font-weight:400; color:rgba(255,255,255,0.35); letter-spacing:1px; margin-top:10px; z-index:2; min-height:16px; transition:opacity 0.3s ease; }
  .loader-stage .stage-pct { color:rgba(76,218,100,0.7); font-weight:600; margin-left:6px; }
  .loader-particle { position:absolute; width:3px; height:3px; background:rgba(76,218,100,0.4); border-radius:50%; animation:particle-rise linear infinite; }
  @keyframes particle-rise { 0%{transform:translateY(0) scale(1); opacity:0.6;} 100%{transform:translateY(-100vh) scale(0); opacity:0;} }
  .loader-brand { position:absolute; bottom:30px; left:40px; font-size:11px; letter-spacing:2px; color:rgba(255,255,255,0.25); z-index:2; }
  .loader-skip { position:absolute; bottom:30px; right:40px; font-size:12px; color:rgba(255,255,255,0.35); cursor:pointer; z-index:2; transition:color 0.2s; border:none; background:none; letter-spacing:1px; font-family:inherit; }
  .loader-skip:hover { color:rgba(255,255,255,0.7); }
</style>
</head>
<body>
<!-- ═══ SIMS 4 LADESCREEN ═══ -->
<div id="sims-loader">
  <canvas id="plumbob-canvas"></canvas>
  <div class="loader-title">Duplicate Scanner</div>
  <div class="loader-version">v3.2.0</div>
  <div class="loader-bar-wrap"><div class="loader-bar" id="loader-bar"></div></div>
  <div class="loader-tip" id="loader-tip"></div>
  <div class="loader-stage" id="loader-stage"></div>
  <div class="loader-brand">SIMS 4 TOOLS</div>
  <button class="loader-skip" onclick="dismissLoader()">Überspringen ›</button>
</div>
<script src="/three.min.js"></script>
<script>
// ═══ PLUMBOB 3D + LADESCREEN LOGIK ═══
var _loaderDismissed = false;
function dismissLoader() {
  if (_loaderDismissed) return;
  _loaderDismissed = true;
  var el = document.getElementById('sims-loader');
  if (el) { el.classList.add('hidden'); setTimeout(function(){ el.remove(); }, 900); }
}
// Fortschrittsbalken von außen steuerbar
var _loaderProgress = 0;
function setLoaderProgress(pct) {
  _loaderProgress = Math.min(100, Math.max(0, pct));
  var b = document.getElementById('loader-bar');
  if (b) b.style.width = _loaderProgress + '%';
  _updateLoaderStage();
  if (_loaderProgress >= 100) setTimeout(dismissLoader, 500);
}

// ═══ READINESS TRACKING — Loader bleibt bis ALLES fertig ═══
var _scanReady = false, _savegameReady = false, _libraryReady = false;
function _checkAllReady() {
  if (_loaderDismissed) return;
  var done = (_scanReady?1:0) + (_savegameReady?1:0) + (_libraryReady?1:0);
  // Scan=0-40%, Savegame=40-70%, Library=70-100%
  var minPct = 0;
  if (_scanReady) minPct = 40;
  if (_savegameReady) minPct = Math.max(minPct, 70);
  if (_libraryReady) minPct = Math.max(minPct, 100);
  if (done >= 3) minPct = 100;
  if (_loaderProgress < minPct) setLoaderProgress(minPct);
}

// ═══ STAGE-ANZEIGE unter dem Tipp ═══
function _updateLoaderStage() {
  var el = document.getElementById('loader-stage');
  if (!el || _loaderDismissed) return;
  var pct = Math.round(_loaderProgress);
  var stage = '';
  if (!_scanReady) stage = '📦 Scan-Daten laden';
  else if (!_savegameReady && !_libraryReady) stage = '💾 Spielstand & Bibliothek laden';
  else if (!_savegameReady) stage = '💾 Spielstand wird analysiert';
  else if (!_libraryReady) stage = '📚 Bibliothek wird geladen';
  else stage = '✅ Alles bereit!';
  el.innerHTML = stage + ' <span class="stage-pct">' + pct + '%</span>';
}

// ═══ MINI-LOADER Hilfsfunktionen (einheitlich für alle Tabs) ═══
var _miniPlumbobSVG = '<svg class="mini-plumbob" viewBox="0 0 54 70"><defs><linearGradient id="mlG" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#7af59a"/><stop offset="50%" stop-color="#3ed85e"/><stop offset="100%" stop-color="#1a8c3a"/></linearGradient></defs><polygon points="27,2 52,28 27,68 2,28" fill="url(#mlG)" opacity="0.85" stroke="#7af59a" stroke-width="0.5"/><polygon points="27,8 46,28 27,60 8,28" fill="#4cda64" opacity="0.25"/></svg>';
var _miniTips = [
  "Retikuliere Splines \u2026", "Sortiere Simoleons \u2026", "Platziere M\u00f6bel \u2026",
  "Z\u00e4hle Plumbobs \u2026", "Lade Nachbarschaften \u2026", "Erstelle Sim-Portraits \u2026",
  "Analysiere Mod-Dateien \u2026", "Katalogisiere Custom Content \u2026",
  "Berechne Duplikate \u2026", "Dekomprimiere QFS-Daten \u2026"
];
function _miniLoaderHTML(id, text, pct) {
  var tip = _miniTips[Math.floor(Math.random()*_miniTips.length)];
  return '<div class="sims-mini-loader" id="'+id+'">' + _miniPlumbobSVG +
    '<div class="mini-loader-text" id="'+id+'-text">'+text+'</div>' +
    '<div class="mini-loader-bar-wrap"><div class="mini-loader-bar" id="'+id+'-bar" style="width:'+(pct||5)+'%"></div></div>' +
    '<div style="font-size:12px;color:rgba(76,218,100,0.7);font-weight:600;margin-bottom:6px;min-height:16px;" id="'+id+'-info">'+(pct||0)+'%</div>' +
    '<div class="mini-loader-tip" id="'+id+'-tip">'+tip+'</div></div>';
}
function _setMiniBar(id, pct) {
  var b = document.getElementById(id+'-bar');
  if (b) b.style.width = Math.min(pct,100)+'%';
  var info = document.getElementById(id+'-info');
  if (info) info.textContent = Math.round(Math.min(pct,100)) + '%';
}
function _rotateMiniTip(id) {
  var el = document.getElementById(id+'-tip');
  if (!el) return;
  el.style.opacity='0';
  setTimeout(function(){
    el.textContent = _miniTips[Math.floor(Math.random()*_miniTips.length)];
    el.style.opacity='1';
  }, 350);
}
// Starte Tipp-Rotation für Mini-Loader
var _miniTipTimers = {};
function _startMiniTipRotation(id) {
  if (_miniTipTimers[id]) clearInterval(_miniTipTimers[id]);
  _miniTipTimers[id] = setInterval(function(){ _rotateMiniTip(id); }, 3000);
}
function _stopMiniTipRotation(id) {
  if (_miniTipTimers[id]) { clearInterval(_miniTipTimers[id]); delete _miniTipTimers[id]; }
}

(function(){
  // ─── Partikel ───
  var loader = document.getElementById('sims-loader');
  for (var i = 0; i < 20; i++) {
    var p = document.createElement('div');
    p.className = 'loader-particle';
    p.style.left = Math.random()*100 + '%';
    p.style.bottom = '-10px';
    p.style.animationDuration = (4+Math.random()*6) + 's';
    p.style.animationDelay = (Math.random()*8) + 's';
    p.style.width = p.style.height = (2+Math.random()*3) + 'px';
    loader.appendChild(p);
  }

  // ─── Lade-Tipps (Sims 4 Fun + Programm-Infos) ───
  var tips = [
    // Sims 4 Fun
    "Retikuliere Splines \u2026", "Sortiere Simoleons \u2026", "Platziere M\u00f6bel \u2026",
    "Z\u00e4hle Plumbobs \u2026", "Kalibriere Wunschbrunnen \u2026", "Lade Nachbarschaften \u2026",
    "Erstelle Sim-Portraits \u2026", "\u00dcbersetze Sim-Namen \u2026",
    "Dekomprimiere QFS-Daten \u2026", "Baue Vorschaubilder auf \u2026",
    // Programm-Infos
    "\ud83d\udee0\ufe0f Findet Duplikate, korrupte Mods & CC-Konflikte",
    "\ud83e\udea8 Skin-Diagnose erkennt Stein-Haut automatisch",
    "\ud83c\udfad Tray-Analyse zeigt CC in Grundst\u00fccken & R\u00e4umen",
    "\ud83d\udcbe Savegame-Analyse liest alle Sims aus deinem Spielstand",
    "\ud83d\uddd1\ufe0f Mods k\u00f6nnen direkt gel\u00f6scht oder deaktiviert werden",
    "\ud83d\udcda Die Bibliothek zeigt gespeicherte Sims mit Portraits",
    "\u2699\ufe0f Script-Mods brechen fast immer nach Patches",
    "\ud83d\udd0d \u00dcber 20 Analyse-Tools in einer Oberfl\u00e4che",
    "\ud83d\udce6 Package-Dateien werden per DBPF-Format gelesen",
    "\ud83c\udfae Unterst\u00fctzt alle Sims 4 Erweiterungen & Packs"
  ];
  var tipIdx = Math.floor(Math.random()*tips.length);
  var tipEl = document.getElementById('loader-tip');
  tipEl.textContent = tips[tipIdx];
  setInterval(function(){
    tipEl.style.opacity = '0';
    setTimeout(function(){
      tipIdx = (tipIdx+1) % tips.length;
      tipEl.textContent = tips[tipIdx];
      tipEl.style.opacity = '1';
    }, 400);
  }, 2800);

  // ─── Echter Scan-Fortschritt via /api/progress ───
  function pollScanProgress(){
    if (_loaderDismissed) return;
    fetch('/api/progress?token=' + encodeURIComponent(TOKEN))
      .then(function(r){ return r.json(); })
      .then(function(d){
        if (_loaderDismissed) return;
        if (d.active || d.done) {
          // Echte Prozent: Scan = 0-40% des Hauptloaders
          var scanPct = 0;
          if (d.total > 0) scanPct = Math.round((d.cur / d.total) * 100);
          if (d.done) scanPct = 100;
          // Skaliere Scan-Fortschritt auf 0-40% des Hauptloaders (Rest für Savegame/Lib)
          var mappedPct = Math.round(scanPct * 0.4);
          if (_loaderProgress < mappedPct) {
            _loaderProgress = mappedPct;
            var b = document.getElementById('loader-bar');
            if (b) b.style.width = _loaderProgress + '%';
          }
          _updateLoaderStage();
          // Phase-Info aktualisieren
          if (d.msg && !_scanReady) {
            var stEl = document.getElementById('loader-stage');
            if (stEl) stEl.innerHTML = '\ud83d\udce6 ' + d.msg + ' <span class=\"stage-pct\">' + Math.round(_loaderProgress) + '%</span>';
          }
        }
        if (!_scanReady) setTimeout(pollScanProgress, 600);
      })
      .catch(function(){ if (!_scanReady) setTimeout(pollScanProgress, 1500); });
  }
  setTimeout(pollScanProgress, 500);

  // ─── Savegame + Bibliothek Progress-Polling (für Hauptloader-Stage) ───
  function pollSubProgress(){
    if (_loaderDismissed) return;
    var pending = [];
    if (!_savegameReady) pending.push(fetch('/api/savegame?token=' + encodeURIComponent(TOKEN)).then(function(r){return r.json();}));
    if (!_libraryReady) pending.push(fetch('/api/library?token=' + encodeURIComponent(TOKEN)).then(function(r){return r.json();}));
    if (pending.length === 0) return;
    Promise.all(pending).then(function(results){
      if (_loaderDismissed) return;
      var stEl = document.getElementById('loader-stage');
      // Berechne den echten Gesamtfortschritt
      var sgPct = _savegameReady ? 100 : 0;
      var libPct = _libraryReady ? 100 : 0;
      var sgMsg = '', libMsg = '';
      for (var i = 0; i < results.length; i++) {
        var d = results[i];
        if (!d) continue;
        if (d.progress && d.progress.pct !== undefined) {
          // Bestimme ob das Savegame oder Library ist
          if (!_savegameReady && d.progress.phase && (d.progress.msg||'').indexOf('Spielstand') >= 0 || (d.progress.msg||'').indexOf('Portrait') >= 0 || (d.progress.msg||'').indexOf('Wiki') >= 0 || (d.progress.phase||'').indexOf('read') >= 0 || (d.progress.phase||'').indexOf('sims') >= 0 || (d.progress.phase||'').indexOf('wiki') >= 0 || (d.progress.phase||'').indexOf('tray_portraits') >= 0) {
            sgPct = d.progress.pct;
            sgMsg = d.progress.msg || '';
          } else {
            libPct = d.progress.pct;
            libMsg = d.progress.msg || '';
          }
        }
      }
      // Skaliere: Scan=0-40%, Savegame=40-70%, Library=70-100%
      var totalPct = 40;
      if (_scanReady) totalPct = 40;
      if (!_savegameReady) totalPct += Math.round(sgPct * 0.3);
      else totalPct += 30;
      if (!_libraryReady) totalPct += Math.round(libPct * 0.3);
      else totalPct += 30;
      if (_loaderProgress < totalPct) {
        _loaderProgress = totalPct;
        var b = document.getElementById('loader-bar');
        if (b) b.style.width = _loaderProgress + '%';
      }
      // Stage-Text: zeige was gerade aktiv lädt
      if (stEl && !_loaderDismissed) {
        var txt = '';
        if (!_savegameReady && sgMsg) txt = '\ud83d\udcbe ' + sgMsg;
        else if (!_libraryReady && libMsg) txt = '\ud83d\udcda ' + libMsg;
        else if (!_savegameReady) txt = '\ud83d\udcbe Spielstand wird analysiert…';
        else if (!_libraryReady) txt = '\ud83d\udcda Bibliothek wird geladen…';
        if (txt) stEl.innerHTML = txt + ' <span class=\"stage-pct\">' + Math.round(_loaderProgress) + '%</span>';
      }
      if (!_savegameReady || !_libraryReady) setTimeout(pollSubProgress, 800);
    }).catch(function(){ if (!_savegameReady || !_libraryReady) setTimeout(pollSubProgress, 2000); });
  }
  setTimeout(pollSubProgress, 1200);

  // ─── THREE.JS PLUMBOB ───
  if (typeof THREE !== 'undefined') {
    var canvas = document.getElementById('plumbob-canvas');
    var W = 220, H = 280;
    canvas.width = W; canvas.height = H;
    canvas.style.width = W+'px'; canvas.style.height = H+'px';

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(35, W/H, 0.1, 100);
    camera.position.set(0, 0.3, 4.5);
    camera.lookAt(0, 0, 0);

    var renderer = new THREE.WebGLRenderer({ canvas:canvas, alpha:true, antialias:true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);

    // Hexagonal bipyramid
    var topY=1.35, botY=-1.0, midY=0.05, rad=0.7;
    var verts=[], idx=[];
    verts.push(0, topY, 0);
    for(var j=0;j<6;j++){
      var a=(j/6)*Math.PI*2 - Math.PI/6;
      verts.push(Math.cos(a)*rad, midY, Math.sin(a)*rad);
    }
    verts.push(0, botY, 0);
    for(var j=0;j<6;j++){ var n1=(j%6)+1, n2=((j+1)%6)+1; idx.push(0,n1,n2); }
    for(var j=0;j<6;j++){ var n1=(j%6)+1, n2=((j+1)%6)+1; idx.push(7,n2,n1); }

    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
    geo.setIndex(idx);
    geo.computeVertexNormals();

    var mat = new THREE.MeshPhongMaterial({
      color:0x3ed85e, emissive:0x1a6b2a, emissiveIntensity:0.35,
      specular:0xaaffcc, shininess:90,
      transparent:true, opacity:0.82,
      side:THREE.DoubleSide, flatShading:true
    });
    var pb = new THREE.Mesh(geo, mat);
    scene.add(pb);

    var innerMat = new THREE.MeshBasicMaterial({
      color:0x7af59a, transparent:true, opacity:0.18,
      side:THREE.DoubleSide, blending:THREE.AdditiveBlending
    });
    var inner = new THREE.Mesh(geo.clone(), innerMat);
    inner.scale.set(0.92,0.92,0.92);
    scene.add(inner);

    var wireMat = new THREE.MeshBasicMaterial({
      color:0x8fffa8, transparent:true, opacity:0.12, wireframe:true
    });
    var wire = new THREE.Mesh(geo.clone(), wireMat);
    scene.add(wire);

    var kl = new THREE.DirectionalLight(0xffffff, 1.0); kl.position.set(2,4,3); scene.add(kl);
    var rl = new THREE.DirectionalLight(0x88ffaa, 0.6); rl.position.set(-2,-1,-3); scene.add(rl);
    scene.add(new THREE.AmbientLight(0x3a7a4a, 0.5));
    var bl = new THREE.PointLight(0x44dd66, 0.4, 8); bl.position.set(0,-2,1); scene.add(bl);

    var t=0;
    function anim(){
      if (_loaderDismissed) return;
      requestAnimationFrame(anim);
      t += 0.012;
      pb.rotation.y = inner.rotation.y = wire.rotation.y = t*0.8;
      var fy = Math.sin(t*1.1)*0.15;
      pb.position.y = inner.position.y = wire.position.y = fy;
      var tl = Math.sin(t*0.7)*0.06;
      pb.rotation.z = inner.rotation.z = wire.rotation.z = tl;
      innerMat.opacity = 0.15 + Math.sin(t*2)*0.08;
      renderer.render(scene, camera);
    }
    anim();
  }
})();
</script>
<div id="toast-container"></div>
<div id="batch-progress-overlay" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.7); z-index:99998; display:none; align-items:center; justify-content:center;">
  <div style="background:#1e293b; border-radius:12px; padding:24px 32px; min-width:400px; max-width:500px; box-shadow:0 8px 32px rgba(0,0,0,0.5);">
    <h3 id="batch-progress-title" style="margin:0 0 12px; color:#e2e8f0;">Batch-Aktion…</h3>
    <div style="background:#0f172a; border-radius:8px; height:24px; overflow:hidden; position:relative; margin-bottom:8px;">
      <div id="batch-progress-bar" style="height:100%; background:linear-gradient(90deg,#6366f1,#a78bfa); width:0%; transition:width 0.2s ease; border-radius:8px;"></div>
    </div>
    <div id="batch-progress-text" style="font-size:12px; color:#94a3b8; margin-bottom:4px;">0 / 0</div>
    <div id="batch-progress-file" style="font-size:11px; color:#64748b; word-break:break-all; max-height:40px; overflow:hidden;"></div>
  </div>
</div>
<div style="display:flex;align-items:center;gap:16px;margin-bottom:0;">
  <div>
    <h1 style="margin:0;">🎮 Sims 4 Mod-Scanner</h1>
    <p class="muted" style="margin:4px 0 0;">Dein Werkzeug zum Aufräumen — findet Duplikate, Konflikte, kaputte Dateien &amp; mehr.</p>
  </div>
</div>

<div id="section-nav">
  <button class="nav-tab active" onclick="switchTab('dashboard')" id="nav-dashboard">🏠 Dashboard</button>
  <div class="nav-tab-sep"></div>
  <button class="nav-tab" onclick="switchTab('duplicates')" id="nav-groups">📂 Duplikate <span class="nav-badge badge-zero" id="nav-badge-groups">0</span></button>
  <button class="nav-tab" onclick="switchTab('corrupt')" id="nav-corrupt">💀 Korrupte <span class="nav-badge badge-zero" id="nav-badge-corrupt">0</span></button>
  <button class="nav-tab" onclick="switchTab('addons')" id="nav-addons">🧩 Addons</button>
  <button class="nav-tab" onclick="switchTab('contained')" id="nav-contained">🏷️ Enthaltene</button>
  <button class="nav-tab" onclick="switchTab('conflicts')" id="nav-conflicts">⚔️ Konflikte</button>
  <button class="nav-tab" onclick="switchTab('skincheck')" id="nav-skincheck">🧑 Skin-Diagnose <span class="nav-badge badge-zero" id="nav-badge-skincheck">0</span></button>
  <div class="nav-tab-sep"></div>
  <button class="nav-tab" onclick="switchTab('outdated')" id="nav-outdated">⏰ Veraltet <span class="nav-badge badge-zero" id="nav-badge-analysis">0</span></button>
  <button class="nav-tab" onclick="switchTab('deps')" id="nav-deps">🔗 Abhängigkeiten</button>
  <button class="nav-tab" onclick="switchTab('errors')" id="nav-errors">📋 Fehler <span class="nav-badge badge-zero" id="nav-badge-errors">0</span></button>
  <div class="nav-tab-sep"></div>
  <button class="nav-tab" onclick="switchTab('tray')" id="nav-tray">🎭 Tray</button>
  <button class="nav-tab" onclick="switchTab('gallery')" id="nav-gallery">🖼️ CC-Galerie</button>
  <button class="nav-tab" onclick="switchTab('savegames')" id="nav-savegames">💾 Savegames</button>
  <div class="nav-tab-sep"></div>
  <button class="nav-tab" onclick="switchTab('stats')" id="nav-stats">📊 Statistik</button>
  <button class="nav-tab" onclick="switchTab('creators')" id="nav-creators">👤 Creators</button>
  <button class="nav-tab" onclick="switchTab('allmods')" id="nav-allmods">📁 Alle Mods</button>
  <div class="nav-tab-sep"></div>
  <button class="nav-tab" onclick="switchTab('import')" id="nav-import">📥 Import</button>
  <button class="nav-tab" onclick="switchTab('quarantine')" id="nav-quarantine">🗃️ Quarantäne</button>
  <button class="nav-tab" onclick="switchTab('batch')" id="nav-batch">⚡ Batch</button>
  <button class="nav-tab" onclick="switchTab('log')" id="nav-log">📜 Log</button>
  <span id="nav-group-maintenance" style="display:contents;">
  <div class="nav-tab-sep"></div>
  <button class="nav-tab" onclick="switchTab('scriptcheck')" id="nav-scriptcheck">🛡️ Script-Check</button>
  <button class="nav-tab" onclick="switchTab('cccheck')" id="nav-cccheck">🔧 CC-Check</button>
  <button class="nav-tab" onclick="switchTab('savehealth')" id="nav-savehealth">❤️ Save-Health</button>
  <div class="nav-tab-sep"></div>
  <button class="nav-tab" onclick="switchTab('cache')" id="nav-cache">🗑️ Cache</button>
  <button class="nav-tab" onclick="switchTab('trayclean')" id="nav-trayclean">🗂️ Tray-Cleaner</button>
  <button class="nav-tab" onclick="switchTab('backup')" id="nav-backup">💼 Backup</button>
  <button class="nav-tab" onclick="switchTab('diskusage')" id="nav-diskusage">📏 Speicherplatz</button>
  </span>
  <div class="nav-tab-sep"></div>
  <button class="nav-tab" onclick="switchTab('packages')" id="nav-packages">📦 Packages</button>
  <button class="nav-tab" onclick="switchTab('history')" id="nav-history">📚 Verlauf</button>
  <button class="nav-tab" onclick="switchTab('cheats')" id="nav-cheats">🎮 Cheats</button>
  <div class="nav-tab-sep"></div>
  <button class="nav-tab" onclick="startTutorial()" title="Tutorial nochmal anzeigen">❓ Tutorial</button>
  <button class="nav-tab" onclick="openBugReport()" title="Bug melden">🐛 Bug</button>
  <a class="nav-tab" href="https://buymeacoffee.com/MrBlackMautz" target="_blank" title="Unterstütze den Entwickler" style="text-decoration:none;">☕ Spenden</a>
</div>
<!-- Hidden badge elements for backwards compat -->
<span id="nav-badge-corrupt" style="display:none;">0</span>
<span id="nav-badge-addon" style="display:none;">0</span>
<span id="nav-badge-conflict" style="display:none;">0</span>
<span id="nav-badge-contained" style="display:none;">0</span>
<span id="nav-badge-outdated" style="display:none;">0</span>
<span id="nav-badge-deps" style="display:none;">0</span>
<span id="nav-badge-nonmod" style="display:none;">0</span>
<span id="nav-badge-quarantine" style="display:none;">0</span>

<div class="dash-header" id="dash-header" data-tab="dashboard">
  <h2>📋 Auf einen Blick</h2>
  <p class="muted small">Das hat der Scanner bei deinen Mods gefunden. Klicke auf eine Karte um direkt dorthin zu springen.</p>
</div>
<!-- Gesundheits-Score -->
<div id="dash-health-score" data-tab="dashboard" style="display:none; margin-bottom:16px; background:linear-gradient(135deg,#0f172a 60%,#1e1b4b); border:1px solid #334155; border-radius:12px; padding:20px 24px;">
  <div style="display:flex; align-items:center; gap:24px; flex-wrap:wrap;">
    <div style="position:relative; width:100px; height:100px; flex-shrink:0;">
      <svg viewBox="0 0 36 36" style="width:100px;height:100px;transform:rotate(-90deg);">
        <circle cx="18" cy="18" r="15.9" fill="none" stroke="#1e293b" stroke-width="3"></circle>
        <circle id="health-ring" cx="18" cy="18" r="15.9" fill="none" stroke="#22c55e" stroke-width="3" stroke-dasharray="100" stroke-dashoffset="0" stroke-linecap="round" style="transition:stroke-dashoffset 1s ease, stroke 0.5s;"></circle>
      </svg>
      <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;">
        <span id="health-score-num" style="font-size:28px;font-weight:800;color:#22c55e;">—</span>
        <span style="font-size:9px;color:#64748b;margin-top:-2px;">von 100</span>
      </div>
    </div>
    <div style="flex:1;min-width:200px;">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <span id="health-emoji" style="font-size:20px;">🩺</span>
        <span id="health-label" style="font-size:18px;font-weight:bold;color:#e2e8f0;">Mod-Gesundheit</span>
      </div>
      <div id="health-detail" class="muted" style="font-size:12px;line-height:1.6;"></div>
    </div>
    <div id="health-stats-mini" style="display:grid;grid-template-columns:1fr 1fr;gap:6px 16px;font-size:12px;"></div>
  </div>
</div>
<div id="dash-safety" data-tab="dashboard" style="background:linear-gradient(135deg,#0f172a,#1e1b4b); border:1px solid #2563eb; border-radius:12px; padding:16px 20px; margin-bottom:12px;">
  <div style="display:flex;align-items:flex-start;gap:14px;">
    <span style="font-size:28px;">🛡️</span>
    <div>
      <div style="font-size:15px;font-weight:bold;color:#93c5fd;margin-bottom:6px;">Wichtig bevor du loslegst!</div>
      <div style="font-size:13px;color:#cbd5e1;line-height:1.8;">
        <div style="margin-bottom:6px;"><span style="background:#14532d;color:#86efac;padding:2px 8px;border-radius:6px;font-weight:bold;">📦 Quarantäne = SICHER</span> Dateien werden nur <b>verschoben</b>, nicht gelöscht. Du kannst sie jederzeit im Tab <b>🗃️ Quarantäne</b> zurückholen.</div>
        <div style="margin-bottom:6px;"><span style="background:#1e3a5f;color:#93c5fd;padding:2px 8px;border-radius:6px;font-weight:bold;">🔒 Sicherheit</span> Es wird <b>niemals etwas sofort gelöscht</b> — alle Aktionen verschieben Dateien zuerst in die Quarantäne. Endgültig löschen kannst du nur im Tab <b>🗃️ Quarantäne</b>.</div>
        <div><span style="background:#1e3a5f;color:#93c5fd;padding:2px 8px;border-radius:6px;font-weight:bold;">💡 Tipp</span> Erstelle im Tab <b>💾 Backup</b> eine Sicherung deiner Mods <b>bevor</b> du aufräumst. Falls etwas schiefgeht, kannst du alles wiederherstellen.</div>
      </div>
      <button class="btn btn-ghost" style="margin-top:8px;font-size:11px;padding:4px 12px;" onclick="this.closest('#dash-safety').style.display='none';localStorage.setItem('dash_safety_hidden','1');">✓ Verstanden, nicht mehr anzeigen</button>
    </div>
  </div>
</div>
<script>if(localStorage.getItem('dash_safety_hidden')==='1') document.getElementById('dash-safety').style.display='none';</script>
<div class="dashboard" id="dashboard" data-tab="dashboard">
  <div class="dash-card dash-critical dash-hidden" id="dash-corrupt" onclick="switchTab('corrupt')">
    <div class="dash-icon">💀</div>
    <div class="dash-count" id="dash-corrupt-count">0</div>
    <div class="dash-label">Korrupte Dateien</div>
    <div class="dash-desc">Beschädigte .package-Dateien die Fehler im Spiel verursachen. <b>Sofort entfernen!</b></div>
    <span class="dash-action">Jetzt anschauen →</span>
  </div>
  <div class="dash-card dash-warn" id="dash-dupes" onclick="switchTab('duplicates')">
    <div class="dash-icon">📂</div>
    <div class="dash-count" id="dash-dupes-count">0</div>
    <div class="dash-label">Duplikate</div>
    <div class="dash-desc">Doppelte oder sehr ähnliche Mod-Dateien. Aufräumen spart Speicher &amp; verhindert Probleme.</div>
    <span class="dash-action">Aufräumen →</span>
  </div>
  <div class="dash-card dash-warn dash-hidden" id="dash-conflicts" onclick="switchTab('conflicts')">
    <div class="dash-icon">⚔️</div>
    <div class="dash-count" id="dash-conflicts-count">0</div>
    <div class="dash-label">Konflikte</div>
    <div class="dash-desc">Mods die sich gegenseitig überschreiben — nur einer kann funktionieren.</div>
    <span class="dash-action">Prüfen →</span>
  </div>
  <div class="dash-card dash-critical dash-hidden" id="dash-skincheck" onclick="switchTab('skincheck')">
    <div class="dash-icon">🧑</div>
    <div class="dash-count" id="dash-skincheck-count">0</div>
    <div class="dash-label">Skin-Probleme</div>
    <div class="dash-desc">Skin/Overlay-Konflikte die Stein-Haut und Textur-Fehler verursachen können.</div>
    <span class="dash-action">Diagnose →</span>
  </div>
  <div class="dash-card dash-info dash-hidden" id="dash-outdated" onclick="switchTab('outdated')">
    <div class="dash-icon">⏰</div>
    <div class="dash-count" id="dash-outdated-count">0</div>
    <div class="dash-label">Veraltete Mods</div>
    <div class="dash-desc">Vor dem letzten Spiel-Patch erstellt — könnten nicht mehr funktionieren.</div>
    <span class="dash-action">Prüfen →</span>
  </div>
  <div class="dash-card dash-ok dash-hidden" id="dash-addons" onclick="switchTab('addons')">
    <div class="dash-icon">🧩</div>
    <div class="dash-count" id="dash-addons-count">0</div>
    <div class="dash-label">Addons erkannt</div>
    <div class="dash-desc">Erweiterungen die zusammengehören — <b>kein Handlungsbedarf!</b></div>
    <span class="dash-action">Details →</span>
  </div>
  <div class="dash-card dash-warn dash-hidden" id="dash-contained" onclick="switchTab('contained')">
    <div class="dash-icon">📦</div>
    <div class="dash-count" id="dash-contained-count">0</div>
    <div class="dash-label">Enthaltene Mods</div>
    <div class="dash-desc">Ein Mod steckt komplett in einem Bundle — der Einzelne ist <b>redundant</b> und kann entfernt werden.</div>
    <span class="dash-action">Prüfen →</span>
  </div>
  <div class="dash-card dash-critical dash-hidden" id="dash-missingdeps" onclick="switchTab('deps')">
    <div class="dash-icon">❌</div>
    <div class="dash-count" id="dash-missingdeps-count">0</div>
    <div class="dash-label">Fehlende Abhängigkeiten</div>
    <div class="dash-desc">Mods importieren Bibliotheken die nicht installiert sind — werden nicht funktionieren!</div>
    <span class="dash-action">Prüfen →</span>
  </div>
  <div class="dash-card dash-critical dash-hidden" id="dash-errors" onclick="switchTab('errors')">
    <div class="dash-icon">📋</div>
    <div class="dash-count" id="dash-errors-count">0</div>
    <div class="dash-label">Fehler-Logs</div>
    <div class="dash-desc" id="dash-errors-desc">Tiefenanalyse deiner Fehlerlogs — erkennt beteiligte Mods, zeigt Lösungen &amp; BetterExceptions-Hinweise.</div>
    <span class="dash-action">Fehler analysieren →</span>
  </div>
  <div class="dash-card dash-info dash-hidden" id="dash-nonmod" onclick="switchTab('allmods')">
    <div class="dash-icon">📄</div>
    <div class="dash-count" id="dash-nonmod-count">0</div>
    <div class="dash-label">Sonstige Dateien</div>
    <div class="dash-desc">Nicht-Mod-Dateien (txt, png, html…) im Mods-Ordner — können aufgeräumt werden.</div>
    <span class="dash-action">Anzeigen →</span>
  </div>
  <div class="dash-card dash-ok" id="dash-total" onclick="switchTab('allmods')">
    <div class="dash-icon">📦</div>
    <div class="dash-count" id="dash-total-count">…</div>
    <div class="dash-label">Mods gescannt</div>
    <div class="dash-desc">Deine gesamte Mod-Sammlung wurde analysiert.</div>
    <span class="dash-action">Statistik →</span>
  </div>
</div>

<div class="box" id="help-section" data-tab="dashboard" style="margin-bottom:12px;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:15px;font-weight:bold;">📖 Kurzanleitung</span>
    <button class="help-toggle" id="help-toggle" onclick="document.getElementById('help-panel').classList.toggle('open'); this.textContent = document.getElementById('help-panel').classList.contains('open') ? '▲ Zuklappen' : '▼ Hilfe aufklappen';">▲ Zuklappen</button>
  </div>
  <div class="help-panel open" id="help-panel">

    <div style="margin-bottom:14px;">
      <p class="muted" style="margin:0 0 10px;"><b>So räumst du deine Mods auf — in 3 Schritten:</b></p>
      <div class="help-step">
        <span class="help-num">1</span>
        <div class="help-text">Schau dir das <b>Dashboard</b> und den <b>Gesundheits-Score</b> an — sie zeigen auf einen Blick, ob es Probleme gibt. Klicke auf eine Karte um direkt zum Problem zu springen.</div>
      </div>
      <div class="help-step">
        <span class="help-num">2</span>
        <div class="help-text">Markiere überflüssige Dateien mit einem <b>Häkchen ☑️</b> und verschiebe sie in die <b>🗃️ Quarantäne</b>. Nichts wird gelöscht — du kannst alles wiederherstellen.</div>
      </div>
      <div class="help-step">
        <span class="help-num">3</span>
        <div class="help-text">Starte dein Spiel und teste. Falls etwas fehlt → <b>🗃️ Quarantäne</b> öffnen und wiederherstellen.</div>
      </div>
    </div>

    <div class="hr"></div>
    <p style="font-weight:bold;font-size:13px;margin:12px 0 8px;color:#e2e8f0;">🧭 Alle Tabs im Überblick</p>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">
      <div style="background:rgba(30,41,59,0.7);border:1px solid #334155;border-radius:10px;padding:10px 12px;">
        <div style="font-size:12px;font-weight:bold;color:#e2e8f0;margin-bottom:6px;">📂 Probleme finden</div>
        <div style="font-size:11px;color:#94a3b8;line-height:1.6;">
          <b>📂 Duplikate</b> — doppelte Mod-Dateien<br>
          <b>💀 Korrupte</b> — kaputte .package-Dateien<br>
          <b>🧩 Addons</b> — Mods die andere Mods brauchen<br>
          <b>🏷️ Enthaltene</b> — in anderen Mods eingebaut<br>
          <b>⚔️ Konflikte</b> — Mods die sich beißen
        </div>
      </div>
      <div style="background:rgba(30,41,59,0.7);border:1px solid #334155;border-radius:10px;padding:10px 12px;">
        <div style="font-size:12px;font-weight:bold;color:#e2e8f0;margin-bottom:6px;">🔍 Analyse</div>
        <div style="font-size:11px;color:#94a3b8;line-height:1.6;">
          <b>⏰ Veraltet</b> — vor dem letzten Patch erstellt<br>
          <b>🔗 Abhängigkeiten</b> — fehlende Dateien<br>
          <b>📋 Fehler</b> — LastException-Logs<br>
          <b>🛡️ Script-Check</b> — Script-Mods prüfen<br>
          <b>🔧 CC-Check</b> — CC-Gesundheitscheck
        </div>
      </div>
      <div style="background:rgba(30,41,59,0.7);border:1px solid #334155;border-radius:10px;padding:10px 12px;">
        <div style="font-size:12px;font-weight:bold;color:#e2e8f0;margin-bottom:6px;">🎭 Übersicht & Daten</div>
        <div style="font-size:11px;color:#94a3b8;line-height:1.6;">
          <b>🎭 Tray</b> — Sims & Häuser im Tray<br>
          <b>🖼️ CC-Galerie</b> — deine CC durchstöbern<br>
          <b>💾 Savegames</b> — Spielstände verwalten<br>
          <b>📊 Statistik</b> — Mod-Statistiken<br>
          <b>👤 Creators</b> — Mods nach Ersteller<br>
          <b>📁 Alle Mods</b> — komplette Mod-Liste
        </div>
      </div>
      <div style="background:rgba(30,41,59,0.7);border:1px solid #334155;border-radius:10px;padding:10px 12px;">
        <div style="font-size:12px;font-weight:bold;color:#e2e8f0;margin-bottom:6px;">🛠 Werkzeuge</div>
        <div style="font-size:11px;color:#94a3b8;line-height:1.6;">
          <b>📥 Import</b> — Mods importieren<br>
          <b>🗃️ Quarantäne</b> — sicherer Papierkorb<br>
          <b>⚡ Batch</b> — Massenaktionen<br>
          <b>🗑️ Cache</b> / <b>🗂️ Tray-Cleaner</b> / <b>💼 Backup</b><br>
          <b>📏 Speicherplatz</b> / <b>📦 Packages</b> / <b>❤️ Save-Health</b>
        </div>
      </div>
    </div>

    <div class="hr"></div>
    <p style="font-weight:bold;font-size:13px;margin:12px 0 8px;color:#e2e8f0;">🎨 Konflikte — Farbcode</p>
    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
      <span style="background:rgba(239,68,68,0.2);border:1px solid #ef4444;color:#fca5a5;padding:4px 10px;border-radius:6px;font-size:11px;white-space:nowrap;">⚠️ <b>Kritisch</b> — Gameplay-Bruch</span>
      <span style="background:rgba(251,191,36,0.15);border:1px solid #fbbf24;color:#fde68a;padding:4px 10px;border-radius:6px;font-size:11px;white-space:nowrap;">⚡ <b>Mittel</b> — Darstellungsfehler</span>
      <span style="background:rgba(34,197,94,0.15);border:1px solid #22c55e;color:#86efac;padding:4px 10px;border-radius:6px;font-size:11px;white-space:nowrap;">✅ <b>Niedrig</b> — meist gewollt</span>
      <span style="background:rgba(148,163,184,0.15);border:1px solid #94a3b8;color:#cbd5e1;padding:4px 10px;border-radius:6px;font-size:11px;white-space:nowrap;">💤 <b>Harmlos</b> — ignorieren</span>
      <span style="background:rgba(96,165,250,0.15);border:1px solid #60a5fa;color:#93c5fd;padding:4px 10px;border-radius:6px;font-size:11px;white-space:nowrap;">✅ <b>Gewollt</b> — behalten</span>
    </div>
    <div style="font-size:11px;color:#64748b;margin-bottom:12px;">💡 Hintergrundfarben bei Einträgen = nur zur Gruppen-Unterscheidung, nicht zur Schweregrad-Anzeige.</div>

    <div class="hr"></div>
    <p style="font-weight:bold;font-size:13px;margin:12px 0 8px;color:#e2e8f0;">🛡️ Tipps</p>
    <div class="muted" style="font-size:12px;line-height:1.6;">
      ✅ Immer <b>Quarantäne</b> statt direkt löschen · ✅ Nach Aufräumen <b>Spiel testen</b><br>
      ✅ Im Zweifel <b>behalten</b> — doppelte CAS-Teile sind harmlos<br>
      ⚠️ <b>Script-Mods</b> nach Patches zuerst deaktivieren · ⚠️ <b>Kritische Konflikte</b> konsequent aufräumen
    </div>
  </div>
</div>
<div class="box" id="global-search-box" style="background:linear-gradient(135deg,#0f172a 60%,#1e1b4b);border:1px solid #4f46e5;margin-bottom:12px;">
  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
    <span style="font-size:20px;">🔍</span>
    <input class="search" id="global-search" placeholder="Globale Suche — durchsucht ALLE Mods, Duplikate, Konflikte, Notizen, Tags, CurseForge…" style="flex:1;min-width:200px;font-size:14px;padding:12px 16px;border:1px solid #4f46e5;">
    <span id="global-search-count" class="muted small"></span>
    <button class="btn btn-ghost" onclick="document.getElementById('global-search').value=''; globalSearch();" style="font-size:11px;">✖ Leeren</button>
  </div>
  <div id="global-search-results" style="display:none;margin-top:12px;max-height:70vh;overflow-y:auto;"></div>
</div>

<div id="update-banner" style="display:none;background:linear-gradient(135deg,#f59e0b,#d97706);color:#1a1a1a;padding:10px 18px;text-align:center;font-weight:700;font-size:14px;position:relative;z-index:900;border-radius:0 0 12px 12px;box-shadow:0 2px 12px rgba(245,158,11,0.3);">
  <span id="update-text"></span>
  <a id="update-link" href="#" target="_blank" style="display:inline-block;margin-left:12px;background:#451a03;color:#fff;padding:4px 14px;border-radius:8px;text-decoration:none;font-size:13px;font-weight:700;">⬇ Herunterladen</a>
  <button onclick="document.getElementById('update-banner').style.display='none'" style="position:absolute;right:12px;top:50%;transform:translateY(-50%);background:none;border:none;color:#1a1a1a;font-size:18px;cursor:pointer;font-weight:bold;">✕</button>
</div>
<a id="discord-float" href="https://discord.gg/HWWEr7pQpR" target="_blank" title="Discord Support Server">
  <span class="discord-icon">💬</span>
  <span>Discord Support</span>
</a>
<div id="bugreport-overlay">
  <div id="bugreport-card">
    <h2>🐛 Bug melden</h2>
    <div class="bug-sub">Dein Bericht wird automatisch mit System-Infos, Scan-Daten und Fehlerlogs an den Entwickler gesendet.</div>

    <div class="bug-field">
      <label>📋 Was für ein Problem hast du?</label>
      <select id="bug-category">
        <option value="">— Bitte auswählen —</option>
        <option value="crash">💥 Scanner stürzt ab / friert ein</option>
        <option value="scan">🔍 Scan funktioniert nicht richtig</option>
        <option value="display">🖥️ Anzeige-Fehler (Seite sieht kaputt aus)</option>
        <option value="action">⚡ Aktion funktioniert nicht (Quarantäne, Löschen etc.)</option>
        <option value="import">📥 Import funktioniert nicht</option>
        <option value="curseforge">🔥 CurseForge-Integration Problem</option>
        <option value="performance">🐢 Scanner ist sehr langsam</option>
        <option value="other">❓ Sonstiges</option>
      </select>
    </div>

    <div class="bug-field">
      <label>🔎 Was ist passiert? (Wähle alles aus was zutrifft)</label>
      <div class="bug-checks">
        <label><input type="checkbox" class="bug-symptom" value="Fehlermeldung angezeigt"> Fehlermeldung angezeigt</label>
        <label><input type="checkbox" class="bug-symptom" value="Seite lädt nicht"> Seite lädt nicht</label>
        <label><input type="checkbox" class="bug-symptom" value="Daten fehlen / sind falsch"> Daten fehlen / falsch</label>
        <label><input type="checkbox" class="bug-symptom" value="Button reagiert nicht"> Button reagiert nicht</label>
        <label><input type="checkbox" class="bug-symptom" value="Scanner hängt / keine Reaktion"> Scanner hängt</label>
        <label><input type="checkbox" class="bug-symptom" value="Spiel startet danach nicht"> Spiel startet danach nicht</label>
        <label><input type="checkbox" class="bug-symptom" value="Dateien verschwunden"> Dateien verschwunden</label>
        <label><input type="checkbox" class="bug-symptom" value="Sonstiges Problem"> Sonstiges</label>
      </div>
    </div>

    <div class="bug-field">
      <label>📝 Beschreibe das Problem kurz (optional aber hilfreich)</label>
      <textarea id="bug-description" placeholder="Z.B.: Ich habe auf Quarantäne geklickt aber nichts ist passiert…"></textarea>
    </div>

    <div class="bug-info">📎 <b>Folgende Infos werden automatisch mitgesendet:</b> System-Info, Scanner-Version, Spielversion, Scan-Ergebnis, Mod-Ordner, Mod-Statistik nach Typ, lastException.txt, lastUIException.txt, Scanner-Log</div>
    <div id="bug-status" class="bug-status"></div>
    <div class="bug-footer">
      <button class="tut-btn tut-btn-skip" onclick="closeBugReport()">Abbrechen</button>
      <button class="tut-btn tut-btn-primary" id="bug-send-btn" onclick="sendBugReport()" style="background:#dc2626;border-color:#dc2626;">🐛 Absenden</button>
    </div>
  </div>
</div>

<div class="box notice" data-tab="import">
  <b>🛡️ Sicherheitshinweis:</b> Alle Aktionen verschieben Dateien in die <b>📦 Quarantäne</b> — nichts wird sofort gelöscht! Du kannst alles jederzeit im Tab <b>🗃️ Quarantäne</b> zurückholen.
</div>

<div class="box" id="import-section" data-tab="import" style="border:1px solid #2563eb;background:linear-gradient(135deg,#0f172a 60%,#1e1b4b);">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📥 Mod-Import-Manager</h2>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Ziehe <b>Dateien oder ganze Ordner</b> hierher (z.B. direkt aus einer entpackten RAR/ZIP). <b>Alles</b> wird 1:1 übernommen — Ordnerstruktur, Configs, Scripts, alles! Bei <b>bereits vorhandenen Dateien</b> wirst du gefragt.</div>

  <div id="import-dropzone" style="margin:12px 0;padding:28px 20px;border:2px dashed #334155;border-radius:12px;text-align:center;cursor:pointer;transition:all 0.2s;background:#0f1422;">
    <div style="font-size:32px;margin-bottom:6px;">📂</div>
    <div style="color:#94a3b8;font-size:14px;"><b>Mod-Dateien oder Ordner hierher ziehen</b></div>
    <div class="muted small" style="margin-top:4px;">oder klicke hier um Dateien auszuwählen</div>
    <input type="file" id="import-file-input" multiple style="display:none;">
    <input type="file" id="import-folder-input" webkitdirectory style="display:none;">
    <div style="margin-top:8px;"><button class="btn btn-ghost" id="btn-import-folder-select" style="padding:4px 14px;font-size:12px;" onclick="event.stopPropagation(); document.getElementById('import-folder-input').click();">📁 Ordner auswählen</button></div>
  </div>

  <div style="margin:12px 0; display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
    <input type="text" id="import-source" placeholder="Oder: ganzen Quell-Ordner angeben (z.B. C:\\Users\\Name\\Downloads)" style="flex:1; min-width:300px; padding:8px 12px; background:#0f1115; border:1px solid #334155; border-radius:6px; color:#e7e7e7; font-size:14px;">
    <button class="btn btn-ok" id="btn-import-scan" title="Scannt den Quell-Ordner und importiert alle Dateien">🔍 Ordner scannen</button>
  </div>

  <div id="import-target-row" style="margin:8px 0 12px; display:none;">
    <label class="muted small">Ziel-Unterordner im Mods-Ordner (optional):</label>
    <input type="text" id="import-target-subfolder" placeholder="(direkt in Mods-Ordner)" style="width:300px; padding:6px 10px; background:#0f1115; border:1px solid #334155; border-radius:6px; color:#e7e7e7; font-size:13px; margin-left:8px;">
  </div>

  <div id="import-status" class="muted small" style="margin:4px 0;"></div>

  <div id="import-actions" style="display:none; margin:8px 0; gap:8px; display:none;">
    <button class="btn btn-ok" id="btn-import-all-update" title="Alle Updates übernehmen (überschreibt vorhandene)">🔄 Alle Updates übernehmen</button>
    <button class="btn btn-ghost" id="btn-import-clear">✖ Liste leeren</button>
  </div>

  <div id="import-results" style="margin-top:8px;"></div>
</div>

<div id="last" class="muted" data-tab="batch">Letzte Aktion: –</div>
<div id="watcher-banner" data-tab="dashboard" style="display:none;padding:8px 16px;margin:4px 0;border-radius:8px;background:linear-gradient(90deg,#1e3a5f,#1e293b);border:1px solid #334155;color:#94a3b8;font-size:0.95em;display:flex;align-items:center;gap:8px;" class="muted small">
  <span id="watcher-dot" style="width:8px;height:8px;border-radius:50%;background:#22c55e;display:inline-block;animation:watcherPulse 2s ease-in-out infinite;"></span>
  <span>👁️ Datei-Watcher aktiv — <span id="watcher-files">0</span> Dateien überwacht</span>
  <span id="watcher-event" style="margin-left:auto;opacity:0.7;"></span>
</div>
<style>
@keyframes watcherPulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
</style>

<div class="box" id="batchbar" data-tab="batch">
  <div class="flex" style="justify-content:space-between;">
    <div>
      <b>📋 Sammel-Aktionen</b>
      <span class="pill" id="selcount">0 ausgewählt</span><br>
      <span class="muted small">Hier kannst du alle Dateien, bei denen du ein <b>Häkchen ☑️</b> gesetzt hast, auf einmal verarbeiten.</span><br>
      <span class="muted small" style="color:#86efac;">🛡️ <b>Sicher:</b> Alle Dateien werden in die <b>📦 Quarantäne</b> verschoben — nichts wird sofort gelöscht. Du kannst alles jederzeit zurückholen.</span><br>
      <span class="muted small" style="opacity:0.6;">Log-Datei: <code id="logfile"></code></span>
    </div>
    <div class="flex">
      <button class="btn btn-ok" id="btn_q_sel" title="SICHER: Verschiebt alle markierten Dateien in einen Quarantäne-Ordner. Du kannst sie jederzeit wiederherstellen!">📦 In Quarantäne verschieben</button>
      <button class="btn btn-ghost" id="btn_clear_sel" title="Entfernt alle Häkchen — keine Dateien werden verändert">✖ Auswahl leeren</button>
      <button class="btn btn-ghost" id="reload" title="Scannt alle Mod-Ordner komplett neu — kann bei vielen Mods ein paar Minuten dauern">↻ Neu scannen</button>
      <button class="btn btn-ghost" id="btn_save_html" title="Speichert eine Kopie dieser Seite als HTML-Datei auf dem Desktop — praktisch zum Teilen oder Archivieren">📄 Bericht speichern</button>
    </div>
  </div>
  <div class="hr"></div>
  <div id="batchstatus" class="muted small">Bereit.</div>
</div>

<div class="box" id="log-section" data-tab="log">
  <div class="flex" style="justify-content:space-between;">
    <div>
      <b>Aktionen-Log</b> <span class="pill">wird im Browser gespeichert</span>
      <span class="muted small" style="margin-left:4px;">Alle Quarantäne/Lösch-Aktionen werden hier protokolliert</span>
    </div>
    <div class="flex">
      <button class="btn btn-ghost" id="log_copy">📋 Log kopieren</button>
      <button class="btn btn-ghost" id="log_csv">💾 CSV exportieren</button>
      <button class="btn btn-danger" id="log_clear">🧹 Log leeren</button>
    </div>
  </div>
  <div style="margin-top:10px;" id="log"></div>
</div>

<div class="topgrid" data-tab="duplicates">
  <div class="box">
    <h3>🔍 Suche & Filter</h3>
    <p class="muted small" style="margin:0 0 8px;">Filtere die Ergebnisse oder suche nach bestimmten Mod-Namen.</p>
    <input class="search" id="q" placeholder="Mod-Name eingeben… z.B. wicked, mccc, littlemssam">
    <div class="flex" style="margin-top:10px;">
      <label title="Dateien mit exakt gleichem Namen in verschiedenen Ordnern"><input type="checkbox" id="f_name" checked> 📛 Name-Duplikate</label>
      <label title="Dateien die Byte-für-Byte identisch sind (egal wie sie heißen)"><input type="checkbox" id="f_content" checked> 📦 Inhalt-Duplikate</label>
      <label title="Dateien mit sehr ähnlichem Namen (z.B. verschiedene Versionen)"><input type="checkbox" id="f_similar" checked> 🔤 Ähnliche Namen</label>
      <label title="Gruppiert Dateien nach ihrem Unterordner"><input type="checkbox" id="g_mod" checked> 📁 nach Unterordner gruppieren</label>
      <label title="Zeigt den kompletten Dateipfad statt nur den Dateinamen"><input type="checkbox" id="show_full" checked> 📂 voller Pfad</label>
      <label title="Bei Sammel-Aktionen (Rest in Quarantäne etc.) wird bevorzugt eine Datei aus dem Haupt-Mod-Ordner behalten">
        <input type="checkbox" id="keep_ord1" checked> ⭐ Haupt-Ordner bevorzugen
      </label>
      <label title="Zeigt auch Gruppen an, die du als 'Ist korrekt' markiert hast"><input type="checkbox" id="f_show_ignored"> 👁 Ignorierte anzeigen</label>
    </div>
    <div class="hr"></div>
    <div id="summary" class="muted">Lade…</div>
  </div>

  <div class="box">
    <h3>📁 Gescannte Ordner</h3>
    <ul id="roots" class="muted" style="margin:0; padding-left:18px;"></ul>
    <div class="hr"></div>
    <div class="muted small">ℹ️ <b>Inhalt-Duplikat</b> = Dateien sind zu 100% identisch (sicher löschbar).<br><b>Name-Duplikat</b> = Gleicher Name, aber Inhalt könnte unterschiedlich sein (erst prüfen!).</div>
  </div>
</div>

<div class="box" id="view-header" data-tab="duplicates">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2 id="view-title">📂 Duplikat-Gruppen</h2>
    <div class="view-toggle" id="view-toggle">
      <button class="active" data-view="groups" title="Zeigt zusammengehörige Dateien als Gruppen">📂 Gruppen-Ansicht</button>
      <button data-view="perfile" title="Zeigt alle Infos pro einzelner Datei auf einer Karte">📋 Pro Datei</button>
    </div>
  </div>
  <div class="info-hint" style="margin-top:8px;">💡 <b>So funktioniert es:</b> Jede Gruppe zeigt Dateien die zusammengehören (z.B. Duplikate). Setze ein <b>Häkchen ☑️</b> bei der Datei, die du <b>nicht brauchst</b>, und nutze dann oben <b>📦 Quarantäne</b>. Der Button <b>"📦 Rest in Quarantäne"</b> hilft dir: er verschiebt automatisch alle außer der besten Datei.</div>
</div>

<div id="groups-view" data-tab="duplicates">
<div class="box">
  <div id="groups">Lade…</div>
</div>
</div>

<div id="perfile-view" data-tab="duplicates">
<div class="box">
  <div style="background:#1a2238; border:1px solid #2b3553; border-radius:12px; padding:14px; margin-bottom:14px;">
    <p style="margin:0 0 8px; font-size:14px; font-weight:bold; color:#e2e8f0;">📋 Pro-Datei-Ansicht — Was ist das?</p>
    <p class="muted" style="margin:0 0 8px;">Hier siehst du <b>jede Datei einzeln</b> mit allen Infos auf einen Blick. Kein Hin- und Herscrollen zwischen verschiedenen Sektionen mehr!</p>
    <div style="display:grid; grid-template-columns:auto 1fr; gap:6px 12px; font-size:12px; margin-top:8px;">
      <span class="corrupt-status no_dbpf" style="text-align:center;">⚠️ Korrupt</span>
      <span class="muted">Datei ist beschädigt oder hat falsches Format — kann Fehler im Spiel verursachen</span>
      <span class="conflict-badge" style="text-align:center;">🔀 Konflikt</span>
      <span class="muted">Teilt sich IDs mit anderen Mods — eins überschreibt das andere, nur eins funktioniert</span>
      <span class="addon-badge" style="text-align:center;">🧩 Addon</span>
      <span class="muted">Ergänzt einen anderen Mod — <b>OK, beide behalten!</b></span>
      <span class="pill" style="background:#4c1d95;color:#c4b5fd; text-align:center;">Inhalt-Duplikat</span>
      <span class="muted">Exakt gleicher Inhalt wie eine andere Datei — eine davon ist überflüssig</span>
      <span class="pill" style="background:#1e3a5f;color:#60a5fa; text-align:center;">Name-Duplikat</span>
      <span class="muted">Gleicher Dateiname in verschiedenen Ordnern</span>
      <span class="pill" style="background:#134e4a;color:#5eead4; text-align:center;">Ähnlich</span>
      <span class="muted">Sehr ähnlicher Name — könnte eine alte/neue Version sein</span>
    </div>
    <p class="muted small" style="margin:10px 0 0;">💡 Tipp: Dateien mit den meisten Auffälligkeiten stehen ganz oben. Nutze die Suche um eine bestimmte Datei zu finden.</p>
  </div>
  <input class="search" id="pf-search" placeholder="Datei suchen… z.B. wicked, littlemssam, asketo">
  <div id="perfile-summary" class="muted" style="margin-top:8px;"></div>
  <div id="perfile-list" style="margin-top:12px;"></div>
</div>
</div>

<div class="box" id="corrupt-section" data-tab="corrupt">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>⚠️ Korrupte / Verdächtige .package-Dateien</h2>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Diese .package-Dateien sind beschädigt oder haben ein ungültiges Format. Sie verursachen möglicherweise Fehler im Spiel. <b>Empfehlung:</b> Lösche sie oder lade sie neu vom Ersteller herunter.</div>
  <div id="corrupt-summary" class="muted"></div>
  <div id="corrupt-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="addon-section" data-tab="addons">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🧩 Addon-Beziehungen (erwartet)</h2>
  </div>
  <div style="background:#0f2922; border:1px solid #065f46; border-radius:10px; padding:14px; margin-bottom:14px;">
    <p style="margin:0 0 8px; font-size:14px; font-weight:bold; color:#6ee7b7;">✅ Alles OK — das hier sind keine Probleme!</p>
    <p class="muted" style="margin:0 0 6px;">Diese Packages teilen sich <b>absichtlich</b> Ressource-IDs. Das passiert, wenn ein <b>Addon/Erweiterung</b> einen bestehenden Mod ergänzt oder anpasst.</p>
    <p class="muted" style="margin:0 0 6px;">Beispiel: <i>LittleMsSam_DressCodeLotTrait<b>!_Addon_LotChallenge</b>.package</i> erweitert den Basis-Mod <i>LittleMsSam_DressCodeLotTrait.package</i>.</p>
    <p class="muted" style="margin:0 0 6px;">👉 <b>Beide behalten!</b> Addon + Basis-Mod gehören zusammen. Wenn du eins löschst, funktioniert das andere nicht mehr richtig.</p>
    <p class="muted small" style="margin:0;">Tipp: Falls ein Addon nach einem Update Probleme macht, prüfe ob <b>beide</b> (Addon + Basis) auf dem gleichen Stand sind.</p>
  </div>
  <div id="addon-summary" class="muted"></div>
  <div id="addon-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="contained-section" data-tab="contained">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📦 Enthaltene Mods (Redundant)</h2>
  </div>
  <div style="background:#1e1b00; border:1px solid #78350f; border-radius:10px; padding:14px; margin-bottom:14px;">
    <p style="margin:0 0 8px; font-size:14px; font-weight:bold; color:#fbbf24;">⚠️ Diese Mods sind doppelt vorhanden!</p>
    <p class="muted" style="margin:0 0 6px;">Hier wurde erkannt, dass <b>alle Ressourcen</b> eines Standalone-Mods bereits in einem größeren <b>Bundle/Paket</b> enthalten sind.</p>
    <p class="muted" style="margin:0 0 6px;">Beispiel: <i>BosseladyTV_Better_Fast_Internet</i> steckt komplett in <i>BosseladyTV_Better_Lot_Traits_<b>BG_Bundle</b></i>. Der Einzelne ist überflüssig.</p>
    <p class="muted" style="margin:0 0 6px;">👉 <b>Den kleineren Einzelmod entfernen!</b> Das Bundle enthält ihn bereits. Beide gleichzeitig verursachen unnötige Konflikte.</p>
    <p class="muted small" style="margin:0;">Tipp: Prüfe ob es sich wirklich um ein Bundle handelt (oft erkennbar an <b>Bundle</b>, <b>Pack</b> oder <b>Collection</b> im Namen).</p>
  </div>
  <div id="contained-summary" class="muted"></div>
  <div id="contained-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="conflict-section" data-tab="conflicts">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🔀 Ressource-Konflikte (Doppelte Mod-IDs)</h2>
  </div>
  <div style="background:#1e1b2e; border:1px solid #3a3a5e; border-radius:10px; padding:14px; margin-bottom:14px;">
    <p style="margin:0 0 8px; font-size:14px; font-weight:bold; color:#c4b5fd;">💡 Was bedeutet das?</p>
    <p class="muted" style="margin:0 0 6px;">Jede Mod-Datei (.package) enthält <b>Ressourcen</b> mit eindeutigen IDs — z.B. Haare, Kleidung, Objekte oder Gameplay-Änderungen.</p>
    <p class="muted" style="margin:0 0 6px;">Wenn <b>zwei Packages die gleichen IDs</b> haben, überschreibt eins das andere. Das heißt: <b>nur eins funktioniert</b>, das andere wird vom Spiel ignoriert!</p>
    <p class="muted" style="margin:0 0 6px;">👉 <b>Was tun?</b> Meistens sind es alte/neue Versionen desselben Mods. Behalte die <b>neuere</b> (schau aufs Datum) und verschiebe die andere in Quarantäne.</p>
    <p class="muted small" style="margin:0;">Tipp: Bei <b>CAS Part</b>-Konflikten (Haare, Kleidung, Make-up) sieht man nur eine Variante im Spiel. Bei <b>Tuning</b>-Konflikten (Gameplay) kann es zu Fehlern oder Abstürzen kommen.</p>
  </div>
  <div id="conflict-summary" class="muted"></div>
  <div id="conflict-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="skincheck-section" data-tab="skincheck">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🧑 Skin-Diagnose</h2>
  </div>
  <div style="background:#2d1b1b; border:1px solid #7f1d1d; border-radius:10px; padding:14px; margin-bottom:14px;">
    <p style="margin:0 0 8px; font-size:14px; font-weight:bold; color:#fca5a5;">🪨 Was ist die "Stein-Haut"?</p>
    <p class="muted" style="margin:0 0 6px;">Wenn ein Sim im Spiel plötzlich eine <b>graue/steinige Textur</b> hat, aber in "Sim erstellen" (CAS) normal aussieht, liegt es fast immer an einem <b>Skin/Overlay-Mod-Konflikt</b>.</p>
    <p class="muted" style="margin:0 0 6px;">Das passiert wenn <b>zwei Skin-Mods die gleichen CAS-Part-IDs</b> verwenden — der eine überschreibt den anderen, und die alte Textur wird als Stein-Fläche angezeigt.</p>
    <p class="muted" style="margin:0 0 8px;">Auch <b>korrupte Skin-Mods</b> oder <b>Skin-Recolors ohne Basis-Mod</b> können diesen Effekt verursachen.</p>
    <p style="margin:0; font-size:13px; font-weight:bold; color:#fbbf24;">💡 Lösung: Die hier markierten Mods prüfen und nur EINEN Skin-/Overlay-Mod pro Typ behalten.</p>
  </div>
  <div id="skincheck-summary" class="muted"></div>
  <div id="skincheck-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="outdated-section" data-tab="outdated">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>⏰ Veraltete Mods</h2>
    <span class="muted small" id="outdated-game-ver"></span>
  </div>
  <div style="padding:10px 14px;background:#1e293b;border-radius:8px;margin-bottom:10px;">
    <p class="muted" style="margin:0 0 6px;">Diese Mods wurden <b>vor dem letzten Spiel-Patch</b> zuletzt geändert. Sie könnten nach dem Update nicht mehr funktionieren.</p>
    <p class="muted" style="margin:0 0 6px;">⚠️ <b>Hohes Risiko:</b> Script-Mods (.ts4script) — brechen fast immer nach Patches.</p>
    <p class="muted" style="margin:0 0 6px;">⚡ <b>Mittleres Risiko:</b> Tuning/Gameplay-Mods — können nach Patches Fehler verursachen.</p>
    <p class="muted small" style="margin:0;">✅ <b>Niedriges Risiko:</b> CAS/CC und Objekte — brechen selten, meistens nur bei großen Updates.</p>
  </div>
  <div style="margin-bottom:8px;">
    <label class="muted small"><input type="checkbox" id="outdated-filter-high" checked> ⚠️ Hohes Risiko</label>
    <label class="muted small" style="margin-left:12px;"><input type="checkbox" id="outdated-filter-mid" checked> ⚡ Mittleres Risiko</label>
    <label class="muted small" style="margin-left:12px;"><input type="checkbox" id="outdated-filter-low"> ✅ Niedriges Risiko</label>
  </div>
  <div id="outdated-summary" class="muted"></div>
  <div id="outdated-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="deps-section" data-tab="deps">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🔗 Mod-Abhängigkeiten</h2>
    <span class="muted small" id="deps-summary"></span>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier siehst du, welche Mods <b>zusammengehören</b>. Script+Package-Paare sollten immer gemeinsam behalten oder entfernt werden. Mod-Familien (viele Dateien mit gleichem Prefix) gehören vermutlich zum selben Mod.</div>
  <div style="margin-bottom:8px;">
    <label class="muted small"><input type="checkbox" id="deps-filter-missing" checked> ❌ Fehlende Abhängigkeiten</label>
    <label class="muted small" style="margin-left:12px;"><input type="checkbox" id="deps-filter-imports" checked> 📦 Import-Abhängigkeiten</label>
    <label class="muted small" style="margin-left:12px;"><input type="checkbox" id="deps-filter-pairs" checked> 🔗 Script-Paare</label>
    <label class="muted small" style="margin-left:12px;"><input type="checkbox" id="deps-filter-namedeps" checked> 📎 Namens-Abhängigkeiten</label>
    <label class="muted small" style="margin-left:12px;"><input type="checkbox" id="deps-filter-families" checked> 👨‍👩‍👧‍👦 Mod-Familien</label>
  </div>
  <div id="deps-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="error-section" data-tab="errors">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🔍 Fehler-Analyse</h2>
    <button class="btn btn-ghost" id="btn_reload_errors">↻ Fehler neu laden</button>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier werden die Fehlerlogs deines Spiels (lastException.txt, lastUIException.txt) automatisch ausgelesen und verständlich erklärt. So findest du heraus, welcher Mod ein Problem verursacht hat.</div>
  <div id="error-summary" class="muted">Lade Fehler…</div>
  <div id="exc-file-list" style="margin-top:10px;"></div>
  <div id="error-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="history-section" data-tab="history">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📊 Verlauf &amp; Mod-Inventar</h2>
    <button class="btn btn-ghost" id="btn_reload_history">↻ Aktualisieren</button>
  </div>

  <div class="info-hint">💡 <b>Was ist das?</b> Der Verlauf zeigt dir wieviele Mods du installiert hast und was sich seit dem letzten Scan geändert hat (neue Mods, gelöschte Mods, Updates). So behältst du den Überblick.</div>
  <div id="mod-snapshot" style="margin-bottom:16px;">
    <h3 style="margin:12px 0 8px;">📦 Mod-Inventar</h3>
    <div id="mod-snapshot-content" class="muted">Lade…</div>
  </div>

  <div id="mod-changes" style="margin-bottom:16px; display:none;">
    <h3 style="margin:12px 0 8px;">🔄 Änderungen seit letztem Scan</h3>
    <div id="mod-changes-content"></div>
  </div>

  <div id="scan-history">
    <h3 style="margin:12px 0 8px;">📈 Scan-Verlauf</h3>
    <div id="scan-history-content" class="muted">Lade…</div>
  </div>

  <div id="history-chart-area" style="display:none; margin-top:16px;">
    <h3 style="margin:0 0 8px; font-size:14px;">📊 Verlaufs-Diagramm</h3>
    <div class="chart-container">
      <canvas id="history-chart"></canvas>
    </div>
  </div>
</div>
<div class="box" id="progress-section" data-tab="dashboard" style="display:none;">
  <h2>🔄 Scan läuft…</h2>
  <div id="progress-phase" class="muted" style="margin-bottom:8px;">Starte…</div>
  <div style="background:#23293a; border-radius:8px; height:28px; overflow:hidden; position:relative; margin-bottom:8px;">
    <div id="progress-bar" style="height:100%; background:linear-gradient(90deg,#6366f1,#a78bfa); width:0%; transition:width 0.3s ease; border-radius:8px; display:flex; align-items:center; justify-content:center;">
      <span id="progress-pct" style="color:#fff; font-size:12px; font-weight:600; text-shadow:0 1px 2px rgba(0,0,0,0.5);"></span>
    </div>
  </div>
  <div id="progress-detail" class="muted" style="font-size:12px;"></div>
</div>

<div class="box" id="all-ok-banner" data-tab="dashboard" style="display:none; text-align:center; padding:30px;">
  <div style="font-size:48px; margin-bottom:12px;">✅</div>
  <h2 style="color:#4ade80; margin:0 0 8px;">Alles sieht gut aus!</h2>
  <p class="muted" style="max-width:500px;margin:0 auto;">Keine Duplikate, keine korrupten Dateien, keine Konflikte gefunden. Deine Mod-Sammlung ist aufgeräumt!</p>
</div>

<div class="box" id="stats-section" data-tab="stats">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📊 Mod-Statistiken</h2>
    <button class="btn btn-ghost" id="btn_export_modlist" title="Exportiere komplette Mod-Liste als CSV-Datei">📥 Mod-Liste exportieren</button>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Eine Übersicht über deine gesamte Mod-Sammlung: Wie viele Mods du hast, welche Kategorien, welche Ordner am größten sind und welche Dateien am meisten Platz brauchen.</div>
  <div id="stats-overview" class="muted">Lade…</div>
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:12px;">
    <div>
      <h3 style="margin:0 0 8px; font-size:14px;">🎨 Mod-Kategorien</h3>
      <div id="stats-categories"></div>
    </div>
    <div>
      <h3 style="margin:0 0 8px; font-size:14px;">📁 Größte Ordner</h3>
      <div id="stats-folders"></div>
    </div>
  </div>
  <div style="margin-top:16px;">
    <h3 style="margin:0 0 8px; font-size:14px;">📀 Top 10 größte Mods</h3>
    <div id="stats-biggest"></div>
  </div>
  <div style="margin-top:20px;">
    <h3 style="margin:0 0 8px; font-size:14px;">📅 Mod-Aktivität (Installations-Heatmap)</h3>
    <div class="info-hint">💡 Zeigt wann du Mods installiert/geändert hast — wie auf GitHub! Dunklere Kästchen = mehr Mod-Aktivität an dem Tag.</div>
    <div id="stats-heatmap" style="overflow-x:auto; padding:8px 0;"></div>
  </div>
</div>

<!-- CC-Galerie -->
<div class="box" id="gallery-section" data-tab="gallery">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🖼️ CC-Galerie</h2>
    <span class="muted small" id="gallery-summary"></span>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier siehst du alle CC-Mods mit Vorschaubild als <b>Bild-Grid</b>. Filtere nach Kategorie, Alter, Geschlecht oder suche nach Namen. Klicke auf ein Bild für die Großansicht.</div>
  <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center;">
    <input id="gallery-search" type="text" placeholder="🔍 Suche in CC-Galerie…" style="padding:6px 12px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:12px;width:200px;">
    <select id="gallery-cat-filter" style="padding:6px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:12px;">
      <option value="">Alle Kategorien</option>
    </select>
    <select id="gallery-age-filter" style="padding:6px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:12px;">
      <option value="">Alle Altersgruppen</option>
      <option value="Kleinkind">Kleinkind</option>
      <option value="Kind">Kind</option>
      <option value="Teen">Teen</option>
      <option value="Erwachsene">Erwachsene</option>
      <option value="Ältere">Ältere</option>
    </select>
    <select id="gallery-gender-filter" style="padding:6px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:12px;">
      <option value="">Alle Geschlechter</option>
      <option value="Weiblich">Weiblich</option>
      <option value="Männlich">Männlich</option>
    </select>
    <label class="muted small"><input type="checkbox" id="gallery-recolor-only"> 🎨 Nur Recolors</label>
  </div>
  <div id="gallery-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;"></div>
  <div id="gallery-loadmore" style="text-align:center;margin-top:12px;display:none;">
    <button class="btn" onclick="galleryLoadMore()">🖼️ Mehr laden…</button>
  </div>
</div>

<!-- ═══ SAVEGAME-ANALYSE SECTION ═══ -->
<div class="box" id="savegame-section" data-tab="savegames">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>💾 Savegame-Analyse — Sims in deinem Spielstand</h2>
    <div style="display:flex;gap:6px;align-items:center;">
      <select id="savegame-select" class="filter-input" onchange="switchSavegame()" style="display:none;max-width:280px;font-size:12px;">
      </select>
      <button class="btn btn-ok" id="btn-savegame-analyze" onclick="startSavegameAnalysis()">🔍 Analysieren</button>
    </div>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Diese Analyse liest deinen <b>aktuellsten Spielstand</b> und zeigt dir alle <b>Sims</b> die darin vorhanden sind. So vermeidest du es, Sims <b>versehentlich doppelt</b> in deiner Welt zu platzieren! Du kannst oben auch einen anderen Spielstand auswählen.</div>
  <div id="savegame-status" class="muted" style="margin:12px 0;">⏳ Spielstand wird automatisch analysiert…</div>
  <div id="savegame-summary" style="display:none;"></div>
  <div id="savegame-filters" style="display:none; margin:12px 0; gap:8px; flex-wrap:wrap; align-items:center;">
    <input type="text" id="savegame-search" placeholder="🔍 Sim-Name suchen…" class="filter-input" style="width:220px;" oninput="filterSavegameSims()">
    <select id="savegame-sort" class="filter-input" onchange="filterSavegameSims()">
      <option value="name">Name A–Z</option>
      <option value="name-desc">Name Z–A</option>
      <option value="household">Nach Haushalt</option>
      <option value="age">Nach Alter</option>
      <option value="skills">Meiste Skills</option>
      <option value="mood">Beste Stimmung</option>
      <option value="sim-age">Älteste (Spieltage)</option>
      <option value="simoleons">💰 Reichste</option>
      <option value="career">💼 Karriere</option>
      <option value="world">Nach Welt</option>
    </select>
    <select id="savegame-age-filter" class="filter-input" onchange="filterSavegameSims()">
      <option value="all">Alle Alter</option>
      <option value="Baby">👶 Baby</option>
      <option value="Kleinkind">🧒 Kleinkind</option>
      <option value="Kind">🧒 Kind</option>
      <option value="Teen">🧑 Teen</option>
      <option value="Junger Erwachsener">🧑 Junger Erwachsener</option>
      <option value="Erwachsener">🧑 Erwachsener</option>
      <option value="Älterer">👴 Älterer</option>
    </select>
    <select id="savegame-gender-filter" class="filter-input" onchange="filterSavegameSims()">
      <option value="all">Alle</option>
      <option value="Männlich">♂️ Männlich</option>
      <option value="Weiblich">♀️ Weiblich</option>
    </select>
    <select id="savegame-world-filter" class="filter-input" onchange="filterSavegameSims()">
      <option value="all">🏘️ Alle Welten</option>
    </select>
    <select id="savegame-species-filter" class="filter-input" onchange="filterSavegameSims()">
      <option value="all">🧬 Alle Spezies</option>
      <option value="human">🧑 Nur Menschen</option>
      <option value="Haustier">🐾 Haustiere</option>
      <option value="Pferd">🐴 Pferde</option>
      <option value="Werwolf">🐺 Werwölfe</option>
      <option value="Zauberer">🧙 Zauberer</option>
      <option value="Fee">🧚 Feen</option>
      <option value="Vampir">🧛 Vampire</option>
      <option value="Meerjungfrau">🧜 Meerjungfrauen</option>
      <option value="Alien">👽 Aliens</option>
    </select>
    <label class="muted small" style="cursor:pointer;"><input type="checkbox" id="savegame-group-hh" onchange="filterSavegameSims()" checked> 👨‍👩‍👧 Nach Haushalt gruppieren</label>
    <label class="muted small" style="cursor:pointer;font-weight:600;color:#a78bfa;"><input type="checkbox" id="savegame-played-filter" onchange="filterSavegameSims()"> 🎮 Meine Sims</label>
    <label class="muted small" style="cursor:pointer;"><input type="checkbox" id="savegame-portrait-filter" onchange="filterSavegameSims()"> 📸 Nur mit Foto</label>
    <label class="muted small" style="cursor:pointer;"><input type="checkbox" id="savegame-basegame-filter" onchange="filterSavegameSims()"> 🏠 Nur Basegame</label>
    <label class="muted small" style="cursor:pointer;"><input type="checkbox" id="savegame-townie-filter" onchange="filterSavegameSims()"> 🤖 Nur Townies</label>
    <label class="muted small" style="cursor:pointer;"><input type="checkbox" id="savegame-dupe-filter" onchange="filterSavegameSims()"> ⚠️ Nur Duplikate</label>
    <label class="muted small" style="cursor:pointer;"><input type="checkbox" id="savegame-cc-filter" onchange="filterSavegameSims()"> 🧩 Nur mit CC</label>
    <label class="muted small" style="cursor:pointer;"><input type="checkbox" id="savegame-library-filter" onchange="filterSavegameSims()"> 📚 In Bibliothek</label>
  </div>
  <div id="savegame-list" style="display:none;"></div>
</div>

<!-- ═══ BIBLIOTHEK SECTION ═══ -->
<div class="box" id="library-section" data-tab="savegames">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📚 Bibliothek — Gespeicherte Haushalte im Tray</h2>
    <div style="display:flex;gap:6px;align-items:center;">
      <button class="btn btn-ok" id="btn-library-analyze" onclick="startLibraryAnalysis()">🔍 Laden</button>
      <button class="btn btn-ghost" id="btn-library-refresh" onclick="startLibraryAnalysis(true)" style="display:none;">🔄 Neu</button>
    </div>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier siehst du <b>alle Haushalte</b> in deiner Tray-Bibliothek mit Portraits. Sims die auch im aktiven Spielstand vorkommen werden mit <span style="color:#86efac;">✅ Im Spiel</span> markiert, reine Bibliotheks-Sims mit <span style="color:#c4b5fd;">📚 Nur Bibliothek</span>. Haushalte mit Custom Content zeigen ein <span style="color:#fbbf24;">🧩 CC</span> Badge — klick darauf für Details.</div>
  <div id="library-status" class="muted" style="margin:12px 0;">⏳ Bibliothek wird automatisch geladen…</div>
  <div id="library-summary" style="display:none;"></div>
  <div id="library-filters" style="display:none; margin:12px 0; gap:8px; flex-wrap:wrap; align-items:center;">
    <input type="text" id="library-search" placeholder="🔍 Name/Haushalt suchen…" class="filter-input" style="width:220px;" oninput="filterLibrary()">
    <select id="library-sort" class="filter-input" onchange="filterLibrary()">
      <option value="name">Name A–Z</option>
      <option value="name-desc">Name Z–A</option>
      <option value="size-desc">Meiste Sims zuerst</option>
      <option value="size-asc">Wenigste Sims zuerst</option>
      <option value="cc-desc">Meiste CC zuerst</option>
    </select>
    <select id="library-status-filter" class="filter-input" onchange="filterLibrary()">
      <option value="all">Alle Haushalte</option>
      <option value="active">✅ Mit aktiven Sims</option>
      <option value="libonly">📚 Nur Bibliothek-Sims</option>
      <option value="mixed">🔀 Gemischt (aktiv + Bibliothek)</option>
    </select>
    <select id="library-cc-filter" class="filter-input" onchange="filterLibrary()">
      <option value="all">CC: Alle</option>
      <option value="with-cc">🧩 Mit CC</option>
      <option value="no-cc">✅ Ohne CC</option>
    </select>
    <label class="muted small" style="cursor:pointer;"><input type="checkbox" id="library-creator-filter" onchange="filterLibrary()"> 🎨 Mit Creator</label>
    <label class="muted small" style="cursor:pointer;"><input type="checkbox" id="library-dupe-filter" onchange="filterLibrary()"> ⚠️ Duplikate</label>
    <label class="muted small" style="cursor:pointer;"><input type="checkbox" id="library-safe-filter" onchange="filterLibrary()"> 🗑️ Löschbar</label>
    <label class="muted small" style="cursor:pointer;"><input type="checkbox" id="library-group-hh" onchange="filterLibrary()" checked> 👨‍👩‍👧 Nach Haushalt</label>
  </div>
  <div id="library-list" style="display:none;"></div>
</div>

<!-- ═══ TRAY-ANALYSE SECTION (Backup — Details zu CC in Grundstücken & Räumen) ═══ -->
<div class="box" id="tray-section" data-tab="tray">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🎭 Tray-Analyse — CC in Grundstücken & Räumen</h2>
    <div>
      <button class="btn btn-ok" id="btn-tray-analyze" onclick="startTrayAnalysis()">🔍 Analysieren</button>
      <button class="btn btn-ghost" id="btn-tray-refresh" onclick="startTrayAnalysis(true)" style="display:none;">🔄 Neu laden</button>
    </div>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Detailansicht aller <b>Tray-Einträge</b> (Grundstücke, Räume, Haushalte) mit CC-Referenzen. CC pro Sim siehst du oben auf den Sim-Karten — hier findest du die <b>vollständige Liste</b> inkl. Grundstücke &amp; Räume.</div>
  <div id="tray-status" class="muted" style="margin:12px 0;">⏳ Tray-Analyse wird automatisch gestartet…</div>
  <div id="tray-summary" style="display:none;"></div>
  <div id="tray-filters" style="display:none; margin:12px 0; gap:8px; flex-wrap:wrap; align-items:center;">
    <input type="text" id="tray-search" placeholder="🔍 Sim/Haus suchen…" class="filter-input" style="width:220px;" oninput="filterTrayItems()">
    <select id="tray-type-filter" class="filter-input" onchange="filterTrayItems()">
      <option value="all">Alle Typen</option>
      <option value="1">🧑 Haushalte</option>
      <option value="2">🏠 Grundstücke</option>
      <option value="3">🛋️ Räume</option>
    </select>
    <select id="tray-cc-filter" class="filter-input" onchange="filterTrayItems()">
      <option value="all">Alle</option>
      <option value="cc">Nur mit CC</option>
      <option value="nocc">Ohne CC</option>
    </select>
    <select id="tray-sort" class="filter-input" onchange="filterTrayItems()">
      <option value="name">Name A–Z</option>
      <option value="cc-desc">Meiste CC zuerst</option>
      <option value="cc-asc">Wenigste CC zuerst</option>
      <option value="type">Nach Typ</option>
    </select>
  </div>
  <div id="tray-items" style="display:none;"></div>
  <div id="tray-most-used" style="display:none; margin-top:20px;"></div>
</div>

<div class="box" id="creators-section" data-tab="creators">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🔗 Mod-Creator & Download-Links</h2>
    <button class="btn btn-ghost" id="btn_toggle_creator_form" title="Neuen Creator/Download-Link hinzufügen">➕ Creator hinzufügen</button>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier kannst du eigene Creator-Links hinterlegen. Wenn ein Dateiname ein bestimmtes Muster enthält (z.B. <code>wickedwhims</code>), wird automatisch ein klickbarer Badge angezeigt. So findest du schnell die Download-Seite für Updates!</div>

  <div id="creator-form-box" style="display:none; margin:12px 0; padding:14px; background:#1a1d2e; border:1px solid #334155; border-radius:10px;">
    <h3 style="margin:0 0 10px; font-size:14px;" id="creator-form-title">➕ Neuen Creator hinzufügen</h3>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
      <div>
        <label style="font-size:12px; color:#9ca3af;">Dateiname-Muster <span style="color:#f87171;">*</span></label>
        <input type="text" id="cr_key" placeholder="z.B. wickedwhims, mccc, littlemssam" style="width:100%;padding:8px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:13px;box-sizing:border-box;">
        <div style="font-size:11px;color:#6b7280;margin-top:2px;">Wird im Dateinamen gesucht (Kleinbuchstaben)</div>
      </div>
      <div>
        <label style="font-size:12px; color:#9ca3af;">Creator-Name <span style="color:#f87171;">*</span></label>
        <input type="text" id="cr_name" placeholder="z.B. TURBODRIVER" style="width:100%;padding:8px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:13px;box-sizing:border-box;">
      </div>
      <div>
        <label style="font-size:12px; color:#9ca3af;">Download/Website-URL</label>
        <input type="text" id="cr_url" placeholder="https://example.com" style="width:100%;padding:8px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:13px;box-sizing:border-box;">
      </div>
      <div>
        <label style="font-size:12px; color:#9ca3af;">Icon/Emoji</label>
        <input type="text" id="cr_icon" placeholder="🔗" maxlength="4" style="width:100%;padding:8px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:13px;box-sizing:border-box;">
      </div>
    </div>
    <div class="flex" style="margin-top:10px; gap:8px;">
      <button class="btn btn-ok" id="btn_save_creator">💾 Speichern</button>
      <button class="btn btn-ghost" id="btn_cancel_creator">Abbrechen</button>
      <input type="hidden" id="cr_edit_mode" value="">
    </div>
  </div>

  <div id="creators-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="allmods-section" data-tab="allmods">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🏷️ Alle Mods — Tags &amp; Notizen</h2>
    <div class="flex" style="gap:6px;">
      <select id="allmods-cat-filter" style="padding:6px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:12px;">
        <option value="">Alle Kategorien</option>
      </select>
      <select id="allmods-tag-filter" style="padding:6px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:12px;">
        <option value="">Alle Tags</option>
        <option value="__tagged">🏷️ Nur getaggte</option>
        <option value="__untagged">Ohne Tags</option>
        <option value="__noted">📝 Mit Notiz</option>
      </select>
      <input type="text" id="allmods-search" placeholder="🔍 Mod suchen…" style="padding:6px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:12px;width:220px;">
    </div>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier siehst du <b>alle gescannten Mods</b> auf einen Blick. Du kannst jeder Datei Tags und Notizen zuweisen, um deine Mod-Sammlung zu organisieren. Nutze die Suche und Filter oben rechts.</div>
  <div id="allmods-summary" class="muted" style="margin:8px 0;">Warte auf Scan…</div>
  <div id="allmods-list" style="margin-top:8px;"></div>
  <div id="allmods-loadmore" style="text-align:center;margin-top:12px;display:none;">
    <button class="btn btn-ghost" id="btn_allmods_more">⬇️ Mehr laden…</button>
  </div>
</div>

<div class="box" id="nonmod-section" data-tab="allmods" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📄 Sonstige Dateien im Mods-Ordner</h2>
    <span class="muted" id="nonmod-summary">Warte auf Scan…</span>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Diese Dateien liegen in deinem Mods-Ordner, sind aber <b>keine Mods</b> (.package/.ts4script). Das Spiel ignoriert sie — sie stören nicht, nehmen aber Platz weg. Typisch: Readmes, Vorschau-Bilder, alte Archive.</div>
  <div id="nonmod-list" style="margin-top:8px;"></div>
</div>

<div class="box" id="quarantine-section" data-tab="quarantine" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📦 Quarantäne-Manager</h2>
    <button class="btn btn-ghost" id="btn_reload_quarantine">↻ Aktualisieren</button>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier siehst du alle Dateien, die du in Quarantäne verschoben hast. Du kannst sie einzeln <b>zurückholen</b> (zurück in den Mods-Ordner) oder <b>endgültig löschen</b>.</div>
  <div id="quarantine-summary" class="muted">Lade…</div>
  <div id="quarantine-list" style="margin-top:12px;"></div>
</div>

<!-- ════════════════════════════════════════════════════ -->
<!-- ═══ CACHE-CLEANER ═══ -->
<!-- ════════════════════════════════════════════════════ -->
<div class="box" id="cache-cleaner-section" data-tab="cache" style="border:1px solid #1e3a5f;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🧹 Cache-Cleaner</h2>
    <button class="btn btn-ghost" onclick="loadCacheInfo()">↻ Aktualisieren</button>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Sims 4 speichert Bilder und Daten in Cache-Dateien um schneller zu laden. Diese können mit der Zeit <b>sehr groß werden</b> (mehrere GB!) und sogar <b>Probleme verursachen</b> (z.B. lange Ladezeiten, schwarze Thumbnails).<br><b>Keine Sorge:</b> Das Spiel erstellt alle Caches beim nächsten Start automatisch neu. <b>⚠️ Schließe das Spiel vor dem Bereinigen!</b></div>
  <div id="cache-list" style="margin-top:12px;">
    <div class="muted">⏳ Cache-Infos werden geladen…</div>
  </div>
  <div id="cache-actions" style="margin-top:12px; display:none;">
    <button class="btn btn-ok" onclick="cleanSelectedCaches()">🧹 Ausgewählte bereinigen</button>
    <button class="btn btn-ghost" onclick="cleanAllCaches()">🧹 Alle bereinigen</button>
    <span id="cache-result" class="muted small" style="margin-left:12px;"></span>
  </div>
</div>

<!-- ════════════════════════════════════════════════════ -->
<!-- ═══ MOD-BACKUP ═══ -->
<!-- ════════════════════════════════════════════════════ -->
<div class="box" id="backup-section" data-tab="backup" style="border:1px solid #1e3a5f;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>💾 Mod-Backup</h2>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Sichert deine <b>komplette Mod-Sammlung</b> als ZIP-Datei. Falls beim Aufräumen mal etwas schiefgeht, kannst du alles aus dem Backup wiederherstellen. Die ZIP-Datei wird im Unterordner <code>ModBackups</code> deines Sims 4 Ordners gespeichert.</div>
  <div style="margin-top:12px;">
    <button class="btn btn-ok" id="btn-create-backup" onclick="createModBackup()">💾 Backup erstellen</button>
    <span id="backup-status" class="muted small" style="margin-left:12px;"></span>
  </div>
</div>

<!-- ════════════════════════════════════════════════════ -->
<!-- ═══ TRAY-CLEANER ═══ -->
<!-- ════════════════════════════════════════════════════ -->
<div class="box" id="tray-cleaner-section" data-tab="trayclean" style="border:1px solid #1e3a5f;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🗂️ Tray-Cleaner</h2>
    <button class="btn btn-ghost" onclick="scanTrayOrphans()">🔍 Verwaiste Dateien suchen</button>
  </div>
  <div class="info-hint" style="line-height:1.6;">💡 <b>Was ist der Tray-Ordner?</b> Dort speichert Sims 4 deine erstellten Sims, Häuser und Zimmer (alles was du in der Galerie/Bibliothek siehst).<br><br><b>Was macht der Tray-Cleaner?</b> Wenn du einen Sim oder ein Haus löschst, bleiben manchmal Reste übrig — Bilddaten, Raumpläne oder Blueprints ohne zugehörigen Eintrag. Das sind <b>"verwaiste Dateien"</b> — sie machen nichts kaputt, belegen aber Speicherplatz.<br><br>✅ <b>Verwaiste Dateien können bedenkenlos gelöscht werden.</b> Deine gespeicherten Sims und Häuser werden dadurch <b>nicht</b> gelöscht — nur der Datenmüll.</div>
  <div id="tray-clean-result" style="margin-top:12px;">
    <div class="muted">⏳ Wird automatisch gesucht…</div>
  </div>
</div>

<!-- ════════════════════════════════════════════════════ -->
<!-- ═══ SCRIPT-SICHERHEITSCHECK ═══ -->
<!-- ════════════════════════════════════════════════════ -->
<div class="box" id="script-security-section" data-tab="scriptcheck" style="border:1px solid #1e3a5f;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🛡️ Script-Sicherheitscheck</h2>
    <button class="btn btn-ghost" onclick="runScriptSecurityCheck()">🔍 Scripts prüfen</button>
  </div>
  <div class="info-hint" style="line-height:1.6;">💡 <b>Was sind Script-Mods?</b> Manche Mods enthalten Python-Scripts (<code>.ts4script</code>-Dateien) die dem Spiel neue Funktionen geben (z.B. MCCC, WickedWhims).<br><br><b>Was prüft der Check?</b> Er schaut ob in den Scripts bestimmte Befehle vorkommen, die <b>theoretisch</b> riskant sein könnten — z.B. Internet-Zugriff, Datei-Löschung oder Zugriff auf dein System.<br><br>⚠️ <b>Wichtig: Ein Fund heißt NICHT dass der Mod gefährlich ist!</b> Die meisten bekannten Mods (MCCC, WickedWhims, etc.) brauchen solche Funktionen um zu arbeiten. Verdächtig ist vor allem ein <b>unbekannter</b> Mod der z.B. auf das Internet zugreift oder Dateien löscht.</div>
  <div id="script-security-result" style="margin-top:12px;">
    <div class="muted">⏳ Wird automatisch geprüft…</div>
  </div>
</div>

<!-- ════════════════════════════════════════════════════ -->
<!-- ═══ BROKEN CC FINDER ═══ -->
<!-- ════════════════════════════════════════════════════ -->
<div class="box" id="broken-cc-section" data-tab="cccheck" style="border:1px solid #1e3a5f;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>� CC-Gesundheitscheck</h2>
    <button class="btn btn-ghost" onclick="findBrokenCC()">🔍 Jetzt prüfen</button>
  </div>
  <div class="info-hint">💡 Prüft alle deine Mod-Dateien auf Probleme. <b>❌ Fehler</b> = Datei ist kaputt, solltest du löschen. <b>⚠️ Hinweis</b> = kosmetisches Problem, Mod funktioniert trotzdem.</div>
  <div id="broken-cc-result" style="margin-top:12px;">
    <div class="muted">⏳ Wird automatisch geprüft…</div>
  </div>
</div>

<!-- ════════════════════════════════════════════════════ -->
<!-- ═══ PACKAGE-BROWSER ═══ -->
<!-- ════════════════════════════════════════════════════ -->
<div class="box" id="package-browser-section" data-tab="packages" style="border:1px solid #1e3a5f;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📦 Package-Browser</h2>
    <span class="muted" id="package-browser-count"></span>
  </div>
  <div class="info-hint">💡 Zeigt alle deine Mod-Dateien. Klicke auf eine Datei um zu sehen was drin steckt — z.B. ob es Kleidung, Möbel oder ein Gameplay-Mod ist.</div>
  <div style="margin-top:12px;">
    <input type="text" id="package-browse-filter" placeholder="🔍 Package suchen…" oninput="filterPackageList()" style="width:100%; padding:8px 12px; background:#0f1115; border:1px solid #334155; border-radius:6px; color:#e7e7e7; font-size:14px; margin-bottom:8px;">
    <div id="package-browse-list" style="max-height:300px; overflow-y:auto; border:1px solid #334155; border-radius:6px; background:#0f1115;">
      <div class="muted" style="padding:12px;">⏳ Wird nach Scan automatisch geladen…</div>
    </div>
  </div>
  <div id="package-browse-result" style="margin-top:12px;"></div>
</div>

<!-- ════════════════════════════════════════════════════ -->
<!-- ═══ SAVE-GESUNDHEITSCHECK ═══ -->
<!-- ════════════════════════════════════════════════════ -->
<div class="box" id="save-health-section" data-tab="savehealth" style="border:1px solid #1e3a5f;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>❤️ Save-Gesundheitscheck</h2>
    <button class="btn btn-ghost" onclick="checkSaveHealth()">🩺 Speicherstand prüfen</button>
  </div>
  <div class="info-hint">💡 Analysiert den geladenen Speicherstand auf Probleme: obdachlose Sims, fehlende Namen, doppelte Namen, negative Lebenstage, und mehr. <b>Lade erst den Speicherstand im Tray &amp; CC Tab.</b></div>
  <div id="save-health-result" style="margin-top:12px;">
    <div class="muted">⏳ Wird nach Savegame-Analyse automatisch geprüft…</div>
  </div>
</div>

<!-- ════════════════════════════════════════════════════ -->
<!-- ═══ SPEICHERPLATZ-VISUALISIERUNG ═══ -->
<!-- ════════════════════════════════════════════════════ -->
<div class="box" id="disk-usage-section" data-tab="diskusage" style="border:1px solid #1e3a5f;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📊 Speicherplatz-Analyse</h2>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Zeigt dir genau, <b>wie viel Speicherplatz</b> deine Mods belegen — aufgeteilt nach Ordnern und Dateitypen. So findest du schnell heraus, welche Ordner am größten sind.</div>
  <div id="disk-usage-chart" style="margin-top:12px;">
    <div class="muted">Wird automatisch nach dem Scan angezeigt…</div>
  </div>
</div>

<!-- ════════════════════════════════════════════════════ -->
<!-- ═══ CHEATS ═══ -->
<!-- ════════════════════════════════════════════════════ -->
<div class="box" id="cheats-section" data-tab="cheats" style="border:1px solid #1e3a5f;">
  <div class="flex" style="justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:6px;">
    <h2>🎮 Sims 4 Cheat-Konsole</h2>
    <span class="cheat-count" id="cheat-match-count"></span>
  </div>
  <div class="info-hint" style="margin-bottom:14px;">💡 <b>Cheats öffnen:</b> Im Spiel <kbd>Strg</kbd> + <kbd>Shift</kbd> + <kbd>C</kbd> drücken. Klicke auf einen Cheat um ihn zu kopieren — dann im Spiel mit <kbd>Strg+V</kbd> einfügen.<br>Viele Cheats benötigen zuerst <code style="color:#79c0ff;">testingcheats true</code>. Markiere deine Lieblings-Cheats mit ⭐ für schnellen Zugriff.</div>
  <div class="cheat-toolbar">
    <div class="cheat-search-wrap">
      <input type="text" class="cheat-search" id="cheat-search" placeholder="Cheat suchen… z.B. motherlode, Karriere, Fitness" oninput="filterCheats()">
    </div>
    <div class="cheat-count" id="cheat-fav-count-badge" style="display:flex;align-items:center;gap:6px;padding:0 14px;font-size:13px;color:#fbbf24;white-space:nowrap;">⭐ <span id="cheat-fav-count-num">0</span></div>
  </div>
  <div class="cheat-cats" id="cheat-cats"></div>
  <div class="cheat-grid" id="cheat-grid"></div>
</div>

<script>
const TOKEN = __TOKEN__;
const LOGFILE = __LOGFILE__;
document.getElementById('logfile').textContent = LOGFILE;

const LOG_KEY = 'dupe_actionlog_v2';
let logEntries = [];
try { logEntries = JSON.parse(localStorage.getItem(LOG_KEY) || '[]'); } catch(e) { logEntries = []; }

// ═══════════════════════════════════════════════════
// ═══ TOAST-BENACHRICHTIGUNGEN ═══
// ═══════════════════════════════════════════════════
const _toastIcons = { success:'✅', error:'❌', warning:'⚠️', info:'ℹ️' };
function showToast(msg, type='info', duration=4000) {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = 'toast toast-' + type;
  t.style.setProperty('--toast-duration', (duration/1000)+'s');
  t.innerHTML = '<span class="toast-icon">' + (_toastIcons[type]||'ℹ️') + '</span><span>' + esc(msg) + '</span><span class="toast-close" onclick="this.parentElement.remove()">✕</span>';
  c.appendChild(t);
  setTimeout(() => { if(t.parentElement) t.remove(); }, duration + 350);
}

const selected = new Set();

// ═══════════════════════════════════════════════════
// ═══ TAB-NAVIGATION ═══
// ═══════════════════════════════════════════════════
let _activeTab = 'dashboard';

// Sections die per data bedingt sichtbar sind (display:none wenn leer)
const _conditionalSections = new Set([
  'nonmod-section','quarantine-section',
  'progress-section','all-ok-banner','groups-view','perfile-view'
]);

function switchTab(tabName) {
  _activeTab = tabName;
  // Alle data-tab Elemente verarbeiten
  document.querySelectorAll('[data-tab]').forEach(el => {
    const elTab = el.getAttribute('data-tab');
    if (elTab === tabName) {
      // Element gehört zum aktiven Tab
      if (_conditionalSections.has(el.id)) {
        // Bedingte Sektionen: nur anzeigen wenn Daten vorhanden (has-content)
        el.removeAttribute('data-tab-hidden');
        el.style.display = el.classList.contains('has-content') ? '' : 'none';
      } else {
        el.style.display = '';
        el.removeAttribute('data-tab-hidden');
      }
    } else {
      // Element gehört zu anderem Tab — verstecken
      el.setAttribute('data-tab-hidden', '1');
      el.style.display = 'none';
    }
  });

  // Tab-Buttons aktualisieren
  document.querySelectorAll('#section-nav .nav-tab').forEach(btn => {
    btn.classList.remove('active');
  });
  const activeBtn = document.querySelector('#section-nav .nav-tab[onclick*=\"' + tabName + '\"]');
  if (activeBtn) activeBtn.classList.add('active');

  // Spezialbehandlung: Duplikate-Tab hat groups/perfile Toggle
  if (tabName === 'duplicates') applyDuplicatesView();

  // Nach Tab-Wechsel zum Anfang scrollen
  window.scrollTo({top: 0, behavior: 'smooth'});

  // Cheats beim ersten Mal rendern
  if (tabName === 'cheats' && !window._cheatsRendered) renderCheats();
}

// ═══════════════════════════════════════════════════
// ═══ CHEAT-KONSOLE ═══
// ═══════════════════════════════════════════════════
const _CHEATS = [
  { cat: 'Allgemein', icon: '⚙️', color: '#94a3b8', cheats: [
    { code: 'testingcheats true', desc: 'Erweiterte Cheats aktivieren' },
    { code: 'testingcheats false', desc: 'Erweiterte Cheats deaktivieren' },
    { code: 'help', desc: 'Listet alle Cheat-Codes auf' },
    { code: 'resetSim Vorname Nachname', desc: 'Setzt den genannten Sim zurück' },
    { code: 'fullscreen', desc: 'Vollbildmodus umschalten' },
    { code: 'headlineEffects off', desc: 'Plumbob + Gedankenblasen ausblenden' },
    { code: 'headlineEffects on', desc: 'Plumbob + Gedankenblasen einblenden' },
    { code: 'cas.fulleditmode', desc: 'Volle CAS-Bearbeitung im Spiel', req: 'testingcheats' },
    { code: 'Death.toggle false', desc: 'Sims können nicht sterben' },
    { code: 'Death.toggle true', desc: 'Sims können wieder sterben' },
    { code: 'ui.toggle_silence_phone', desc: 'Handy lautlos / laut schalten' },
  ]},
  { cat: 'Geld', icon: '💰', color: '#22c55e', cheats: [
    { code: 'kaching', desc: '+1.000 Simoleons' },
    { code: 'rosebud', desc: '+1.000 Simoleons' },
    { code: 'motherlode', desc: '+50.000 Simoleons' },
    { code: 'money 1000000', desc: 'Konto auf 1 Mio. setzen', req: 'testingcheats' },
    { code: 'sims.modify_funds +50000', desc: '50.000 hinzufügen', req: 'testingcheats' },
    { code: 'sims.modify_funds -50000', desc: '50.000 abziehen', req: 'testingcheats' },
    { code: 'FreeRealEstate on', desc: 'Alle Grundstücke kostenlos' },
    { code: 'FreeRealEstate off', desc: 'Grundstückspreise zurücksetzen' },
  ]},
  { cat: 'Bedürfnisse', icon: '❤️', color: '#ef4444', cheats: [
    { code: 'sims.fill_all_commodities', desc: 'Alle Bedürfnisse aller Sims füllen' },
    { code: 'stats.fill_commodities_household', desc: 'Bedürfnisse des Haushalts füllen' },
    { code: 'sims.give_satisfaction_points 5000', desc: '5.000 Zufriedenheitspunkte', req: 'testingcheats' },
    { code: 'aspirations.complete_current_milestone', desc: 'Aktuelle Bestrebens-Stufe abschließen' },
    { code: 'households.autopay_bills', desc: 'Rechnungen automatisch bezahlen' },
  ]},
  { cat: 'Bau & Kauf', icon: '🏠', color: '#3b82f6', cheats: [
    { code: 'bb.moveobjects', desc: 'Objekte frei platzieren (0-9 = Höhe)' },
    { code: 'bb.showhiddenobjects', desc: 'Versteckte Objekte freischalten' },
    { code: 'bb.showliveeditobjects', desc: 'Welt-Deko-Objekte freischalten' },
    { code: 'bb.enablefreebuild', desc: 'Bauen auf versteckten Grundstücken' },
    { code: 'bb.ignoregameplayunlocksentitlement', desc: 'Karriere-Belohnungsobjekte freischalten' },
    { code: 'object.setashead', desc: 'Objekt als Kopfschmuck (Shift-Klick)', req: 'testingcheats' },
  ]},
  { cat: 'Karriere', icon: '💼', color: '#f59e0b', cheats: [
    { code: 'careers.promote Astronaut', desc: 'Astronaut befördern', req: 'testingcheats' },
    { code: 'careers.promote Athletic', desc: 'Sportler befördern', req: 'testingcheats' },
    { code: 'careers.promote Business', desc: 'Business befördern', req: 'testingcheats' },
    { code: 'careers.promote Criminal', desc: 'Verbrecher befördern', req: 'testingcheats' },
    { code: 'careers.promote Culinary', desc: 'Leckermaul befördern', req: 'testingcheats' },
    { code: 'careers.promote Detective', desc: 'Polizist befördern', req: 'testingcheats' },
    { code: 'careers.promote Doctor', desc: 'Arzt befördern', req: 'testingcheats' },
    { code: 'careers.promote Entertainer', desc: 'Entertainer befördern', req: 'testingcheats' },
    { code: 'careers.promote Painter', desc: 'Maler befördern', req: 'testingcheats' },
    { code: 'careers.promote Secretagent', desc: 'Geheimagent befördern', req: 'testingcheats' },
    { code: 'careers.promote Techguru', desc: 'Technik-Guru befördern', req: 'testingcheats' },
    { code: 'careers.promote Styleinfluencer', desc: 'Stilbeeinflusser befördern', req: 'testingcheats' },
    { code: 'careers.promote adult_writer', desc: 'Schriftsteller befördern', req: 'testingcheats' },
    { code: 'careers.promote Actor', desc: 'Schauspieler befördern', req: 'testingcheats' },
    { code: 'careers.promote Activist', desc: 'Politiker befördern', req: 'testingcheats' },
    { code: 'careers.promote adult_critic', desc: 'Kritiker befördern', req: 'testingcheats' },
    { code: 'careers.promote Social', desc: 'Soziale Medien befördern', req: 'testingcheats' },
    { code: 'careers.promote Military', desc: 'Militär befördern', req: 'testingcheats' },
    { code: 'careers.promote Education', desc: 'Bildungswesen befördern', req: 'testingcheats' },
    { code: 'careers.promote Engineer', desc: 'Ingenieur befördern', req: 'testingcheats' },
    { code: 'careers.promote Law', desc: 'Recht befördern', req: 'testingcheats' },
    { code: 'careers.promote adult_active_scientist', desc: 'Wissenschaftler befördern', req: 'testingcheats' },
    { code: 'careers.promote adult_active_Reaper', desc: 'Schnitter befördern', req: 'testingcheats' },
    { code: 'careers.promote Mortician', desc: 'Bestatter befördern', req: 'testingcheats' },
    { code: 'careers.promote Romance', desc: 'Romantiktherapeut befördern', req: 'testingcheats' },
    { code: 'careers.promote Noble', desc: 'Adel befördern', req: 'testingcheats' },
    { code: 'careers.add_career Astronaut', desc: 'Karriere Astronaut starten', req: 'testingcheats' },
    { code: 'careers.remove_career Astronaut', desc: 'Karriere Astronaut beenden', req: 'testingcheats' },
  ]},
  { cat: 'Fähigkeiten', icon: '⚔️', color: '#a855f7', cheats: [
    { code: 'stats.set_skill_level Major_Fishing 10', desc: 'Angeln auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Charisma 10', desc: 'Charisma auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Comedy 10', desc: 'Comedy auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Skill_Fitness 10', desc: 'Fitness auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Gardening 10', desc: 'Gartenarbeit auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_GourmetCooking 10', desc: 'Feinschmecker-Kochen Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Guitar 10', desc: 'Gitarre auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Handiness 10', desc: 'Geschicklichkeit auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_HomestyleCooking 10', desc: 'Kochen auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Logic 10', desc: 'Logik auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Mischief 10', desc: 'Schelm auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Painting 10', desc: 'Malen auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Piano 10', desc: 'Klavier auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Programming 10', desc: 'Programmieren auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_RocketScience 10', desc: 'Raumfahrttechnik auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Violin 10', desc: 'Geige auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_VideoGaming 10', desc: 'Videospiele auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Writing 10', desc: 'Schreiben auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Bartending 10', desc: 'Mixen auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Singing 10', desc: 'Singen auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Wellness 10', desc: 'Wellness auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Photography 10', desc: 'Fotografie auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Baking 10', desc: 'Backen auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_DJ 10', desc: 'DJ-Mixen auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Parenting 10', desc: 'Erziehung auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Herbalism 10', desc: 'Kräuterkunde auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Acting 10', desc: 'Schauspielerei auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Archaeology 10', desc: 'Archäologie auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Robotic 10', desc: 'Robotik auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Research 10', desc: 'Forschen & Debattieren Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Rockclimbing 10', desc: 'Klettern auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Skiing 10', desc: 'Ski fahren auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Snowboarding 10', desc: 'Snowboarden auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level AdultMajor_FlowerArranging 10', desc: 'Blumenbinden auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level AdultMajor_Fabrication 10', desc: 'Herstellung auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Skill_CrossStitch 10', desc: 'Kreuzstich auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Vet 10', desc: 'Tierarzt auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_PipeOrgan 10', desc: 'Orgel auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Romance 10', desc: 'Romantik auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Swordsmanship 10', desc: 'Schwertkampf auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level AdultMajor_EquestrianSkill 10', desc: 'Reiten auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Pottery 10', desc: 'Töpfern auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Tattooing 10', desc: 'Tätowieren auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Major_Papercraft 10', desc: 'Papierbastelei auf Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level VampireLore 15', desc: 'Vampirsaga auf Stufe 15', req: 'testingcheats' },
    { code: 'stats.set_skill_level Minor_Dancing 5', desc: 'Tanzen auf Stufe 5', req: 'testingcheats' },
    { code: 'stats.set_skill_level Minor_Mediaproduction 5', desc: 'Medienproduktion auf Stufe 5', req: 'testingcheats' },
    { code: 'stats.set_skill_level AdultMinor_JuiceFizzing 5', desc: 'Aufsprudeln auf Stufe 5', req: 'testingcheats' },
    { code: 'stats.set_skill_level AdultMinor_RanchNectar 5', desc: 'Nektarherstellung auf Stufe 5', req: 'testingcheats' },
    { code: 'stats.set_skill_level AdultMinor_Thanatology 5', desc: 'Thanatologie auf Stufe 5', req: 'testingcheats' },
  ]},
  { cat: 'Kinder-Skills', icon: '👶', color: '#ec4899', cheats: [
    { code: 'stats.set_skill_level Skill_Child_Creativity 10', desc: 'Kind: Kreativität Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Skill_Child_Mental 10', desc: 'Kind: Mental Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Skill_Child_Motor 10', desc: 'Kind: Motorik Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Skill_Child_Social 10', desc: 'Kind: Sozial Stufe 10', req: 'testingcheats' },
    { code: 'stats.set_skill_level Toddler_Communication 5', desc: 'Kleinkind: Kommunikation Stufe 5', req: 'testingcheats' },
    { code: 'stats.set_skill_level Toddler_Imagination 5', desc: 'Kleinkind: Fantasie Stufe 5', req: 'testingcheats' },
    { code: 'stats.set_skill_level Toddler_Movement 5', desc: 'Kleinkind: Motorik Stufe 5', req: 'testingcheats' },
    { code: 'stats.set_skill_level Toddler_Potty 5', desc: 'Kleinkind: Töpfchen Stufe 5', req: 'testingcheats' },
    { code: 'stats.set_skill_level Toddler_Thinking 5', desc: 'Kleinkind: Denken Stufe 5', req: 'testingcheats' },
  ]},
  { cat: 'Okkult', icon: '🧛', color: '#7c3aed', cheats: [
    { code: 'traits.equip_trait trait_OccultVampire', desc: 'Sim in Vampir verwandeln' },
    { code: 'traits.remove_trait trait_OccultVampire', desc: 'Vampir entfernen' },
    { code: 'traits.equip_trait trait_OccultWerewolf', desc: 'Sim in Werwolf verwandeln' },
    { code: 'traits.remove_trait trait_OccultWerewolf', desc: 'Werwolf entfernen' },
    { code: 'traits.equip_trait trait_Occult_WitchOccult', desc: 'Sim in Magier verwandeln' },
    { code: 'traits.remove_trait trait_Occult_WitchOccult', desc: 'Magier entfernen' },
    { code: 'traits.equip_trait trait_OccultMermaid', desc: 'Sim in Meerjungfrau verwandeln' },
    { code: 'traits.remove_trait trait_OccultMermaid', desc: 'Meerjungfrau entfernen' },
    { code: 'traits.equip_trait trait_OccultAlien', desc: 'Sim in Alien verwandeln' },
    { code: 'traits.remove_trait trait_OccultAlien', desc: 'Alien entfernen' },
    { code: 'stats.set_stat rankedStatistic_WitchOccult_WitchXP 2850', desc: 'Magier: Max XP (Virtuose)', req: 'testingcheats' },
    { code: 'stats.set_stat rankedStatistic_Werewolf_Progression 3000', desc: 'Werwolf: Max XP (Apex)', req: 'testingcheats' },
  ]},
  { cat: 'Geister', icon: '👻', color: '#6366f1', cheats: [
    { code: 'traits.equip_trait hunger', desc: 'Geist: Tod durch Hunger' },
    { code: 'traits.equip_trait drown', desc: 'Geist: Tod durch Ertrinken' },
    { code: 'traits.equip_trait electrocution', desc: 'Geist: Tod durch Stromschlag' },
    { code: 'traits.equip_trait embarrassment', desc: 'Geist: Tod durch Blamage' },
    { code: 'traits.equip_trait laugh', desc: 'Geist: Tod durch Lachanfall' },
    { code: 'traits.equip_trait oldage', desc: 'Geist: Tod durch Altersschwäche' },
    { code: 'traits.equip_trait exhaust', desc: 'Geist: Tod durch Überanstrengung' },
    { code: 'traits.equip_trait cowplant', desc: 'Geist: Kuhpflanze' },
    { code: 'traits.equip_trait steam', desc: 'Geist: Tod in Sauna' },
    { code: 'traits.equip_trait Ghost_Frozen', desc: 'Geist: Tod durch Erfrieren' },
    { code: 'traits.equip_trait Ghost_Overheat', desc: 'Geist: Tod durch Hitze' },
    { note: '↩️ Rückgängig: traits.remove_trait statt traits.equip_trait verwenden' },
  ]},
  { cat: 'Jahreszeiten', icon: '🌦️', color: '#0ea5e9', cheats: [
    { code: 'seasons.advance_season', desc: 'Zur nächsten Jahreszeit wechseln' },
    { code: 'seasons.set_season 1', desc: 'Frühling setzen' },
    { code: 'seasons.set_season 2', desc: 'Sommer setzen' },
    { code: 'seasons.set_season 3', desc: 'Herbst setzen' },
    { code: 'seasons.set_season 4', desc: 'Winter setzen' },
    { code: 'weather.summon_lightning_strike', desc: 'Blitz in der Nachbarschaft' },
    { code: 'weather.lightning_strike_object', desc: 'Blitz in zufälliges Objekt' },
  ]},
  { cat: 'Ökologie', icon: '🌿', color: '#10b981', cheats: [
    { code: 'eco_footprint.set_eco_footprint_state 0', desc: 'Grüner ökologischer Abdruck', req: 'testingcheats' },
    { code: 'eco_footprint.set_eco_footprint_state 1', desc: 'Neutraler ökologischer Abdruck', req: 'testingcheats' },
    { code: 'eco_footprint.set_eco_footprint_state 2', desc: 'Industrieller ökologischer Abdruck', req: 'testingcheats' },
  ]},
  { cat: 'Teenager', icon: '📚', color: '#f97316', cheats: [
    { code: 'careers.promote Teen_Retail', desc: 'Einzelhandel befördern', req: 'testingcheats' },
    { code: 'careers.promote Babysitter', desc: 'Babysitter befördern', req: 'testingcheats' },
    { code: 'careers.promote Barista', desc: 'Barista befördern', req: 'testingcheats' },
    { code: 'careers.promote FastFood', desc: 'Fastfood befördern', req: 'testingcheats' },
    { code: 'careers.promote Manual', desc: 'Handarbeiter befördern', req: 'testingcheats' },
    { code: 'careers.promote Scout', desc: 'Pfadfinder befördern', req: 'testingcheats' },
    { code: 'careers.add_career HSTeam_FootballTeam', desc: 'Football-Team beitreten' },
    { code: 'careers.add_career HSTeam_CheerTeam', desc: 'Cheerleading-Team beitreten' },
    { code: 'careers.add_career HSTeam_ChessTeam', desc: 'Schach-Team beitreten' },
    { code: 'careers.add_career HSTeam_ComputerTeam', desc: 'Computer-Team beitreten' },
  ]},
  { cat: 'Handelsvorteile', icon: '🏪', color: '#14b8a6', cheats: [
    { code: 'bucks.unlock_perk StorePlacard_1 true', desc: 'Plakette "Mein erster Simoleon"' },
    { code: 'bucks.unlock_perk PedestalMimic true', desc: 'Provokativer Ausstelltisch' },
    { code: 'bucks.unlock_perk RetailOutfit true', desc: 'Pfiffiges Shirt' },
    { code: 'bucks.unlock_perk RegisterMimic true', desc: 'Ladenkasse von Morgen' },
    { code: 'bucks.unlock_perk AdditionalWorker_1 true', desc: 'Zusätzlicher Angestellter Nr. 1' },
    { code: 'bucks.unlock_perk AdditionalWorker_2 true', desc: 'Zusätzlicher Angestellter Nr. 2' },
    { code: 'bucks.unlock_perk RestockSpeed_Small true', desc: 'Schneller auffüllen (gering)' },
    { code: 'bucks.unlock_perk RestockSpeed_Large true', desc: 'Schneller auffüllen (extrem)' },
    { code: 'bucks.unlock_perk CheckoutSpeed_Small true', desc: 'Schneller kassieren (gering)' },
    { code: 'bucks.unlock_perk CheckoutSpeed_Large true', desc: 'Schneller kassieren (extrem)' },
    { code: 'bucks.unlock_perk SureSaleSocial true', desc: 'Sicherer Verkauf' },
    { code: 'bucks.unlock_perk InstantRestock true', desc: 'Sofort auffüllen' },
    { code: 'bucks.unlock_perk CustomerPurchaseIntent true', desc: 'Seriöser Kunde' },
    { code: 'bucks.unlock_perk ImproveRetailSocials true', desc: 'Raffinierter Verkäufer' },
  ]},
];

let _cheatActiveCat = null;
let _cheatFavCache = new Set();
window._cheatsRendered = false;

function _loadCheatFavs() {
  return _cheatFavCache;
}
function _saveCheatFavs(favSet) {
  _cheatFavCache = favSet;
  // Persist to server (fire-and-forget)
  postAction('save_cheat_favs', '', { favs: [...favSet] }).catch(e => console.warn('save_cheat_favs failed:', e));
}
async function _initCheatFavs() {
  try {
    const r = await postAction('load_cheat_favs', '');
    if (r.favs && Array.isArray(r.favs) && r.favs.length > 0) {
      _cheatFavCache = new Set(r.favs);
    } else {
      // Migrate from localStorage if present (one-time)
      try {
        const old = JSON.parse(localStorage.getItem('sims4_cheat_favs') || '[]');
        if (Array.isArray(old) && old.length > 0) {
          _cheatFavCache = new Set(old);
          _saveCheatFavs(_cheatFavCache);
          localStorage.removeItem('sims4_cheat_favs');
        }
      } catch(m) {}
    }
  } catch(e) { console.warn('load_cheat_favs failed:', e); }
}

function toggleCheatFav(code, ev) {
  ev.stopPropagation();
  const favs = _loadCheatFavs();
  if (favs.has(code)) favs.delete(code); else favs.add(code);
  _saveCheatFavs(favs);
  // Komplett neu rendern damit Fav-Karte oben aktualisiert wird
  renderCheats();
  filterCheats();
}

function _updateFavBadge() {
  const favs = _loadCheatFavs();
  const badge = document.getElementById('cheat-fav-count-badge');
  const num = document.getElementById('cheat-fav-count-num');
  if (num) num.textContent = favs.size;
  if (badge) badge.style.display = favs.size > 0 ? 'flex' : 'none';
}

function _buildFavCard(favs) {
  // Sammle alle Fav-Cheats aus allen Kategorien
  let favCheats = [];
  _CHEATS.forEach(g => {
    g.cheats.forEach(c => {
      if (c.code && favs.has(c.code)) favCheats.push(c);
    });
  });
  if (favCheats.length === 0) return '';

  let html = '<div class="cheat-card cheat-card-fav" data-cheat-cat="__favs__" style="grid-column:1/-1;border-color:#eab30833;">';
  html += '<div class="cheat-card-head" style="border-bottom-color:#eab30822;"><div class="cheat-card-icon" style="background:#eab30815;color:#eab308;">⭐</div>';
  html += '<div><div class="cheat-card-title" style="color:#fbbf24;">Meine Favoriten</div>';
  html += '<div class="cheat-card-desc">' + favCheats.length + ' gespeichert — Klicke ⭐ zum Entfernen</div></div></div>';
  html += '<div class="cheat-card-body">';
  favCheats.forEach(c => {
    const searchText = (c.code + ' ' + c.desc).toLowerCase();
    html += '<div class="cheat-row" data-search="' + esc(searchText) + '" onclick="copyCheat(this, \'' + c.code.replace(/'/g, "\\'") + '\')" title="Klicken zum Kopieren">';
    html += '<span class="cheat-row-code">' + esc(c.code) + '</span>';
    if (c.req) html += '<span class="cheat-req">' + esc(c.req) + '</span>';
    html += '<span class="cheat-row-desc">' + esc(c.desc) + '</span>';
    html += '<span class="cheat-row-fav is-fav" data-fav-code="' + esc(c.code) + '" onclick="toggleCheatFav(\'' + c.code.replace(/'/g, "\\'") + '\', event)">⭐</span>';
    html += '<span class="cheat-row-copy">📋</span>';
    html += '</div>';
  });
  html += '</div></div>';
  return html;
}

function renderCheats() {
  window._cheatsRendered = true;
  const grid = document.getElementById('cheat-grid');
  const cats = document.getElementById('cheat-cats');
  const favs = _loadCheatFavs();

  // Kategorie-Buttons
  let catHtml = '<button class="cheat-cat-btn active" onclick="filterCheatCat(null, this)">Alle</button>';
  if (favs.size > 0) {
    catHtml += '<button class="cheat-cat-btn" onclick="filterCheatCat(\'__favs__\', this)" style="border-color:#eab30844;color:#fbbf24;">⭐ Favoriten <span style="opacity:.5;font-size:10px;">' + favs.size + '</span></button>';
  }
  _CHEATS.forEach(g => {
    catHtml += '<button class="cheat-cat-btn" onclick="filterCheatCat(\'' + g.cat.replace(/'/g, "\\'") + '\', this)">' + g.icon + ' ' + g.cat + ' <span style="opacity:.5;font-size:10px;">' + g.cheats.filter(c=>c.code).length + '</span></button>';
  });
  cats.innerHTML = catHtml;

  // Favoriten-Karte ganz oben + normale Karten
  let html = _buildFavCard(favs);

  _CHEATS.forEach(g => {
    html += '<div class="cheat-card" data-cheat-cat="' + esc(g.cat) + '">';
    html += '<div class="cheat-card-head"><div class="cheat-card-icon" style="background:' + g.color + '15;color:' + g.color + ';">' + g.icon + '</div>';
    html += '<div><div class="cheat-card-title">' + esc(g.cat) + '</div>';
    html += '<div class="cheat-card-desc">' + g.cheats.filter(c=>c.code).length + ' Cheats</div></div></div>';
    html += '<div class="cheat-card-body">';
    g.cheats.forEach(c => {
      if (c.note) {
        html += '<div class="cheat-note">' + c.note + '</div>';
        return;
      }
      const isFav = favs.has(c.code);
      const searchText = (c.code + ' ' + c.desc).toLowerCase();
      html += '<div class="cheat-row" data-search="' + esc(searchText) + '" onclick="copyCheat(this, \'' + c.code.replace(/'/g, "\\'") + '\')" title="Klicken zum Kopieren">';
      html += '<span class="cheat-row-code">' + esc(c.code) + '</span>';
      if (c.req) html += '<span class="cheat-req">' + esc(c.req) + '</span>';
      html += '<span class="cheat-row-desc">' + esc(c.desc) + '</span>';
      html += '<span class="cheat-row-fav' + (isFav ? ' is-fav' : '') + '" data-fav-code="' + esc(c.code) + '" onclick="toggleCheatFav(\'' + c.code.replace(/'/g, "\\'") + '\', event)">' + (isFav ? '⭐' : '☆') + '</span>';
      html += '<span class="cheat-row-copy">📋</span>';
      html += '</div>';
    });
    html += '</div></div>';
  });
  grid.innerHTML = html;
  _updateFavBadge();
  updateCheatCount();
}

function copyCheat(el, code) {
  navigator.clipboard.writeText(code).then(() => {
    el.classList.add('cheat-copied');
    const copyEl = el.querySelector('.cheat-row-copy');
    if (copyEl) copyEl.textContent = '✅';
    showToast('Kopiert: ' + code, 'success', 2000);
    setTimeout(() => {
      el.classList.remove('cheat-copied');
      if (copyEl) copyEl.textContent = '📋';
    }, 1500);
  });
}

function filterCheatCat(cat, btn) {
  _cheatActiveCat = cat;
  document.querySelectorAll('.cheat-cat-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  filterCheats();
}

function filterCheats() {
  const query = (document.getElementById('cheat-search').value || '').toLowerCase().trim();
  const cards = document.querySelectorAll('.cheat-card');
  let total = 0;
  cards.forEach(card => {
    const cat = card.getAttribute('data-cheat-cat');
    if (_cheatActiveCat && cat !== _cheatActiveCat) { card.classList.add('cheat-hidden'); return; }
    card.classList.remove('cheat-hidden');
    const rows = card.querySelectorAll('.cheat-row');
    let visibleInCard = 0;
    rows.forEach(row => {
      const searchText = row.getAttribute('data-search') || '';
      if (query && !searchText.includes(query)) {
        row.classList.add('cheat-hidden');
      } else {
        row.classList.remove('cheat-hidden');
        visibleInCard++;
      }
    });
    if (query && visibleInCard === 0) card.classList.add('cheat-hidden');
    else total += visibleInCard;
  });
  updateCheatCount(total);
}

function updateCheatCount(n) {
  const el = document.getElementById('cheat-match-count');
  if (!el) return;
  const totalCheats = _CHEATS.reduce((s, g) => s + g.cheats.filter(c=>c.code).length, 0);
  if (n === undefined) el.textContent = totalCheats + ' Cheats';
  else el.textContent = n + ' / ' + totalCheats + ' Cheats';
}

// Duplikate-Tab: groups-view vs perfile-view
function applyDuplicatesView() {
  const gv = document.getElementById('groups-view');
  const pv = document.getElementById('perfile-view');
  if (currentView === 'groups') {
    gv.style.display = 'block';
    gv.classList.add('has-content');
    pv.style.display = 'none';
    pv.classList.remove('has-content');
  } else {
    gv.style.display = 'none';
    gv.classList.remove('has-content');
    pv.style.display = 'block';
    pv.classList.add('has-content');
  }
}

// Hilfsfunktion: Bedingte Sektion anzeigen (ersetzt direkte display-Steuerung)
function showConditionalSection(id, show) {
  const el = document.getElementById(id);
  if (!el) return;
  if (show) {
    el.classList.add('has-content');
    // Nur anzeigen wenn der richtige Tab aktiv ist
    if (el.getAttribute('data-tab') === _activeTab) {
      el.style.display = '';
    }
  } else {
    el.classList.remove('has-content');
    el.style.display = 'none';
  }
}

// Initial: Dashboard anzeigen
document.addEventListener('DOMContentLoaded', () => {
  switchTab('dashboard');
});

function esc(s) {
  return String(s ?? '')
    .replaceAll('&','&amp;')
    .replaceAll('<','&lt;')
    .replaceAll('>','&gt;')
    .replaceAll('"','&quot;')
    .replaceAll("'","&#39;");
}

function renderLog() {
  document.getElementById('log').textContent = logEntries.join('\\n');
}
renderLog();

function addLog(line) {
  const ts = new Date().toLocaleString();
  logEntries.unshift(`[${ts}] ${line}`);
  if (logEntries.length > 500) logEntries = logEntries.slice(0, 500);
  localStorage.setItem(LOG_KEY, JSON.stringify(logEntries));
  renderLog();
}

async function copyText(text) {
  try { await navigator.clipboard.writeText(text); }
  catch (e) {
    const ta = document.createElement('textarea');
    ta.value = text; document.body.appendChild(ta);
    ta.select(); document.execCommand('copy'); ta.remove();
  }
}

document.getElementById('log_copy').addEventListener('click', async () => {
  await copyText(logEntries.join('\\n'));
  addLog('LOG COPIED');
});

document.getElementById('log_csv').addEventListener('click', async () => {
  // Create CSV from log entries
  const csv = logEntries.map(line => {
    // Escape CSV fields properly
    return '"' + line.replace(/"/g, '""') + '"';
  }).join('\\n');
  
  // Add header
  const csvWithHeader = '"Timestamp | Action | Info"\\n' + csv;
  
  // Create download
  const blob = new Blob([csvWithHeader], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', `dupe_actions_${new Date().toISOString().split('T')[0]}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  addLog('CSV EXPORTED');
});

document.getElementById('log_clear').addEventListener('click', () => {
  if (!confirm('Log wirklich leeren?')) return;
  logEntries = [];
  localStorage.setItem(LOG_KEY, JSON.stringify(logEntries));
  renderLog();
});

function setLast(text) {
  document.getElementById('last').textContent = 'Letzte Aktion: ' + text;
}

function setBatchStatus(text) {
  document.getElementById('batchstatus').textContent = text;
}

function updateSelCount() {
  document.getElementById('selcount').textContent = `${selected.size} ausgewählt`;
}

async function loadData() {
  const r = await fetch('/api/data?token=' + encodeURIComponent(TOKEN));
  const j = await r.json();
  if (!j.ok) throw new Error(j.error || 'unknown');
  return j.data;
}

async function postAction(action, path, extra={}) {
  const res = await fetch('/api/action', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ token: TOKEN, action, path, ...extra })
  });
  const j = await res.json();
  if (!j.ok) throw new Error(j.error || 'unknown');
  return j;
}

function matchesFilters(text, term) {
  term = term.trim().toLowerCase();
  if (!term) return true;
  return text.toLowerCase().includes(term);
}

function humanSize(bytes) {
  const units = ['B','KB','MB','GB','TB'];
  let x = Number(bytes);
  let i = 0;
  while (x >= 1024 && i < units.length-1) { x /= 1024; i++; }
  return i === 0 ? `${Math.round(x)} B` : `${x.toFixed(2)} ${units[i]}`;
}

function uniqueCount(arr) { return new Set(arr).size; }

// Cluster-Rendering: Gruppiert Dateien innerhalb einer Ähnlich-Gruppe nach identischem Inhalt (Hash)
function renderClusters(files, gi) {
  // Gruppiere nach Hash
  const byHash = new Map();
  const noHash = [];
  for (const f of files) {
    if (f.hash) {
      if (!byHash.has(f.hash)) byHash.set(f.hash, []);
      byHash.get(f.hash).push(f);
    } else {
      noHash.push(f);
    }
  }

  // Trenne: Cluster (2+ mit gleichem Hash) vs Einzigartige
  const clusters = [];
  const unique = [...noHash];
  for (const [hash, group] of byHash) {
    if (group.length >= 2) {
      clusters.push(group);
    } else {
      unique.push(group[0]);
    }
  }

  // Wenn keine Cluster gefunden → keine Sub-Gruppierung nötig
  if (clusters.length === 0) return null;

  let html = '';
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

  for (let ci = 0; ci < clusters.length; ci++) {
    const cluster = clusters[ci];
    const letter = letters[ci] || (ci + 1);
    const size = cluster[0].size_h || '?';
    html += `<div style="margin:8px 0 4px 0;padding:8px 12px;background:#0a2010;border:1px solid #22c55e40;border-left:3px solid #22c55e;border-radius:8px;">
      <div style="font-size:13px;font-weight:bold;color:#86efac;margin-bottom:4px;">
        🔗 Cluster ${esc(String(letter))} — ${cluster.length}× identisch (je ${esc(size)})
        <span class="pill" style="background:#14532d;color:#86efac;font-size:11px;">Behalte 1, lösche ${cluster.length - 1}</span>
      </div>
      ${cluster.map(f => renderFileRow(f, gi)).join('')}
    </div>`;
  }

  if (unique.length > 0) {
    html += `<div style="margin:8px 0 4px 0;padding:8px 12px;background:#1e1b4b40;border:1px solid #8b5cf640;border-left:3px solid #8b5cf6;border-radius:8px;">
      <div style="font-size:13px;font-weight:bold;color:#c4b5fd;margin-bottom:4px;">
        ✨ Einzigartig — ${unique.length} Datei(en)
        <span class="pill" style="background:#312e81;color:#c4b5fd;font-size:11px;">Manuell prüfen</span>
      </div>
      ${unique.map(f => renderFileRow(f, gi)).join('')}
    </div>`;
  }

  return html;
}

function fmtGroupHeader(g) {
  const t = g.type === 'name' ? 'Name' : g.type === 'similar' ? 'Ähnlich' : 'Inhalt';
  const count = g.files.length;
  const per = g.size_each ? ('je ~ ' + humanSize(g.size_each)) : '';
  const folders = uniqueCount(g.files.map(f => f.mod_folder || '(Mods-Root)'));

  // Bei ähnlichen Gruppen: Versions-Info anzeigen
  let versionHint = '';
  let deepHint = '';
  if (g.type === 'similar') {
    const versions = g.files.map(f => f.version || '').filter(v => v);
    if (versions.length > 0) {
      versionHint = `<span class="pill" style="background:#1e3a5f;color:#60a5fa;">Versionen: ${versions.map(v => esc(v)).join(', ')}</span>`;
    }
    // Deep comparison badge
    if (g.deep_comparison) {
      const dc = g.deep_comparison;
      const icon = dc.recommendation === 'update' ? '⬆️' : dc.recommendation === 'different' ? '✅' : '❓';
      deepHint = `<span class="pill" style="background:${dc.recommendation_color}20;color:${dc.recommendation_color};border:1px solid ${dc.recommendation_color};">
        ${icon} ${dc.overlap_pct}% Überlappung</span>`;
    }
  }

  // Kategorie-Badge aus Gruppen-Info
  let catBadge = '';
  if (g.group_category) {
    let cs = 'background:#1e293b;color:#94a3b8;';
    const gc = g.group_category;
    if (gc.includes('Haare')) cs = 'background:#7c3aed33;color:#c084fc;border:1px solid #7c3aed;font-weight:bold;';
    else if (gc.includes('Make-Up')) cs = 'background:#ec489922;color:#f472b6;border:1px solid #ec4899;';
    else if (gc.includes('Accessoire')) cs = 'background:#f59e0b22;color:#fbbf24;border:1px solid #f59e0b;';
    else if (gc.includes('Kleidung')) cs = 'background:#06b6d422;color:#22d3ee;border:1px solid #06b6d4;';
    catBadge = `<span class="pill" style="${cs}font-size:11px;">${esc(gc)}</span>`;
  }

  return `<span><b>${esc(g.key_short)}</b>
    <span class="pill" style="${g.type === 'similar' ? 'background:#1e3a5f;color:#60a5fa;' : ''}">${t}</span>
    <span class="pill">${count} Dateien</span>
    <span class="pill">${folders} Ordner</span>
    ${per ? `<span class="pill">${esc(per)}</span>` : ''}
    ${catBadge}
    ${versionHint}
    ${deepHint}
  </span>`;
}

function removeRowsForPath(path) {
  document.querySelectorAll('button[data-path]').forEach(btn => {
    if (btn.dataset.path === path) {
      const fileDiv = btn.closest('.file');
      if (fileDiv) fileDiv.remove();
    }
  });
  // also unselect checkbox
  document.querySelectorAll('input.sel[data-path]').forEach(cb => {
    if (cb.dataset.path === path) cb.checked = false;
  });
  selected.delete(path);
  updateSelCount();
}

function preferKeepPath(files) {
  // Prefer Ordner 1 if enabled, otherwise first.
  const preferOrd1 = document.getElementById('keep_ord1').checked;
  if (!files || files.length === 0) return null;
  if (preferOrd1) {
    const inOrd1 = files.find(f => f.root_index === 1);
    if (inOrd1) return inOrd1.path;
  }
  return files[0].path;
}

function renderDeepInfo(f, gi) {
  if (!f.deep) return '';
  const d = f.deep;

  // Thumbnail
  const thumb = d.thumbnail_b64
    ? `<img src="${d.thumbnail_b64}" class="thumb-clickable" onclick="openCompareGallery(${gi})" style="max-width:72px;max-height:72px;border-radius:6px;border:1px solid #444;margin-right:12px;float:left;background:#1e293b;" title="🖼️ Klicken um alle Bilder der Gruppe zu vergleichen" />`
    : '';

  // Kategorie mit dynamischer Farbe
  let catStyle = 'background:#1e3a5f;color:#60a5fa';
  if (d.category && d.category.includes('Haare')) catStyle = 'background:#7c3aed22;color:#c084fc;border:1px solid #7c3aed';
  else if (d.category && d.category.includes('Make-Up')) catStyle = 'background:#ec489922;color:#f472b6;border:1px solid #ec4899';
  else if (d.category && d.category.includes('Accessoire')) catStyle = 'background:#f59e0b22;color:#fbbf24;border:1px solid #f59e0b';
  else if (d.category && d.category.includes('Kleidung')) catStyle = 'background:#06b6d422;color:#22d3ee;border:1px solid #06b6d4';
  const cat = d.category
    ? `<span class="pill" style="${catStyle};font-size:11px;" title="Automatisch erkannte Mod-Kategorie">${esc(d.category)}</span>`
    : '';

  // Resource count
  const resCount = `<span class="pill" style="background:#1e293b;font-size:11px;" title="Anzahl der Ressourcen in dieser .package">📦 ${d.total_resources} Ressourcen</span>`;

  // Type breakdown pills (top 5)
  const types = Object.entries(d.type_breakdown || {}).slice(0, 5)
    .map(([k, v]) => `<span class="pill" style="background:#1e293b;font-size:11px;" title="Ressource-Typ: ${esc(k)}">${esc(k)}: ${v}</span>`).join(' ');

  // CAS body types mit Kategorie-Farben
  const _btStyle = (b) => {
    const hair = ['Haare','Haarfarbe'];
    const cloth = ['Oberteil','Ganzkörper','Unterteil','Schuhe','Socken','Strumpfhose','Handschuhe'];
    const makeup = ['Make-Up','Lidschatten','Lippenstift','Wimpern','Gesichtsbehaarung','Gesichts-Overlay','Kopf','Körper'];
    const acc = ['Hut','Brille','Halskette','Armband','Ohrringe','Ring','Oberteil-Accessoire','Tattoo','Ohrläppchen','Zähne','Fingernägel','Fußnägel'];
    if (hair.includes(b)) return {bg:'#7c3aed33',fg:'#c084fc',bd:'#7c3aed',icon:'💇 '};
    if (cloth.includes(b)) return {bg:'#0e7490aa',fg:'#67e8f9',bd:'#06b6d4',icon:'👚 '};
    if (makeup.includes(b)) return {bg:'#9d174daa',fg:'#f9a8d4',bd:'#ec4899',icon:'💄 '};
    if (acc.includes(b)) return {bg:'#92400eaa',fg:'#fcd34d',bd:'#f59e0b',icon:'💍 '};
    return {bg:'#4a1942',fg:'#f0abfc',bd:'#7c3aed',icon:''};
  };
  const cas = d.cas_body_types && d.cas_body_types.length
    ? `<div style="margin-top:4px;">👗 <span style="color:#f0abfc;font-size:12px;">Body: ${d.cas_body_types.map(b => {
        const s = _btStyle(b);
        return `<span class="pill" style="background:${s.bg};color:${s.fg};border:1px solid ${s.bd};font-size:11px;font-weight:bold;">${s.icon}${esc(b)}</span>`;
      }).join(' ')}</span></div>`
    : '';

  // Tuning names
  const tuning = d.tuning_names && d.tuning_names.length
    ? `<div style="margin-top:4px;">📝 <span style="font-size:11px;color:#94a3b8;">Tuning: </span>${d.tuning_names.slice(0, 5).map(n => `<code style="font-size:11px;background:#1e293b;padding:1px 5px;border-radius:4px;">${esc(n)}</code>`).join(' ')}</div>`
    : '';

  // Age/Gender badges
  const ageGender = d.age_gender && d.age_gender.length
    ? `<div style="margin-top:4px;">👤 <span style="font-size:11px;color:#94a3b8;">Für: </span>${d.age_gender.map(ag => {
        const isAge = ['Kleinkind','Kind','Teen','Erwachsene','Ältere'].includes(ag);
        const bgCol = isAge ? '#1e3a5f' : '#3b1f5e';
        const fgCol = isAge ? '#93c5fd' : '#d8b4fe';
        return `<span class="pill" style="background:${bgCol};color:${fgCol};font-size:10px;font-weight:bold;">${esc(ag)}</span>`;
      }).join(' ')}</div>`
    : '';

  // Recolor badge
  const recolor = d.is_recolor
    ? `<span class="pill" style="background:#92400e;color:#fde68a;border:1px solid #f59e0b;font-size:10px;margin-left:4px;" title="Kein eigenes Mesh — wahrscheinlich ein Recolor/Retexture">🎨 Recolor</span>`
    : '';

  return `
  <div class="deep-info" style="margin-top:8px;padding:8px 12px;background:#0f172a;border:1px solid #334155;border-radius:8px;font-size:12px;">
    ${thumb}
    <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;">
      ${cat} ${recolor} ${resCount}
    </div>
    <div style="margin-top:4px;display:flex;flex-wrap:wrap;gap:3px;">${types}</div>
    ${cas}
    ${ageGender}
    ${tuning}
    <div style="clear:both;"></div>
  </div>`;
}

function getTrayWarning(path) {
  if (!_trayData || !_trayData.mod_usage) return '';
  // Normalize path for comparison (lowercase + forward slash)
  const np = (path || '').toLowerCase().replace(/\\\\/g, '/');
  for (const [mp, info] of Object.entries(_trayData.mod_usage)) {
    const nmp = mp.toLowerCase().replace(/\\\\/g, '/');
    if (np === nmp || np.endsWith('/' + nmp.split('/').pop())) {
      const names = (info.used_by || []).slice(0, 3).join(', ');
      const more = info.used_count > 3 ? ` +${info.used_count - 3} mehr` : '';
      return `<span class="tray-warning-badge" title="Wird verwendet von: ${esc(names)}${more}">⚠️ ${info.used_count} Sim${info.used_count !== 1 ? 's' : ''} nutzt diesen Mod</span>`;
    }
  }
  return '';
}

function renderFileRow(f, gi) {
  const exists = f.exists ? '' : ' <span class="pill">fehlt</span>';
  const showFull = document.getElementById('show_full').checked;

  const rel = f.rel && f.rel !== f.path ? f.rel : f.path;
  const mainLine = rel ? rel : f.path;
  const fullLine = (rel && showFull)
    ? `<div class="muted small pathline" style="margin-top:4px;"><code>${esc(f.path)}</code></div>`
    : '';

  // Creator badge
  const fname = (f.path || '').split(/[\\/]/).pop();
  const creator = detectCreator(fname);
  const creatorBadge = creator
    ? `<a href="${esc(creator.url)}" target="_blank" rel="noopener" class="pill" style="background:#312e81;color:#a5b4fc;text-decoration:none;cursor:pointer;" title="Mod von ${esc(creator.name)} — Klicken für Website">${creator.icon} ${esc(creator.name)}</a>`
    : '';
  const cfBadge = renderCurseForgeUI(f.path);
  const trayWarn = getTrayWarning(f.path);

  const btns = `
    <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben — du kannst die Datei jederzeit zurückholen">📦 Quarantäne</button>
    <button class="btn" data-act="open_folder" data-path="${esc(f.path)}" title="Öffnet den Ordner im Windows Explorer">📂 Ordner öffnen</button>
    <button class="btn btn-ghost" data-act="copy" data-path="${esc(f.path)}" title="Kopiert den Dateipfad in die Zwischenablage">📋 Pfad kopieren</button>
  `;

  const checked = selected.has(f.path) ? 'checked' : '';

  return `
  <div class="file" data-gi="${gi}">
    <div class="row1">
      <input class="sel selbox" type="checkbox" data-path="${esc(f.path)}" data-gi="${gi}" ${checked}>
      <span class="tag">${esc(f.root_label)}</span>
      <span class="size" title="Dateigröße">${esc(f.size_h || '?')}</span>
      <span class="date" title="Zuletzt geändert — meistens das Datum vom Mod-Ersteller">📅 ${esc(f.mtime || '?')}</span>
      ${creatorBadge}
      ${cfBadge}
      ${trayWarn}
      ${exists}
    </div>
    <div class="pathline" style="margin-top:6px;"><code>${esc(mainLine)}</code></div>
    ${fullLine}
    ${renderDeepInfo(f, gi)}
    ${renderTagsUI(f.path)}
    <div class="flex" style="margin-top:10px;">${btns}</div>
  </div>`;
}

function groupByModFolder(files) {
  const map = new Map();
  for (const f of files) {
    const k = (f.mod_folder || '(Mods-Root)').trim() || '(Mods-Root)';
    if (!map.has(k)) map.set(k, []);
    map.get(k).push(f);
  }
  return Array.from(map.entries()).sort((a,b)=> a[0].localeCompare(b[0]));
}

function isGroupIgnored(g, data) {
  const ignored = data.ignored_groups || [];
  const entry = g.type + '::' + g.key;
  return ignored.includes(entry);
}

function renderGroups(data) {
  const term = document.getElementById('q').value.trim().toLowerCase();
  const showName = document.getElementById('f_name').checked;
  const showContent = document.getElementById('f_content').checked;
  const showSimilar = document.getElementById('f_similar').checked;
  const showIgnored = document.getElementById('f_show_ignored').checked;
  const groupMod = document.getElementById('g_mod').checked;

  const out = [];
  for (let gi = 0; gi < data.groups.length; gi++) {
    const g = data.groups[gi];

    if (g.type === 'name' && !showName) continue;
    if (g.type === 'content' && !showContent) continue;
    if (g.type === 'similar' && !showSimilar) continue;

    const ignored = isGroupIgnored(g, data);
    if (ignored && !showIgnored) continue;

    const hay = (g.type + ' ' + g.key + ' ' + g.key_short + ' ' + g.files.map(x => x.path).join(' '));
    if (!matchesFilters(hay, term)) continue;

    const keepPath = preferKeepPath(g.files);
    const keepHint = keepPath ? `<span class="pill">behalte: ${esc(keepPath.split(/[\\/]/).pop())}</span>` : '';

    let inner = '';
    // Ähnlich-Gruppen: Cluster-Darstellung (identische Dateien sub-gruppieren)
    if (g.type === 'similar' && !groupMod) {
      const clusterHtml = renderClusters(g.files, gi);
      if (clusterHtml) {
        inner = clusterHtml;
      } else {
        inner = g.files.map(f => renderFileRow(f, gi)).join('');
      }
    } else if (groupMod) {
      const grouped = groupByModFolder(g.files);
      for (const [mod, files] of grouped) {
        const roots = [...new Set(files.map(f => f.root_label))].join(', ');
        inner += `<div class="subhead">📦 ${esc(roots)} / ${esc(mod)} <span class="pill">${files.length} Datei(en)</span></div>`;
        inner += files.map(f => renderFileRow(f, gi)).join('');
      }
    } else {
      inner = g.files.map(f => renderFileRow(f, gi)).join('');
    }

    const tools = `
      <div class="flex" style="margin:8px 0 2px 0;">
        <button class="btn" style="background:#1e293b;color:#c084fc;border:1px solid #7c3aed;" onclick="openCompareGallery(${gi})" title="Zeigt alle Vorschaubilder dieser Gruppe nebeneinander zum Vergleichen">🖼️ Bilder vergleichen</button>
        <button class="btn btn-ghost" data-gact="select_all" data-gi="${gi}" title="Setzt bei allen Dateien dieser Gruppe ein Häkchen">✅ Alle markieren</button>
        <button class="btn btn-ghost" data-gact="select_rest" data-gi="${gi}" title="Markiert alle außer der empfohlenen Datei">✅ Rest markieren (1 behalten)</button>
        <button class="btn btn-ok" data-gact="quarantine_rest" data-gi="${gi}" title="Verschiebt alle bis auf die beste Datei sicher in Quarantäne — du kannst sie jederzeit zurückholen">📦 Rest in Quarantäne</button>
        ${ignored
          ? `<button class="btn" style="background:#065f46;color:#6ee7b7;border:1px solid #059669;" data-gact="unignore_group" data-gi="${gi}" data-gkey="${esc(g.key)}" data-gtype="${esc(g.type)}" title="Diese Gruppe wird wieder als potentielles Problem gezählt">↩️ Wieder melden</button>`
          : `<button class="btn" style="background:#1e3a5f;color:#60a5fa;border:1px solid #2563eb;" data-gact="ignore_group" data-gi="${gi}" data-gkey="${esc(g.key)}" data-gtype="${esc(g.type)}" title="Markiert diese Gruppe als 'Ist korrekt' — wird nicht mehr als Problem gezählt">✅ Ist korrekt</button>`
        }
        ${keepHint}
      </div>
    `;

    // Deep comparison bar for similar groups
    let deepCompBar = '';
    if (g.type === 'similar' && g.deep_comparison) {
      const dc = g.deep_comparison;
      const icon = dc.recommendation === 'update' ? '⬆️' : dc.recommendation === 'different' ? '✅' : '❓';
      const recClass = dc.recommendation === 'update' ? 'background:#451a03;border-color:#f59e0b;'
        : dc.recommendation === 'different' ? 'background:#052e16;border-color:#22c55e;'
        : 'background:#1e1b4b;border-color:#8b5cf6;';
      deepCompBar = `
      <div style="margin:8px 0;padding:10px 14px;${recClass}border:1px solid;border-radius:8px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
          <span style="font-size:22px;font-weight:bold;color:${dc.recommendation_color};">${dc.overlap_pct}%</span>
          <span style="color:#9ca3af;font-size:13px;">Überlappung der Resource-Keys (${dc.shared_keys} von ${dc.total_keys} geteilt)</span>
        </div>
        <div style="background:#334155;border-radius:4px;height:8px;overflow:hidden;">
          <div style="background:${dc.recommendation_color};width:${Math.min(dc.overlap_pct,100)}%;height:100%;border-radius:4px;transition:width 0.5s;"></div>
        </div>
        <div style="margin-top:8px;color:${dc.recommendation_color};font-weight:bold;font-size:13px;">
          ${icon} ${esc(dc.recommendation_text)}
        </div>
        <div style="margin-top:4px;color:#9ca3af;font-size:11px;">
          ${dc.recommendation === 'update'
            ? '💡 Die Dateien teilen die meisten Resource-Keys → es handelt sich um dasselbe Item in verschiedenen Versionen.'
            : dc.recommendation === 'different'
            ? '💡 Die Dateien teilen kaum Resource-Keys → es sind verschiedene Items (z.B. verschiedene Kleidungsstücke).'
            : '💡 Teilweise Überlappung — könnte ein Update mit geändertem Inhalt sein, oder ähnliche aber verschiedene Items.'}
        </div>
      </div>`;
    }

    const colorClass = 'color-' + (gi % 6);
    const ignoredClass = ignored ? ' grp-ignored' : '';
    const ignoredBadge = ignored ? '<span class="pill" style="background:#065f46;color:#6ee7b7;border:1px solid #059669;margin-left:6px;">✅ Ignoriert</span>' : '';
    out.push(`<details class="grp ${colorClass}${ignoredClass}">
      <summary>${fmtGroupHeader(g)}${ignoredBadge}</summary>
      <div class="files">${tools}${deepCompBar}${inner}</div>
    </details>`);
  }
  return out.length ? out.join('') : '<p class="muted">Keine Treffer (Filter/Suche?).</p>';
}

function renderSummary(data) {
  const s = data.summary;
  const corruptInfo = s.corrupt_count ? `<br>⚠️ Korrupte .package-Dateien: <b style="color:#ef4444;">${s.corrupt_count}</b>` : '';
  const conflictInfo = s.conflict_count ? `<br>🔀 Ressource-Konflikte: <b style="color:#8b5cf6;">${s.conflict_count}</b> Gruppen` : '';
  const addonInfo = s.addon_count ? `<br>🧩 Addon-Beziehungen: <b style="color:#6ee7b7;">${s.addon_count}</b> (OK — erwartet)` : '';
  const outdatedInfo = s.outdated_count ? `<br>⏰ Vor letztem Patch geändert: <b style="color:#fbbf24;">${s.outdated_count}</b> Mods` : '';
  const skinInfo = s.skin_conflict_count ? `<br>🧑 Skin-Probleme: <b style="color:#ef4444;">${s.skin_conflict_count}</b> (kann Stein-Haut verursachen!)` : '';
  const ignoredGrp = countIgnoredGroups(data);
  const ignoredLabel = ignoredGrp ? ` <span style="color:#6ee7b7;">(${ignoredGrp} ignoriert)</span>` : '';
  return `
    Erstellt: <b>${esc(data.created_at)}</b><br>
    Gruppen: <b>${s.groups_name}</b> Name / <b>${s.groups_content}</b> Inhalt / <b>${s.groups_similar || 0}</b> Ähnlich${ignoredLabel}<br>
    Einträge: <b>${s.entries_total}</b><br>
    Verschwendeter Speicher (identische Duplikate): <b>${esc(s.wasted_h)}</b>
    ${corruptInfo}
    ${conflictInfo}
    ${skinInfo}
    ${addonInfo}
    ${outdatedInfo}
  `;
}

function renderRoots(data) {
  return data.roots.map(r => `<li><b>${esc(r.label)}:</b> <code>${esc(r.path)}</code></li>`).join('');
}

function renderCorrupt(data) {
  const section = document.getElementById('corrupt-section');
  const list = data.corrupt || [];
  if (list.length === 0) {
    document.getElementById('corrupt-summary').innerHTML = '<span style="color:#22c55e;">✅ Keine korrupten Dateien gefunden.</span>';
    document.getElementById('corrupt-list').innerHTML = '';
    return;
  }

  // Zusammenfassung nach Status
  const byStatus = {};
  for (const c of list) {
    byStatus[c.status_label] = (byStatus[c.status_label] || 0) + 1;
  }
  const summaryParts = Object.entries(byStatus).map(([k,v]) => `<b>${v}</b> ${esc(k)}`).join(', ');
  document.getElementById('corrupt-summary').innerHTML = `${list.length} Datei(en) gefunden: ${summaryParts}`;

  const cards = list.map(c => {
    const isWarn = c.status === 'wrong_version';
    const checked = selected.has(c.path) ? 'checked' : '';
    return `<div class="corrupt-card${isWarn ? ' warn' : ''}">
      <div>
        <input class="sel selbox" type="checkbox" data-path="${esc(c.path)}" ${checked} style="margin-right:8px;">
        <span class="corrupt-status ${esc(c.status)}">${esc(c.status_label)}</span>
        <span style="margin-left:8px; font-weight:bold;">${esc(c.rel || c.path)}</span>
        <span class="muted small" style="margin-left:8px;">${esc(c.size_h)} | ${esc(c.mtime)}</span>
        <div class="muted small" style="margin-top:4px;">${esc(c.status_hint)}</div>
        ${renderTagsUI(c.path)}
      </div>
      <div>
        <button class="btn btn-danger" style="font-size:12px;" onclick="doQuarantine('${esc(c.path).replace(/'/g,"\\'")}')">📦 Quarantäne</button>
      </div>
    </div>`;
  }).join('');
  document.getElementById('corrupt-list').innerHTML = cards;
}

function renderAddons(data) {
  const section = document.getElementById('addon-section');
  const list = data.addon_pairs || [];
  if (list.length === 0) {
    document.getElementById('addon-summary').innerHTML = '<span class="muted">Keine Addon-Beziehungen erkannt.</span>';
    document.getElementById('addon-list').innerHTML = '';
    return;
  }

  document.getElementById('addon-summary').innerHTML =
    `<span class="addon-ok">✅ ${list.length} Addon-Paar(e)</span> erkannt — diese gehören zusammen und sind kein Problem.`;

  const cards = list.map((c, i) => {
    const colorClass = 'color-' + (i % 6);

    const fileRows = c.files.map(f => {
      const showFull = document.getElementById('show_full').checked;
      const rel = f.rel && f.rel !== f.path ? f.rel : '';
      const mainLine = rel ? rel : f.path;
      const fullLine = (rel && showFull)
        ? `<div class="muted small pathline" style="margin-top:4px;"><code>${esc(f.path)}</code></div>`
        : '';
      const checked = selected.has(f.path) ? 'checked' : '';
      return `<div class="file" style="padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
        <div class="row1">
          <input class="sel selbox" type="checkbox" data-path="${esc(f.path)}" ${checked}>
          <span class="tag">${esc(f.root_label)}</span>
          <span class="size" title="Dateigröße">${esc(f.size_h || '?')}</span>
          <span class="date" title="Zuletzt geändert — meistens das Datum vom Mod-Ersteller">📅 ${esc(f.mtime || '?')}</span>
        </div>
        <div class="pathline" style="margin-top:4px;"><code>${esc(mainLine)}</code></div>
        ${fullLine}
        ${renderTagsUI(f.path)}
        <div class="flex" style="margin-top:8px;">
          <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben — du kannst die Datei jederzeit zurückholen">📦 Quarantäne</button>
          <button class="btn" data-act="open_folder" data-path="${esc(f.path)}" title="Öffnet den Ordner im Windows Explorer">📂 Ordner öffnen</button>
          <button class="btn btn-ghost" data-act="copy" data-path="${esc(f.path)}" title="Kopiert den Dateipfad in die Zwischenablage">📋 Pfad kopieren</button>
        </div>
      </div>`;
    }).join('');

    const typePills = c.top_types.map(([name, count]) =>
      `<span class="conflict-type-pill">${esc(name)}: ${count}</span>`
    ).join('');

    return `<details class="grp ${colorClass}" style="margin-bottom:8px;">
      <summary style="cursor:pointer;">
        <span class="addon-badge">${c.shared_count} geteilte Keys</span>
        <span class="addon-ok">✅ Addon</span>
        <span class="muted small" style="margin-left:8px;">${c.files.map(f => esc((f.rel||f.path).split(/[\\\\/]/).pop())).join(' ↔ ')}</span>
      </summary>
      <div style="margin-top:8px;">
        <div class="conflict-types" style="margin-bottom:8px;">Geteilte Typen: ${typePills}</div>
        <div class="muted small" style="margin-bottom:8px; color:#6ee7b7;">👍 Diese Dateien gehören zusammen — beide behalten!</div>
        ${fileRows}
      </div>
    </details>`;
  }).join('');
  document.getElementById('addon-list').innerHTML = cards;
}

function renderContainedIn(data) {
  const list = data.contained_in || [];
  if (list.length === 0) {
    document.getElementById('contained-summary').innerHTML = '<span style="color:#22c55e;">\u2705 Keine redundanten Mods gefunden.</span>';
    document.getElementById('contained-list').innerHTML = '';
    return;
  }

  const subsets = list.filter(c => !c.is_variant);
  const variants = list.filter(c => c.is_variant);
  let summaryParts = [];
  if (subsets.length) summaryParts.push(`<b>${subsets.length}</b> in Bundle enthalten`);
  if (variants.length) summaryParts.push(`<b>${variants.length}</b> Mod-Variante(n) (identische Keys)`);
  document.getElementById('contained-summary').innerHTML = summaryParts.join(' · ') + ' erkannt — redundante Mods können entfernt werden.';

  const cards = list.map((c, i) => {
    const colorClass = 'color-' + (i % 6);
    const contained = c.contained;
    const container = c.container;
    const containedName = (contained.rel || contained.path).split(/[\\\\/]/).pop();
    const containerName = (container.rel || container.path).split(/[\\\\/]/).pop();
    const pct = c.container_total > 0 ? Math.round(c.shared_count / c.container_total * 100) : 0;
    const isVariant = c.is_variant || false;

    // Bei Varianten: neuere behalten
    let recommendRemove = contained;
    let recommendKeep = container;
    if (isVariant) {
      // Neueste Datei behalten
      if (contained.mtime > container.mtime) {
        recommendKeep = contained;
        recommendRemove = container;
      }
    }
    const removeName = (recommendRemove.rel || recommendRemove.path).split(/[\\\\/]/).pop();
    const keepName = (recommendKeep.rel || recommendKeep.path).split(/[\\\\/]/).pop();

    const fileRows = c.files.map(f => {
      const showFull = document.getElementById('show_full').checked;
      const rel = f.rel && f.rel !== f.path ? f.rel : '';
      const mainLine = rel ? rel : f.path;
      const fullLine = (rel && showFull)
        ? `<div class="muted small pathline" style="margin-top:4px;"><code>${esc(f.path)}</code></div>`
        : '';
      const checked = selected.has(f.path) ? 'checked' : '';
      const isRemove = f.path === recommendRemove.path;
      return `<div class="file" style="padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
        <div class="row1">
          <input class="sel selbox" type="checkbox" data-path="${esc(f.path)}" ${checked}>
          <span class="tag">${esc(f.root_label)}</span>
          ${isRemove
            ? '<span style="background:#ef4444;color:#fff;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;margin-right:6px;">⚠️ Redundant — entfernen</span>'
            : isVariant
              ? '<span style="background:#60a5fa;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;margin-right:6px;">✅ Neuer — behalten</span>'
              : '<span style="background:#22c55e;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;margin-right:6px;">📦 Bundle — behalten</span>'}
          <span class="size" title="Dateigröße">${esc(f.size_h || '?')}</span>
          <span class="date" title="Zuletzt geändert">📅 ${esc(f.mtime || '?')}</span>
        </div>
        <div class="pathline" style="margin-top:4px;"><code>${esc(mainLine)}</code></div>
        ${fullLine}
        ${renderTagsUI(f.path)}
        <div class="flex" style="margin-top:8px;">
          <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben — du kannst die Datei jederzeit zurückholen">📦 Quarantäne</button>
          <button class="btn" data-act="open_folder" data-path="${esc(f.path)}" title="Öffnet den Ordner im Windows Explorer">📂 Ordner öffnen</button>
          <button class="btn btn-ghost" data-act="copy" data-path="${esc(f.path)}" title="Kopiert den Dateipfad in die Zwischenablage">📋 Pfad kopieren</button>
        </div>
      </div>`;
    }).join('');

    const typePills = c.top_types.map(([name, count]) =>
      `<span class="conflict-type-pill">${esc(name)}: ${count}</span>`
    ).join('');

    const badgeLabel = isVariant ? '🔄 Variante' : '📦 Enthalten';
    const badgeColor = isVariant ? '#60a5fa' : '#f59e0b';
    const borderColor = isVariant ? '#3b82f6' : '#f59e0b';

    const infoBox = isVariant
      ? `<div style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:10px 12px; margin-bottom:10px;">
          <span style="color:#60a5fa; font-weight:bold;">🔄 Gleicher Mod, verschiedene Optionen:</span>
          <span class="muted"> Beide Dateien haben <b>exakt die gleichen ${c.shared_count} Resource-IDs</b> — nur der Inhalt unterscheidet sich leicht (z.B. mit/ohne einer Option). Du brauchst nur <b>eine</b> Variante!</span>
        </div>`
      : `<div style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:10px 12px; margin-bottom:10px;">
          <span style="color:#fbbf24; font-weight:bold;">📦 Subset erkannt:</span>
          <span class="muted"> <b>${esc(containedName)}</b> (${c.shared_count} Ressourcen) ist komplett in <b>${esc(containerName)}</b> (${c.container_total} Ressourcen) enthalten.</span>
        </div>`;

    const recommendation = isVariant
      ? `💡 Empfehlung: <b>${esc(keepName)}</b> behalten (neuster Stand: ${esc(recommendKeep.mtime)}) — die andere Variante entfernen.`
      : `💡 Empfehlung: <b>${esc(removeName)}</b> entfernen — das Bundle enthält alles bereits.`;

    return `<details class="grp ${colorClass}" style="margin-bottom:8px; border-left:3px solid ${borderColor};">
      <summary style="cursor:pointer;">
        <span style="background:${badgeColor};color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;margin-right:6px;">${badgeLabel}</span>
        <span class="conflict-badge">${c.shared_count}${isVariant ? '' : '/' + c.container_total} Keys${isVariant ? ' identisch' : ' (' + pct + '%)'}</span>
        <span class="muted small" style="margin-left:8px;">${isVariant
          ? esc(containedName) + ' ↔ ' + esc(containerName)
          : '<b>' + esc(containedName) + '</b> steckt in <b>' + esc(containerName) + '</b>'}</span>
      </summary>
      <div style="margin-top:8px;">
        ${infoBox}
        <div class="conflict-types" style="margin-bottom:8px;">Geteilte Typen: ${typePills}</div>
        <div class="muted small" style="margin-bottom:8px;">${recommendation}</div>
        <div class="flex" style="margin-bottom:8px;">
          <button class="btn btn-ok" data-act="quarantine" data-path="${esc(recommendRemove.path)}">📦 Redundanten Mod in Quarantäne</button>
        </div>
        ${fileRows}
      </div>
    </details>`;
  }).join('');
  document.getElementById('contained-list').innerHTML = cards;
}

function renderConflicts(data) {
  const section = document.getElementById('conflict-section');
  const list = data.conflicts || [];
  if (list.length === 0) {
    document.getElementById('conflict-summary').innerHTML = '<span style="color:#22c55e;">\u2705 Keine Ressource-Konflikte gefunden.</span>';
    document.getElementById('conflict-list').innerHTML = '';
    return;
  }

  // Vorab prüfen welche Konflikte zusammengehörige Mods sind (→ "Gewollt")
  const listWithRelated = list.map(c => {
    const fnames = c.files.map(f => (f.rel||f.path).split(/[\\\\/]/).pop().replace(/\.[^.]+$/, '').replace(/^[^a-zA-Z0-9]+/, '').toLowerCase());
    let commonPrefix = fnames[0] || '';
    for (let fi = 1; fi < fnames.length; fi++) {
      let j = 0;
      while (j < commonPrefix.length && j < fnames[fi].length && commonPrefix[j] === fnames[fi][j]) j++;
      commonPrefix = commonPrefix.substring(0, j);
    }
    commonPrefix = commonPrefix.replace(/[_\-\s!.+]+$/, '');
    return { ...c, _namesRelated: commonPrefix.length >= 5 };
  });

  const gewolltCount = listWithRelated.filter(c => c._namesRelated).length;
  const highCount = listWithRelated.filter(c => !c._namesRelated && c.severity === 'hoch').length;
  const midCount = listWithRelated.filter(c => !c._namesRelated && c.severity === 'mittel').length;
  const lowCount = listWithRelated.filter(c => !c._namesRelated && c.severity === 'niedrig').length;
  const harmCount = listWithRelated.filter(c => !c._namesRelated && c.severity === 'harmlos').length;
  document.getElementById('conflict-summary').innerHTML =
    `<b>${list.length}</b> Konflikt-Gruppe(n) gefunden: ` +
    (highCount ? `<span style="color:#ef4444;font-weight:bold;">⚠️ ${highCount} kritisch</span> ` : '') +
    (midCount ? `<span style="color:#fbbf24;font-weight:bold;">⚡ ${midCount} mittel</span> ` : '') +
    (lowCount ? `<span style="color:#6ee7b7;font-weight:bold;">✅ ${lowCount} niedrig</span> ` : '') +
    (harmCount ? `<span style="color:#94a3b8;font-weight:bold;">💤 ${harmCount} harmlos</span> ` : '') +
    (gewolltCount ? `<span style="color:#60a5fa;font-weight:bold;">✅ ${gewolltCount} gewollt</span>` : '');

  const cards = list.map((c, i) => {
    const colorClass = 'color-' + (i % 6);

    // Prüfe ob Dateinamen ähnlich sind (gleicher Creator/Mod-Prefix)
    const fnames = c.files.map(f => (f.rel||f.path).split(/[\\\\/]/).pop().replace(/\.[^.]+$/, '').replace(/^[^a-zA-Z0-9]+/, '').toLowerCase());
    let commonPrefix = fnames[0] || '';
    for (let fi = 1; fi < fnames.length; fi++) {
      let j = 0;
      while (j < commonPrefix.length && j < fnames[fi].length && commonPrefix[j] === fnames[fi][j]) j++;
      commonPrefix = commonPrefix.substring(0, j);
    }
    commonPrefix = commonPrefix.replace(/[_\-\s!.+]+$/, '');
    const namesRelated = commonPrefix.length >= 5;

    const relatedHint = '';  // Info wird jetzt direkt im Severity-Badge + Reason angezeigt

    const fileRows = c.files.map(f => {
      const showFull = document.getElementById('show_full').checked;
      const rel = f.rel && f.rel !== f.path ? f.rel : '';
      const mainLine = rel ? rel : f.path;
      const fullLine = (rel && showFull)
        ? `<div class="muted small pathline" style="margin-top:4px;"><code>${esc(f.path)}</code></div>`
        : '';
      const checked = selected.has(f.path) ? 'checked' : '';
      return `<div class="file" style="padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
        <div class="row1">
          <input class="sel selbox" type="checkbox" data-path="${esc(f.path)}" ${checked}>
          <span class="tag">${esc(f.root_label)}</span>
          <span class="size" title="Dateigröße">${esc(f.size_h || '?')}</span>
          <span class="date" title="Zuletzt geändert — meistens das Datum vom Mod-Ersteller">📅 ${esc(f.mtime || '?')}</span>
        </div>
        <div class="pathline" style="margin-top:6px;"><code>${esc(mainLine)}</code></div>
        ${fullLine}
        ${renderTagsUI(f.path)}
        <div class="flex" style="margin-top:10px;">
          <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben — du kannst die Datei jederzeit zurückholen">📦 Quarantäne</button>
          <button class="btn" data-act="open_folder" data-path="${esc(f.path)}" title="Öffnet den Ordner im Windows Explorer">📂 Ordner öffnen</button>
          <button class="btn btn-ghost" data-act="copy" data-path="${esc(f.path)}" title="Kopiert den Dateipfad in die Zwischenablage">📋 Pfad kopieren</button>
        </div>
      </div>`;
    }).join('');

    const typePills = c.top_types.map(([name, count]) =>
      `<span class="conflict-type-pill">${esc(name)}: ${count}</span>`
    ).join('');

    // Empfehlung: neueste behalten
    let newest = c.files[0];
    for (const f of c.files) {
      if (f.mtime > newest.mtime) newest = f;
    }
    const keepName = (newest.rel || newest.path).split(/[\\\\/]/).pop();

    // Schweregrad — bei zusammengehörigen Mods auf "Gewollt" herunterstufen
    const sevColors = {hoch:'#ef4444',mittel:'#fbbf24',niedrig:'#22c55e',harmlos:'#94a3b8',gewollt:'#60a5fa'};
    const sevIcons = {hoch:'⚠️',mittel:'⚡',niedrig:'✅',harmlos:'💤',gewollt:'✅'};
    const sevLabels = {hoch:'Kritisch',mittel:'Mittel',niedrig:'Niedrig',harmlos:'Harmlos',gewollt:'Gewollt'};
    const sev = namesRelated ? 'gewollt' : (c.severity || 'mittel');
    const sevBadge = `<span style="background:${sevColors[sev]||'#94a3b8'};color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;margin-right:6px;">${sevIcons[sev]||'❓'} ${sevLabels[sev]||sev}</span>`;
    const sevReason = namesRelated
      ? `<div class="muted small" style="margin-bottom:6px;color:#60a5fa;">Dateien gehören zusammen (${esc(commonPrefix)}…) — geteilte Ressourcen sind gewollt, kein Handlungsbedarf</div>`
      : (c.severity_reason ? `<div class="muted small" style="margin-bottom:6px;color:${sevColors[sev]||'#94a3b8'};">${esc(c.severity_reason)}</div>` : '');

    // Tuning-Namen
    const tuningNames = (c.tuning_names || []).length > 0
      ? `<div style="margin-bottom:8px;"><span class="muted small">🎯 Betroffene Tunings:</span> ${c.tuning_names.map(n => `<span style="background:#1e293b;border:1px solid #475569;border-radius:4px;padding:1px 6px;font-size:11px;margin:2px;display:inline-block;">${esc(n)}</span>`).join('')}</div>`
      : '';

    return `<details class="grp ${colorClass}" style="margin-bottom:8px;${sev === 'hoch' ? 'border-left:3px solid #ef4444;' : sev === 'niedrig' ? 'border-left:3px solid #22c55e;' : sev === 'harmlos' ? 'border-left:3px solid #64748b;' : sev === 'gewollt' ? 'border-left:3px solid #60a5fa;' : ''}">
      <summary style="cursor:pointer;">
        ${sevBadge}
        <span class="conflict-badge">${c.shared_count} geteilte Keys</span>
        <span class="pill">${c.files.length} Packages</span>
        <span class="muted small" style="margin-left:8px;">${c.files.map(f => esc((f.rel||f.path).split(/[\\\\/]/).pop())).join(' ↔ ')}</span>
      </summary>
      <div style="margin-top:8px;">
        ${sevReason}
        <div class="conflict-types" style="margin-bottom:8px;">Häufigste Typen: ${typePills}</div>
        ${tuningNames}
        ${relatedHint}
        <div class="muted small" style="margin-bottom:8px;">💡 Empfehlung: <b>${esc(keepName)}</b> behalten (neuster Stand: ${esc(newest.mtime)})</div>
        <div class="flex" style="margin-bottom:8px;">
          <button class="btn btn-ok" data-conflict-rest="${i}">📦 Rest in Quarantäne (neueste behalten)</button>
        </div>
        ${fileRows}
      </div>
    </details>`;
  }).join('');
  document.getElementById('conflict-list').innerHTML = cards;

  // Event-Delegation für "Rest in Quarantäne"-Buttons
  document.getElementById('conflict-list').querySelectorAll('[data-conflict-rest]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const ci = parseInt(e.target.dataset.conflictRest);
      const c = list[ci];
      if (!c) return;
      let newest = c.files[0];
      for (const f of c.files) { if (f.mtime > newest.mtime) newest = f; }
      const rest = c.files.filter(f => f.path !== newest.path);
      const keepFile = (newest.rel||newest.path).split(/[\\\\/]/).pop();
      const removeFiles = rest.map(f=>(f.rel||f.path).split(/[\\\\/]/).pop()).join('\\n');
      if (!confirm('📦 ' + rest.length + ' Datei(en) in Quarantäne verschieben?\\n\\nBehalte: ' + keepFile + '\\n\\nEntferne:\\n' + removeFiles)) return;
      for (const f of rest) {
        await doQuarantine(f.path);
      }
    });
  });
}

function renderSkinCheck(data) {
  const list = data.skin_conflicts || [];
  const summaryEl = document.getElementById('skincheck-summary');
  const listEl = document.getElementById('skincheck-list');

  if (list.length === 0) {
    summaryEl.innerHTML = '<span style="color:#22c55e;">✅ Keine Skin/Overlay-Probleme gefunden — alles sauber!</span>';
    listEl.innerHTML = '';
    return;
  }

  const highCount = list.filter(c => c.severity === 'hoch').length;
  const midCount = list.filter(c => c.severity === 'mittel').length;
  const lowCount = list.filter(c => c.severity === 'niedrig').length;
  summaryEl.innerHTML =
    `<b>${list.length}</b> Skin-Problem(e) erkannt: ` +
    (highCount ? `<span style="color:#ef4444;font-weight:bold;">⚠️ ${highCount} kritisch</span> ` : '') +
    (midCount ? `<span style="color:#fbbf24;font-weight:bold;">⚡ ${midCount} mittel</span> ` : '') +
    (lowCount ? `<span style="color:#60a5fa;font-weight:bold;">ℹ️ ${lowCount} Hinweis</span> ` : '');

  const cards = list.map((sc, i) => {
    const sevColors = {hoch:'#ef4444', mittel:'#fbbf24', niedrig:'#60a5fa'};
    const sevIcons = {hoch:'⚠️', mittel:'⚡', niedrig:'ℹ️'};
    const sevLabels = {hoch:'Kritisch', mittel:'Mittel', niedrig:'Hinweis'};
    const cardClass = sc.severity === 'hoch' ? 'skin-card' : sc.severity === 'niedrig' ? 'skin-card skin-info' : 'skin-card skin-warn';
    const sevBadge = `<span class="skin-badge skin-badge-${sc.severity}" style="background:${sevColors[sc.severity]||'#94a3b8'}22;color:${sevColors[sc.severity]||'#94a3b8'};border:1px solid ${sevColors[sc.severity]||'#94a3b8'};">${sevIcons[sc.severity]||'❓'} ${sevLabels[sc.severity]||sc.severity}</span>`;

    // Skin detail reasons
    const detailRows = (sc.skin_details || []).map(sd => {
      const fname = (sd.file.rel || sd.file.path || '').split(/[\\\\/]/).pop();
      const reasons = (sd.reasons || []).map(r => `<span class="skin-reason">${esc(r)}</span>`).join(' ');
      return `<div style="margin:4px 0;"><b style="color:#f0abfc;">${esc(fname)}</b> ${reasons}</div>`;
    }).join('');

    // File rows with actions
    const fileRows = (sc.files || []).map(f => {
      const showFull = document.getElementById('show_full') && document.getElementById('show_full').checked;
      const rel = f.rel && f.rel !== f.path ? f.rel : '';
      const mainLine = rel ? rel : f.path;
      const fullLine = (rel && showFull)
        ? `<div class="muted small pathline" style="margin-top:4px;"><code>${esc(f.path)}</code></div>`
        : '';
      const checked = selected.has(f.path) ? 'checked' : '';

      // Deep info (category, body types)
      let deepInfo = '';
      const d = f.deep || {};
      if (d.category) {
        deepInfo += `<span class="pill" style="background:#1e293b;font-size:11px;">${esc(d.category)}</span> `;
      }
      if (d.cas_body_types && d.cas_body_types.length) {
        deepInfo += d.cas_body_types.map(bt => `<span class="pill" style="background:#4a1942;color:#f0abfc;border:1px solid #7c3aed;font-size:11px;">${esc(bt)}</span>`).join(' ');
      }

      return `<div class="file" style="padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
        <div class="row1">
          <input class="sel selbox" type="checkbox" data-path="${esc(f.path)}" ${checked}>
          <span class="tag">${esc(f.root_label || '')}</span>
          <span class="size">${esc(f.size_h || '?')}</span>
          <span class="date" title="Zuletzt geändert">📅 ${esc(f.mtime || '?')}</span>
        </div>
        <div class="pathline" style="margin-top:6px;"><code>${esc(mainLine)}</code></div>
        ${fullLine}
        ${deepInfo ? `<div style="margin-top:4px;">${deepInfo}</div>` : ''}
        <div class="flex" style="margin-top:10px;">
          <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben">📦 Quarantäne</button>
          <button class="btn" data-act="open_folder" data-path="${esc(f.path)}" title="Ordner im Explorer öffnen">📂 Ordner öffnen</button>
          <button class="btn btn-ghost" data-act="copy" data-path="${esc(f.path)}" title="Pfad kopieren">📋 Pfad kopieren</button>
        </div>
      </div>`;
    }).join('');

    // Type pills (if conflict)
    const typePills = (sc.top_types || []).map(([name, count]) =>
      `<span class="conflict-type-pill">${esc(name)}: ${count}</span>`
    ).join('');

    return `<div class="${cardClass}" style="margin-bottom:10px;">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
        <span style="font-size:22px;">${sc.icon || '🧑'}</span>
        ${sevBadge}
        ${sc.shared_count > 0 ? `<span class="conflict-badge">${sc.shared_count} geteilte Keys</span>` : ''}
        <span class="pill">${(sc.files||[]).length} Datei(en)</span>
      </div>
      <div style="font-weight:bold;color:#fca5a5;margin-bottom:6px;">${esc(sc.label || '')}</div>
      <div class="muted small" style="margin-bottom:8px;">${esc(sc.hint || '')}</div>
      <div style="background:#1e293b;border-radius:8px;padding:8px 12px;margin-bottom:10px;border-left:3px solid #fbbf24;">
        <span style="font-weight:bold;color:#fbbf24;">💡 Empfehlung:</span> <span class="muted">${esc(sc.action || '')}</span>
      </div>
      ${detailRows ? `<div style="background:#1a1325;border-radius:8px;padding:8px 12px;margin-bottom:10px;border:1px solid #4c1d95;"><span style="font-weight:bold;color:#c4b5fd;font-size:12px;">🔍 Skin-Details:</span>${detailRows}</div>` : ''}
      ${typePills ? `<div class="conflict-types" style="margin-bottom:8px;">Geteilte Typen: ${typePills}</div>` : ''}
      ${fileRows}
    </div>`;
  }).join('');

  listEl.innerHTML = cards;
}

function buildPerFileMap(data) {
  // Sammle ALLE Findings pro Dateipfad
  const map = new Map(); // path -> { file, findings: [] }

  function ensure(f) {
    if (!map.has(f.path)) {
      map.set(f.path, { file: f, findings: [] });
    }
    return map.get(f.path);
  }

  // Gruppen (Name/Inhalt/Ähnlich)
  for (const g of (data.groups || [])) {
    const typeLabel = g.type === 'name' ? 'Name-Duplikat' : g.type === 'content' ? 'Inhalt-Duplikat' : 'Ähnlicher Name';
    const typeClass = g.type === 'name' ? 'pf-name-dupe' : g.type === 'content' ? 'pf-content-dupe' : 'pf-similar-dupe';
    const partners = g.files.map(f => f.path);
    for (const f of g.files) {
      const entry = ensure(f);
      entry.findings.push({
        category: 'group',
        type: g.type,
        typeLabel,
        typeClass,
        key: g.key_short,
        sizeEach: g.size_each,
        partners: partners.filter(p => p !== f.path),
        partnerFiles: g.files.filter(x => x.path !== f.path),
      });
    }
  }

  // Korrupte
  for (const c of (data.corrupt || [])) {
    const entry = ensure(c);
    entry.findings.push({
      category: 'corrupt',
      typeLabel: 'Korrupt',
      typeClass: 'pf-corrupt',
      statusLabel: c.status_label,
      statusHint: c.status_hint,
      status: c.status,
    });
  }

  // Addon-Paare
  for (const a of (data.addon_pairs || [])) {
    const partners = a.files.map(f => f.path);
    for (const f of a.files) {
      const entry = ensure(f);
      entry.findings.push({
        category: 'addon',
        typeLabel: 'Addon-Beziehung',
        typeClass: 'pf-addon',
        sharedCount: a.shared_count,
        topTypes: a.top_types,
        partners: partners.filter(p => p !== f.path),
        partnerFiles: a.files.filter(x => x.path !== f.path),
      });
    }
  }

  // Konflikte
  for (const c of (data.conflicts || [])) {
    const partners = c.files.map(f => f.path);
    for (const f of c.files) {
      const entry = ensure(f);
      entry.findings.push({
        category: 'conflict',
        typeLabel: 'Ressource-Konflikt',
        typeClass: 'pf-conflict',
        sharedCount: c.shared_count,
        topTypes: c.top_types,
        partners: partners.filter(p => p !== f.path),
        partnerFiles: c.files.filter(x => x.path !== f.path),
      });
    }
  }

  // Skin-Konflikte
  for (const sc of (data.skin_conflicts || [])) {
    const partners = (sc.files || []).map(f => f.path);
    for (const f of (sc.files || [])) {
      const entry = ensure(f);
      entry.findings.push({
        category: 'skin',
        typeLabel: 'Skin-Konflikt',
        typeClass: 'pf-conflict',
        severity: sc.severity,
        label: sc.label,
        hint: sc.hint,
        partners: partners.filter(p => p !== f.path),
        partnerFiles: (sc.files || []).filter(x => x.path !== f.path),
      });
    }
  }

  return map;
}

function countIgnoredGroups(data) {
  const ignored = data.ignored_groups || [];
  let count = 0;
  for (const g of (data.groups || [])) {
    if (ignored.includes(g.type + '::' + g.key)) count++;
  }
  return count;
}

function updateNavBadges(data) {
  const s = data.summary || {};
  const ignoredCount = countIgnoredGroups(data);
  const groups = (s.groups_name||0) + (s.groups_content||0) + (s.groups_similar||0) - ignoredCount;
  const corrupt = s.corrupt_count || 0;
  const addon = s.addon_count || 0;
  const conflict = s.conflict_count || 0;
  const contained = s.contained_count || 0;
  const outdated = s.outdated_count || 0;
  const deps = s.dependency_count || 0;
  const skinConflicts = s.skin_conflict_count || 0;

  // Tab-Badges aktualisieren
  const dupBadge = document.getElementById('nav-badge-groups');
  dupBadge.textContent = groups;
  dupBadge.classList.toggle('badge-zero', groups === 0);

  const analysisBadge = document.getElementById('nav-badge-analysis');
  const analysisTotal = corrupt + outdated + deps;
  analysisBadge.textContent = analysisTotal;
  analysisBadge.classList.toggle('badge-zero', analysisTotal === 0);

  // Hidden badge spans für Kompatibilität
  document.getElementById('nav-badge-corrupt').textContent = corrupt;
  document.getElementById('nav-badge-addon').textContent = addon;
  document.getElementById('nav-badge-conflict').textContent = conflict;
  document.getElementById('nav-badge-contained').textContent = contained;
  document.getElementById('nav-badge-outdated').textContent = outdated;
  document.getElementById('nav-badge-deps').textContent = deps;

  // Skin-Diagnose Badge
  const skinBadge = document.getElementById('nav-badge-skincheck');
  skinBadge.textContent = skinConflicts;
  skinBadge.classList.toggle('badge-zero', skinConflicts === 0);

  // --- Dashboard-Karten aktualisieren ---
  const totalFiles = s.total_files || 0;
  const wastedMB = s.wasted_h || '';

  // Korrupte
  document.getElementById('dash-corrupt-count').textContent = corrupt;
  document.getElementById('dash-corrupt').classList.toggle('dash-hidden', corrupt === 0);

  // Duplikate
  document.getElementById('dash-dupes-count').textContent = groups;
  const dupeDesc = document.querySelector('#dash-dupes .dash-desc');
  if (groups === 0 && ignoredCount === 0) {
    dupeDesc.innerHTML = '<b style="color:#4ade80;">✅ Keine Duplikate gefunden!</b> Alles sauber.';
    document.getElementById('dash-dupes').className = 'dash-card dash-ok';
  } else if (groups === 0 && ignoredCount > 0) {
    dupeDesc.innerHTML = '<b style="color:#4ade80;">✅ Alle ' + ignoredCount + ' Gruppen als korrekt markiert.</b>';
    document.getElementById('dash-dupes').className = 'dash-card dash-ok';
  } else {
    const ignoredHint = ignoredCount > 0 ? ' <span style="color:#6ee7b7;">(' + ignoredCount + ' ignoriert)</span>' : '';
    dupeDesc.innerHTML = 'Doppelte oder sehr ähnliche Mod-Dateien.' + (wastedMB ? ' <b>' + esc(wastedMB) + ' verschwendet.</b>' : '') + ignoredHint + ' Aufräumen empfohlen.';
  }

  // Konflikte
  document.getElementById('dash-conflicts-count').textContent = conflict;
  document.getElementById('dash-conflicts').classList.toggle('dash-hidden', conflict === 0);

  // Skin-Diagnose
  document.getElementById('dash-skincheck-count').textContent = skinConflicts;
  document.getElementById('dash-skincheck').classList.toggle('dash-hidden', skinConflicts === 0);

  // Enthaltene Mods
  document.getElementById('dash-contained-count').textContent = contained;
  document.getElementById('dash-contained').classList.toggle('dash-hidden', contained === 0);

  // Veraltet
  document.getElementById('dash-outdated-count').textContent = outdated;
  document.getElementById('dash-outdated').classList.toggle('dash-hidden', outdated === 0);

  // Addons
  document.getElementById('dash-addons-count').textContent = addon;
  document.getElementById('dash-addons').classList.toggle('dash-hidden', addon === 0);

  // Fehlende Abhängigkeiten
  const missingDeps = s.missing_dep_count || 0;
  document.getElementById('dash-missingdeps-count').textContent = missingDeps;
  document.getElementById('dash-missingdeps').classList.toggle('dash-hidden', missingDeps === 0);

  // Sonstige Dateien
  const nonmod = s.non_mod_count || 0;
  document.getElementById('nav-badge-nonmod').textContent = nonmod;
  document.getElementById('dash-nonmod-count').textContent = nonmod;
  document.getElementById('dash-nonmod').classList.toggle('dash-hidden', nonmod === 0);

  // Gesamt
  document.getElementById('dash-total-count').textContent = totalFiles;
}

function renderNonModFiles(data) {
  const nonmod = data.non_mod_files || [];
  const byExt = data.non_mod_by_ext || [];
  const section = document.getElementById('nonmod-section');
  const list = document.getElementById('nonmod-list');
  const summary = document.getElementById('nonmod-summary');
  if (!nonmod.length) {
    showConditionalSection('nonmod-section', false);
    return;
  }
  showConditionalSection('nonmod-section', true);
  const totalSize = nonmod.reduce((a, f) => a + (f.size || 0), 0);
  summary.innerHTML = `<b>${nonmod.length}</b> Dateien — ${humanSize(totalSize)} belegt`;
  let html = '';
  // Gruppiert nach Dateityp
  const extIcons = {'.txt':'📝', '.png':'🖼️', '.jpg':'🖼️', '.jpeg':'🖼️', '.gif':'🖼️', '.bmp':'🖼️',
    '.html':'🌐', '.htm':'🌐', '.log':'📋', '.cfg':'⚙️', '.ini':'⚙️', '.json':'📊', '.xml':'📊',
    '.dat':'💾', '.tmbin':'🔧', '.tmcatalog':'🔧', '.mp4':'🎬', '.avi':'🎬', '.mov':'🎬',
    '.mp3':'🎵', '.wav':'🎵', '.pdf':'📕', '.doc':'📕', '.docx':'📕', '.zip':'📦', '.7z':'📦', '.rar':'📦'};
  const extLabels = {'.txt':'Text-Dateien', '.png':'PNG-Bilder', '.jpg':'JPEG-Bilder', '.html':'HTML-Dateien',
    '.htm':'HTML-Dateien', '.log':'Log-Dateien', '.cfg':'Konfiguration', '.ini':'Einstellungen',
    '.json':'JSON-Daten', '.xml':'XML-Daten', '.dat':'Datendateien', '.tmbin':'TurboDriver-Daten',
    '.tmcatalog':'TurboDriver-Katalog', '.mp4':'Videos', '.gif':'GIF-Bilder', '.pdf':'PDF-Dokumente',
    '.7z':'Archive', '.rar':'Archive', '.zip':'Archive'};
  for (const [ext, files] of byExt) {
    const icon = extIcons[ext] || '📄';
    const label = extLabels[ext] || (ext ? ext.toUpperCase().substring(1) + '-Dateien' : 'Ohne Endung');
    const extSize = files.reduce((a, f) => a + (f.size || 0), 0);
    html += `<details style="margin-bottom:6px;"><summary style="cursor:pointer;padding:6px 10px;background:#1e293b;border-radius:6px;border:1px solid #334155;font-size:13px;">`;
    html += `${icon} <b>${esc(label)}</b> <span class="muted">(${files.length} Dateien, ${humanSize(extSize)})</span></summary>`;
    html += `<div style="padding:6px 0 6px 16px;">`;
    for (const f of files) {
      html += `<div style="display:flex;align-items:center;gap:8px;padding:3px 0;font-size:12px;border-bottom:1px solid #1e293b;">`;
      html += `<span style="flex:1;word-break:break-all;" title="${esc(f.path)}">${esc(f.rel || f.name)}</span>`;
      html += `<span class="muted" style="flex-shrink:0;">${esc(f.mod_folder)}</span>`;
      html += `<span class="muted" style="flex-shrink:0;width:70px;text-align:right;">${esc(f.size_h)}</span>`;
      html += `</div>`;
    }
    html += `</div></details>`;
  }
  list.innerHTML = html;
}

const KNOWN_CREATORS = {
  'wickedwhims': {name: 'TURBODRIVER', url: 'https://wickedwhimsmod.com/', icon: '🔞'},
  'wonderfulwhims': {name: 'TURBODRIVER', url: 'https://wonderfulwhims.com/', icon: '💕'},
  'mccc': {name: 'Deaderpool', url: 'https://deaderpool-mccc.com/downloads.html', icon: '🎮'},
  'mc_cmd': {name: 'Deaderpool (MCCC)', url: 'https://deaderpool-mccc.com/downloads.html', icon: '🎮'},
  'littlemssam': {name: 'LittleMsSam', url: 'https://lms-mods.com/', icon: '🌸'},
  'basemental': {name: 'Basemental', url: 'https://basementalcc.com/', icon: '💊'},
  'kawaiistacie': {name: 'KawaiiStacie', url: 'https://www.patreon.com/kawaiistacie', icon: '🌈'},
  'sacrificial': {name: 'Sacrificial', url: 'https://sacrificialmods.com/', icon: '🔪'},
  'kuttoe': {name: 'Kuttoe', url: '', icon: '🏠'},
  'zerbu': {name: 'Zerbu', url: 'https://zerbu.tumblr.com/', icon: '🏗️'},
  'tmex': {name: 'TwistedMexi', url: 'https://twistedmexi.com/', icon: '🔧'},
  'twistedmexi': {name: 'TwistedMexi', url: 'https://twistedmexi.com/', icon: '🔧'},
  'simrealist': {name: 'SimRealist', url: 'https://simrealist.itch.io/', icon: '🏥'},
  'lumpinou': {name: 'Lumpinou', url: 'https://lumpinoumods.com/', icon: '💝'},
  'coldsims': {name: 'ColdSims', url: '', icon: '❄️'},
  'ravasheen': {name: 'Ravasheen', url: 'https://ravasheen.com/', icon: '✨'},
  'ilkavelle': {name: 'IlkaVelle', url: '', icon: '🎨'},
  'simscommunitylib': {name: 'Sims4CommunityLib', url: 'https://github.com/ColonolNutty/Sims4CommunityLibrary', icon: '📚'},
  's4cl': {name: 'Sims4CommunityLib', url: 'https://github.com/ColonolNutty/Sims4CommunityLibrary', icon: '📚'},
  'bienchen': {name: 'Bienchen', url: '', icon: '🐝'},
  'scarletredesign': {name: 'ScarletReDesign', url: '', icon: '🎨'},
  'helaene': {name: 'Helaene', url: '', icon: '✂️'},
  'aretha': {name: 'Aretha', url: '', icon: '👗'},
  'adeepindigo': {name: 'ADeepIndigo', url: '', icon: '🎨'},
  'kiara': {name: 'Kiara Zurk', url: '', icon: '💇'},
  'simpledimples': {name: 'SimpleDimples', url: '', icon: '👶'},
  'arethabee': {name: 'Aretha', url: '', icon: '👗'}
};

// Custom creators (from server, merged at runtime)
let CUSTOM_CREATORS = {};

// CurseForge-Daten (from Overwolf manifest)
let CURSEFORGE_DATA = {};  // normpath -> {name, author, url, has_update, ...}
let _CF_CACHE = {};  // fast lookup cache: short-key -> info

// Vorberechnete Such-Indizes (werden bei Datenänderung neu gebaut)
let _CATEGORY_INDEX = {};   // path -> ['📛 Name-Duplikat', ...]
let _SEARCH_HAY_CACHE = {}; // path -> lowercase haystack string
let _SEARCH_INDEX_DIRTY = true;

// Mod-Notizen & Tags (from server, persistent)
let MOD_NOTES = {};
let MOD_TAGS = {};
const AVAILABLE_TAGS = [
  {name: 'Wichtig', color: '#dc2626', bg: '#7f1d1d'},
  {name: 'Favorit', color: '#f59e0b', bg: '#78350f'},
  {name: 'Testen', color: '#3b82f6', bg: '#1e3a5f'},
  {name: 'CAS/CC', color: '#ec4899', bg: '#831843'},
  {name: 'Build/Buy', color: '#8b5cf6', bg: '#4c1d95'},
  {name: 'Gameplay', color: '#10b981', bg: '#065f46'},
  {name: 'Veraltet', color: '#f97316', bg: '#9a3412'},
  {name: 'Behalten', color: '#22c55e', bg: '#14532d'},
  {name: 'Entfernen', color: '#ef4444', bg: '#7f1d1d'},
  {name: 'Script', color: '#06b6d4', bg: '#164e63'},
];

function detectCreator(filename) {
  const lower = (filename || '').toLowerCase();
  // Custom creators have priority
  for (const [key, info] of Object.entries(CUSTOM_CREATORS)) {
    if (lower.includes(key)) return {...info, custom: true, key};
  }
  for (const [key, info] of Object.entries(KNOWN_CREATORS)) {
    if (lower.includes(key)) return {...info, custom: false, key};
  }
  return null;
}

async function loadCreators() {
  try {
    const r = await fetch('/api/creators?token=' + TOKEN);
    const j = await r.json();
    if (j.ok) CUSTOM_CREATORS = j.creators || {};
  } catch(e) { console.error('[CREATORS]', e); }
  renderCreatorsList();
}

async function loadNotes() {
  try {
    const r = await fetch('/api/notes?token=' + TOKEN);
    const j = await r.json();
    if (j.ok) MOD_NOTES = j.notes || {};
  } catch(e) { console.error('[NOTES]', e); }
}

async function loadTags() {
  try {
    const r = await fetch('/api/tags?token=' + TOKEN);
    const j = await r.json();
    if (j.ok) MOD_TAGS = j.tags || {};
  } catch(e) { console.error('[TAGS]', e); }
}

async function loadCurseForge() {
  try {
    const r = await fetch('/api/curseforge?token=' + TOKEN);
    const j = await r.json();
    if (j.ok) {
      CURSEFORGE_DATA = j.curseforge || {};
      _buildCFCache();
      _SEARCH_INDEX_DIRTY = true;
    }
  } catch(e) { console.error('[CURSEFORGE]', e); }
}

// Baut den CurseForge-Cache (einmal nach loadCurseForge)
function _buildCFCache() {
  _CF_CACHE = {};
  for (const [k, v] of Object.entries(CURSEFORGE_DATA)) {
    _CF_CACHE[k] = v;  // full norm path
    // Kurzschlüssel: letzte 2 Pfad-Teile
    const parts = k.split('\\');
    if (parts.length >= 2) {
      _CF_CACHE[parts.slice(-2).join('\\')] = v;
    }
    // Nur Dateiname als letzter Fallback
    if (parts.length >= 1) {
      const fn = parts[parts.length - 1];
      if (!_CF_CACHE[fn]) _CF_CACHE[fn] = v;  // first-wins für Dateinamen
    }
  }
}

function getCurseForgeInfo(filePath) {
  if (!filePath || !CURSEFORGE_DATA) return null;
  const norm = filePath.replace(/\//g, '\\').toLowerCase();
  // O(1) Lookup: Vollpfad
  if (_CF_CACHE[norm]) return _CF_CACHE[norm];
  // O(1) Lookup: letzte 2 Teile
  const parts = norm.split('\\');
  if (parts.length >= 2) {
    const short = parts.slice(-2).join('\\');
    if (_CF_CACHE[short]) return _CF_CACHE[short];
  }
  // O(1) Lookup: nur Dateiname
  if (parts.length >= 1 && _CF_CACHE[parts[parts.length - 1]]) {
    return _CF_CACHE[parts[parts.length - 1]];
  }
  return null;
}

function renderCurseForgeUI(filePath) {
  const cf = getCurseForgeInfo(filePath);
  if (!cf) return '';
  let badge = `<a href="${esc(cf.url)}" target="_blank" rel="noopener" class="pill" style="background:#f16436;color:#fff;text-decoration:none;cursor:pointer;font-size:10px;" title="Installiert über CurseForge\nMod: ${esc(cf.name)}\nAutor: ${esc(cf.author)}">🔥 CurseForge</a>`;
  if (cf.has_update) {
    badge += ` <span class="pill" style="background:#065f46;color:#22c55e;font-size:10px;cursor:pointer;" title="Update verfügbar!\nNeue Version: ${esc(cf.latest_version || '?')}\nDatei: ${esc(cf.latest_file_name || '?')}" onclick="if(confirm('Update für ${esc(cf.name).replace(/'/g, '\\\'')} öffnen?')) window.open('${esc(cf.url)}', '_blank')">⬆️ Update</span>`;
  }
  return badge;
}

async function saveNote(path, note) {
  try {
    await postAction('save_note', path, {note});
    MOD_NOTES[path] = note;
    if (!note) delete MOD_NOTES[path];
  } catch(e) { console.error('[SAVE_NOTE]', e); }
}

async function addTag(path, tag) {
  try {
    const res = await postAction('add_tag', path, {tag});
    MOD_TAGS[path] = res.tags || [];
  } catch(e) { console.error('[ADD_TAG]', e); }
}

async function removeTag(path, tag) {
  try {
    const res = await postAction('remove_tag', path, {tag});
    MOD_TAGS[path] = res.tags || [];
    if (MOD_TAGS[path].length === 0) delete MOD_TAGS[path];
  } catch(e) { console.error('[REMOVE_TAG]', e); }
}

function renderNotesUI(path) {
  const note = MOD_NOTES[path] || '';
  const hasNote = !!note;
  const safePath = btoa(unescape(encodeURIComponent(path)));
  return `<div class="note-area" data-note-path="${esc(path)}" data-note-b64="${safePath}">
    ${hasNote
      ? `<div class="note-display" onclick="this.style.display='none'; this.nextElementSibling.style.display='block'; this.nextElementSibling.querySelector('textarea').focus();" title="Klicken zum Bearbeiten">
          <span>📝</span><span>${esc(note)}</span>
        </div>
        <div style="display:none;">
          <textarea class="note-input" placeholder="Notiz schreiben…">${esc(note)}</textarea>
          <div class="flex" style="margin-top:4px; gap:4px;">
            <button class="note-btn note-btn-save" data-note-action="save">💾 Speichern</button>
            <button class="note-btn" data-note-action="delete">🗑</button>
            <button class="note-btn" data-note-action="cancel">Abbrechen</button>
          </div>
        </div>`
      : `<button class="note-btn" data-note-action="open" title="Notiz hinzufügen" style="font-size:11px;">📝 Notiz</button>`
    }
  </div>`;
}

function renderTagsUI(path) {
  const fileTags = MOD_TAGS[path] || [];
  const safePath = btoa(unescape(encodeURIComponent(path)));
  let html = '<div class="mod-tags-area" data-tags-path="' + esc(path) + '" data-tags-b64="' + safePath + '">';
  for (const t of fileTags) {
    const def = AVAILABLE_TAGS.find(at => at.name === t) || {color:'#94a3b8', bg:'#334155'};
    html += `<span class="mod-tag-pill" style="background:${def.bg};color:${def.color};">${esc(t)}<span class="tag-remove" data-tag-remove="${esc(t)}">✕</span></span>`;
  }
  html += `<span class="tag-add-btn" data-tag-add="1" title="Tag hinzufügen">🏷️ +</span>`;
  html += '</div>';
  return html;
}

function b64ToPath(b64) {
  return decodeURIComponent(escape(atob(b64)));
}

// Tag-Menü
let _tagMenuEl = null;
function showTagMenu(evt, path) {
  evt.stopPropagation();
  closeTagMenu();
  const existing = MOD_TAGS[path] || [];
  const available = AVAILABLE_TAGS.filter(t => !existing.includes(t.name));
  if (available.length === 0) return;

  const menu = document.createElement('div');
  menu.className = 'tag-menu';
  menu.style.position = 'fixed';
  menu.style.left = evt.clientX + 'px';
  menu.style.top = evt.clientY + 'px';
  for (const t of available) {
    const btn = document.createElement('button');
    btn.className = 'tag-menu-item';
    btn.style.background = t.bg;
    btn.style.color = t.color;
    btn.textContent = t.name;
    btn.onclick = async (e) => {
      e.stopPropagation();
      closeTagMenu();
      await addTag(path, t.name);
      // Re-render tags for this path
      const area = document.querySelector('[data-tags-path="' + CSS.escape(path) + '"]');
      if (area) area.outerHTML = renderTagsUI(path);
    };
    menu.appendChild(btn);
  }
  document.body.appendChild(menu);
  _tagMenuEl = menu;
  // Reposition if off screen
  setTimeout(() => {
    const r = menu.getBoundingClientRect();
    if (r.right > window.innerWidth) menu.style.left = (window.innerWidth - r.width - 8) + 'px';
    if (r.bottom > window.innerHeight) menu.style.top = (window.innerHeight - r.height - 8) + 'px';
  }, 0);
}
function closeTagMenu() {
  if (_tagMenuEl) { _tagMenuEl.remove(); _tagMenuEl = null; }
}
document.addEventListener('click', closeTagMenu);

// Event delegation for tags
document.addEventListener('click', async (ev) => {
  // Tag remove
  const removeBtn = ev.target.closest('[data-tag-remove]');
  if (removeBtn) {
    ev.stopPropagation();
    const area = removeBtn.closest('.mod-tags-area');
    const path = b64ToPath(area.dataset.tagsB64);
    const tag = removeBtn.dataset.tagRemove;
    await removeTag(path, tag);
    area.outerHTML = renderTagsUI(path);
    return;
  }
  // Tag add
  const addBtn = ev.target.closest('[data-tag-add]');
  if (addBtn) {
    const area = addBtn.closest('.mod-tags-area');
    const path = b64ToPath(area.dataset.tagsB64);
    showTagMenu(ev, path);
    return;
  }
  // Note actions
  const noteBtn = ev.target.closest('[data-note-action]');
  if (noteBtn) {
    const action = noteBtn.dataset.noteAction;
    const area = noteBtn.closest('.note-area');
    const path = b64ToPath(area.dataset.noteB64);
    if (action === 'open') {
      area.innerHTML = `
        <textarea class="note-input" placeholder="Notiz schreiben…"></textarea>
        <div class="flex" style="margin-top:4px; gap:4px;">
          <button class="note-btn note-btn-save" data-note-action="save">💾 Speichern</button>
          <button class="note-btn" data-note-action="cancel">Abbrechen</button>
        </div>`;
      area.querySelector('textarea').focus();
    } else if (action === 'save') {
      const ta = area.querySelector('textarea');
      const text = ta.value.trim();
      await saveNote(path, text);
      area.outerHTML = renderNotesUI(path);
    } else if (action === 'delete') {
      await saveNote(path, '');
      area.outerHTML = renderNotesUI(path);
    } else if (action === 'cancel') {
      area.outerHTML = renderNotesUI(path);
    }
    return;
  }
});

function renderCreatorsList() {
  const el = document.getElementById('creators-list');
  const all = {};
  // Built-in first, then custom (custom override if same key)
  for (const [k,v] of Object.entries(KNOWN_CREATORS)) all[k] = {...v, custom: false};
  for (const [k,v] of Object.entries(CUSTOM_CREATORS)) all[k] = {...v, custom: true};

  const sorted = Object.entries(all).sort((a,b) => a[1].name.localeCompare(b[1].name));
  const customCount = Object.keys(CUSTOM_CREATORS).length;
  const totalCount = sorted.length;

  let html = `<div style="margin-bottom:10px;" class="muted">${totalCount} Creator gespeichert (${customCount} eigene, ${totalCount - customCount} vorinstalliert)</div>`;
  html += '<div style="display:flex; flex-wrap:wrap; gap:6px;">';
  for (const [key, info] of sorted) {
    const urlPart = info.url
      ? `<a href="${esc(info.url)}" target="_blank" rel="noopener" style="color:#a5b4fc;text-decoration:underline;font-size:11px; margin-left:4px;" title="${esc(info.url)}">🔗</a>`
      : '';
    const editBtn = `<button class="btn-x" data-edit-creator="${esc(key)}" data-cr-name="${esc(info.name)}" data-cr-url="${esc(info.url||'')}" data-cr-icon="${esc(info.icon||'')}" data-cr-custom="${info.custom}" title="Creator bearbeiten" style="margin-left:2px;background:none;border:none;color:#facc15;cursor:pointer;font-size:12px;padding:0 2px;">✏️</button>`;
    const isOverride = info.custom && KNOWN_CREATORS.hasOwnProperty(key);
    let delBtn = '';
    if (info.custom && !isOverride) {
      delBtn = `<button class="btn-x" data-del-creator="${esc(key)}" title="Eigenen Creator-Link entfernen" style="margin-left:2px;background:none;border:none;color:#f87171;cursor:pointer;font-size:12px;padding:0 2px;">✕</button>`;
    } else if (isOverride) {
      delBtn = `<button class="btn-x" data-del-creator="${esc(key)}" title="Auf Original zurücksetzen" style="margin-left:2px;background:none;border:none;color:#38bdf8;cursor:pointer;font-size:12px;padding:0 2px;">↩️</button>`;
    }
    const bg = info.custom ? '#312e81' : '#1e293b';
    const border = info.custom ? '#6366f1' : '#334155';
    html += `<div style="display:inline-flex;align-items:center;gap:4px;padding:4px 10px;background:${bg};border:1px solid ${border};border-radius:16px;font-size:12px;" title="Muster: ${esc(key)}${info.url ? '\\nURL: ' + esc(info.url) : ''}">
      <span>${info.icon || '🔗'}</span>
      <span style="font-weight:600;">${esc(info.name)}</span>
      <code style="color:#6b7280;font-size:10px;">${esc(key)}</code>
      ${urlPart}${editBtn}${delBtn}
    </div>`;
  }
  html += '</div>';
  el.innerHTML = html;
}

// Form handlers
function openCreatorForm(editKey, name, url, icon) {
  const box = document.getElementById('creator-form-box');
  const title = document.getElementById('creator-form-title');
  const keyInput = document.getElementById('cr_key');
  const editMode = document.getElementById('cr_edit_mode');
  if (editKey) {
    title.textContent = '✏️ Creator bearbeiten: ' + editKey;
    keyInput.value = editKey;
    keyInput.readOnly = true;
    keyInput.style.opacity = '0.6';
    document.getElementById('cr_name').value = name || '';
    document.getElementById('cr_url').value = url || '';
    document.getElementById('cr_icon').value = icon || '';
    editMode.value = editKey;
  } else {
    title.textContent = '➕ Neuen Creator hinzufügen';
    keyInput.value = '';
    keyInput.readOnly = false;
    keyInput.style.opacity = '1';
    document.getElementById('cr_name').value = '';
    document.getElementById('cr_url').value = '';
    document.getElementById('cr_icon').value = '';
    editMode.value = '';
  }
  box.style.display = '';
  box.scrollIntoView({behavior:'smooth', block:'nearest'});
}

document.getElementById('btn_toggle_creator_form').addEventListener('click', () => {
  const box = document.getElementById('creator-form-box');
  if (box.style.display !== 'none') { box.style.display = 'none'; return; }
  openCreatorForm(null);
});
document.getElementById('btn_cancel_creator').addEventListener('click', () => {
  document.getElementById('creator-form-box').style.display = 'none';
});
document.getElementById('btn_save_creator').addEventListener('click', async () => {
  const key = document.getElementById('cr_key').value.trim().toLowerCase();
  const cname = document.getElementById('cr_name').value.trim();
  const curl = document.getElementById('cr_url').value.trim();
  const cicon = document.getElementById('cr_icon').value.trim() || '🔗';
  const editMode = document.getElementById('cr_edit_mode').value;
  if (!key || !cname) { alert('Bitte Muster und Creator-Name ausfüllen!'); return; }
  const act = editMode ? 'edit_creator' : 'add_creator';
  try {
    const r = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({token: TOKEN, action: act, key, cname, curl, cicon})
    });
    const j = await r.json();
    if (j.ok) {
      document.getElementById('cr_key').value = '';
      document.getElementById('cr_key').readOnly = false;
      document.getElementById('cr_key').style.opacity = '1';
      document.getElementById('cr_name').value = '';
      document.getElementById('cr_url').value = '';
      document.getElementById('cr_icon').value = '';
      document.getElementById('cr_edit_mode').value = '';
      document.getElementById('creator-form-box').style.display = 'none';
      await loadCreators();
      // Refresh file cards to show new badges
      if (window.__DATA) {
        document.getElementById('groups').innerHTML = renderGroups(window.__DATA);
      }
    } else { showToast(j.error || 'unbekannt', 'error'); }
  } catch(e) { showToast(e.message, 'error'); }
});

// Edit creator (event delegation)
document.addEventListener('click', (ev) => {
  const btn = ev.target.closest('[data-edit-creator]');
  if (!btn) return;
  const key = btn.dataset.editCreator;
  const name = btn.dataset.crName;
  const url = btn.dataset.crUrl;
  const icon = btn.dataset.crIcon;
  openCreatorForm(key, name, url, icon);
});

// Delete custom creator (event delegation)
document.addEventListener('click', async (ev) => {
  const btn = ev.target.closest('[data-del-creator]');
  if (!btn) return;
  const key = btn.dataset.delCreator;
  const isOverride = KNOWN_CREATORS.hasOwnProperty(key);
  const msg = isOverride
    ? `"${key}" auf den vorinstallierten Original-Wert zurücksetzen?`
    : `Creator-Link "${key}" wirklich entfernen?`;
  if (!confirm(msg)) return;
  try {
    const r = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({token: TOKEN, action: 'delete_creator', key})
    });
    const j = await r.json();
    if (j.ok) {
      await loadCreators();
      if (window.__DATA) {
        document.getElementById('groups').innerHTML = renderGroups(window.__DATA);
      }
    }
  } catch(e) { showToast(e.message, 'error'); }
});

function _buildSearchIndex(data) {
  if (!data) return;
  // 1. Kategorie-Index: path -> [Kategorie-Labels]
  _CATEGORY_INDEX = {};
  for (const g of (data.groups||[])) {
    const label = g.type === 'name' ? '📛 Name-Duplikat' : g.type === 'content' ? '📦 Inhalt-Duplikat' : '🔤 Ähnlich';
    for (const gf of (g.files||[])) {
      if (!_CATEGORY_INDEX[gf.path]) _CATEGORY_INDEX[gf.path] = [];
      _CATEGORY_INDEX[gf.path].push(label);
    }
  }
  for (const c of (data.corrupt||[])) {
    if (!_CATEGORY_INDEX[c.path]) _CATEGORY_INDEX[c.path] = [];
    _CATEGORY_INDEX[c.path].push('💀 Korrupt');
  }
  for (const conf of (data.conflicts||[])) {
    for (const cf2 of (conf.files||[])) {
      if (!_CATEGORY_INDEX[cf2.path]) _CATEGORY_INDEX[cf2.path] = [];
      _CATEGORY_INDEX[cf2.path].push('⚔️ Konflikt');
    }
  }
  for (const ap of (data.addon_pairs||[])) {
    for (const af of (ap.files||[])) {
      if (!_CATEGORY_INDEX[af.path]) _CATEGORY_INDEX[af.path] = [];
      _CATEGORY_INDEX[af.path].push('🧩 Addon');
    }
  }
  // 2. Haystack-Cache: path -> suchbarer String
  _SEARCH_HAY_CACHE = {};
  const allFiles = collectAllUniqueFiles(data);
  for (const f of allFiles) {
    const fpath = f.path || '';
    const fname = fpath.split(/[\\\\/]/).pop().toLowerCase();
    const ftags = MOD_TAGS[fpath] || [];
    const fnote = MOD_NOTES[fpath] || '';
    const cfInfo = getCurseForgeInfo(fpath);
    _SEARCH_HAY_CACHE[fpath] = (fname + ' ' + (f.rel||'') + ' ' + (f.mod_folder||'') + ' ' + ftags.join(' ') + ' ' + fnote + ' ' + (cfInfo ? cfInfo.name + ' ' + cfInfo.author : '')).toLowerCase();
  }
  _SEARCH_INDEX_DIRTY = false;
}

let _globalSearchTimer = null;
document.getElementById('global-search').addEventListener('input', function() {
  clearTimeout(_globalSearchTimer);
  _globalSearchTimer = setTimeout(globalSearch, 300);
});
document.getElementById('global-search').addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { this.value = ''; globalSearch(); }
});

function globalSearch() {
  const term = (document.getElementById('global-search').value || '').trim().toLowerCase();
  const resultsDiv = document.getElementById('global-search-results');
  const countSpan = document.getElementById('global-search-count');

  if (!term || term.length < 2) {
    resultsDiv.style.display = 'none';
    resultsDiv.innerHTML = '';
    countSpan.textContent = '';
    return;
  }

  const data = window.__DATA;
  if (!data) { countSpan.textContent = 'Kein Scan geladen'; return; }

  // Index bei Bedarf einmal aufbauen
  if (_SEARCH_INDEX_DIRTY) _buildSearchIndex(data);

  const results = [];
  const MAX = 100;
  const allFiles = collectAllUniqueFiles(data);

  for (const f of allFiles) {
    if (results.length >= MAX) break;
    const fpath = f.path || '';
    // O(1) Haystack-Lookup statt Neuberechnung
    const hay = _SEARCH_HAY_CACHE[fpath] || '';
    if (!hay.includes(term)) continue;
    // O(1) Kategorie-Lookup statt verschachtelte Schleifen
    const cats = _CATEGORY_INDEX[fpath] || ['✅ OK'];
    results.push({file: f, categories: cats, cfInfo: getCurseForgeInfo(fpath)});
  }

  countSpan.textContent = results.length >= MAX ? `${MAX}+ Treffer` : `${results.length} Treffer`;

  if (results.length === 0) {
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<div class="muted" style="padding:12px;">Keine Treffer gefunden.</div>';
    return;
  }

  const html = results.map(r => {
    const f = r.file;
    const fpath = f.path || '';
    const fname = fpath.split(/[\\\\/]/).pop();
    const creator = detectCreator(fname);
    const creatorBadge = creator ? `<span class="pill" style="background:#312e81;color:#a5b4fc;font-size:10px;">${creator.icon} ${esc(creator.name)}</span>` : '';
    const cfBadge = r.cfInfo ? renderCurseForgeUI(fpath) : '';
    const catBadges = r.categories.map(c => `<span class="pill" style="font-size:10px;">${c}</span>`).join('');
    const tagBadges = (MOD_TAGS[fpath]||[]).map(t => {
      const td = AVAILABLE_TAGS.find(x => x.name === t);
      return td ? `<span class="pill" style="background:${td.bg};color:${td.color};font-size:10px;">${t}</span>` : '';
    }).join('');
    const note = MOD_NOTES[fpath];
    const noteSnippet = note ? `<span class="muted small" style="margin-left:8px;">📝 ${esc(note.substring(0,60))}${note.length>60?'…':''}</span>` : '';

    return `<div style="padding:8px 12px;background:#0f172a;border:1px solid #1e293b;border-radius:8px;margin-bottom:4px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
      <span style="font-weight:bold;font-size:12px;max-width:35%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${esc(fpath)}">${esc(fname)}</span>
      <span class="muted small">${esc(f.size_h||'?')}</span>
      ${catBadges}
      ${creatorBadge}
      ${cfBadge}
      ${tagBadges}
      ${noteSnippet}
      <span class="muted small" style="margin-left:auto;">${esc(f.mod_folder||'')}</span>
      <button class="btn btn-ghost" style="font-size:10px;padding:2px 6px;" data-act="open_folder" data-path="${esc(fpath)}">📂</button>
      <button class="btn btn-ghost" style="font-size:10px;padding:2px 6px;" data-act="copy" data-path="${esc(fpath)}">📋</button>
    </div>`;
  }).join('');

  resultsDiv.style.display = 'block';
  resultsDiv.innerHTML = html;
}

// Initial load
loadCreators();
loadNotes();
loadTags();
loadCurseForge();

const TUTORIAL_STEPS = [
  {icon:'🎮',title:'Willkommen beim Sims 4 Mod-Scanner!',body:'<b>Schön, dass du da bist!</b> Dieses Tool hilft dir, deine Mods-Sammlung sauber und organisiert zu halten.<br><br>Klicke <b>Weiter</b>, um die <b>interaktive Tour</b> zu starten — wir zeigen dir alles Schritt für Schritt!<br><br><b>💡 Tipp:</b> Du kannst das Tutorial jederzeit über den <b>❓ Tutorial</b>-Button erneut starten.',target:null,tab:null},
  {icon:'🧭',title:'Die Tab-Navigation',body:'Das ist die <b>Tab-Leiste</b>. Hier findest du <b>alle 30 Bereiche</b> des Scanners — von Duplikaten über Fehler-Analyse bis zur Cheat-Konsole.<br><br>Die <b>Badges</b> hinter den Tabs zeigen die Anzahl der Funde an.',target:'#section-nav',tab:'dashboard'},
  {icon:'🏠',title:'Das Dashboard',body:'Das <b>Dashboard</b> ist dein Startpunkt:<br><ul><li>💀 Korrupte Dateien</li><li>📂 Duplikate</li><li>⚔️ Konflikte</li><li>🧑 Skin-Probleme</li><li>📋 Fehler-Logs</li></ul>Klicke auf eine <b>Karte</b> um direkt zum passenden Tab zu springen!',target:'#dashboard',tab:'dashboard'},
  {icon:'📂',title:'Tab: Duplikate',body:'Hier findest du doppelte Dateien:<br><ul><li><b>📦 Inhalt-Duplikate</b> — 100% identische Kopien</li><li><b>📛 Name-Duplikate</b> — Gleicher Name, verschiedene Ordner</li><li><b>🔤 Ähnliche Namen</b> — Verschiedene Versionen</li></ul>Setze <b>Häkchen ☑️</b> bei Dateien die du entfernen willst.',target:'#nav-groups',tab:'dashboard'},
  {icon:'⚔️',title:'Konflikte & Schweregrade',body:'Konflikte werden nach <b>Schweregrad</b> markiert:<br><br><span style="background:#ef4444;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;">⚠️ Kritisch</span> <span style="color:#ef4444;">3+ Tuning-Ressourcen</span><br><span style="background:#fbbf24;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;">⚡ Mittel</span> <span style="color:#fbbf24;">CAS/Sim-Data</span><br><span style="background:#22c55e;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;">✅ Niedrig</span> <span style="color:#22c55e;">Texturen/Meshes</span><br><span style="background:#94a3b8;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;">💤 Harmlos</span> <span style="color:#94a3b8;">Einzelne Assets</span>',target:'#nav-conflicts',tab:'dashboard'},
  {icon:'🧑',title:'Skin-Diagnose',body:'Hilft beim berüchtigten <b>Stein-Haut-Bug</b>!<br><ul><li>Welche Skin-Mods die <b>gleichen CAS-Part-IDs</b> verwenden</li><li>Welche <b>Overlay-Mods sich überschreiben</b></li><li>Ob ein Skin-Recolor <b>ohne Basis-Mod</b> installiert ist</li></ul><b>💡 Lösung:</b> Nur EINEN Skin-/Overlay-Mod pro Typ behalten!',target:'#nav-skincheck',tab:'dashboard'},
  {icon:'⏰',title:'Analyse-Tabs',body:'Die tiefere Analyse deiner Mods:<br><ul><li><b>⏰ Veraltet</b> — Vor dem letzten Patch erstellt</li><li><b>🔗 Abhängigkeiten</b> — Welche Mods Voraussetzungen brauchen</li><li><b>📋 Fehler</b> — Tiefenanalyse aller Fehlerlogs mit Mod-Erkennung &amp; BetterExceptions</li></ul>',target:'#nav-errors',tab:'dashboard'},
  {icon:'🎭',title:'Tray, Galerie & Savegames',body:'Deine gespeicherten Inhalte:<br><ul><li><b>🎭 Tray</b> — Mod-Abhängigkeiten deiner Sims/Häuser</li><li><b>🖼️ CC-Galerie</b> — Custom Content Vorschaubilder</li><li><b>💾 Savegames</b> — Spielstand-Analyse</li></ul>⚠️ Bei Mod-Löschung wirst du <b>gewarnt</b> wenn ein Sim den Mod nutzt!',target:'#nav-tray',tab:'dashboard'},
  {icon:'⚡',title:'Aktionen & Quarantäne',body:'Für jede Datei stehen Aktionen bereit:<br><ul><li><b>📦 Quarantäne</b> — Verschiebt sicher (rückgängig machbar!)</li><li><b>📂 Öffnen</b> — Zeigt den Ordner im Explorer</li></ul><b>🛡️ Es wird niemals sofort gelöscht!</b> Alles geht zuerst in die Quarantäne.',target:'#nav-quarantine',tab:'dashboard'},
  {icon:'🛠',title:'Werkzeug-Tabs',body:'Praktische Werkzeuge:<br><ul><li><b>📥 Import</b> — Neue Mods importieren</li><li><b>🗃️ Quarantäne</b> — Verschobene Dateien verwalten</li><li><b>⚡ Batch</b> — Alle markierten auf einmal verarbeiten</li><li><b>📜 Log</b> — Alle Aktionen nachverfolgen</li></ul>',target:'#nav-import',tab:'dashboard'},
  {icon:'🔎',title:'Globale Suche',body:'Die <b>Globale Suche</b> durchsucht <b>ALLES</b> auf einmal:<br><ul><li>Dateinamen und Pfade</li><li>Notizen und Tags</li><li>Creator-Informationen</li><li>CurseForge-Daten</li></ul>Einfach eintippen — die Ergebnisse erscheinen sofort!',target:'#global-search-box',tab:'dashboard'},
  {icon:'🏷️',title:'Notizen & Tags',body:'Du kannst zu jeder Mod <b>persönliche Notizen</b> und <b>Tags</b> hinzufügen:<br><br><b>📝 Notizen</b> — Freitext, z.B. "Funktioniert super mit XY Mod"<br><b>🏷️ Tags</b> — Labels wie "Favorit", "Testen", "Behalten"<br><br>Alles wird gespeichert und überlebt Rescans!',target:null,tab:null},
  {icon:'🛡️',title:'Sicherheit & Pflege',body:'Tabs für die Pflege deiner Mods:<br><ul><li><b>🛡️ Script-Check</b> — Scripts auf Risiken prüfen</li><li><b>🔧 CC-Check</b> — Kaputtes CC finden</li><li><b>❤️ Save-Health</b> — Spielstand-Gesundheit</li><li><b>🗑️ Cache</b> — Cache bereinigen</li><li><b>🗂️ Tray-Cleaner</b> — Verwaiste Tray-Dateien</li><li><b>💼 Backup</b> — Mods-Ordner sichern</li><li><b>📏 Speicherplatz</b> — Speicherverbrauch</li></ul>',target:'#nav-group-maintenance',tab:'dashboard'},
  {icon:'📦',title:'Package-Browser',body:'Im <b>📦 Package-Browser</b> schaust du <b>in deine Mod-Dateien hinein</b>:<br><ul><li>Durchsuchbare Liste aller .package-Dateien</li><li>Zeigt was drin steckt — Kleidung, Möbel, Haare…</li><li>Erkennt <b>Ressource-Typen</b> (CAS Parts, Objekte, Tuning…)</li></ul>Perfekt um unbekannte Mods zu identifizieren!',target:'#nav-packages',tab:'dashboard'},
  {icon:'📚',title:'Verlauf & Statistik',body:'<b>📚 Verlauf:</b><br><ul><li><b>📸 Mod-Snapshot</b> — Ein Foto deiner Sammlung pro Scan</li><li><b>📊 Verlaufs-Diagramm</b> — Entwicklung über Zeit</li></ul><b>📊 Statistik / 👤 Creators / 📁 Alle Mods:</b><br><ul><li>Gesamtzahlen und Analyse</li><li>Mod-Ersteller verwalten</li></ul>',target:'#nav-history',tab:'dashboard'},
  {icon:'🎮',title:'Cheat-Konsole',body:'Dein <b>Nachschlagewerk für alle Sims 4 Cheats</b>!<br><ul><li><b>Durchsuchbar</b> — Tippe z.B. "Geld" oder "Karriere" ein</li><li><b>Nach Kategorien</b> sortiert</li><li><b>Ein-Klick kopieren</b> — Im Spiel mit <kbd>Strg+V</kbd> einfügen</li><li><b>⭐ Favoriten</b> — Deine Lieblings-Cheats merken</li></ul><b>💡</b> Cheat-Konsole im Spiel: <kbd>Strg</kbd>+<kbd>Shift</kbd>+<kbd>C</kbd>',target:'#nav-cheats',tab:'cheats'},
  {icon:'🎉',title:'Fertig! Viel Spaß!',body:'Du kennst jetzt alle <b>wichtigen Funktionen</b>!<br><br><b>Noch ein paar Tipps:</b><ul><li>Der <b>🔄 Auto-Watcher</b> erkennt Änderungen automatisch</li><li>Erstelle <b>Creator-Verknüpfungen</b> unter <b>👤 Creators</b></li><li>Nutze den <b>📥 Import</b>-Tab für neue Mods</li><li>Die <b>🎮 Cheat-Konsole</b> hilft beim Testen</li></ul><b>🎮 Happy Simming!</b>',target:null,tab:'dashboard'}
];

let tutorialStep = 0;
let _tutRafId = null;

function renderTutorialStep() {
  const step = TUTORIAL_STEPS[tutorialStep];
  const tooltip = document.getElementById('tutorial-tooltip');
  const spotlight = document.getElementById('tutorial-spotlight');

  // Fill content
  document.getElementById('tut-step-icon').textContent = step.icon;
  document.getElementById('tut-step-title').textContent = step.title;
  document.getElementById('tut-step-body').innerHTML = step.body;

  // Progress bar
  const pct = Math.round((tutorialStep / (TUTORIAL_STEPS.length - 1)) * 100);
  document.getElementById('tut-progress-fill').style.width = pct + '%';
  document.getElementById('tut-progress-text').textContent = (tutorialStep + 1) + ' / ' + TUTORIAL_STEPS.length;

  // Buttons
  document.getElementById('tut-btn-prev').style.display = tutorialStep === 0 ? 'none' : '';
  const isLast = tutorialStep === TUTORIAL_STEPS.length - 1;
  document.getElementById('tut-btn-next').textContent = isLast ? '✅ Fertig!' : 'Weiter →';
  document.getElementById('tut-btn-skip').style.display = isLast ? 'none' : '';

  // Switch tab if needed
  if (step.tab) switchTab(step.tab);

  // Position spotlight + tooltip
  positionTutorial();
}

function positionTutorial() {
  const step = TUTORIAL_STEPS[tutorialStep];
  const tooltip = document.getElementById('tutorial-tooltip');
  const spotlight = document.getElementById('tutorial-spotlight');

  if (_tutRafId) { cancelAnimationFrame(_tutRafId); _tutRafId = null; }

  // Reset any previous constrained sizing
  tooltip.style.maxHeight = '';
  tooltip.style.overflowY = '';

  if (!step.target) {
    // Centered modal mode
    spotlight.classList.remove('visible');
    tooltip.classList.remove('pos-mode');
    tooltip.classList.add('center-mode');
    tooltip.style.top = '';
    tooltip.style.left = '';
    return;
  }

  const targetEl = document.querySelector(step.target);
  if (!targetEl) {
    spotlight.classList.remove('visible');
    tooltip.classList.remove('pos-mode');
    tooltip.classList.add('center-mode');
    tooltip.style.top = '';
    tooltip.style.left = '';
    return;
  }

  // Scroll target into view
  targetEl.scrollIntoView({ behavior:'smooth', block:'nearest', inline:'nearest' });

  _tutRafId = requestAnimationFrame(() => {
    setTimeout(() => {
      let rect = targetEl.getBoundingClientRect();
      // display:contents elements have zero-size rects — compute from children
      if (rect.width === 0 && rect.height === 0 && targetEl.children.length > 0) {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (const child of targetEl.children) {
          const cr = child.getBoundingClientRect();
          if (cr.width === 0 && cr.height === 0) continue;
          minX = Math.min(minX, cr.left);
          minY = Math.min(minY, cr.top);
          maxX = Math.max(maxX, cr.right);
          maxY = Math.max(maxY, cr.bottom);
        }
        if (minX !== Infinity) {
          rect = { top: minY, left: minX, right: maxX, bottom: maxY,
                   width: maxX - minX, height: maxY - minY };
        }
      }
      const pad = 10;

      // Position spotlight around target
      spotlight.classList.add('visible');
      spotlight.style.top = (rect.top - pad) + 'px';
      spotlight.style.left = (rect.left - pad) + 'px';
      spotlight.style.width = (rect.width + pad * 2) + 'px';
      spotlight.style.height = (rect.height + pad * 2) + 'px';

      // Position tooltip near target
      tooltip.classList.remove('center-mode');
      tooltip.classList.add('pos-mode');
      tooltip.style.maxHeight = '';

      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const gap = 16;
      const margin = 10;

      // Temporarily remove max-height constraint to measure natural height
      let th = tooltip.offsetHeight;
      let tw = tooltip.offsetWidth;

      let top, left;
      const spaceBelow = vh - rect.bottom - gap - pad - margin;
      const spaceAbove = rect.top - gap - pad - margin;

      if (spaceBelow >= th) {
        // Fits below
        top = rect.bottom + gap + pad;
      } else if (spaceAbove >= th) {
        // Fits above
        top = rect.top - gap - pad - th;
      } else if (spaceBelow >= spaceAbove) {
        // More space below — put there but cap height
        top = rect.bottom + gap + pad;
        const maxH = spaceBelow - 10;
        tooltip.style.maxHeight = maxH + 'px';
        tooltip.style.overflowY = 'auto';
      } else {
        // More space above — put there but cap height
        const maxH = spaceAbove - 10;
        tooltip.style.maxHeight = maxH + 'px';
        tooltip.style.overflowY = 'auto';
        top = margin;
      }

      // Clamp top so tooltip is always visible
      th = tooltip.offsetHeight;
      top = Math.max(margin, Math.min(top, vh - th - margin));

      // Center horizontally on target, clamped to viewport
      left = rect.left + rect.width / 2 - tw / 2;
      left = Math.max(margin, Math.min(left, vw - tw - margin));

      tooltip.style.top = top + 'px';
      tooltip.style.left = left + 'px';
    }, 180);
  });
}

function startTutorial() {
  tutorialStep = 0;
  document.getElementById('tutorial-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';
  renderTutorialStep();
}

function closeTutorial() {
  document.getElementById('tutorial-overlay').classList.remove('active');
  document.getElementById('tutorial-spotlight').classList.remove('visible');
  document.getElementById('tutorial-tooltip').classList.remove('pos-mode');
  document.getElementById('tutorial-tooltip').classList.remove('center-mode');
  document.body.style.overflow = '';
  if (document.getElementById('tut-dont-show').checked) {
    markTutorialSeen();
  }
  switchTab('dashboard');
}

function tutorialNext() {
  if (tutorialStep < TUTORIAL_STEPS.length - 1) {
    tutorialStep++;
    renderTutorialStep();
  } else {
    closeTutorial();
  }
}

function tutorialPrev() {
  if (tutorialStep > 0) {
    tutorialStep--;
    renderTutorialStep();
  }
}

function tutorialGoTo(i) {
  tutorialStep = i;
  renderTutorialStep();
}

async function markTutorialSeen() {
  try {
    await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ token: TOKEN, action: 'mark_tutorial_seen' })
    });
  } catch(e) { console.warn('Tutorial-Status konnte nicht gespeichert werden', e); }
}

async function checkTutorialOnStart() {
  try {
    const r = await fetch('/api/tutorial?token=' + encodeURIComponent(TOKEN));
    const d = await r.json();
    if (d.ok && !d.tutorial_seen) {
      startTutorial();
    }
  } catch(e) { console.warn('Tutorial-Check fehlgeschlagen', e); }
}

// Tutorial keyboard navigation
document.addEventListener('keydown', function(e) {
  const overlay = document.getElementById('tutorial-overlay');
  if (!overlay.classList.contains('active')) return;
  if (e.key === 'ArrowRight' || e.key === 'Enter') { e.preventDefault(); tutorialNext(); }
  if (e.key === 'ArrowLeft') { e.preventDefault(); tutorialPrev(); }
  if (e.key === 'Escape') { e.preventDefault(); closeTutorial(); }
});

// Reposition on window resize
window.addEventListener('resize', function() {
  const overlay = document.getElementById('tutorial-overlay');
  if (overlay && overlay.classList.contains('active') && TUTORIAL_STEPS[tutorialStep] && TUTORIAL_STEPS[tutorialStep].target) {
    positionTutorial();
  }
});

// Check on page load
checkTutorialOnStart();

function openBugReport() {
  document.getElementById('bug-category').value = '';
  document.getElementById('bug-description').value = '';
  document.querySelectorAll('.bug-symptom').forEach(cb => cb.checked = false);
  document.getElementById('bug-status').className = 'bug-status';
  document.getElementById('bug-status').textContent = '';
  document.getElementById('bug-send-btn').disabled = false;
  document.getElementById('bug-send-btn').textContent = '🐛 Absenden';
  document.getElementById('bugreport-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeBugReport() {
  document.getElementById('bugreport-overlay').classList.remove('active');
  document.body.style.overflow = '';
}

async function sendBugReport() {
  const category = document.getElementById('bug-category').value;
  const desc = document.getElementById('bug-description').value.trim();
  const symptoms = [];
  document.querySelectorAll('.bug-symptom:checked').forEach(cb => symptoms.push(cb.value));

  if (!category) {
    document.getElementById('bug-status').className = 'bug-status error';
    document.getElementById('bug-status').textContent = '⚠️ Bitte wähle eine Kategorie aus!';
    return;
  }
  if (symptoms.length === 0 && !desc) {
    document.getElementById('bug-status').className = 'bug-status error';
    document.getElementById('bug-status').textContent = '⚠️ Bitte wähle mindestens ein Symptom oder beschreibe das Problem!';
    return;
  }
  const btn = document.getElementById('bug-send-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Wird gesendet…';
  try {
    const r = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ token: TOKEN, action: 'send_bug_report', category: category, symptoms: symptoms, description: desc })
    });
    const d = await r.json();
    if (d.ok) {
      document.getElementById('bug-status').className = 'bug-status success';
      document.getElementById('bug-status').textContent = '✅ Bug-Report wurde erfolgreich gesendet! Danke für deine Hilfe!';
      setTimeout(() => closeBugReport(), 3000);
    } else {
      document.getElementById('bug-status').className = 'bug-status error';
      document.getElementById('bug-status').textContent = '❌ Fehler: ' + (d.error || 'Unbekannt');
      btn.disabled = false;
      btn.textContent = '🐛 Absenden';
    }
  } catch(e) {
    document.getElementById('bug-status').className = 'bug-status error';
    document.getElementById('bug-status').textContent = '❌ Verbindungsfehler: ' + e.message;
    btn.disabled = false;
    btn.textContent = '🐛 Absenden';
  }
}

// Bug Report Keyboard
document.addEventListener('keydown', function(e) {
  const ov = document.getElementById('bugreport-overlay');
  if (!ov.classList.contains('active')) return;
  if (e.key === 'Escape') { e.preventDefault(); closeBugReport(); }
});

function checkAllOK(data) {
  const s = data.summary || {};
  const groups = (s.groups_name||0) + (s.groups_content||0) + (s.groups_similar||0);
  const errData = window.__errorData || {total:0, hoch:0, mittel:0};
  const hasProblems = groups > 0 || s.corrupt_count > 0 || s.conflict_count > 0 || (s.missing_dep_count||0) > 0 || (s.skin_conflict_count||0) > 0 || errData.hoch > 0;
  showConditionalSection('all-ok-banner', !hasProblems);
  renderHealthScore(data);
}

function renderHealthScore(data) {
  const el = document.getElementById('dash-health-score');
  if (!el) return;
  const s = data.summary || {};
  const total = s.total_files || 0;
  if (total === 0) { el.style.display = 'none'; return; }
  el.style.display = '';

  const corrupt = s.corrupt_count || 0;
  const dupes = (s.groups_content||0);
  const conflicts = s.conflict_count || 0;
  const outdated = s.outdated_count || 0;
  const missingDeps = s.missing_dep_count || 0;
  const contained = s.contained_count || 0;
  const skinConf = s.skin_conflict_count || 0;

  // Fehler-Logs mit einbeziehen
  const errData = window.__errorData || {total:0, hoch:0, mittel:0};
  const errHoch = errData.hoch || 0;
  const errMittel = errData.mittel || 0;

  // Score berechnen (100 = perfekt)
  let score = 100;
  // Korrupte: -10 pro Datei (sehr schlecht)
  score -= corrupt * 10;
  // Fehlende Deps: -8 pro Stück
  score -= missingDeps * 8;
  // Fehler-Logs (schwerwiegend): -7 pro Stück
  score -= errHoch * 7;
  // Fehler-Logs (mittel): -3 pro Stück
  score -= errMittel * 3;
  // Skin-Konflikte: -6 pro Stück (Stein-Haut!)
  score -= skinConf * 6;
  // Inhalt-Duplikate: -3 pro Gruppe
  score -= dupes * 3;
  // Konflikte: -2 pro Stück
  score -= conflicts * 2;
  // Veraltet: -0.5 pro Mod (nicht so schlimm)
  score -= Math.min(outdated * 0.5, 15);
  // Enthaltene: -1 pro Stück
  score -= contained * 1;
  score = Math.max(0, Math.min(100, Math.round(score)));

  // Farbe und Label
  let color, emoji, label;
  if (score >= 90) { color = '#22c55e'; emoji = '🎉'; label = 'Ausgezeichnet!'; }
  else if (score >= 75) { color = '#4ade80'; emoji = '😊'; label = 'Gut!'; }
  else if (score >= 60) { color = '#fbbf24'; emoji = '😐'; label = 'Geht so'; }
  else if (score >= 40) { color = '#f59e0b'; emoji = '😟'; label = 'Solltest du aufräumen'; }
  else { color = '#ef4444'; emoji = '😱'; label = 'Dringend aufräumen!'; }

  // Ring animieren
  const ring = document.getElementById('health-ring');
  const circumference = 2 * Math.PI * 15.9; // ~100
  ring.style.strokeDasharray = circumference;
  ring.style.strokeDashoffset = circumference - (score / 100) * circumference;
  ring.style.stroke = color;

  // Score-Zahl
  const numEl = document.getElementById('health-score-num');
  numEl.textContent = score;
  numEl.style.color = color;

  // Label
  document.getElementById('health-emoji').textContent = emoji;
  document.getElementById('health-label').textContent = label;
  document.getElementById('health-label').style.color = color;

  // Detail-Text
  const problems = [];
  if (corrupt > 0) problems.push(`💀 ${corrupt} korrupte Datei(en)`);
  if (errHoch > 0) problems.push(`📋 ${errHoch} schwere Fehler-Log(s)`);
  if (missingDeps > 0) problems.push(`❌ ${missingDeps} fehlende Abhängigkeit(en)`);
  if (dupes > 0) problems.push(`📂 ${dupes} Inhalt-Duplikat(e)`);
  if (conflicts > 0) problems.push(`⚔️ ${conflicts} Konflikt(e)`);
  if (errMittel > 0) problems.push(`📋 ${errMittel} mittlere Fehler-Log(s)`);
  if (outdated > 0) problems.push(`⏰ ${outdated} veraltete Mod(s)`);
  if (contained > 0) problems.push(`📦 ${contained} redundante Mod(s)`);
  const detailEl = document.getElementById('health-detail');
  if (problems.length === 0) {
    detailEl.innerHTML = '✅ Keine Probleme gefunden — deine Mod-Sammlung ist sauber!';
  } else {
    detailEl.innerHTML = problems.join(' • ');
  }

  // Mini-Statistiken
  const miniEl = document.getElementById('health-stats-mini');
  miniEl.innerHTML = `
    <div><span style="color:#94a3b8;">📦 Mods:</span> <b>${total}</b></div>
    <div><span style="color:#94a3b8;">📏 Größe:</span> <b>${esc(s.total_size_h || '?')}</b></div>
    <div><span style="color:#94a3b8;">🗑️ Verschwendet:</span> <b style="color:#f59e0b;">${esc(s.wasted_h || '0 B')}</b></div>
    <div><span style="color:#94a3b8;">🔧 Probleme:</span> <b style="color:${score >= 90 ? '#22c55e' : color};">${problems.length}</b></div>
  `;
}

function renderDependencies(data) {
  const section = document.getElementById('deps-section');
  const deps = data.dependencies || [];
  if (deps.length === 0) {
    document.getElementById('deps-list').innerHTML = '<span style="color:#22c55e;">\u2705 Keine fehlenden Abh\u00e4ngigkeiten gefunden.</span>';
    return;
  }

  const showMissing = document.getElementById('deps-filter-missing').checked;
  const showImports = document.getElementById('deps-filter-imports').checked;
  const showPairs = document.getElementById('deps-filter-pairs').checked;
  const showNameDeps = document.getElementById('deps-filter-namedeps').checked;
  const showFamilies = document.getElementById('deps-filter-families').checked;

  const filtered = deps.filter(d => {
    if (d.type === 'missing_import') return showMissing;
    if (d.type === 'import_dependency') return showImports;
    if (d.type === 'script_pair') return showPairs;
    if (d.type === 'name_dependency') return showNameDeps;
    if (d.type === 'mod_family') return showFamilies;
    return true;
  });

  const missingCount = deps.filter(d => d.type === 'missing_import').length;
  document.getElementById('deps-summary').innerHTML =
    `${deps.length} Beziehungen erkannt (${filtered.length} angezeigt)` +
    (missingCount > 0 ? ` — <b style="color:#ef4444;">❌ ${missingCount} fehlende Abhängigkeit${missingCount > 1 ? 'en' : ''}!</b>` : '');

  const html = filtered.map((d, i) => {
    const typeColors = {
      'missing_import': '#ef4444',
      'import_dependency': '#22c55e',
      'script_pair': '#3b82f6',
      'name_dependency': '#f59e0b',
      'mod_family': '#8b5cf6',
    };
    const typeLabels = {
      'missing_import': '❌ Fehlt!',
      'import_dependency': '✅ Installiert',
      'script_pair': 'Script+Package',
      'name_dependency': 'Abhängigkeit',
      'mod_family': 'Familie',
    };
    const color = typeColors[d.type] || '#64748b';
    const filesHtml = (d.files || []).map(fp => {
      const name = fp.split(/[\\\\/]/).pop();
      const ext = name.split('.').pop().toLowerCase();
      const extBadge = ext === 'ts4script'
        ? '<span style="background:#7f1d1d;color:#fca5a5;padding:1px 6px;border-radius:4px;font-size:10px;margin-left:4px;">Script</span>'
        : ext === 'package'
          ? '<span style="background:#1e3a5f;color:#93c5fd;padding:1px 6px;border-radius:4px;font-size:10px;margin-left:4px;">Package</span>'
          : '';
      return `<div style="padding:4px 8px;background:#0f172a;border-radius:4px;margin:2px 0;font-size:12px;display:flex;align-items:center;gap:6px;">
        <span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${esc(fp)}">${esc(name)}</span>${extBadge}
        <button class="btn btn-ghost" style="font-size:10px;padding:2px 6px;margin-left:auto;" data-act="open_folder" data-path="${esc(fp)}">📂</button>
      </div>`;
    }).join('');
    const countInfo = d.count ? ` (${d.count} Dateien)` : ` (${d.files.length} Dateien)`;
    return `<details class="grp color-${i % 6}" style="margin-bottom:6px;${d.type === 'missing_import' ? 'border-left:3px solid #ef4444;' : ''}">
      <summary style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <span style="font-size:16px;">${d.icon}</span>
        <b style="font-size:13px;">${esc(d.label)}${countInfo}</b>
        <span style="background:${color};color:#fff;padding:1px 8px;border-radius:10px;font-size:10px;">${typeLabels[d.type] || d.type}</span>
      </summary>
      <div style="margin-top:8px;padding:6px 10px;background:#111827;border-radius:8px;">
        <p class="muted small" style="margin:0 0 6px;">${esc(d.hint)}</p>
        ${filesHtml}
      </div>
    </details>`;
  }).join('');

  document.getElementById('deps-list').innerHTML = html || '<div class="muted">Keine Abhängigkeiten gefunden.</div>';
}

// Event listeners for dependency filters
['deps-filter-missing', 'deps-filter-imports', 'deps-filter-pairs', 'deps-filter-namedeps', 'deps-filter-families'].forEach(id => {
  document.getElementById(id).addEventListener('change', () => {
    if (window.__DATA) renderDependencies(window.__DATA);
  });
});

function renderStats(data) {
  const s = data.summary || {};
  const stats = data.stats || {};

  // Übersicht
  const overviewHtml = `
    <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:8px;">
      <div style="background:#1e293b; border-radius:10px; padding:14px; text-align:center;">
        <div style="font-size:28px; font-weight:bold; color:#6366f1;">${s.total_files || 0}</div>
        <div class="muted small">Dateien gesamt</div>
      </div>
      <div style="background:#1e293b; border-radius:10px; padding:14px; text-align:center;">
        <div style="font-size:28px; font-weight:bold; color:#22c55e;">${esc(s.total_size_h || '?')}</div>
        <div class="muted small">Gesamtgröße</div>
      </div>
      <div style="background:#1e293b; border-radius:10px; padding:14px; text-align:center;">
        <div style="font-size:28px; font-weight:bold; color:#f59e0b;">${esc(s.wasted_h || '0 B')}</div>
        <div class="muted small">Verschwendet (Duplikate)</div>
      </div>
      <div style="background:#1e293b; border-radius:10px; padding:14px; text-align:center;">
        <div style="font-size:28px; font-weight:bold; color:#ef4444;">${s.corrupt_count || 0}</div>
        <div class="muted small">Korrupte Dateien</div>
      </div>
    </div>`;
  document.getElementById('stats-overview').innerHTML = overviewHtml;

  // Kategorie-Balken
  const cats = stats.category_counts || [];
  const catMax = cats.length > 0 ? cats[0][1] : 1;
  const catColors = {
    'CAS (Haare 💇)':'#a855f7', 'CAS (Kleidung 👚)':'#06b6d4', 'CAS (Make-Up 💄)':'#ec4899',
    'CAS (Accessoire 💍)':'#f59e0b', 'CAS (Kleidung/Haare/Make-Up)':'#8b5cf6',
    'Objekt/Möbel':'#22c55e', 'Gameplay-Mod (Tuning)':'#ef4444', 'Mesh/Build-Mod':'#14b8a6',
    'Textur/Override':'#f97316', 'Sonstiges':'#64748b', 'Unbekannt':'#475569',
  };
  const catHtml = cats.map(([name, count]) => {
    const pct = Math.round(count / catMax * 100);
    const color = catColors[name] || '#6366f1';
    return `<div style="margin-bottom:4px; display:flex; align-items:center; gap:8px;">
      <div style="min-width:180px; font-size:12px; color:#cbd5e1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${esc(name)}</div>
      <div style="flex:1; background:#0f172a; border-radius:4px; height:18px; overflow:hidden;">
        <div style="width:${pct}%; background:${color}; height:100%; border-radius:4px; min-width:2px;"></div>
      </div>
      <div style="min-width:40px; text-align:right; font-size:12px; color:#94a3b8;">${count}</div>
    </div>`;
  }).join('');
  document.getElementById('stats-categories').innerHTML = catHtml || '<span class="muted small">Keine Daten</span>';

  // Top 10 Ordner
  const folders = stats.top10_folders || [];
  const folderMax = folders.length > 0 ? folders[0].size : 1;
  const folderHtml = folders.map(f => {
    const pct = Math.round(f.size / folderMax * 100);
    return `<div style="margin-bottom:4px; display:flex; align-items:center; gap:8px;">
      <div style="min-width:180px; font-size:12px; color:#cbd5e1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${esc(f.name)}">📁 ${esc(f.name)}</div>
      <div style="flex:1; background:#0f172a; border-radius:4px; height:18px; overflow:hidden;">
        <div style="width:${pct}%; background:#3b82f6; height:100%; border-radius:4px; min-width:2px;"></div>
      </div>
      <div style="min-width:80px; text-align:right; font-size:11px; color:#94a3b8;">${esc(f.size_h)} (${f.count})</div>
    </div>`;
  }).join('');
  document.getElementById('stats-folders').innerHTML = folderHtml || '<span class="muted small">Keine Daten</span>';

  // Top 10 größte Dateien
  const biggest = stats.top10_biggest || [];
  const bigHtml = biggest.map((f, i) => {
    const name = (f.rel || f.path || '').split(/[\\\\/]/).pop();
    const creator = detectCreator(name);
    const creatorBadge = creator ? `<span style="background:#1e3a5f;color:#60a5fa;font-size:10px;padding:1px 6px;border-radius:4px;margin-left:4px;" title="Mod-Ersteller: ${esc(creator.name)}">${creator.icon} ${esc(creator.name)}</span>` : '';
    return `<div style="display:flex;align-items:center;gap:10px;padding:6px 10px;background:#0f172a;border:1px solid #1e293b;border-radius:6px;margin-bottom:4px;">
      <span style="color:#64748b;font-weight:bold;min-width:20px;">#${i+1}</span>
      <div style="flex:1;min-width:0;">
        <div style="font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${esc(f.path)}">${esc(name)}${creatorBadge}</div>
        <div class="muted" style="font-size:11px;">${esc(f.mod_folder)} | ${esc(f.size_h)}</div>
      </div>
      <div style="font-weight:bold;color:#f59e0b;font-size:13px;">${esc(f.size_h)}</div>
    </div>`;
  }).join('');
  document.getElementById('stats-biggest').innerHTML = bigHtml || '<span class="muted small">Keine Daten</span>';

  // --- Mod-Aktivitäts-Heatmap (GitHub-Style) ---
  const heatmap = stats.activity_heatmap || {};
  const heatmapEl = document.getElementById('stats-heatmap');
  const hmKeys = Object.keys(heatmap);
  if (hmKeys.length === 0) {
    heatmapEl.innerHTML = '<span class="muted small">Keine Datums-Daten verfügbar</span>';
  } else {
    // Letzte 365 Tage berechnen
    const today = new Date();
    const days = [];
    for (let i = 364; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      const entry = heatmap[key] || { count: 0, mods: [], more: 0 };
      // Compat: falls noch altes Format (nur Zahl)
      const count = typeof entry === 'number' ? entry : (entry.count || 0);
      const mods = typeof entry === 'object' ? (entry.mods || []) : [];
      const more = typeof entry === 'object' ? (entry.more || 0) : 0;
      days.push({ date: d, key, count, mods, more });
    }
    // Max-Wert für Farbskalierung
    const maxCount = Math.max(1, ...days.map(d => d.count));
    // Farbstufen (5 Stufen)
    function hmColor(count) {
      if (count === 0) return '#161b22';
      const ratio = count / maxCount;
      if (ratio <= 0.15) return '#0e4429';
      if (ratio <= 0.35) return '#006d32';
      if (ratio <= 0.6) return '#26a641';
      return '#39d353';
    }
    // Monate für Beschriftung
    const monthNames = ['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'];
    const startDay = days[0].date.getDay();
    const offset = startDay === 0 ? 6 : startDay - 1;
    const cellSize = 13;
    const cellGap = 3;
    const step = cellSize + cellGap;
    const weeksCount = Math.ceil((days.length + offset) / 7);
    const svgW = weeksCount * step + 40;
    const svgH = 7 * step + 30;
    let svg = `<svg width="${svgW}" height="${svgH}" style="font-family:system-ui;font-size:10px;">`;
    // Wochentag-Labels
    const dayLabels = ['Mo','','Mi','','Fr','','So'];
    dayLabels.forEach((lbl, i) => {
      if (lbl) svg += `<text x="0" y="${28 + i * step + cellSize - 2}" fill="#8b949e" font-size="10">${lbl}</text>`;
    });
    // Monats-Labels
    let lastMonth = -1;
    days.forEach((d, i) => {
      const col = Math.floor((i + offset) / 7);
      const m = d.date.getMonth();
      if (m !== lastMonth) {
        lastMonth = m;
        svg += `<text x="${30 + col * step}" y="12" fill="#8b949e" font-size="10">${monthNames[m]}</text>`;
      }
    });
    // Zellen (mit data-Attribut für Tooltip)
    days.forEach((d, i) => {
      const col = Math.floor((i + offset) / 7);
      const row = (i + offset) % 7;
      const x = 30 + col * step;
      const y = 20 + row * step;
      const color = hmColor(d.count);
      svg += `<rect class="hm-cell" x="${x}" y="${y}" width="${cellSize}" height="${cellSize}" rx="2" ry="2" fill="${color}" style="outline:1px solid #21262d;cursor:${d.count > 0 ? 'pointer' : 'default'};" data-idx="${i}"></rect>`;
    });
    svg += '</svg>';

    // Custom Tooltip div
    const tooltipId = 'hm-tooltip';
    const tooltipHtml = `<div id="${tooltipId}" style="display:none;position:fixed;z-index:9999;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:10px 14px;max-width:340px;font-size:12px;color:#e2e8f0;box-shadow:0 4px 16px rgba(0,0,0,0.5);pointer-events:auto;">
      <div id="hm-tt-title" style="font-weight:bold;font-size:13px;margin-bottom:4px;"></div>
      <div id="hm-tt-list" style="max-height:260px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:#475569 #1e293b;padding-right:4px;"></div>
    </div>`;

    // Legende
    const legend = `<div style="display:flex;align-items:center;gap:6px;margin-top:6px;font-size:11px;color:#8b949e;">
      <span>Weniger</span>
      <span style="display:inline-block;width:12px;height:12px;background:#161b22;border-radius:2px;border:1px solid #21262d;"></span>
      <span style="display:inline-block;width:12px;height:12px;background:#0e4429;border-radius:2px;"></span>
      <span style="display:inline-block;width:12px;height:12px;background:#006d32;border-radius:2px;"></span>
      <span style="display:inline-block;width:12px;height:12px;background:#26a641;border-radius:2px;"></span>
      <span style="display:inline-block;width:12px;height:12px;background:#39d353;border-radius:2px;"></span>
      <span>Mehr</span>
    </div>`;
    heatmapEl.innerHTML = svg + tooltipHtml + legend;

    // Tooltip Event-Handler
    const tooltip = document.getElementById(tooltipId);
    const ttTitle = document.getElementById('hm-tt-title');
    const ttList = document.getElementById('hm-tt-list');
    let hideTimeout = null;
    function showTooltip() { clearTimeout(hideTimeout); tooltip.style.display = 'block'; }
    function scheduleHide() { hideTimeout = setTimeout(() => { tooltip.style.display = 'none'; }, 200); }
    tooltip.addEventListener('mouseenter', showTooltip);
    tooltip.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
    heatmapEl.querySelectorAll('.hm-cell').forEach(rect => {
      const idx = parseInt(rect.getAttribute('data-idx'));
      const d = days[idx];
      rect.addEventListener('mouseenter', (e) => {
        showTooltip();
        if (d.count === 0) {
          ttTitle.textContent = `${d.key} — Keine Mods`;
          ttList.innerHTML = '';
        } else {
          ttTitle.textContent = `📅 ${d.key} — ${d.count} Mod${d.count !== 1 ? 's' : ''}`;
          let listHtml = d.mods.map(m => `<div style="padding:2px 0;border-bottom:1px solid #1e293b;">📦 ${esc(m)}</div>`).join('');
          if (d.more > 0) listHtml += `<div style="padding:2px 0;color:#8b949e;font-style:italic;">… und ${d.more} weitere</div>`;
          ttList.innerHTML = listHtml;
          ttList.scrollTop = 0;
        }
        const r = rect.getBoundingClientRect();
        tooltip.style.left = Math.min(r.left, window.innerWidth - 360) + 'px';
        tooltip.style.top = (r.bottom + 8) + 'px';
      });
      rect.addEventListener('mouseleave', scheduleHide);
    });
  }
}

async function loadQuarantine() {
  try {
    const resp = await fetch('/api/quarantine?token=' + TOKEN);
    const json = await resp.json();
    if (!json.ok) throw new Error(json.error);
    renderQuarantine(json);
  } catch(e) {
    document.getElementById('quarantine-summary').innerHTML = '<span style="color:#ef4444;">Fehler: ' + esc(e.message) + '</span>';
  }
}

function renderQuarantine(qdata) {
  const files = qdata.files || [];
  const section = document.getElementById('quarantine-section');

  if (files.length === 0) {
    showConditionalSection('quarantine-section', false);
    document.getElementById('nav-badge-quarantine').textContent = '0';
    return;
  }
  showConditionalSection('quarantine-section', true);
  document.getElementById('nav-badge-quarantine').textContent = files.length;

  document.getElementById('quarantine-summary').innerHTML =
    `<b>${files.length}</b> Dateien in Quarantäne | Gesamtgröße: <b>${esc(qdata.total_size_h)}</b>`;

  const cards = files.map(f => {
    const creator = detectCreator(f.name);
    const creatorBadge = creator ? ` <span style="background:#1e3a5f;color:#60a5fa;font-size:10px;padding:1px 6px;border-radius:4px;">${creator.icon} ${esc(creator.name)}</span>` : '';
    return `<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;background:#0f172a;border:1px solid #334155;border-radius:8px;margin-bottom:4px;">
      <span style="font-size:16px;">📦</span>
      <div style="flex:1;min-width:0;">
        <div style="font-weight:bold;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${esc(f.path)}">${esc(f.name)}${creatorBadge}</div>
        <div class="muted" style="font-size:11px;">${esc(f.q_dir)} | ${esc(f.size_h)} | ${esc(f.mtime)}</div>
      </div>
      <div style="display:flex;gap:4px;flex-shrink:0;">
        <button class="btn btn-ok" style="font-size:11px;padding:3px 10px;" data-act="restore" data-path="${esc(f.path)}" title="Zurück in den Mods-Ordner verschieben">↩️ Zurückholen</button>
        <button class="btn btn-danger" style="font-size:11px;padding:3px 10px;" data-act="delete_q" data-path="${esc(f.path)}" title="Endgültig vom PC löschen">🗑</button>
      </div>
    </div>`;
  }).join('');
  document.getElementById('quarantine-list').innerHTML = cards;
}

// ═══════════════════════════════════════════════════
// ═══ CACHE-CLEANER ═══
// ═══════════════════════════════════════════════════
async function loadCacheInfo() {
  const el = document.getElementById('cache-list');
  el.innerHTML = '<div class="muted">Lade Cache-Infos…</div>';
  try {
    const resp = await fetch('/api/cache-info?token=' + TOKEN);
    const json = await resp.json();
    if (!json.ok) throw new Error(json.error);
    const caches = json.caches || [];
    if (caches.length === 0) {
      el.innerHTML = '<div class="muted">Keine Caches gefunden.</div>';
      document.getElementById('cache-actions').style.display = 'none';
      return;
    }
    let html = '<table style="width:100%;border-collapse:collapse;font-size:13px;">';
    html += '<tr style="border-bottom:1px solid #334155;"><th style="text-align:left;padding:6px;">☑</th><th style="text-align:left;padding:6px;">Cache</th><th style="text-align:right;padding:6px;">Größe</th><th style="padding:6px;">Status</th></tr>';
    for (const c of caches) {
      const sizeStr = c.size > 1048576 ? (c.size / 1048576).toFixed(1) + ' MB' : (c.size / 1024).toFixed(0) + ' KB';
      const exists = c.exists ? '<span style="color:#22c55e;">✓ vorhanden</span>' : '<span class="muted">— fehlt</span>';
      const checked = c.exists ? 'checked' : 'disabled';
      html += `<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;"><input type="checkbox" class="cache-cb" value="${esc(c.key)}" ${checked}></td><td style="padding:6px;">${esc(c.label)}</td><td style="text-align:right;padding:6px;">${sizeStr}</td><td style="padding:6px;text-align:center;">${exists}</td></tr>`;
    }
    html += '</table>';
    html += `<div class="muted small" style="margin-top:8px;">Gesamt: <b>${(json.total_size / 1048576).toFixed(1)} MB</b></div>`;
    el.innerHTML = html;
    document.getElementById('cache-actions').style.display = 'flex';
  } catch(e) {
    el.innerHTML = '<div style="color:#ef4444;">Fehler: ' + esc(e.message) + '</div>';
  }
}

async function cleanSelectedCaches() {
  const cbs = document.querySelectorAll('.cache-cb:checked');
  const targets = Array.from(cbs).map(cb => cb.value);
  if (targets.length === 0) { showToast('Keine Caches ausgewählt', 'warning'); return; }
  await doCleanCaches(targets);
}

async function cleanAllCaches() {
  await doCleanCaches(['localthumbcache', 'cachestr', 'onlinethumbnailcache', 'avatarcache', 'localsimtexturecache']);
}

async function doCleanCaches(targets) {
  const el = document.getElementById('cache-result');
  el.textContent = 'Bereinige…';
  try {
    const resp = await fetch('/api/action', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token:TOKEN, action:'clean_cache', targets})});
    const json = await resp.json();
    if (!json.ok) throw new Error(json.error);
    const freed = (json.total_freed / 1048576).toFixed(1);
    el.innerHTML = `<span style="color:#22c55e;">✅ ${json.results.length} Cache(s) bereinigt — ${freed} MB freigegeben</span>`;
    showToast(`Cache bereinigt: ${freed} MB frei`, 'success');
    loadCacheInfo();
  } catch(e) {
    el.innerHTML = '<span style="color:#ef4444;">Fehler: ' + esc(e.message) + '</span>';
    showToast('Cache-Bereinigung fehlgeschlagen', 'error');
  }
}

// ═══════════════════════════════════════════════════
// ═══ MOD-BACKUP ═══
// ═══════════════════════════════════════════════════
async function createModBackup() {
  const btn = document.getElementById('btn-create-backup');
  const status = document.getElementById('backup-status');
  btn.disabled = true;
  status.innerHTML = '<span style="color:#60a5fa;">⏳ Backup wird erstellt… (kann bei vielen Mods dauern)</span>';
  try {
    const resp = await fetch('/api/action', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token:TOKEN, action:'create_backup'})});
    const json = await resp.json();
    if (!json.ok) throw new Error(json.error);
    const zipMB = (json.zip_size / 1048576).toFixed(1);
    status.innerHTML = `<span style="color:#22c55e;">✅ Backup erstellt: ${json.file_count} Dateien, ${zipMB} MB</span><br><span class="muted small" style="word-break:break-all;">${esc(json.path)}</span>`;
    showToast(`Backup erstellt: ${json.file_count} Dateien, ${zipMB} MB`, 'success');
  } catch(e) {
    status.innerHTML = '<span style="color:#ef4444;">Fehler: ' + esc(e.message) + '</span>';
    showToast('Backup fehlgeschlagen', 'error');
  }
  btn.disabled = false;
}

// ═══════════════════════════════════════════════════
// ═══ TRAY-CLEANER ═══
// ═══════════════════════════════════════════════════
async function scanTrayOrphans() {
  const el = document.getElementById('tray-clean-result');
  el.innerHTML = '<div class="muted">🔍 Durchsuche den Tray-Ordner nach verwaisten Dateien…</div>';
  try {
    const resp = await fetch('/api/action', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token:TOKEN, action:'clean_tray', delete:false})});
    const json = await resp.json();
    if (!json.ok) throw new Error(json.error);
    const orphans = json.orphans || [];
    if (orphans.length === 0) {
      el.innerHTML = `<div style="background:#22c55e15; border:1px solid #22c55e40; border-radius:8px; padding:16px; text-align:center;">
        <div style="font-size:24px;">✅</div>
        <div style="color:#22c55e; font-weight:bold; font-size:16px;">Alles sauber!</div>
        <div class="muted">Keine verwaisten Tray-Dateien gefunden. Dein Tray-Ordner ist ordentlich!</div>
      </div>`;
      return;
    }
    const totalMB = (json.orphan_size / 1048576).toFixed(1);
    let html = `<div style="background:#f59e0b15; border:1px solid #f59e0b40; border-radius:8px; padding:12px 16px; margin-bottom:12px;">
      <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:22px;">🗂️</span>
        <div>
          <div style="font-weight:bold;color:#fbbf24;"><b>${orphans.length}</b> verwaiste Dateien gefunden (${totalMB} MB)</div>
          <div class="muted" style="font-size:12px; margin-top:4px;">Das sind Reste von gelöschten Sims, Häusern oder Zimmern, die kein zugehöriges .trayitem mehr haben. Sie belegen unnötig Speicherplatz.</div>
        </div>
      </div>
    </div>`;
    // Gruppiert nach Dateityp
    const extCounts = {};
    for (const o of orphans) {
      const ext = o.name.split('.').pop() || 'unbekannt';
      extCounts[ext] = (extCounts[ext] || 0) + 1;
    }
    html += '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;">';
    for (const [ext, cnt] of Object.entries(extCounts)) {
      html += `<span style="background:#1e293b;padding:3px 10px;border-radius:12px;font-size:11px;">.${esc(ext)} <b>${cnt}</b></span>`;
    }
    html += '</div>';
    html += '<div style="max-height:200px;overflow-y:auto;border:1px solid #334155;border-radius:6px;padding:8px;background:#0f172a;">';
    for (const o of orphans.slice(0, 100)) {
      const sz = (o.size / 1024).toFixed(0);
      html += `<div class="muted small" style="padding:2px 0;">${esc(o.name)} <span style="opacity:0.5;">(${sz} KB)</span></div>`;
    }
    if (orphans.length > 100) html += `<div class="muted small">…und ${orphans.length - 100} weitere</div>`;
    html += '</div>';
    html += `<div style="margin-top:10px;display:flex;align-items:center;gap:12px;">
      <button class="btn" style="background:#f59e0b;color:#000;" onclick="deleteTrayOrphans()">📦 ${orphans.length} verwaiste Dateien in Quarantäne verschieben (${totalMB} MB)</button>
    </div>
    <div class="muted" style="font-size:11px;margin-top:6px;">🛡️ Die Dateien werden <b>nicht gelöscht</b>, sondern in den Ordner <code>Tray/_tray_quarantine/</code> verschoben. Du kannst sie dort jederzeit wiederherstellen.</div>`;
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div style="color:#ef4444;">Fehler: ' + esc(e.message) + '</div>';
  }
}

async function deleteTrayOrphans() {
  if (!confirm('📦 Verwaiste Tray-Dateien in Quarantäne verschieben?\n\nDie Dateien werden NICHT gelöscht, sondern in den Ordner Tray/_tray_quarantine/ verschoben.\nDu kannst sie dort jederzeit wiederherstellen.\n\nFortfahren?')) return;
  const el = document.getElementById('tray-clean-result');
  try {
    const resp = await fetch('/api/action', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token:TOKEN, action:'clean_tray', delete:true})});
    const json = await resp.json();
    if (!json.ok) throw new Error(json.error);
    el.innerHTML = `<div style="background:#22c55e15; border:1px solid #22c55e40; border-radius:8px; padding:16px; text-align:center;">
      <div style="font-size:24px;">✅</div>
      <div style="color:#22c55e; font-weight:bold;">📦 ${json.deleted} Dateien in Quarantäne verschoben!</div>
      <div class="muted" style="margin-top:4px;">Die Dateien liegen in: <code>${esc(json.quarantined_to || 'Tray/_tray_quarantine/')}</code></div>
      <div class="muted" style="font-size:11px; margin-top:4px;">Falls im Spiel etwas fehlt, verschiebe die Dateien einfach zurück in den Tray-Ordner.</div>
    </div>`;
    showToast(`📦 ${json.deleted} Tray-Dateien in Quarantäne`, 'success');
  } catch(e) {
    el.innerHTML = '<div style="color:#ef4444;">Fehler: ' + esc(e.message) + '</div>';
    showToast('Tray-Bereinigung fehlgeschlagen', 'error');
  }
}

// ═══════════════════════════════════════════════════
// ═══ SCRIPT-SICHERHEITSCHECK ═══
// ═══════════════════════════════════════════════════
// Script-Check: Erklärungen und Gefährdungsstufen für jedes Muster
const _scriptPatternInfo = {
  'os.remove':      {severity:'low', icon:'📁', label:'Kann Dateien löschen', explain:'Der Mod kann einzelne Dateien von deinem PC löschen. Normale Mods machen das z.B. um eigene Temp-Dateien aufzuräumen.', tip:'Bei bekannten Mods (MCCC etc.) normal. Bei unbekannten Mods vorsichtig sein.'},
  'os.unlink':      {severity:'low', icon:'📁', label:'Kann Dateien löschen', explain:'Wie os.remove — löscht einzelne Dateien.', tip:'Meistens harmlos, wird für eigene Cache-Dateien verwendet.'},
  'shutil.rmtree':  {severity:'medium', icon:'📂', label:'Kann ganze Ordner löschen', explain:'Der Mod kann komplette Ordner mit allem Inhalt löschen. Das ist mächtiger als einzelne Dateien löschen.', tip:'Sollte nur bei vertrauenswürdigen Mods vorkommen.'},
  'shutil.move':    {severity:'low', icon:'📂', label:'Kann Dateien verschieben', explain:'Der Mod kann Dateien an andere Orte verschieben.', tip:'Normal — viele Mods organisieren damit ihre eigenen Dateien.'},
  'subprocess':     {severity:'high', icon:'⚙️', label:'Kann externe Programme starten', explain:'Der Mod kann andere Programme auf deinem PC starten (z.B. einen Browser oder ein Tool).', tip:'Bei unbekannten Mods ein Warnsignal! Bekannte Mods wie MCCC nutzen das aber manchmal.'},
  'eval(':          {severity:'high', icon:'🔓', label:'Kann beliebigen Code ausführen', explain:'eval() führt Text als Programmcode aus. Das kann theoretisch alles tun.', tip:'In seriösen Mods selten nötig. Bei unbekannten Mods verdächtig.'},
  'exec(':          {severity:'high', icon:'🔓', label:'Kann beliebigen Code ausführen', explain:'Wie eval() — führt Text als Programmcode aus.', tip:'In seriösen Mods selten nötig. Bei unbekannten Mods verdächtig.'},
  '__import__':     {severity:'medium', icon:'📦', label:'Lädt Bibliotheken dynamisch', explain:'Der Mod lädt andere Python-Module zur Laufzeit. Das ist eine fortgeschrittene Technik.', tip:'Kommt in größeren Mods wie MCCC vor. Bei kleinen unbekannten Mods ungewöhnlich.'},
  'ctypes':         {severity:'high', icon:'🖥️', label:'Zugriff auf System-Funktionen', explain:'Der Mod greift direkt auf Windows/System-Funktionen zu. Das umgeht die normalen Sicherheitsebenen.', tip:'Nur bei sehr bekannten und vertrauenswürdigen Mods akzeptabel.'},
  'socket':         {severity:'medium', icon:'🌐', label:'Netzwerk-Verbindung', explain:'Der Mod kann sich mit dem Internet oder anderen Computern verbinden.', tip:'Mods wie MCCC nutzen das für Update-Checks. Bei unbekannten Mods prüfen wozu.'},
  'urllib':         {severity:'medium', icon:'🌐', label:'Lädt Daten aus dem Internet', explain:'Der Mod kann Dateien oder Daten aus dem Internet herunterladen.', tip:'Wird für Update-Checks und Online-Funktionen genutzt. Normal bei bekannten Mods.'},
  'requests':       {severity:'medium', icon:'🌐', label:'Lädt Daten aus dem Internet', explain:'Wie urllib — kann Daten aus dem Internet laden oder senden.', tip:'Wird für Update-Checks verwendet. Bei bekannten Mods kein Problem.'},
  'keylog':         {severity:'critical', icon:'🚨', label:'Mögliche Tastatur-Überwachung', explain:'Das Wort \"keylog\" deutet auf Tastatur-Aufzeichnung hin. Das ist ein starkes Warnsignal!', tip:'SOFORT LÖSCHEN wenn du den Mod nicht kennst! Seriöse Mods machen sowas nie.'},
  'winreg':         {severity:'high', icon:'🖥️', label:'Windows-Registry-Zugriff', explain:'Der Mod kann Windows-Einstellungen (Registry) lesen oder ändern.', tip:'Sollte in Sims-Mods nicht vorkommen. Bei unbekannten Mods verdächtig.'},
  'cryptograph':    {severity:'medium', icon:'🔐', label:'Verschlüsselung', explain:'Der Mod nutzt Verschlüsselungsfunktionen. Kann harmlos sein (z.B. für sichere Verbindungen) oder auf verschleierte Aktivitäten hindeuten.', tip:'Bei bekannten Mods meist für HTTPS-Verbindungen. Bei unbekannten Mods prüfen.'},
  'UNLESBAR':       {severity:'high', icon:'❌', label:'Script kann nicht gelesen werden', explain:'Das Script-Archiv ist beschädigt oder in einem unbekannten Format.', tip:'Neu herunterladen oder löschen.'},
};

function _getScriptSeverity(findings) {
  const levels = {critical:4, high:3, medium:2, low:1};
  let max = 0;
  for (const f of findings) {
    const info = _scriptPatternInfo[f.pattern] || {};
    const lvl = levels[info.severity] || 1;
    if (lvl > max) max = lvl;
  }
  if (max >= 4) return {label:'Kritisch', color:'#ef4444', bg:'#7f1d1d', icon:'🚨', border:'#ef4444'};
  if (max >= 3) return {label:'Hoch', color:'#f59e0b', bg:'#92400e', icon:'⚠️', border:'#f59e0b'};
  if (max >= 2) return {label:'Mittel', color:'#60a5fa', bg:'#1e3a5f', icon:'ℹ️', border:'#3b82f6'};
  return {label:'Niedrig', color:'#22c55e', bg:'#14532d', icon:'✅', border:'#22c55e'};
}

async function runScriptSecurityCheck() {
  const el = document.getElementById('script-security-result');
  el.innerHTML = '<div class="muted">⏳ Analysiere Scripts… (kann bei vielen Mods dauern)</div>';
  try {
    const resp = await fetch('/api/action', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token:TOKEN, action:'script_security_check'})});
    const json = await resp.json();
    if (!json.ok) throw new Error(json.error);
    const scripts = json.scripts || [];
    const totalChecked = (json.suspicious_count || 0) + (json.safe_count || 0);
    if (scripts.length === 0) {
      el.innerHTML = `<div style="background:#22c55e15; border:1px solid #22c55e40; border-radius:8px; padding:16px; text-align:center;">
        <div style="font-size:24px;">✅</div>
        <div style="color:#22c55e; font-weight:bold; font-size:16px;">Alles sicher!</div>
        <div class="muted">Alle ${totalChecked} Script-Mods wurden geprüft — keine verdächtigen Muster gefunden.</div>
      </div>`;
      return;
    }

    // Zusammenfassung mit Erklärung
    let html = `<div style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:12px 16px; margin-bottom:12px;">
      <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
        <span style="font-size:18px;">🛡️</span>
        <div>
          <div><b>${totalChecked}</b> Scripts geprüft — <b style="color:#f59e0b;">${json.suspicious_count}</b> mit Funden, <b style="color:#22c55e;">${json.safe_count || 0}</b> unauffällig</div>
          <div class="muted" style="font-size:12px; margin-top:4px;">Funde bedeuten <b>nicht</b> dass ein Mod gefährlich ist! Bekannte Mods wie MCCC oder WickedWhims haben immer Funde weil sie fortgeschrittene Funktionen nutzen.</div>
        </div>
      </div>
    </div>`;

    // Legende
    html += `<div style="display:flex; gap:8px; margin-bottom:12px; flex-wrap:wrap; font-size:11px;">
      <span style="background:#7f1d1d;color:#ef4444;padding:2px 8px;border-radius:6px;">🚨 Kritisch = Sofort prüfen!</span>
      <span style="background:#92400e;color:#f59e0b;padding:2px 8px;border-radius:6px;">⚠️ Hoch = Bei unbekannten Mods vorsichtig</span>
      <span style="background:#1e3a5f;color:#60a5fa;padding:2px 8px;border-radius:6px;">ℹ️ Mittel = Normal bei bekannten Mods</span>
      <span style="background:#14532d;color:#22c55e;padding:2px 8px;border-radius:6px;">✅ Niedrig = Meistens harmlos</span>
    </div>`;

    for (const s of scripts) {
      const sizeKB = (s.size / 1024).toFixed(0);
      const sev = _getScriptSeverity(s.findings);
      const creator = detectCreator(s.name);
      const isKnown = !!creator;
      const knownBadge = isKnown
        ? `<span style="background:#14532d;color:#22c55e;padding:1px 6px;border-radius:4px;font-size:10px;margin-left:6px;">✅ Bekannter Mod</span>`
        : `<span style="background:#1e293b;color:#94a3b8;padding:1px 6px;border-radius:4px;font-size:10px;margin-left:6px;">❓ Unbekannter Ersteller</span>`;

      html += `<details style="margin-bottom:8px;padding:0;background:#0f172a;border:1px solid ${sev.border}40;border-left:3px solid ${sev.border};border-radius:8px;">
        <summary style="padding:10px 12px;cursor:pointer;display:flex;align-items:center;gap:8px;list-style:none;">
          <span style="background:${sev.bg};color:${sev.color};padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;">${sev.icon} ${sev.label}</span>
          <span style="font-weight:bold;font-size:12px;" title="${esc(s.path)}">${esc(s.name)}</span>
          <span class="muted" style="font-size:11px;">(${sizeKB} KB, ${s.findings.length} Fund${s.findings.length !== 1 ? 'e' : ''})</span>
          ${knownBadge}
        </summary>
        <div style="padding:8px 12px 12px 16px;border-top:1px solid #1e293b;">`;

      if (isKnown) {
        html += `<div style="background:#14532d40;border:1px solid #22c55e30;border-radius:6px;padding:8px 12px;margin-bottom:8px;font-size:12px;color:#86efac;">
          ✅ <b>Bekannter Mod von ${esc(creator.name)}.</b> Die Funde unten sind normal — dieser Mod braucht diese Funktionen um zu arbeiten.</div>`;
      } else {
        html += `<div style="background:#92400e40;border:1px solid #f59e0b30;border-radius:6px;padding:8px 12px;margin-bottom:8px;font-size:12px;color:#fbbf24;">
          ❓ <b>Unbekannter Mod-Ersteller.</b> Prüfe ob du diesen Mod bewusst installiert hast. Wenn du dir unsicher bist, google nach dem Mod-Namen.</div>`;
      }

      for (const f of s.findings) {
        const info = _scriptPatternInfo[f.pattern] || {severity:'low', icon:'❓', label:f.desc, explain:'Unbekanntes Muster.', tip:''};
        const sevColors = {critical:'#ef4444', high:'#f59e0b', medium:'#60a5fa', low:'#22c55e'};
        const sevColor = sevColors[info.severity] || '#94a3b8';
        html += `<div style="background:#111827;border:1px solid #1e293b;border-radius:6px;padding:8px 12px;margin-bottom:4px;">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
            <span>${info.icon}</span>
            <span style="color:${sevColor};font-weight:bold;font-size:12px;">${esc(info.label)}</span>
            <code style="background:#1e293b;padding:1px 6px;border-radius:3px;font-size:10px;color:#94a3b8;">${esc(f.pattern)}</code>
            <span class="muted" style="font-size:10px;margin-left:auto;">in ${esc(f.file)}</span>
          </div>
          <div style="font-size:11px;color:#cbd5e1;margin-bottom:2px;">📋 ${esc(info.explain)}</div>
          ${info.tip ? `<div style="font-size:11px;color:#86efac;">💡 ${esc(info.tip)}</div>` : ''}
        </div>`;
      }

      // Empfehlung pro Script
      const sevLevel = {critical:4, high:3, medium:2, low:1};
      const maxSev = Math.max(...s.findings.map(f => sevLevel[(_scriptPatternInfo[f.pattern]||{}).severity] || 1));
      let recommendation = '';
      if (isKnown) {
        recommendation = '<div style="margin-top:8px;padding:8px 12px;background:#14532d40;border-radius:6px;font-size:12px;color:#86efac;">👍 <b>Empfehlung:</b> Behalten — bekannter und vertrauenswürdiger Mod.</div>';
      } else if (maxSev >= 4) {
        recommendation = '<div style="margin-top:8px;padding:8px 12px;background:#7f1d1d;border-radius:6px;font-size:12px;color:#fca5a5;">🚨 <b>Empfehlung:</b> Diesen Mod sofort löschen oder in Quarantäne verschieben, wenn du ihn nicht bewusst installiert hast!</div>';
      } else if (maxSev >= 3) {
        recommendation = '<div style="margin-top:8px;padding:8px 12px;background:#92400e40;border-radius:6px;font-size:12px;color:#fbbf24;">⚠️ <b>Empfehlung:</b> Prüfe ob du diesen Mod kennst. Wenn nicht — zur Sicherheit in Quarantäne verschieben.</div>';
      } else {
        recommendation = '<div style="margin-top:8px;padding:8px 12px;background:#1e3a5f40;border-radius:6px;font-size:12px;color:#93c5fd;">ℹ️ <b>Empfehlung:</b> Wahrscheinlich harmlos. Trotzdem gut zu wissen dass der Mod diese Funktionen nutzt.</div>';
      }
      html += recommendation;

      // Aktions-Buttons für unbekannte Mods
      if (!isKnown) {
        html += `<div style="margin-top:8px;display:flex;gap:6px;">
          <button class="btn btn-ok" style="font-size:11px;" data-act="quarantine" data-path="${esc(s.path)}">📦 Quarantäne</button>
          <button class="btn" style="font-size:11px;" data-act="open_folder" data-path="${esc(s.path)}">📂 Ordner öffnen</button>
        </div>`;
      }

      html += '</div></details>';
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div style="color:#ef4444;">Fehler: ' + esc(e.message) + '</div>';
  }
}

// ═══════════════════════════════════════════════════
// ═══ BROKEN CC FINDER ═══
// ═══════════════════════════════════════════════════
const _issueHelp = {
  'Leere/zu kleine Datei': {
    icon: '🗑️', color: '#ef4444', category: 'error',
    explain: 'Diese Datei ist leer oder viel zu klein um ein echtes Package zu sein.',
    tip: 'Kann bedenkenlos gelöscht werden — enthält keine Mod-Daten.'
  },
  'Datei nicht lesbar': {
    icon: '🔒', color: '#ef4444', category: 'error',
    explain: 'Die Datei kann nicht geöffnet werden (Berechtigungsproblem oder gesperrt).',
    tip: 'Starte den Scanner als Administrator oder schließe Programme die auf die Datei zugreifen.'
  },
  'Package hat 0 Ressourcen (leer)': {
    icon: '📭', color: '#ef4444', category: 'error',
    explain: 'Die Datei hat ein gültiges Format, enthält aber keine Inhalte.',
    tip: 'Kann gelöscht werden — der Mod macht nichts.'
  },
};

function _getIssueHelp(issue) {
  if (_issueHelp[issue]) return _issueHelp[issue];
  if (issue.includes('Ungültiges Package-Format')) return {
    icon: '💀', color: '#ef4444', category: 'error',
    explain: 'Das Dateiformat ist ungültig oder die Datei ist für ein anderes Spiel (Sims 2/3).',
    tip: 'Löschen oder durch die richtige Version ersetzen (neu herunterladen).'
  };
  if (issue.includes('CAS-Teil') && issue.includes('ohne Thumbnail')) return {
    icon: '👗', color: '#f59e0b', category: 'warning',
    explain: 'Kleidung/Haare ohne Vorschaubild. Im CAS siehst du evtl. kein Bild beim Scrollen — der Mod funktioniert aber trotzdem!',
    tip: 'Meistens harmlos. Viele ältere Mods haben keine eingebetteten Thumbnails. Das Spiel erstellt sie beim ersten Benutzen selbst.'
  };
  if (issue.includes('Fehler beim Lesen')) return {
    icon: '⚠️', color: '#ef4444', category: 'error',
    explain: 'Die Datei konnte nicht analysiert werden.',
    tip: 'Möglicherweise beschädigt — neu herunterladen oder löschen.'
  };
  return {icon: '❓', color: '#94a3b8', category: 'warning', explain: issue, tip: ''};
}

async function findBrokenCC() {
  const el = document.getElementById('broken-cc-result');
  el.innerHTML = '<div class="muted">⏳ Prüfe alle Packages… (kann bei vielen Mods etwas dauern)</div>';
  try {
    const resp = await fetch('/api/action', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token:TOKEN, action:'find_broken_cc'})});
    const json = await resp.json();
    if (!json.ok) throw new Error(json.error);
    const broken = json.broken || [];
    const okCount = json.checked - broken.length;
    if (broken.length === 0) {
      el.innerHTML = `<div style="background:#22c55e15; border:1px solid #22c55e40; border-radius:8px; padding:16px; text-align:center;">
        <div style="font-size:24px;">✅</div>
        <div style="color:#22c55e; font-weight:bold; font-size:16px;">Alles in Ordnung!</div>
        <div class="muted">Alle ${json.checked} Packages wurden geprüft — keine Probleme gefunden.</div>
      </div>`;
      return;
    }

    // Aufteilen in Fehler und Hinweise
    const errors = broken.filter(b => _getIssueHelp(b.issue).category === 'error');
    const warnings = broken.filter(b => _getIssueHelp(b.issue).category === 'warning');

    let html = `<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:8px; margin-bottom:16px;">`;
    html += `<div style="background:#0f1115; padding:12px; border-radius:8px; text-align:center;">
      <div style="font-size:11px; color:#94a3b8;">Geprüft</div>
      <div style="font-size:20px; font-weight:bold;">${json.checked}</div></div>`;
    html += `<div style="background:#0f1115; padding:12px; border-radius:8px; text-align:center;">
      <div style="font-size:11px; color:#94a3b8;">In Ordnung</div>
      <div style="font-size:20px; font-weight:bold; color:#22c55e;">✅ ${okCount}</div></div>`;
    if (errors.length > 0) html += `<div style="background:#ef444415; padding:12px; border-radius:8px; text-align:center; border:1px solid #ef444440;">
      <div style="font-size:11px; color:#ef4444;">Fehler</div>
      <div style="font-size:20px; font-weight:bold; color:#ef4444;">❌ ${errors.length}</div></div>`;
    if (warnings.length > 0) html += `<div style="background:#f59e0b15; padding:12px; border-radius:8px; text-align:center; border:1px solid #f59e0b40;">
      <div style="font-size:11px; color:#f59e0b;">Hinweise</div>
      <div style="font-size:20px; font-weight:bold; color:#f59e0b;">⚠️ ${warnings.length}</div></div>`;
    html += `</div>`;

    // Fehler zuerst
    if (errors.length > 0) {
      html += `<div style="margin-bottom:12px;">`;
      html += `<h3 style="color:#ef4444; margin:0 0 8px 0; font-size:14px;">❌ Kaputte Dateien — solltest du löschen oder ersetzen:</h3>`;
      for (const b of errors) {
        const info = _getIssueHelp(b.issue);
        const sizeKB = (b.size / 1024).toFixed(0);
        html += `<details style="background:#0f172a; border:1px solid #334155; border-radius:6px; margin-bottom:4px; padding:0;">`;
        html += `<summary style="padding:8px 12px; cursor:pointer; display:flex; align-items:center; gap:8px; list-style:none;">`;
        html += `<span>${info.icon}</span>`;
        html += `<div style="flex:1;min-width:0;"><div style="font-size:12px;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${esc(b.path)}">${esc(b.name)}</div>`;
        html += `<div style="font-size:11px;color:${info.color};">${esc(b.issue)} <span class="muted">(${sizeKB} KB)</span></div></div></summary>`;
        html += `<div style="padding:8px 12px 12px 36px; border-top:1px solid #1e293b;">`;
        html += `<div style="font-size:12px; color:#cbd5e1; margin-bottom:4px;">📋 <b>Was bedeutet das?</b> ${esc(info.explain)}</div>`;
        html += `<div style="font-size:12px; color:#22c55e;">💡 <b>Tipp:</b> ${esc(info.tip)}</div>`;
        html += `<div style="margin-top:8px;"><button class="btn btn-ok" style="font-size:11px; padding:3px 10px;" data-bcc-path="${esc(b.path)}" onclick="doQuarantine(this.getAttribute('data-bcc-path'));">📦 Quarantäne</button></div>`;
        html += `</div></details>`;
      }
      html += `</div>`;
    }

    // Hinweise
    if (warnings.length > 0) {
      html += `<details${errors.length === 0 ? ' open' : ''} style="margin-bottom:12px;">`;
      html += `<summary style="cursor:pointer; font-size:14px; color:#f59e0b; font-weight:bold; margin-bottom:8px;">⚠️ ${warnings.length} Hinweis(e) — meistens harmlos (klicken zum Anzeigen)</summary>`;
      html += `<div style="background:#f59e0b08; border:1px solid #f59e0b20; border-radius:8px; padding:12px; margin-bottom:8px;">`;
      html += `<div style="font-size:12px; color:#fbbf24; margin-bottom:8px;">💡 <b>Was bedeutet "CAS-Teile ohne Thumbnail"?</b></div>`;
      html += `<div style="font-size:12px; color:#cbd5e1; line-height:1.6;">Diese Mods enthalten Kleidung, Haare oder Accessoires, aber kein eingebettetes Vorschaubild. `;
      html += `Im Create-a-Sim (CAS) kann es passieren, dass diese Teile <b>kein Bild zeigen</b> beim Durchblättern — der Mod funktioniert aber trotzdem ganz normal!<br><br>`;
      html += `<b>Muss ich etwas tun?</b> Nein! Das Spiel erstellt fehlende Vorschaubilder meistens selbst. Falls dich ein fehlendes Bild stört, kannst du den Mod neu herunterladen — neuere Versionen haben oft Thumbnails dabei.</div>`;
      html += `</div>`;
      for (const b of warnings) {
        const info = _getIssueHelp(b.issue);
        const sizeKB = (b.size / 1024).toFixed(0);
        html += `<div style="display:flex;align-items:center;gap:8px;padding:6px 12px;background:#0f172a;border:1px solid #1e293b;border-radius:6px;margin-bottom:3px;">`;
        html += `<span>${info.icon}</span>`;
        html += `<div style="flex:1;min-width:0;"><div style="font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${esc(b.path)}">${esc(b.name)}</div>`;
        html += `<div style="font-size:11px;color:#94a3b8;">${esc(b.issue)} <span class="muted">(${sizeKB} KB)</span></div></div></div>`;
      }
      html += `</details>`;
    }

    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div style="color:#ef4444;">Fehler: ' + esc(e.message) + '</div>';
  }
}

// ═══════════════════════════════════════════════════
// ═══ PACKAGE-BROWSER ═══
// ═══════════════════════════════════════════════════
let _packageList = [];

function populatePackageList() {
  const data = window.__DATA;
  if (!data) return;
  const allFiles = collectAllUniqueFiles(data);
  _packageList = allFiles.filter(f => (f.path||'').toLowerCase().endsWith('.package')).map(f => ({
    path: f.path,
    name: (f.path||'').split(/[\\/]/).pop(),
    size: f.size || 0
  }));
  _packageList.sort((a,b) => a.name.localeCompare(b.name));
  const countEl = document.getElementById('package-browser-count');
  if (countEl) countEl.textContent = _packageList.length + ' Packages';
  filterPackageList();
}

function filterPackageList() {
  const filter = (document.getElementById('package-browse-filter')?.value || '').toLowerCase();
  const listEl = document.getElementById('package-browse-list');
  if (!listEl) return;
  const filtered = filter ? _packageList.filter(p => p.name.toLowerCase().includes(filter) || p.path.toLowerCase().includes(filter)) : _packageList;
  if (filtered.length === 0) {
    listEl.innerHTML = '<div class="muted" style="padding:12px;">Keine Packages gefunden.</div>';
    return;
  }
  const show = filtered.slice(0, 200);
  let html = '';
  for (const pkg of show) {
    const sizeMB = (pkg.size / 1048576).toFixed(2);
    const safePath = pkg.path.replace(/\\/g, '/');
    html += `<div data-pkg-path="${esc(safePath)}" onclick="browsePackage(this.getAttribute('data-pkg-path'))" style="padding:6px 12px; cursor:pointer; border-bottom:1px solid #1e293b; display:flex; justify-content:space-between; align-items:center; transition:background 0.1s;" onmouseenter="this.style.background='#1e293b'" onmouseleave="this.style.background=''">
      <span style="font-size:13px;">📦 ${esc(pkg.name)}</span>
      <span class="muted" style="font-size:11px;">${sizeMB} MB</span>
    </div>`;
  }
  if (filtered.length > 200) {
    html += `<div class="muted" style="padding:8px 12px; text-align:center;">…und ${filtered.length - 200} weitere (Filter nutzen)</div>`;
  }
  listEl.innerHTML = html;
}

const _typeDescriptions = {
  'CAS Part': {icon:'👗', desc:'Kleidung, Haare, Accessoires (Create-a-Sim)'},
  'Object Definition': {icon:'🪑', desc:'Kaufbare Objekte / Möbel'},
  'Buff Tuning': {icon:'😊', desc:'Stimmungen & Gefühle'},
  'Trait Tuning': {icon:'⭐', desc:'Charakter-Eigenschaften'},
  'Object Tuning': {icon:'⚙️', desc:'Objekt-Verhalten & Einstellungen'},
  'Interaction Tuning': {icon:'💬', desc:'Aktionen & Interaktionen'},
  'Lot Tuning': {icon:'🏠', desc:'Grundstücks-Einstellungen'},
  'Action Tuning': {icon:'🎬', desc:'Animations-Aktionen'},
  'Instance Tuning': {icon:'📋', desc:'Allgemeine Spielmechanik'},
  'Sim Data': {icon:'🧬', desc:'Sim-Daten (Aussehen, Werte)'},
  'Sim Info': {icon:'👤', desc:'Sim-Informationen'},
  'Texture (LRLE)': {icon:'🖼️', desc:'Texturen & Oberflächen'},
  'Mesh (GEOM)': {icon:'📐', desc:'3D-Modelle & Formen'},
  'Blend Geometry': {icon:'🔄', desc:'Körper-Anpassungen'},
  'NameMap': {icon:'🏷️', desc:'Interne Namens-Zuordnungen'},
  'Thumbnail': {icon:'📸', desc:'Vorschaubilder'},
  'DST Image': {icon:'🖼️', desc:'Textur-Details'},
  'Bone Delta': {icon:'🦴', desc:'Körper-Slider-Anpassungen'},
  'Hotspot Control': {icon:'🎯', desc:'Interaktions-Punkte'},
  'Sim Outfit': {icon:'👔', desc:'Gespeicherte Sim-Outfits'},
  'Color List': {icon:'🎨', desc:'Farbpaletten'},
  'Footprint': {icon:'👣', desc:'Objekt-Platzierung / Fußabdruck'},
  'Region Sort': {icon:'🗺️', desc:'Welt-Sortierung'},
  'Slot Tuning': {icon:'📍', desc:'Objekt-Slot-Einstellungen'},
  'Region Tuning': {icon:'🗺️', desc:'Welt-/Nachbarschafts-Einstellungen'},
  'Recipe Tuning': {icon:'🍳', desc:'Koch-Rezepte / Herstellungs-Rezepte'},
  'Aspiration Tuning': {icon:'💭', desc:'Lebensziele & Wünsche'},
  'Career Tuning': {icon:'💼', desc:'Karrieren & Jobs'},
  'Walkby Tuning': {icon:'🚶', desc:'Passanten-Verhalten'},
  'Situation Tuning': {icon:'🎭', desc:'Events & Situationen'},
};

async function browsePackage(pkgPath) {
  if (!pkgPath) return;
  const el = document.getElementById('package-browse-result');
  el.innerHTML = '<div class="muted">⏳ Analysiere Package…</div>';
  try {
    const resp = await fetch('/api/package-detail?token=' + TOKEN + '&path=' + encodeURIComponent(pkgPath));
    const json = await resp.json();
    if (!json.ok) throw new Error(json.error);
    const fileMB = (json.file_size / 1048576).toFixed(2);
    const fname = esc(pkgPath.split(/[\\/]/).pop());
    const intColor = json.integrity === 'ok' ? '#22c55e' : '#ef4444';
    const intText = json.integrity === 'ok' ? '✅ In Ordnung' : '❌ Beschädigt';
    const ratio = json.total_uncompressed > 0 ? ((1 - json.total_compressed / json.total_uncompressed) * 100).toFixed(0) : 0;

    // Mod-Typ bestimmen
    const tc = json.type_counts || {};
    const types = Object.entries(tc).sort((a,b) => b[1] - a[1]);
    let modType = '📦 Unbekannt';
    let modTypeColor = '#94a3b8';
    const hasCAS = tc['CAS Part'] > 0;
    const hasObj = tc['Object Definition'] > 0;
    const hasTuning = types.some(([n]) => n.includes('Tuning'));
    const hasMesh = tc['Mesh (GEOM)'] > 0 || tc['Texture (LRLE)'] > 0;
    if (hasCAS && !hasTuning) { modType = '👗 CAS / Kleidung'; modTypeColor = '#f472b6'; }
    else if (hasCAS && hasTuning) { modType = '👗⚙️ CAS mit Gameplay'; modTypeColor = '#f59e0b'; }
    else if (hasObj && !hasTuning) { modType = '🪑 Objekte / Möbel'; modTypeColor = '#60a5fa'; }
    else if (hasObj && hasTuning) { modType = '🪑⚙️ Objekte mit Gameplay'; modTypeColor = '#f59e0b'; }
    else if (hasTuning) { modType = '⚙️ Gameplay / Script-Mod'; modTypeColor = '#a78bfa'; }
    else if (hasMesh) { modType = '🖼️ Texturen / Meshes'; modTypeColor = '#34d399'; }

    let html = `<div style="background:#1a1f2e; border:1px solid #334155; border-radius:8px; padding:16px; margin-bottom:12px;">`;
    html += `<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">`;
    html += `<h3 style="margin:0; font-size:16px;">📦 ${fname}</h3>`;
    html += `<span style="background:${modTypeColor}22; color:${modTypeColor}; padding:4px 12px; border-radius:12px; font-size:12px; font-weight:bold;">${modType}</span>`;
    html += `</div>`;

    // Info-Karten
    html += `<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:8px; margin-bottom:16px;">`;
    html += `<div style="background:#0f1115; padding:10px; border-radius:6px; text-align:center;">`;
    html += `<div style="font-size:11px; color:#94a3b8;">Status</div>`;
    html += `<div style="font-size:14px; color:${intColor}; font-weight:bold;">${intText}</div></div>`;
    html += `<div style="background:#0f1115; padding:10px; border-radius:6px; text-align:center;">`;
    html += `<div style="font-size:11px; color:#94a3b8;">Dateigröße</div>`;
    html += `<div style="font-size:14px; font-weight:bold;">${fileMB} MB</div></div>`;
    html += `<div style="background:#0f1115; padding:10px; border-radius:6px; text-align:center;">`;
    html += `<div style="font-size:11px; color:#94a3b8;">Inhalte</div>`;
    html += `<div style="font-size:14px; font-weight:bold;">${json.resource_count} Teile</div></div>`;
    html += `<div style="background:#0f1115; padding:10px; border-radius:6px; text-align:center;">`;
    html += `<div style="font-size:11px; color:#94a3b8;">Kompression</div>`;
    html += `<div style="font-size:14px; font-weight:bold;">${ratio}% gespart</div></div>`;
    html += `</div>`;

    // Inhalts-Zusammenfassung
    if (types.length > 0) {
      html += '<div style="margin-bottom:8px;"><b>📋 Was steckt drin:</b></div>';
      html += '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;">';
      for (const [name, count] of types) {
        const info = _typeDescriptions[name] || {icon:'📄', desc:'Sims 4 Ressource'};
        html += `<span title="${esc(info.desc)}" style="background:#1e293b; padding:4px 10px; border-radius:12px; font-size:12px; cursor:help; display:inline-flex; align-items:center; gap:4px;">${info.icon} ${esc(name)} <b style="color:#61dafb;">${count}×</b></span>`;
      }
      html += '</div>';
    }

    // Einfache Zusammenfassung statt Rohdaten
    html += '<details style="margin-top:4px;"><summary style="cursor:pointer; color:#94a3b8; font-size:12px;">🔍 Technische Details anzeigen (${json.resource_count} Einträge)</summary>';
    const entries = json.entries || [];
    if (entries.length > 0) {
      html += '<div style="max-height:300px;overflow-y:auto;border:1px solid #334155;border-radius:6px;margin-top:8px;">';
      html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
      html += '<tr style="position:sticky;top:0;background:#1e293b;"><th style="padding:4px 8px;text-align:left;">Typ</th><th style="padding:4px 8px;text-align:left;">Beschreibung</th><th style="padding:4px 8px;text-align:right;">Größe</th></tr>';
      for (const e of entries) {
        const info = _typeDescriptions[e.type] || {icon:'📄', desc:''};
        html += `<tr style="border-top:1px solid #1e293b;"><td style="padding:3px 8px;">${info.icon} ${esc(e.type)}</td><td style="padding:3px 8px;color:#94a3b8;font-size:10px;">${esc(info.desc)}</td><td style="padding:3px 8px;text-align:right;">${(e.uncomp_size/1024).toFixed(1)} KB</td></tr>`;
      }
      if (json.resource_count > 500) {
        html += `<tr><td colspan="3" class="muted" style="padding:6px 8px;text-align:center;">…und ${json.resource_count - 500} weitere</td></tr>`;
      }
      html += '</table></div>';
    }
    html += '</details></div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div style="color:#ef4444;">Fehler: ' + esc(e.message) + '</div>';
  }
}

// ═══════════════════════════════════════════════════
// ═══ SAVE-GESUNDHEITSCHECK ═══
// ═══════════════════════════════════════════════════
async function checkSaveHealth() {
  const el = document.getElementById('save-health-result');
  el.innerHTML = '<div class="muted">⏳ Prüfe Speicherstand…</div>';
  try {
    const resp = await fetch('/api/save-health?token=' + TOKEN);
    const json = await resp.json();
    if (!json.ok) throw new Error(json.error);
    if (json.status === 'no_data') {
      el.innerHTML = '<div class="muted">⚠️ Kein Speicherstand geladen. Lade erst den Speicherstand im <b>Tray & CC</b> Tab.</div>';
      return;
    }
    const issues = json.issues || [];
    const scoreColor = json.health_score >= 80 ? '#22c55e' : json.health_score >= 50 ? '#f59e0b' : '#ef4444';
    let html = `<div style="display:flex;align-items:center;gap:16px;margin-bottom:12px;">
      <div style="font-size:36px;font-weight:bold;color:${scoreColor};">${json.health_score}%</div>
      <div>
        <div style="font-weight:bold;">Gesundheits-Score</div>
        <div class="muted">${json.sim_count} Sims · ${json.household_count} Haushalte · ${json.world_count} Welten · ${json.save_size_mb.toFixed(1)} MB</div>
      </div>
    </div>`;
    if (issues.length === 0) {
      html += '<div style="color:#22c55e;">✅ Keine Probleme gefunden — dein Speicherstand ist gesund!</div>';
    } else {
      for (const i of issues) {
        const typeIcon = i.type === 'error' ? '❌' : i.type === 'warning' ? '⚠️' : 'ℹ️';
        const typeColor = i.type === 'error' ? '#ef4444' : i.type === 'warning' ? '#f59e0b' : '#60a5fa';
        html += `<div style="padding:8px 12px;margin-bottom:4px;background:#0f172a;border-left:3px solid ${typeColor};border-radius:4px;">
          <div style="font-weight:bold;font-size:13px;">${typeIcon} ${esc(i.category)}</div>
          <div style="font-size:12px;color:${typeColor};">${esc(i.message)}</div>`;
        if (i.details && i.details.length > 0) {
          html += '<div style="margin-top:4px;font-size:11px;opacity:0.7;">';
          for (const d of i.details.slice(0, 10)) {
            html += esc(d) + '<br>';
          }
          if (i.details.length > 10) html += `…und ${i.details.length - 10} weitere`;
          html += '</div>';
        }
        html += '</div>';
      }
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div style="color:#ef4444;">Fehler: ' + esc(e.message) + '</div>';
  }
}

// ═══════════════════════════════════════════════════
// ═══ SPEICHERPLATZ-VISUALISIERUNG ═══
// ═══════════════════════════════════════════════════
function renderDiskUsage(data) {
  const el = document.getElementById('disk-usage-chart');
  const folderSizes = data.folder_sizes || {};
  const entries = Object.entries(folderSizes).filter(([k,v]) => v > 0).sort((a,b) => b[1] - a[1]);
  if (entries.length === 0) {
    el.innerHTML = '<div class="muted">Keine Ordner-Daten vorhanden.</div>';
    return;
  }
  const total = entries.reduce((s, [k,v]) => s + v, 0);
  const colors = ['#3b82f6','#8b5cf6','#ec4899','#f59e0b','#22c55e','#06b6d4','#ef4444','#6366f1','#14b8a6','#f97316','#a855f7','#10b981'];
  let html = `<div style="margin-bottom:12px;"><b>Gesamt:</b> ${(total / 1048576).toFixed(1)} MB</div>`;
  // Bar chart
  html += '<div style="display:flex;height:32px;border-radius:8px;overflow:hidden;margin-bottom:12px;">';
  for (let i = 0; i < entries.length; i++) {
    const [name, size] = entries[i];
    const pct = (size / total * 100);
    if (pct < 0.5) continue;
    const color = colors[i % colors.length];
    html += `<div style="width:${pct.toFixed(1)}%;background:${color};min-width:2px;" title="${esc(name)}: ${(size / 1048576).toFixed(1)} MB (${pct.toFixed(1)}%)"></div>`;
  }
  html += '</div>';
  // Legend
  html += '<div style="display:flex;flex-wrap:wrap;gap:6px 16px;">';
  for (let i = 0; i < entries.length; i++) {
    const [name, size] = entries[i];
    const pct = (size / total * 100).toFixed(1);
    const sizeMB = (size / 1048576).toFixed(1);
    const color = colors[i % colors.length];
    html += `<div style="display:flex;align-items:center;gap:4px;font-size:12px;">
      <span style="width:10px;height:10px;border-radius:2px;background:${color};display:inline-block;"></span>
      <span>${esc(name)}</span>
      <span class="muted">${sizeMB} MB (${pct}%)</span>
    </div>`;
  }
  html += '</div>';
  el.innerHTML = html;
}

// ═══════════════════════════════════════════════════
// ═══ AUTO-RUN TOOL ANALYSES ═══
// ═══════════════════════════════════════════════════
let _toolsAutoRan = false;
function autoRunToolAnalyses() {
  if (_toolsAutoRan) return;
  _toolsAutoRan = true;
  // Kurz warten damit Server bereit ist, dann parallel starten
  setTimeout(() => {
    loadCacheInfo().catch(()=>{});
    scanTrayOrphans().catch(()=>{});
    runScriptSecurityCheck().catch(()=>{});
    findBrokenCC().catch(()=>{});
  }, 500);
}

let _allModsShown = 50;
let _allModsFiltered = [];

function collectAllUniqueFiles(data) {
  // Nutze die vollständige all_files-Liste vom Backend (enthält ALLE gescannten Mods)
  if (data.all_files && data.all_files.length > 0) {
    return data.all_files.slice().sort((a,b) => (a.path||'').localeCompare(b.path||''));
  }
  // Fallback: nur Problemdateien sammeln
  const seen = new Set();
  const all = [];
  for (const g of (data.groups || [])) {
    for (const f of (g.files || [])) {
      if (!seen.has(f.path)) { seen.add(f.path); all.push(f); }
    }
  }
  for (const c of (data.corrupt || [])) {
    if (c.path && !seen.has(c.path)) { seen.add(c.path); all.push(c); }
  }
  for (const conf of (data.conflicts || [])) {
    for (const f of (conf.files || [])) {
      if (f.path && !seen.has(f.path)) { seen.add(f.path); all.push(f); }
    }
  }
  for (const ap of (data.addon_pairs || [])) {
    for (const f of (ap.files || [])) {
      if (f.path && !seen.has(f.path)) { seen.add(f.path); all.push(f); }
    }
  }
  for (const o of (data.outdated || [])) {
    if (o.path && !seen.has(o.path)) { seen.add(o.path); all.push(o); }
  }
  all.sort((a,b) => (a.path||'').localeCompare(b.path||''));
  return all;
}

function renderAllMods(data) {
  const allFiles = collectAllUniqueFiles(data);
  const term = (document.getElementById('allmods-search').value || '').trim().toLowerCase();
  const tagFilter = document.getElementById('allmods-tag-filter').value;
  const catFilter = document.getElementById('allmods-cat-filter').value;

  // Populate tag filter dropdown (once)
  const sel = document.getElementById('allmods-tag-filter');
  if (sel.options.length <= 6) {
    const cfOpt1 = document.createElement('option');
    cfOpt1.value = '__curseforge';
    cfOpt1.textContent = '\ud83d\udd25 CurseForge';
    sel.appendChild(cfOpt1);
    const cfOpt2 = document.createElement('option');
    cfOpt2.value = '__manual';
    cfOpt2.textContent = '\ud83d\udce6 Manuell hinzugef\u00fcgt';
    sel.appendChild(cfOpt2);
    const cfOpt3 = document.createElement('option');
    cfOpt3.value = '__cf_update';
    cfOpt3.textContent = '\u2b06\ufe0f Update verf\u00fcgbar';
    sel.appendChild(cfOpt3);
    for (const t of AVAILABLE_TAGS) {
      const opt = document.createElement('option');
      opt.value = t.name;
      opt.textContent = t.name;
      sel.appendChild(opt);
    }
  }

  // Populate category filter dropdown (dynamically from data)
  const catSel = document.getElementById('allmods-cat-filter');
  if (catSel.options.length <= 1) {
    const cats = (data.stats && data.stats.category_counts) || [];
    for (const [name, count] of cats) {
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = `${name} (${count})`;
      catSel.appendChild(opt);
    }
  }

  // Filter
  const filtered = allFiles.filter(f => {
    const fpath = f.path || '';
    const fname = fpath.split(/[\\\\/]/).pop().toLowerCase();
    const ftags = MOD_TAGS[fpath] || [];
    const fnote = MOD_NOTES[fpath] || '';
    const cfInfo = getCurseForgeInfo(fpath);
    const deep = f.deep || {};
    const fcat = deep.category || '';
    const hay = (fname + ' ' + (f.mod_folder||'') + ' ' + ftags.join(' ') + ' ' + fnote + ' ' + fcat + ' ' + (cfInfo ? cfInfo.name + ' ' + cfInfo.author : '')).toLowerCase();

    if (term && !hay.includes(term)) return false;

    // Category filter
    if (catFilter && fcat !== catFilter) return false;

    if (tagFilter === '__tagged' && ftags.length === 0) return false;
    if (tagFilter === '__untagged' && ftags.length > 0) return false;
    if (tagFilter === '__noted' && !fnote) return false;
    if (tagFilter === '__curseforge' && !cfInfo) return false;
    if (tagFilter === '__manual' && cfInfo) return false;
    if (tagFilter === '__cf_update' && (!cfInfo || !cfInfo.has_update)) return false;
    if (tagFilter && !tagFilter.startsWith('__') && !ftags.includes(tagFilter)) return false;

    return true;
  });

  _allModsFiltered = filtered;
  _allModsShown = 50;

  // Summary
  const tagged = allFiles.filter(f => (MOD_TAGS[f.path]||[]).length > 0).length;
  const noted = allFiles.filter(f => !!MOD_NOTES[f.path]).length;
  const cfCount = allFiles.filter(f => !!getCurseForgeInfo(f.path)).length;
  const cfUpdates = allFiles.filter(f => { const c = getCurseForgeInfo(f.path); return c && c.has_update; }).length;
  const problemCount = (data.summary && data.summary.problem_files) || 0;
  document.getElementById('allmods-summary').innerHTML =
    `<b>${allFiles.length}</b> Mods gesamt | <b>\ud83d\udd25 ${cfCount}</b> CurseForge` +
    (cfUpdates > 0 ? ` (<b>\u2b06\ufe0f ${cfUpdates}</b> Updates)` : '') +
    ` | <b>${allFiles.length - cfCount}</b> manuell | <b>${tagged}</b> getaggt | <b>${noted}</b> mit Notiz` +
    (term || tagFilter || catFilter ? ` | <b>${filtered.length}</b> angezeigt (gefiltert)` : '');

  _renderAllModsPage();
}

function _renderAllModsPage() {
  const filtered = _allModsFiltered;
  const toShow = filtered.slice(0, _allModsShown);

  const cards = toShow.map(f => {
    const fpath = f.path || '';
    const fname = fpath.split(/[\\\\/]/).pop();
    const rel = f.rel && f.rel !== f.path ? f.rel : fpath;
    const showFull = document.getElementById('show_full').checked;
    const fullLine = (f.rel && f.rel !== f.path && showFull)
      ? `<div class="muted small" style="margin-top:2px;"><code>${esc(f.path)}</code></div>` : '';
    const creator = detectCreator(fname);
    const creatorBadge = creator
      ? `<a href="${esc(creator.url)}" target="_blank" rel="noopener" class="pill" style="background:#312e81;color:#a5b4fc;text-decoration:none;cursor:pointer;font-size:10px;" title="Mod von ${esc(creator.name)}">${creator.icon} ${esc(creator.name)}</a>` : '';
    const cfBadge = renderCurseForgeUI(fpath);
    const deep = f.deep || {};
    const fcat = deep.category || '';
    const _catColors = {
      'CAS (Haare 💇)':'#a855f7', 'CAS (Kleidung 👚)':'#06b6d4', 'CAS (Make-Up 💄)':'#ec4899',
      'CAS (Accessoire 💍)':'#f59e0b', 'CAS (Kleidung/Haare/Make-Up)':'#8b5cf6',
      'Objekt/Möbel':'#22c55e', 'Gameplay-Mod (Tuning)':'#ef4444', 'Mesh/Build-Mod':'#14b8a6',
      'Textur/Override':'#f97316', 'Sonstiges':'#64748b',
    };
    const catColor = _catColors[fcat] || '#475569';
    const catBadge = fcat
      ? `<span style="background:${catColor}22;color:${catColor};border:1px solid ${catColor}44;padding:1px 8px;border-radius:10px;font-size:10px;white-space:nowrap;">${esc(fcat)}</span>` : '';

    // Age/Gender + Recolor badges
    const agBadges = (deep.age_gender || []).map(ag => {
      const isAge = ['Kleinkind','Kind','Teen','Erwachsene','Ältere'].includes(ag);
      return `<span style="background:${isAge ? '#1e3a5f' : '#3b1f5e'};color:${isAge ? '#93c5fd' : '#d8b4fe'};padding:0 5px;border-radius:4px;font-size:9px;">${esc(ag)}</span>`;
    }).join(' ');
    const recolorBadge = deep.is_recolor
      ? `<span style="background:#92400e;color:#fde68a;padding:0 5px;border-radius:4px;font-size:9px;">🎨 Recolor</span>` : '';

    return `<div style="padding:10px 14px;background:#0f172a;border:1px solid #1e293b;border-radius:8px;margin-bottom:6px;">
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <span style="font-weight:bold;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:50%;" title="${esc(fpath)}">${esc(fname)}</span>
        <span class="tag" style="font-size:10px;">${esc(f.root_label||'')}</span>
        <span class="muted small">${esc(f.size_h||'?')}</span>
        <span class="muted small">\ud83d\udcc5 ${esc(f.mtime||'?')}</span>
        ${creatorBadge}
        ${cfBadge}
        ${catBadge}
        ${recolorBadge}
        ${agBadges}
        <span class="muted small" style="margin-left:auto;">${esc(f.mod_folder||'')}</span>
      </div>
      <div class="muted small" style="margin-top:2px;"><code>${esc(rel)}</code></div>
      ${fullLine}
      <div style="margin-top:6px;">
        ${renderTagsUI(fpath)}
      </div>
      <div style="margin-top:4px;">
        ${renderNotesUI(fpath)}
      </div>
      <div class="flex" style="margin-top:6px;gap:4px;">
        <button class="btn btn-ghost" style="font-size:11px;padding:3px 8px;" data-act="open_folder" data-path="${esc(fpath)}">📂 Ordner</button>
        <button class="btn btn-ghost" style="font-size:11px;padding:3px 8px;" data-act="copy" data-path="${esc(fpath)}">📋 Pfad</button>
      </div>
    </div>`;
  }).join('');

  document.getElementById('allmods-list').innerHTML = cards || '<div class="muted">Keine Mods gefunden.</div>';

  const moreBtn = document.getElementById('allmods-loadmore');
  if (_allModsShown < filtered.length) {
    moreBtn.style.display = '';
    document.getElementById('btn_allmods_more').textContent = `\u2b07\ufe0f Mehr laden (${_allModsShown} von ${filtered.length})\u2026`;
  } else {
    moreBtn.style.display = 'none';
  }
}

// Event listeners for "Alle Mods" section
let _allModsSearchTimer = null;
document.getElementById('allmods-search').addEventListener('input', () => {
  clearTimeout(_allModsSearchTimer);
  _allModsSearchTimer = setTimeout(() => { if (window.__DATA) renderAllMods(window.__DATA); }, 300);
});
document.getElementById('allmods-tag-filter').addEventListener('change', () => {
  if (window.__DATA) renderAllMods(window.__DATA);
});
document.getElementById('allmods-cat-filter').addEventListener('change', () => {
  if (window.__DATA) renderAllMods(window.__DATA);
});
document.getElementById('btn_allmods_more').addEventListener('click', () => {
  _allModsShown += 50;
  _renderAllModsPage();
});

// ---- CC-Galerie ----
let _galleryFiltered = [];
let _galleryShown = 60;

function renderGallery(data) {
  const allFiles = collectAllUniqueFiles(data);
  // Nur Dateien mit Thumbnail
  const withThumb = allFiles.filter(f => f.deep && f.deep.thumbnail_b64);
  if (withThumb.length === 0) {
    document.getElementById('gallery-grid').innerHTML = '<div class="muted" style="padding:20px;text-align:center;">Keine CC-Vorschaubilder gefunden. Starte erst einen Scan.</div>';
    return;
  }

  // Populate category filter
  const catSel = document.getElementById('gallery-cat-filter');
  if (catSel.options.length <= 1) {
    const cats = {};
    for (const f of withThumb) {
      const cat = (f.deep || {}).category || '';
      if (cat) cats[cat] = (cats[cat] || 0) + 1;
    }
    for (const [name, count] of Object.entries(cats).sort((a, b) => b[1] - a[1])) {
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = `${name} (${count})`;
      catSel.appendChild(opt);
    }
  }

  const term = (document.getElementById('gallery-search').value || '').trim().toLowerCase();
  const catFilter = document.getElementById('gallery-cat-filter').value;
  const ageFilter = document.getElementById('gallery-age-filter').value;
  const genderFilter = document.getElementById('gallery-gender-filter').value;
  const recolorOnly = document.getElementById('gallery-recolor-only').checked;

  const filtered = withThumb.filter(f => {
    const d = f.deep || {};
    const fname = (f.path || '').split(/[\\\\/]/).pop().toLowerCase();
    if (term && !fname.includes(term) && !(d.category || '').toLowerCase().includes(term)) return false;
    if (catFilter && d.category !== catFilter) return false;
    const ag = d.age_gender || [];
    if (ageFilter && !ag.includes(ageFilter)) return false;
    if (genderFilter && !ag.includes(genderFilter)) return false;
    if (recolorOnly && !d.is_recolor) return false;
    return true;
  });

  _galleryFiltered = filtered;
  _galleryShown = Infinity;

  document.getElementById('gallery-summary').innerHTML =
    `<b>${filtered.length}</b> von ${withThumb.length} CC mit Vorschau`;

  _renderGalleryPage();
}

function _renderGalleryPage() {
  const toShow = _galleryFiltered.slice(0, _galleryShown);
  const _catColors = {
    'CAS (Haare 💇)':'#a855f7', 'CAS (Kleidung 👚)':'#06b6d4', 'CAS (Make-Up 💄)':'#ec4899',
    'CAS (Accessoire 💍)':'#f59e0b', 'CAS (Kleidung/Haare/Make-Up)':'#8b5cf6',
    'Objekt/Möbel':'#22c55e', 'Gameplay-Mod (Tuning)':'#ef4444', 'Mesh/Build-Mod':'#14b8a6',
    'Textur/Override':'#f97316', 'Sonstiges':'#64748b',
  };
  const cards = toShow.map(f => {
    const d = f.deep || {};
    const fname = (f.path || '').split(/[\\\\/]/).pop();
    const cat = d.category || '';
    const catColor = _catColors[cat] || '#475569';
    const bodyTypes = (d.cas_body_types || []).slice(0, 2).join(', ');
    const recolor = d.is_recolor ? '<span style="position:absolute;top:4px;right:4px;background:#92400e;color:#fde68a;padding:0 4px;border-radius:3px;font-size:9px;">🎨</span>' : '';
    const agBadges = (d.age_gender || []).map(ag => {
      const isAge = ['Kleinkind','Kind','Teen','Erwachsene','Ältere'].includes(ag);
      return `<span style="background:${isAge ? '#1e3a5f' : '#3b1f5e'};color:${isAge ? '#93c5fd' : '#d8b4fe'};padding:0 3px;border-radius:3px;font-size:8px;">${esc(ag)}</span>`;
    }).join(' ');

    return `<div class="gallery-card" style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;overflow:hidden;cursor:pointer;transition:transform .15s,box-shadow .15s;position:relative;" onclick="openGalleryLightbox('${esc(d.thumbnail_b64)}','${esc(fname)}','${esc(cat)}','${esc(f.path)}')" title="${esc(fname)}">
      ${recolor}
      <div style="width:100%;aspect-ratio:1;background:#1e293b;display:flex;align-items:center;justify-content:center;overflow:hidden;">
        <img src="${d.thumbnail_b64}" style="max-width:100%;max-height:100%;object-fit:contain;" loading="lazy" alt="${esc(fname)}">
      </div>
      <div style="padding:6px 8px;">
        <div style="font-size:10px;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(fname)}</div>
        <div style="font-size:9px;color:${catColor};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(cat)}</div>
        ${bodyTypes ? `<div style="font-size:9px;color:#94a3b8;">${esc(bodyTypes)}</div>` : ''}
        ${agBadges ? `<div style="margin-top:2px;">${agBadges}</div>` : ''}
      </div>
    </div>`;
  }).join('');
  document.getElementById('gallery-grid').innerHTML = cards || '<div class="muted" style="grid-column:1/-1;">Keine CC mit Vorschau gefunden.</div>';
  const moreBtn = document.getElementById('gallery-loadmore');
  moreBtn.style.display = 'none';
}

function galleryLoadMore() {
  _galleryShown += 60;
  _renderGalleryPage();
}

function openGalleryLightbox(src, name, cat, path) {
  const ov = document.getElementById('lightbox-overlay');
  const content = document.getElementById('lightbox-content');
  content.innerHTML = `
    <div class="lb-single" style="text-align:center;">
      <img src="${src}" style="max-width:90vw;max-height:70vh;border-radius:8px;border:2px solid #334155;" alt="${esc(name)}">
      <div style="margin-top:12px;color:#e2e8f0;font-size:14px;font-weight:bold;">${esc(name)}</div>
      <div style="color:#94a3b8;font-size:12px;">${esc(cat)}</div>
      <div style="margin-top:8px;">
        <button class="btn btn-ghost" style="font-size:11px;" data-act="open_folder" data-path="${esc(path)}">📂 Ordner öffnen</button>
        <button class="btn btn-ghost" style="font-size:11px;" data-act="copy" data-path="${esc(path)}">📋 Pfad kopieren</button>
      </div>
    </div>`;
  ov.classList.add('active');
}

// Gallery event listeners
let _gallerySearchTimer = null;
document.getElementById('gallery-search').addEventListener('input', () => {
  clearTimeout(_gallerySearchTimer);
  _gallerySearchTimer = setTimeout(() => { if (window.__DATA) renderGallery(window.__DATA); }, 300);
});
['gallery-cat-filter','gallery-age-filter','gallery-gender-filter'].forEach(id => {
  document.getElementById(id).addEventListener('change', () => { if (window.__DATA) renderGallery(window.__DATA); });
});
document.getElementById('gallery-recolor-only').addEventListener('change', () => { if (window.__DATA) renderGallery(window.__DATA); });

function renderOutdated(data) {
  const section = document.getElementById('outdated-section');
  const list = data.outdated || [];
  const gi = data.game_info;
  if (list.length === 0 || !gi) {
    document.getElementById('outdated-game-ver').innerHTML = '';
    document.getElementById('outdated-summary').innerHTML = '<span style="color:#22c55e;">\u2705 Keine veralteten Mods gefunden.</span>';
    document.getElementById('outdated-list').innerHTML = '';
    return;
  }
  document.getElementById('outdated-game-ver').innerHTML =
    `Spielversion: <b>${esc(gi.version)}</b> | Patch vom: <b>${esc(gi.patch_date)}</b>`;

  const filterHigh = document.getElementById('outdated-filter-high');
  const filterMid = document.getElementById('outdated-filter-mid');
  const filterLow = document.getElementById('outdated-filter-low');

  function _render() {
    const showHigh = filterHigh.checked;
    const showMid = filterMid.checked;
    const showLow = filterLow.checked;
    const filtered = list.filter(f => {
      if (f.risk === 'hoch') return showHigh;
      if (f.risk === 'mittel') return showMid;
      return showLow;
    });

    const high = filtered.filter(f => f.risk === 'hoch').length;
    const mid = filtered.filter(f => f.risk === 'mittel').length;
    const low = filtered.filter(f => f.risk !== 'hoch' && f.risk !== 'mittel').length;
    document.getElementById('outdated-summary').innerHTML =
      `${filtered.length} von ${list.length} Mods angezeigt: ` +
      (high ? `<b style="color:#ef4444;">⚠️ ${high} hoch</b> ` : '') +
      (mid ? `<b style="color:#fbbf24;">⚡ ${mid} mittel</b> ` : '') +
      (low ? `<b style="color:#6ee7b7;">✅ ${low} niedrig</b>` : '');

    const cards = filtered.map(f => {
      const riskColors = {hoch:'#ef4444',mittel:'#fbbf24',niedrig:'#22c55e',unbekannt:'#94a3b8'};
      const riskIcons = {hoch:'⚠️',mittel:'⚡',niedrig:'✅',unbekannt:'❓'};
      const rc = riskColors[f.risk] || '#94a3b8';
      const ri = riskIcons[f.risk] || '❓';
      const name = (f.rel || f.path || '').split(/[\\/]/).pop();
      const folder = f.mod_folder || '';
      const daysStr = f.days_before_patch === 1 ? '1 Tag' : `${f.days_before_patch} Tage`;

      // Patches hinterher
      const patchesBehind = f.patches_behind || 0;
      const patchBadge = patchesBehind > 0
        ? `<span style="background:${patchesBehind >= 3 ? '#7f1d1d' : patchesBehind >= 2 ? '#78350f' : '#1e3a5f'};color:${patchesBehind >= 3 ? '#fca5a5' : patchesBehind >= 2 ? '#fde68a' : '#93c5fd'};padding:1px 6px;border-radius:4px;font-size:10px;font-weight:bold;margin-left:4px;">${patchesBehind} Patch${patchesBehind > 1 ? 'es' : ''} hinterher</span>`
        : '';
      const missedPatches = (f.missed_patches || []);
      const missedList = missedPatches.length > 0
        ? `<div class="muted small" style="margin-top:2px;font-size:10px;">Verpasste Patches: ${missedPatches.map(([v,d]) => `<span style="background:#1e293b;border:1px solid #475569;padding:0 4px;border-radius:3px;margin:1px;">${esc(v)} ${esc(d)}</span>`).join(' ')}</div>`
        : '';

      return `<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 12px;background:#0f172a;border:1px solid #334155;border-radius:8px;margin-bottom:6px;${patchesBehind >= 3 ? 'border-left:3px solid #ef4444;' : ''}">
        <span style="font-size:18px;min-width:24px;text-align:center;margin-top:2px;">${ri}</span>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${esc(f.path)}">${esc(name)}${patchBadge}</div>
          <div class="muted small">${esc(folder)} | ${esc(f.size_h)} | Geändert: ${esc(f.mtime)} | <b style="color:${rc};">${daysStr} vor Patch</b></div>
          <div class="muted small" style="color:${rc};">${esc(f.risk_reason || '')}</div>
          ${missedList}
        </div>
        <div style="display:flex;gap:4px;flex-shrink:0;">
          <button class="btn btn-ghost" style="font-size:11px;padding:3px 8px;" data-act="open_folder" data-path="${esc(f.path)}" title="Ordner öffnen">📂</button>
          <button class="btn btn-ghost" style="font-size:11px;padding:3px 8px;" data-act="copy" data-path="${esc(f.path)}" title="Pfad kopieren">📋</button>
        </div>
      </div>`;
    }).join('');
    document.getElementById('outdated-list').innerHTML = cards || '<div class="muted">Keine Mods mit gewähltem Filter.</div>';
  }

  filterHigh.onchange = _render;
  filterMid.onchange = _render;
  filterLow.onchange = _render;
  _render();
}

function renderPerFile(data) {
  const map = buildPerFileMap(data);
  const term = (document.getElementById('pf-search').value || '').trim().toLowerCase();
  const showFull = document.getElementById('show_full').checked;

  // Sortiere: meiste Findings zuerst, dann alphabetisch
  let entries = Array.from(map.values());
  entries.sort((a, b) => {
    if (b.findings.length !== a.findings.length) return b.findings.length - a.findings.length;
    return a.file.path.localeCompare(b.file.path);
  });

  if (term) {
    entries = entries.filter(e => {
      const noteTxt = MOD_NOTES[e.file.path] || '';
      const tagsTxt = (MOD_TAGS[e.file.path] || []).join(' ');
      const hay = (e.file.path + ' ' + e.file.rel + ' ' + e.findings.map(f => f.typeLabel).join(' ') + ' ' + noteTxt + ' ' + tagsTxt).toLowerCase();
      return hay.includes(term);
    });
  }

  document.getElementById('perfile-summary').innerHTML =
    `<b>${entries.length}</b> Dateien mit Auff\u00e4lligkeiten gefunden.` +
    ` <span class="muted small">Sortiert: meiste Probleme zuerst.</span>`;

  // Z\u00e4hler f\u00fcr Zusammenfassung
  let cntCorrupt = 0, cntConflict = 0, cntAddon = 0, cntDupe = 0;
  for (const e of entries) {
    const cats = new Set(e.findings.map(fi => fi.category));
    if (cats.has('corrupt')) cntCorrupt++;
    if (cats.has('conflict')) cntConflict++;
    if (cats.has('addon')) cntAddon++;
    if (cats.has('group')) cntDupe++;
  }
  const statsHtml = [
    cntCorrupt ? `<span class="corrupt-status no_dbpf">\u26a0\ufe0f ${cntCorrupt} korrupt</span>` : '',
    cntConflict ? `<span class="conflict-badge">\ud83d\udd00 ${cntConflict} Konflikte</span>` : '',
    cntAddon ? `<span class="addon-badge">\ud83e\udde9 ${cntAddon} Addons</span>` : '',
    cntDupe ? `<span class="pill" style="background:#1e3a5f;color:#60a5fa;">${cntDupe} Duplikate</span>` : '',
  ].filter(Boolean).join(' ');
  document.getElementById('perfile-summary').innerHTML += `<div style="margin-top:6px;">${statsHtml}</div>`;

  const cards = entries.map(e => {
    const f = e.file;
    const fname = (f.rel || f.path).split(/[\\\\/]/).pop();
    const relPath = f.rel && f.rel !== f.path ? f.rel : '';
    const fullLine = (relPath && showFull)
      ? `<div class="muted small pathline" style="margin-top:2px;"><code>${esc(f.path)}</code></div>`
      : '';
    const checked = selected.has(f.path) ? 'checked' : '';

    // Kategorie-Badges oben
    const cats = new Set(e.findings.map(fi => fi.category));
    const badges = [];
    if (cats.has('corrupt')) badges.push('<span class="corrupt-status no_dbpf">⚠️ Korrupt</span>');
    if (cats.has('conflict')) badges.push('<span class="conflict-badge">🔀 Konflikt</span>');
    if (cats.has('addon')) badges.push('<span class="addon-badge">🧩 Addon</span>');
    const groupTypes = new Set(e.findings.filter(fi => fi.category === 'group').map(fi => fi.type));
    if (groupTypes.has('content')) badges.push('<span class="pill" style="background:#4c1d95;color:#c4b5fd;">Inhalt-Duplikat</span>');
    if (groupTypes.has('name')) badges.push('<span class="pill" style="background:#1e3a5f;color:#60a5fa;">Name-Duplikat</span>');
    if (groupTypes.has('similar')) badges.push('<span class="pill" style="background:#134e4a;color:#5eead4;">Ähnlich</span>');

    // Finding-Sektionen
    const sections = e.findings.map(fi => {
      if (fi.category === 'corrupt') {
        return `<div class="pf-section pf-corrupt">
          <div class="pf-section-title">\u26a0\ufe0f ${esc(fi.statusLabel)}</div>
          <div class="muted small">${esc(fi.statusHint)}</div>
          <div class="muted small" style="margin-top:6px; color:#fca5a5;">\ud83d\udc49 <b>Empfehlung:</b> Diese Datei in Quarant\u00e4ne verschieben. Sie funktioniert wahrscheinlich nicht und kann Fehler verursachen.</div>
        </div>`;
      }

      if (fi.category === 'group') {
        const icon = fi.type === 'name' ? '\ud83d\udcdb' : fi.type === 'content' ? '\ud83d\udce6' : '\ud83d\udd24';
        const explanation = fi.type === 'content'
          ? 'Diese Dateien sind <b>exakt identisch</b> \u2014 der Inhalt ist Byte f\u00fcr Byte gleich. Eine davon ist \u00fcberfl\u00fcssig und kann gel\u00f6scht werden.'
          : fi.type === 'name'
          ? 'Diese Dateien haben den <b>gleichen Namen</b> aber sind in verschiedenen Ordnern. Meistens ist eine davon veraltet.'
          : 'Diese Dateien haben <b>sehr \u00e4hnliche Namen</b> \u2014 k\u00f6nnten verschiedene Versionen desselben Mods sein.';
        const partnerList = fi.partnerFiles.map(p =>
          `<div class="pf-partner">${esc(p.root_label)} \u00b7 <code>${esc((p.rel||p.path).split(/[\\\\/]/).pop())}</code> \u00b7 ${esc(p.size_h)} \u00b7 ${esc(p.mtime)}</div>`
        ).join('');
        const hint = fi.type === 'content'
          ? `<div class="muted small" style="margin-top:6px; color:#c4b5fd;">\ud83d\udc49 <b>Empfehlung:</b> Behalte die neueste Version und verschiebe die anderen in Quarant\u00e4ne.</div>`
          : fi.type === 'name'
          ? `<div class="muted small" style="margin-top:6px; color:#60a5fa;">\ud83d\udc49 <b>Empfehlung:</b> Pr\u00fcfe welche Version du brauchst (Datum vergleichen). Die \u00e4ltere kann meistens weg.</div>`
          : `<div class="muted small" style="margin-top:6px; color:#5eead4;">\ud83d\udc49 <b>Hinweis:</b> Pr\u00fcfe ob das verschiedene Versionen sind. Falls ja, behalte nur die neueste.</div>`;
        return `<div class="pf-section ${fi.typeClass}">
          <div class="pf-section-title">${icon} ${esc(fi.typeLabel)}: "${esc(fi.key)}"</div>
          <div class="muted small" style="margin-bottom:6px;">${explanation}</div>
          <div class="muted small" style="margin-bottom:4px;"><b>${fi.partners.length}</b> weitere Datei(en) mit gleichem ${fi.type === 'content' ? 'Inhalt' : 'Namen'}:</div>
          ${partnerList}
          ${hint}
        </div>`;
      }

      if (fi.category === 'addon') {
        const typePills = fi.topTypes.map(([n,c]) => `<span class="conflict-type-pill">${esc(n)}: ${c}</span>`).join('');
        const partnerList = fi.partnerFiles.map(p =>
          `<div class="pf-partner">\ud83e\udde9 <code>${esc((p.rel||p.path).split(/[\\\\/]/).pop())}</code> \u00b7 ${esc(p.size_h)} \u00b7 ${esc(p.mtime)}</div>`
        ).join('');
        return `<div class="pf-section pf-addon">
          <div class="pf-section-title">\ud83e\udde9 Addon-Beziehung <span class="addon-ok">\u2705 OK</span></div>
          <div class="muted small">Diese Datei ist ein <b>Addon/Erweiterung</b> f\u00fcr einen anderen Mod (oder umgekehrt). Das ist normal und gewollt!</div>
          <div class="muted small" style="margin-top:4px;">${fi.sharedCount} geteilte Ressource-IDs \u00b7 ${typePills}</div>
          <div class="muted small" style="margin-top:4px;">Geh\u00f6rt zusammen mit:</div>
          ${partnerList}
          <div class="muted small" style="margin-top:6px; color:#6ee7b7;">\ud83d\udc49 <b>Aktion:</b> Nichts tun \u2014 <b>beide behalten!</b> Wenn du eins l\u00f6schst, funktioniert das andere nicht richtig.</div>
        </div>`;
      }

      if (fi.category === 'conflict') {
        const typePills = fi.topTypes.map(([n,c]) => `<span class="conflict-type-pill">${esc(n)}: ${c}</span>`).join('');
        const partnerList = fi.partnerFiles.map(p =>
          `<div class="pf-partner">\ud83d\udd00 <code>${esc((p.rel||p.path).split(/[\\\\/]/).pop())}</code> \u00b7 ${esc(p.size_h)} \u00b7 ${esc(p.mtime)}</div>`
        ).join('');
        const severity = fi.sharedCount >= 10 ? 'hoch' : fi.sharedCount >= 3 ? 'mittel' : 'niedrig';
        const sevColor = severity === 'hoch' ? '#fca5a5' : severity === 'mittel' ? '#fde68a' : '#94a3b8';
        const sevLabel = severity === 'hoch' ? '\u26a0\ufe0f Wichtig' : severity === 'mittel' ? '\u26a0 Pr\u00fcfen' : '\u2139\ufe0f Gering';
        const sevExplain = fi.sharedCount <= 2
          ? 'Nur 1-2 geteilte IDs \u2014 wahrscheinlich harmlos (z.B. Standard-Ressource die viele Mods nutzen).'
          : fi.sharedCount <= 20
          ? 'Mehrere geteilte IDs \u2014 k\u00f6nnte eine alte Version desselben Mods sein. Pr\u00fcfe Datum und Namen.'
          : 'Viele geteilte IDs \u2014 wahrscheinlich derselbe Mod in verschiedenen Versionen. Nur die neueste behalten!';
        return `<div class="pf-section pf-conflict">
          <div class="pf-section-title">\ud83d\udd00 Ressource-Konflikt <span style="color:${sevColor}; font-size:12px; margin-left:8px;">${sevLabel} (${fi.sharedCount} IDs)</span></div>
          <div class="muted small">${sevExplain}</div>
          <div class="muted small" style="margin-top:4px;">${typePills}</div>
          <div class="muted small" style="margin-top:6px;">Kollidiert mit ${fi.partners.length} Datei(en):</div>
          ${partnerList}
          <div class="muted small" style="margin-top:6px; color:#c4b5fd;">\ud83d\udc49 <b>Empfehlung:</b> ${fi.sharedCount <= 2 ? 'Wahrscheinlich OK \u2014 nur handeln wenn du Probleme im Spiel bemerkst.' : 'Behalte die neuere Datei (h\u00f6heres Datum) und verschiebe die \u00e4ltere in Quarant\u00e4ne.'}</div>
        </div>`;
      }

      if (fi.category === 'skin') {
        const sevColor = fi.severity === 'hoch' ? '#fca5a5' : fi.severity === 'niedrig' ? '#93c5fd' : '#fde68a';
        const sevLabel = fi.severity === 'hoch' ? '\u26a0\ufe0f Kritisch' : fi.severity === 'niedrig' ? '\u2139\ufe0f Hinweis' : '\u26a1 Mittel';
        const partnerList = (fi.partnerFiles||[]).map(p =>
          `<div class="pf-partner">\ud83e\uddd1 <code>${esc((p.rel||p.path).split(/[\\\\/]/).pop())}</code> \u00b7 ${esc(p.size_h)} \u00b7 ${esc(p.mtime)}</div>`
        ).join('');
        return `<div class="pf-section pf-skin">
          <div class="pf-section-title">\ud83e\uddd1 ${esc(fi.label || 'Skin-Konflikt')} <span style="color:${sevColor}; font-size:12px; margin-left:8px;">${sevLabel}</span></div>
          <div class="muted small">${esc(fi.hint || 'Skin/Overlay-Mod-Konflikt erkannt.')}</div>
          ${fi.partners && fi.partners.length > 0 ? `<div class="muted small" style="margin-top:6px;">Kollidiert mit:</div>${partnerList}` : ''}
          <div class="muted small" style="margin-top:6px; color:#fca5a5;">\ud83d\udc49 <b>Empfehlung:</b> Nur EINEN Skin/Overlay-Mod dieses Typs behalten. Entferne den anderen, um Stein-Haut zu vermeiden.</div>
        </div>`;
      }

      return '';
    }).join('');

    // Gesamt-Empfehlung pro Karte
    const hasCats = new Set(e.findings.map(fi => fi.category));
    let recommendation = '';
    if (hasCats.has('corrupt')) {
      recommendation = `<div style="background:#2b1111; border:1px solid #6b2b2b; border-radius:8px; padding:8px 12px; margin-top:10px;">
        <span style="color:#fca5a5; font-weight:bold;">\u26a0\ufe0f Empfehlung: In Quarant\u00e4ne verschieben</span>
        <span class="muted small"> \u2014 Datei ist besch\u00e4digt</span>
      </div>`;
    } else if (hasCats.has('conflict') && !hasCats.has('addon')) {
      const maxShared = Math.max(...e.findings.filter(fi => fi.category === 'conflict').map(fi => fi.sharedCount));
      if (maxShared > 2) {
        recommendation = `<div style="background:#1a1a2e; border:1px solid #3a3a5e; border-radius:8px; padding:8px 12px; margin-top:10px;">
          <span style="color:#c4b5fd; font-weight:bold;">\ud83d\udd00 Empfehlung: Datum pr\u00fcfen</span>
          <span class="muted small"> \u2014 Falls eine \u00e4ltere Version: in Quarant\u00e4ne verschieben</span>
        </div>`;
      }
    } else if (hasCats.has('group') && !hasCats.has('conflict') && !hasCats.has('addon')) {
      const hasContent = e.findings.some(fi => fi.type === 'content');
      if (hasContent) {
        recommendation = `<div style="background:#1a1428; border:1px solid #3a2a5e; border-radius:8px; padding:8px 12px; margin-top:10px;">
          <span style="color:#c4b5fd; font-weight:bold;">\ud83d\udce6 Empfehlung: Duplikat entfernen</span>
          <span class="muted small"> \u2014 Identische Kopie existiert, eine davon ist \u00fcberfl\u00fcssig</span>
        </div>`;
      }
    }

    return `<div class="pf-card">
      <div class="pf-header">
        <div style="display:flex; align-items:center; gap:8px;">
          <input class="sel selbox" type="checkbox" data-path="${esc(f.path)}" ${checked}>
          <span class="pf-name">${esc(fname)}</span>
        </div>
        <div class="pf-meta">
          ${badges.join(' ')}
        </div>
      </div>
      <div class="muted small pathline" style="margin-top:4px;"><code>${esc(relPath || f.path)}</code></div>
      ${fullLine}
      <div class="pf-meta" style="margin-top:6px;">
        <span class="tag">${esc(f.root_label)}</span>
        <span class="size" title="Dateigröße">${esc(f.size_h || '?')}</span>
        <span class="date" title="Zuletzt geändert — meistens das Datum vom Mod-Ersteller">📅 ${esc(f.mtime || '?')}</span>
      </div>
      ${renderTagsUI(f.path)}
      ${sections}
      ${recommendation}
      ${renderNotesUI(f.path)}
      <div class="flex" style="margin-top:10px;">
        <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben — du kannst die Datei jederzeit zurückholen">📦 Quarantäne</button>
        <button class="btn" data-act="open_folder" data-path="${esc(f.path)}" title="Öffnet den Ordner im Windows Explorer">📂 Ordner öffnen</button>
        <button class="btn btn-ghost" data-act="copy" data-path="${esc(f.path)}" title="Kopiert den Dateipfad in die Zwischenablage">📋 Pfad kopieren</button>
      </div>
    </div>`;
  }).join('');

  document.getElementById('perfile-list').innerHTML = cards || '<p class="muted">Keine Dateien mit Auffälligkeiten.</p>';
}

// View-Toggle
let currentView = 'groups';
document.getElementById('view-toggle').addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-view]');
  if (!btn) return;
  const view = btn.dataset.view;
  if (view === currentView) return;
  currentView = view;

  // Toggle-Buttons aktiv/inaktiv
  document.querySelectorAll('#view-toggle button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const groupsView = document.getElementById('groups-view');
  const perfileView = document.getElementById('perfile-view');
  const corruptSec = document.getElementById('corrupt-section');
  const addonSec = document.getElementById('addon-section');
  const conflictSec = document.getElementById('conflict-section');
  const title = document.getElementById('view-title');

  if (view === 'groups') {
    groupsView.style.display = 'block';
    perfileView.style.display = 'none';
    title.textContent = 'Gruppen';
  } else {
    groupsView.style.display = 'none';
    perfileView.style.display = 'block';
    title.textContent = 'Pro Datei';
    if (window.__DATA) renderPerFile(window.__DATA);
  }
});

// Per-File Suche
let _pfSearchTimer = null;
document.getElementById('pf-search').addEventListener('input', () => {
  clearTimeout(_pfSearchTimer);
  _pfSearchTimer = setTimeout(() => {
    if (currentView === 'perfile' && window.__DATA) renderPerFile(window.__DATA);
  }, 300);
});

async function reloadData() {
  const data = await loadData();
  window.__DATA = data;
  _SEARCH_INDEX_DIRTY = true;  // Index bei nächster Suche neu bauen
  await Promise.all([loadNotes(), loadTags(), loadCurseForge()]);
  document.getElementById('summary').innerHTML = renderSummary(data);
  document.getElementById('roots').innerHTML = renderRoots(data);
  document.getElementById('groups').innerHTML = renderGroups(data);
  renderCorrupt(data);
  renderAddons(data);
  renderContainedIn(data);
  renderConflicts(data);
  renderSkinCheck(data);
  renderOutdated(data);
  renderDependencies(data);
  updateNavBadges(data);
  checkAllOK(data);
  renderStats(data);
  loadQuarantine();
  renderAllMods(data);
  renderGallery(data);
  renderNonModFiles(data);
  renderDiskUsage(data);
  populatePackageList();
  // Auto-run: Alle Werkzeug-Analysen nach Scan
  autoRunToolAnalyses();
  // Tray-Daten aktualisieren falls im Scan enthalten
  if (data.tray) {
    _trayData = data.tray;
    renderTrayResults();
    document.getElementById('btn-tray-refresh').style.display = 'inline-block';
  }
  if (currentView === 'perfile') renderPerFile(data);
  // re-apply checkbox states (selected Set already)
  document.querySelectorAll('input.sel[data-path]').forEach(cb => {
    cb.checked = selected.has(cb.dataset.path);
  });
  updateSelCount();
}

async function doQuarantine(path) {
  // Dateiname für Bestätigung
  const fname = path.split(/[\\\\/]/).pop();
  // Tray-warning check
  let trayWarn = '';
  if (_trayData && _trayData.mod_usage) {
    const np = path.toLowerCase().replace(/\\\\/g, '/');
    for (const [mp, info] of Object.entries(_trayData.mod_usage)) {
      const nmp = mp.toLowerCase().replace(/\\\\/g, '/');
      if (np === nmp || np.endsWith('/' + nmp.split('/').pop())) {
        const names = (info.used_by || []).slice(0, 5).join(', ');
        trayWarn = `\\n\\n⚠️ ACHTUNG: Dieser Mod wird von ${info.used_count} gespeicherten Sims/Häusern verwendet!\\nVerwendet von: ${names}`;
        break;
      }
    }
  }
  if (!confirm(`📦 In Quarantäne verschieben?\\n\\n${fname}\\n\\nDie Datei wird in den Quarantäne-Ordner verschoben. Du kannst sie im Tab 🗃️ Quarantäne jederzeit zurückholen.${trayWarn}`)) return;
  const res = await postAction('quarantine', path, {});
  console.log('[QUARANTINE]', path, res);
  setLast('📦 Quarantäne: ' + path);
  addLog('QUARANTINE ' + (res.moved ? 'OK' : 'NOTE') + ' :: ' + path + (res.to ? (' -> ' + res.to) : ''));
  removeRowsForPath(path);
  await reloadData();
}

async function doDelete(path) {
  // Safety redirect: "delete" now goes through quarantine.
  // Permanent deletion is only possible from the quarantine tab.
  await doQuarantine(path);
}

async function doRestore(path) {
  const res = await postAction('restore', path, {});
  console.log('[RESTORE]', path, res);
  if (res.restored) {
    setLast('↩️ Zurückgeholt: ' + (res.to || path));
    addLog('RESTORE OK :: ' + path + ' -> ' + (res.to || '?'));
  } else {
    setLast('⚠️ Datei nicht gefunden: ' + path);
    addLog('RESTORE NOTE :: ' + path + ' :: ' + (res.note || ''));
  }
  loadQuarantine();
}

async function doDeleteQ(path) {
  if (!confirm('Datei endgültig löschen?\\n\\n' + path)) return;
  const res = await postAction('delete_q', path, {});
  console.log('[DELETE_Q]', path, res);
  setLast('🗑 Quarantäne-Datei gelöscht: ' + path);
  addLog('DELETE_Q ' + (res.deleted ? 'OK' : 'NOTE') + ' :: ' + path);
  loadQuarantine();
}

async function doOpenFolder(path) {
  const res = await postAction('open_folder', path, {});
  console.log('[OPEN_FOLDER]', path, res);
  setLast('📂 Ordner: ' + path);
  addLog('OPEN_FOLDER :: ' + path);
}

async function copyPath(path) {
  await copyText(path);
  console.log('[COPY]', path);
  setLast('📋 Pfad kopiert: ' + path);
  addLog('COPY :: ' + path);
}

// Selection handling
document.addEventListener('change', (ev) => {
  const cb = ev.target.closest('input.sel[data-path]');
  if (!cb) return;
  const path = cb.dataset.path;
  if (cb.checked) selected.add(path);
  else selected.delete(path);
  updateSelCount();
});

function clearSelection() {
  selected.clear();
  document.querySelectorAll('input.sel[data-path]').forEach(cb => cb.checked = false);
  updateSelCount();
  setBatchStatus('Auswahl geleert.');
}

document.getElementById('btn_clear_sel').addEventListener('click', clearSelection);

// Quarantäne Aktualisieren-Button
document.getElementById('btn_reload_quarantine')?.addEventListener('click', () => loadQuarantine());

function selectGroupAll(gi) {
  const g = window.__DATA?.groups?.[gi];
  if (!g) return;
  for (const f of g.files) selected.add(f.path);
  document.querySelectorAll(`input.sel[data-gi="${gi}"]`).forEach(cb => cb.checked = true);
  updateSelCount();
  setBatchStatus(`Gruppe ${gi}: alle markiert.`);
}

function selectGroupRest(gi) {
  const g = window.__DATA?.groups?.[gi];
  if (!g) return;
  const keep = preferKeepPath(g.files);
  for (const f of g.files) {
    if (f.path !== keep) selected.add(f.path);
  }
  document.querySelectorAll(`input.sel[data-gi="${gi}"]`).forEach(cb => {
    cb.checked = (cb.dataset.path !== keep);
  });
  updateSelCount();
  setBatchStatus(`Gruppe ${gi}: Rest markiert (1 behalten).`);
}

async function batchAction(action, paths, confirmText=null) {
  paths = Array.from(new Set(paths)).filter(Boolean);
  if (paths.length === 0) return;

  if (confirmText) {
    if (!confirm(confirmText)) return;
  }

  const overlay = document.getElementById('batch-progress-overlay');
  const bar = document.getElementById('batch-progress-bar');
  const text = document.getElementById('batch-progress-text');
  const file = document.getElementById('batch-progress-file');
  const title = document.getElementById('batch-progress-title');
  title.textContent = '📦 Quarantäne…';
  bar.style.width = '0%';
  text.textContent = '0 / ' + paths.length;
  file.textContent = '';
  overlay.style.display = 'flex';

  try {
    let ok = 0, fail = 0;
    for (let i = 0; i < paths.length; i++) {
      const p = paths[i];
      const pct = Math.round(((i + 1) / paths.length) * 100);
      bar.style.width = pct + '%';
      text.textContent = (i + 1) + ' / ' + paths.length + (fail > 0 ? ' (' + fail + ' Fehler)' : '');
      file.textContent = p.split(/[/\\]/).pop();
      try {
        // All actions go through quarantine — 'delete' is redirected for safety
        const actualAction = (action === 'delete') ? 'quarantine' : action;
        if (actualAction === 'quarantine') {
          const res = await postAction('quarantine', p, {});
          console.log('[BATCH_QUARANTINE]', p, res);
          addLog(`BATCH QUARANTINE ${res.moved ? 'OK' : 'NOTE'} :: ${p}` + (res.to ? (' -> ' + res.to) : '') + (res.note ? (' :: ' + res.note) : ''));
        }
        removeRowsForPath(p);
        ok += 1;
      } catch (e) {
        console.error('[BATCH_ERR]', action, p, e);
        addLog(`BATCH ERROR ${action} :: ${p} :: ${e.message}`);
        fail += 1;
      }
    }
    setLast(`Batch ${action}: OK ${ok}, Fehler ${fail}`);
    setBatchStatus(`Fertig: ${action} | OK ${ok}, Fehler ${fail}`);
    clearSelection();
    await reloadData();
    showToast(`Batch ${action}: ${ok} OK` + (fail > 0 ? `, ${fail} Fehler` : ''), fail > 0 ? 'warning' : 'success');
  } finally {
    overlay.style.display = 'none';
  }
}

document.getElementById('btn_q_sel').addEventListener('click', async () => {
  await batchAction('quarantine', Array.from(selected), `📦 ${selected.size} Dateien in Quarantäne verschieben?\n\nDie Dateien werden nur verschoben, nicht gelöscht. Du kannst sie im Tab 🗃️ Quarantäne jederzeit zurückholen.`);
});

// btn_d_sel removed — all actions go through quarantine now

document.getElementById('reload').addEventListener('click', async () => {
  try {
    // Trigger real rescan with progress
    const r = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({token: TOKEN, action: 'rescan'})
    });
    const rj = await r.json();
    if (!rj.ok && rj.error === 'scan already running') {
      alert('Ein Scan läuft bereits!');
      return;
    }
    // Show progress bar and start polling
    showConditionalSection('progress-section', true);
    if (_activeTab === 'dashboard') switchTab('dashboard');
    setLast('🔄 Scan gestartet…');
    addLog('RESCAN STARTED');
    pollProgress();
  } catch (e) {
    showToast(e.message, 'error');
  }
});

let _progressTimer = null;
async function pollProgress() {
  try {
    const r = await fetch('/api/progress?token=' + TOKEN);
    const p = await r.json();
    const section = document.getElementById('progress-section');
    const bar = document.getElementById('progress-bar');
    const pct = document.getElementById('progress-pct');
    const phase = document.getElementById('progress-phase');
    const detail = document.getElementById('progress-detail');

    const phaseNames = {
      'collect': '📁 Sammle Dateien…',
      'name': '🔤 Prüfe Dateinamen…',
      'hashing_init': '#️⃣ Vorbereitung Hash-Prüfung…',
      'hashing': '#️⃣ Hash-Prüfung…',
      'integrity': '🔍 Integritäts-Check…',
      'conflicts': '⚡ Konflikte prüfen…',
      'deep': '🔬 Tiefenanalyse…',
      'finalize': '✨ Finalisiere…',
      'done': '✅ Fertig!',
      'error': '❌ Fehler',
    };
    phase.textContent = phaseNames[p.phase] || p.phase || 'Läuft…';
    detail.textContent = p.msg || '';

    if (p.total > 0 && p.cur > 0) {
      const percent = Math.min(100, Math.round((p.cur / p.total) * 100));
      bar.style.width = percent + '%';
      pct.textContent = percent + '%';
    } else if (p.phase === 'done') {
      bar.style.width = '100%';
      pct.textContent = '100%';
    } else {
      // indeterminate — pulsing animation
      bar.style.width = '30%';
      bar.style.animation = 'pulse 1.5s ease-in-out infinite alternate';
      pct.textContent = '';
    }

    if (p.done) {
      bar.style.animation = '';
      bar.style.width = '100%';
      bar.style.background = 'linear-gradient(90deg,#22c55e,#4ade80)';
      pct.textContent = '✅';
      setLast('✅ Scan abgeschlossen');
      addLog('RESCAN DONE');
      // Reload data and hide progress after delay
      setTimeout(async () => {
        await reloadData();
        setTimeout(() => { showConditionalSection('progress-section', false); bar.style.background = ''; }, 2000);
      }, 500);
      return; // stop polling
    }
    if (p.error) {
      bar.style.animation = '';
      bar.style.background = 'linear-gradient(90deg,#ef4444,#f87171)';
      phase.textContent = '❌ Fehler: ' + p.error;
      pct.textContent = '❌';
      setLast('❌ Scan-Fehler');
      addLog('RESCAN ERROR :: ' + p.error);
      setTimeout(() => { showConditionalSection('progress-section', false); bar.style.background = ''; }, 5000);
      return; // stop polling
    }
    // Continue polling
    _progressTimer = setTimeout(pollProgress, 400);
  } catch (e) {
    console.error('[PROGRESS_POLL]', e);
    setTimeout(pollProgress, 1000);
  }
}

(function initImportDropzone() {
  const dropzone = document.getElementById('import-dropzone');
  const fileInput = document.getElementById('import-file-input');
  const folderInput = document.getElementById('import-folder-input');
  if (!dropzone || !fileInput) return;

  // Klick auf Dropzone -> Dateiauswahl öffnen
  dropzone.addEventListener('click', (e) => {
    if (e.target.closest('button')) return; // Ordner-Button nicht doppelt
    fileInput.click();
  });

  // Drag-Events
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add('drag-active');
  });
  dropzone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag-active');
  });
  dropzone.addEventListener('drop', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag-active');
    // webkitGetAsEntry um Ordner rekursiv zu lesen
    const items = e.dataTransfer.items;
    if (items && items.length > 0) {
      const entries = [];
      for (let i = 0; i < items.length; i++) {
        const entry = items[i].webkitGetAsEntry ? items[i].webkitGetAsEntry() : null;
        if (entry) entries.push(entry);
      }
      if (entries.length > 0) {
        const statusEl = document.getElementById('import-status');
        statusEl.innerHTML = '📂 Lese Ordnerstruktur…';
        const collected = await collectFilesFromEntries(entries, '');
        if (collected.length > 0) {
          await handleUploadFiles(collected);
        } else {
          statusEl.innerHTML = '⚠️ Keine Dateien im Ordner gefunden.';
        }
        return;
      }
    }
    // Fallback: normale Dateien
    if (e.dataTransfer.files.length > 0) {
      const plain = [...e.dataTransfer.files].map(f => ({file: f, relativePath: ''}));
      await handleUploadFiles(plain);
    }
  });

  // Einzelne Dateien auswählen
  fileInput.addEventListener('change', async () => {
    if (fileInput.files.length > 0) {
      const plain = [...fileInput.files].map(f => ({file: f, relativePath: ''}));
      await handleUploadFiles(plain);
    }
    fileInput.value = '';
  });

  // Ordner auswählen (webkitdirectory)
  if (folderInput) {
    folderInput.addEventListener('change', async () => {
      if (folderInput.files.length > 0) {
        // webkitRelativePath enthält den vollen relativen Pfad inkl. Dateiname
        const items = [...folderInput.files].map(f => {
          // webkitRelativePath z.B. "ModFolder/subfolder/file.package"
          const parts = f.webkitRelativePath.split('/');
          // Alles außer der Datei selbst = relativer Ordnerpfad
          const relDir = parts.slice(0, -1).join('/');
          return {file: f, relativePath: relDir};
        });
        await handleUploadFiles(items);
      }
      folderInput.value = '';
    });
  }

  // Rekursiv alle Dateien aus FileSystemEntry-Einträgen sammeln
  async function collectFilesFromEntries(entries, basePath) {
    const results = [];
    for (const entry of entries) {
      if (entry.isFile) {
        try {
          const file = await new Promise((res, rej) => entry.file(res, rej));
          results.push({file, relativePath: basePath});
        } catch(e) { console.warn('[ENTRY]', e); }
      } else if (entry.isDirectory) {
        const subPath = basePath ? basePath + '/' + entry.name : entry.name;
        const dirReader = entry.createReader();
        // readEntries kann in Batches kommen, daher Loop
        const allSub = [];
        let batch;
        do {
          batch = await new Promise((res, rej) => dirReader.readEntries(res, rej));
          allSub.push(...batch);
        } while (batch.length > 0);
        const subFiles = await collectFilesFromEntries(allSub, subPath);
        results.push(...subFiles);
      }
    }
    return results;
  }

  // items = [{file: File, relativePath: 'sub/folder'}, ...]
  async function handleUploadFiles(items) {
    const statusEl = document.getElementById('import-status');
    const resultsEl = document.getElementById('import-results');
    const subfolder = document.getElementById('import-target-subfolder')?.value?.trim() || '';
    const targetRow = document.getElementById('import-target-row');

    const modItems = items; // Alle Dateien übernehmen (1:1 wie aus RAR/ZIP)
    if (modItems.length === 0) {
      statusEl.innerHTML = '⚠️ Keine Dateien gefunden.';
      return;
    }

    // Ordnerstruktur-Info anzeigen
    const hasFolders = modItems.some(it => it.relativePath);
    const folderSet = new Set(modItems.filter(it => it.relativePath).map(it => it.relativePath));
    if (hasFolders) {
      statusEl.innerHTML = `📤 Lade ${modItems.length} Datei(en) in ${folderSet.size} Ordner(n) hoch…`;
    } else {
      statusEl.innerHTML = `📤 Lade ${modItems.length} Datei(en) hoch…`;
    }
    resultsEl.innerHTML = '';
    targetRow.style.display = '';

    let newCount = 0, identicalCount = 0, updateCount = 0;
    const updateItems = [];
    const createdFolders = new Set();

    for (let i = 0; i < modItems.length; i++) {
      const item = modItems[i];
      const displayName = item.relativePath ? item.relativePath + '/' + item.file.name : item.file.name;
      statusEl.innerHTML = `📤 Lade ${i+1}/${modItems.length}: <b>${displayName}</b>…`;

      try {
        const b64 = await fileToBase64(item.file);
        const r = await fetch('/api/action', {
          method: 'POST', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({
            token: TOKEN, action: 'import_upload',
            filename: item.file.name, filedata: b64,
            subfolder, relative_path: item.relativePath || ''
          })
        });
        const d = await r.json();
        if (!d.ok) {
          console.error(`[UPLOAD] ${displayName}: ${d.error}`);
          continue;
        }
        if (d.status === 'new') {
          newCount++;
          if (item.relativePath) createdFolders.add(item.relativePath);
        }
        else if (d.status === 'identical') { identicalCount++; }
        else if (d.status === 'update') { updateCount++; updateItems.push({item, data: d, displayName}); }
      } catch (e) {
        console.error('[UPLOAD]', e);
      }
    }

    // Zusammenfassung
    let parts = [];
    if (newCount) parts.push(`📥 ${newCount} neu importiert`);
    if (createdFolders.size > 0) parts.push(`📁 ${createdFolders.size} Unterordner erstellt`);
    if (identicalCount) parts.push(`✅ ${identicalCount} übersprungen (identisch)`);
    if (updateCount) parts.push(`🔄 ${updateCount} Updates`);
    statusEl.innerHTML = `<b>Fertig!</b> ${parts.join(' · ')}`;

    // Update-Tabelle
    if (updateItems.length > 0) {
      let html = '<div style="margin:10px 0 6px;"><b>⚠️ Diese Dateien brauchen deine Entscheidung:</b></div>';
      html += '<table style="width:100%;border-collapse:collapse;font-size:13px;"><thead><tr style="border-bottom:1px solid #334155;text-align:left;"><th style="padding:6px;">Datei</th><th style="padding:6px;">Größe</th><th style="padding:6px;">Vorhandene Datei</th><th style="padding:6px;">Aktion</th></tr></thead><tbody>';

      updateItems.forEach(ui => {
        const match = ui.data.matches.find(m => m.relation === 'update') || ui.data.matches[0];
        const tmpEsc = (ui.data.tmp_path||'').replace(/\\/g,'\\\\');
        const replEsc = (match.path||'').replace(/\\/g,'\\\\');
        const existName = match.path.split('\\').pop().split('/').pop();
        const existSize = match.existing_size_h || '?';

        html += `<tr data-upload-name="${ui.displayName}" style="border-bottom:1px solid #1e293b;">`;
        html += `<td style="padding:6px;">${ui.displayName}</td>`;
        html += `<td style="padding:6px;">${ui.data.size_h}</td>`;
        html += `<td style="padding:6px;font-size:12px;" class="muted">${existName} (${existSize})</td>`;
        html += `<td style="padding:6px;">`;
        html += `<button class="btn btn-ok" style="padding:3px 10px;font-size:12px;" onclick="confirmUploadReplace('${tmpEsc}','${replEsc}',this)">🔄 Ersetzen</button> `;
        html += `<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;" onclick="this.closest('tr').style.display='none'">⏭ Überspringen</button>`;
        html += `</td></tr>`;
      });
      html += '</tbody></table>';
      resultsEl.innerHTML = html;
    } else if (newCount > 0) {
      resultsEl.innerHTML = '<div style="padding:12px;text-align:center;color:#22c55e;">✅ Alle neuen Mods wurden automatisch importiert!' + (createdFolders.size > 0 ? ' Ordnerstruktur wurde 1:1 übernommen.' : '') + '</div>';
    }
  }

  function fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const arrBuf = reader.result;
        const bytes = new Uint8Array(arrBuf);
        let binary = '';
        for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
        resolve(btoa(binary));
      };
      reader.onerror = () => reject(reader.error);
      reader.readAsArrayBuffer(file);
    });
  }
})();

// Upload-Ersetzen bestätigen
async function confirmUploadReplace(tmpPath, replacePath, btn) {
  try {
    const r = await fetch('/api/action', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({token: TOKEN, action: 'import_upload_confirm', tmp_path: tmpPath, replace_path: replacePath})
    });
    const d = await r.json();
    if (d.ok) {
      const row = btn.closest('tr');
      const actCell = row.querySelector('td:last-child');
      if (actCell) actCell.innerHTML = '<span style="color:#22c55e">✅ Aktualisiert</span>';
      row.style.opacity = '0.6';
      setLast('📥 Update: ' + replacePath.split('\\').pop().split('/').pop());
    } else {
      showToast(d.error||'unbekannt', 'error');
    }
  } catch (e) {
    showToast(e.message, 'error');
  }
}

document.getElementById('btn-import-scan').addEventListener('click', async () => {
  const source = document.getElementById('import-source').value.trim();
  if (!source) { alert('Bitte einen Quell-Ordner angeben!'); return; }
  const statusEl = document.getElementById('import-status');
  const resultsEl = document.getElementById('import-results');
  const actionsEl = document.getElementById('import-actions');
  const targetRow = document.getElementById('import-target-row');
  statusEl.textContent = '🔍 Scanne Ordner…';
  resultsEl.innerHTML = '';
  actionsEl.style.display = 'none';
  try {
    const r = await fetch('/api/action', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({token: TOKEN, action: 'import_scan', source})
    });
    const d = await r.json();
    if (!d.ok) { statusEl.textContent = '❌ ' + (d.error||'Fehler'); return; }
    if (d.count === 0) { statusEl.textContent = '⚠️ Keine .package / .ts4script Dateien gefunden.'; return; }
    statusEl.textContent = `✅ ${d.count} Mod-Datei(en) gefunden — prüfe auf Duplikate…`;
    targetRow.style.display = '';
    window.__importFiles = d.files;
    window.__importChecks = {};

    // Phase 1: Alle Dateien prüfen und sofort neue auto-importieren
    let checkedCount = 0;
    let autoImported = 0, updateCount = 0, identicalCount = 0, similarCount = 0;
    const needsDecision = []; // Nur Updates/Ähnliche brauchen User-Entscheidung
    const subfolder = document.getElementById('import-target-subfolder')?.value?.trim() || '';

    for (const f of d.files) {
      const cr = await fetch('/api/action', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({token: TOKEN, action: 'import_check', source_path: f.path})
      });
      const cd = await cr.json();
      checkedCount++;
      statusEl.textContent = `🔍 Prüfe ${checkedCount}/${d.count}…`;
      const st = cd.ok ? cd.status : 'error';
      window.__importChecks[f.path] = cd;

      if (st === 'new') {
        // Direkt importieren — kein Nachfragen nötig
        const ir = await fetch('/api/action', {
          method: 'POST', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({token: TOKEN, action: 'import_execute', source_path: f.path, subfolder, mode: 'copy', replace_path: ''})
        });
        const id = await ir.json();
        if (id.ok) autoImported++;
        statusEl.textContent = `📥 Importiere ${checkedCount}/${d.count}… (${autoImported} neu importiert)`;
      } else if (st === 'identical') {
        identicalCount++;
      } else if (st === 'update') {
        updateCount++;
        needsDecision.push({file: f, check: cd, status: st});
      } else if (st === 'similar') {
        similarCount++;
        needsDecision.push({file: f, check: cd, status: st});
      }
    }

    // Phase 2: Zusammenfassung anzeigen
    let summary = [];
    if (autoImported) summary.push(`📥 ${autoImported} neu importiert`);
    if (identicalCount) summary.push(`✅ ${identicalCount} übersprungen (identisch)`);
    if (updateCount) summary.push(`🔄 ${updateCount} Updates`);
    if (similarCount) summary.push(`🔶 ${similarCount} ähnlich`);
    statusEl.innerHTML = `<b>Fertig!</b> ${summary.join(' · ')}`;

    // Phase 3: Nur Dateien anzeigen die eine Entscheidung brauchen
    if (needsDecision.length > 0) {
      let html = '<div style="margin:10px 0 6px;"><b>⚠️ Diese Dateien brauchen deine Entscheidung:</b></div>';
      html += '<table style="width:100%;border-collapse:collapse;font-size:13px;"><thead><tr style="border-bottom:1px solid #334155;text-align:left;"><th style="padding:6px;">Datei</th><th style="padding:6px;">Größe</th><th style="padding:6px;">Status</th><th style="padding:6px;">Vorhandene Datei</th><th style="padding:6px;">Aktion</th></tr></thead><tbody>';

      needsDecision.forEach((item, idx) => {
        const f = item.file;
        const cd = item.check;
        const st = item.status;
        const statusLabel = st === 'update' ? '<span style="color:#f59e0b">🔄 Update</span>' : '<span style="color:#f97316">🔶 Ähnlich</span>';
        const matchFile = cd.matches && cd.matches[0] ? cd.matches[0] : null;
        const matchInfo = matchFile ? `<span title="${matchFile.path}">${matchFile.name} (${matchFile.size_h})</span>` : '–';
        const replacePath = matchFile ? matchFile.path.replace(/\\/g,'\\\\') : '';
        const srcEsc = f.path.replace(/\\/g,'\\\\');

        html += `<tr data-src="${f.path}" data-status="${st}" style="border-bottom:1px solid #1e293b;">`;
        html += `<td style="padding:6px;">${f.name}</td>`;
        html += `<td style="padding:6px;">${f.size_h}</td>`;
        html += `<td style="padding:6px;">${statusLabel}</td>`;
        html += `<td style="padding:6px;font-size:12px;" class="muted">${matchInfo}</td>`;
        html += `<td style="padding:6px;">`;
        html += `<button class="btn btn-ok" style="padding:3px 10px;font-size:12px;" onclick="importFile('${srcEsc}','update','${replacePath}')">🔄 Ersetzen</button> `;
        html += `<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;" onclick="importFile('${srcEsc}','copy','')">📥 Zusätzlich</button> `;
        html += `<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;" onclick="this.closest('tr').style.display='none'">⏭ Überspringen</button>`;
        html += `</td></tr>`;
      });
      html += '</tbody></table>';
      resultsEl.innerHTML = html;

      if (updateCount > 0) actionsEl.style.display = 'flex';
    } else {
      resultsEl.innerHTML = '<div style="padding:12px;text-align:center;color:#22c55e;">✅ Alle neuen Mods wurden automatisch importiert! Keine weiteren Aktionen nötig.</div>';
    }
  } catch (e) {
    statusEl.textContent = '❌ Fehler: ' + e.message;
  }
});

async function importFile(sourcePath, mode, replacePath) {
  const subfolder = document.getElementById('import-target-subfolder')?.value?.trim() || '';
  try {
    const r = await fetch('/api/action', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({token: TOKEN, action: 'import_execute', source_path: sourcePath, subfolder, mode, replace_path: replacePath})
    });
    const d = await r.json();
    if (d.ok) {
      // Zeile als erledigt markieren
      const rows = document.querySelectorAll('#import-results tr[data-src]');
      rows.forEach(row => {
        if (row.dataset.src === sourcePath) {
          const actCell = row.querySelector('td:last-child');
          if (actCell) actCell.innerHTML = `<span style="color:#22c55e">✅ ${d.mode === 'update' ? 'Aktualisiert' : 'Importiert'}</span>`;
          row.style.opacity = '0.6';
        }
      });
      setLast(`📥 ${mode === 'update' ? 'Update' : 'Import'}: ${sourcePath.split('\\').pop()}`);
    } else {
      showToast(d.error||'unbekannt', 'error');
    }
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// Batch-Import: Alle Updates übernehmen
document.getElementById('btn-import-all-update').addEventListener('click', async () => {
  const rows = document.querySelectorAll('#import-results tr[data-status="update"], #import-results tr[data-status="similar"]');
  const visible = [...rows].filter(r => r.style.display !== 'none');
  if (visible.length === 0) { alert('Keine offenen Updates/Ähnliche mehr.'); return; }
  if (!confirm(`🔄 ${visible.length} Mod(s) aktualisieren? Die vorhandenen Dateien werden überschrieben!`)) return;
  for (const row of visible) {
    const src = row.dataset.src;
    const check = window.__importChecks?.[src];
    const replacePath = check?.matches?.[0]?.path || '';
    await importFile(src, 'update', replacePath);
  }
  setLast(`🔄 ${visible.length} Mods aktualisiert`);
});

// Import-Liste leeren
document.getElementById('btn-import-clear').addEventListener('click', () => {
  document.getElementById('import-results').innerHTML = '';
  document.getElementById('import-status').textContent = '';
  document.getElementById('import-actions').style.display = 'none';
  document.getElementById('import-target-row').style.display = 'none';
  window.__importFiles = null;
  window.__importChecks = {};
});

let _watcherTimer = null;
let _lastWatcherMsg = '';
async function pollWatcher() {
  try {
    const r = await fetch('/api/watcher?token=' + TOKEN);
    const w = await r.json();
    const banner = document.getElementById('watcher-banner');
    const filesSpan = document.getElementById('watcher-files');
    const eventSpan = document.getElementById('watcher-event');

    if (w.active) {
      banner.style.display = 'flex';
      filesSpan.textContent = w.files_watched;
      if (w.auto_rescan_msg && w.auto_rescan_msg !== _lastWatcherMsg) {
        _lastWatcherMsg = w.auto_rescan_msg;
        eventSpan.textContent = w.auto_rescan_msg;
        // Auto-Rescan wurde gestartet — Progress-Polling starten
        if (w.auto_rescan_msg.includes('🔄')) {
          showConditionalSection('progress-section', true);
          if (_activeTab === 'dashboard') switchTab('dashboard');
          if (!_progressTimer) pollProgress();
        }
      } else if (w.last_event) {
        eventSpan.textContent = w.last_event;
      }
    } else {
      banner.style.display = 'none';
    }
  } catch (e) {
    console.error('[WATCHER_POLL]', e);
  }
  _watcherTimer = setTimeout(pollWatcher, 3000);
}
// Watcher-Polling starten
pollWatcher();

// Group and per-file actions (event delegation)
document.getElementById('groups').addEventListener('click', async (ev) => {
  // group actions
  const gbtn = ev.target.closest('button[data-gact]');
  if (gbtn) {
    const gact = gbtn.dataset.gact;
    const gi = Number(gbtn.dataset.gi);
    const g = window.__DATA?.groups?.[gi];
    if (!g) return;

    if (gact === 'ignore_group') {
      const gkey = gbtn.dataset.gkey;
      const gtype = gbtn.dataset.gtype;
      try {
        await postAction('ignore_group', '', { group_key: gkey, group_type: gtype });
        setLast('✅ Gruppe als korrekt markiert: ' + gkey);
        addLog('IGNORE_GROUP ' + gtype + '::' + gkey);
        await reloadData();
      } catch(e) { showToast(e.message, 'error'); }
      return;
    }
    if (gact === 'unignore_group') {
      const gkey = gbtn.dataset.gkey;
      const gtype = gbtn.dataset.gtype;
      try {
        await postAction('unignore_group', '', { group_key: gkey, group_type: gtype });
        setLast('↩️ Gruppe wird wieder gemeldet: ' + gkey);
        addLog('UNIGNORE_GROUP ' + gtype + '::' + gkey);
        await reloadData();
      } catch(e) { showToast(e.message, 'error'); }
      return;
    }
    if (gact === 'select_all') selectGroupAll(gi);
    else if (gact === 'select_rest') selectGroupRest(gi);
    else if (gact === 'quarantine_rest') {
      const keep = preferKeepPath(g.files);
      const rest = g.files.filter(f => f.path !== keep).map(f => f.path);
      await batchAction('quarantine', rest, `📦 Rest der Gruppe in Quarantäne?\n\nBehalte:\n${keep}\n\nAnzahl: ${rest.length}`);
    }
    else if (gact === 'delete_rest') {
      const keep = preferKeepPath(g.files);
      const rest = g.files.filter(f => f.path !== keep).map(f => f.path);
      await batchAction('quarantine', rest, `📦 Rest der Gruppe in Quarantäne verschieben?\n\nBehalte:\n${keep}\n\nAnzahl: ${rest.length}`);
    }
    return;
  }

  // per-file actions
  const btn = ev.target.closest('button[data-act]');
  if (!btn) return;
  const act = btn.dataset.act;
  const path = btn.dataset.path;

  try {
    if (act === 'quarantine') await doQuarantine(path);
    else if (act === 'delete') await doDelete(path);
    else if (act === 'open_folder') await doOpenFolder(path);
    else if (act === 'copy') await copyPath(path);
    else if (act === 'restore') await doRestore(path);
    else if (act === 'delete_q') await doDeleteQ(path);
  } catch (e) {
    showToast(e.message, 'error');
    console.error('[ACTION_ERR]', act, path, e);
    setLast('❌ Fehler: ' + e.message);
    addLog('ERROR ' + act + ' :: ' + path + ' :: ' + e.message);
  }
});

// Global action handler for buttons outside #groups (addon, contained, conflict, quarantine, etc.)
document.addEventListener('click', async (ev) => {
  const btn = ev.target.closest('button[data-act]');
  if (!btn) return;
  // Wenn der Klick innerhalb von #groups ist, wird er dort schon behandelt
  if (btn.closest('#groups')) return;
  const act = btn.dataset.act;
  const path = btn.dataset.path;
  if (!act || !path) return;
  try {
    if (act === 'quarantine') await doQuarantine(path);
    else if (act === 'delete') await doDelete(path);
    else if (act === 'open_folder') await doOpenFolder(path);
    else if (act === 'copy') await copyPath(path);
    else if (act === 'restore') await doRestore(path);
    else if (act === 'delete_q') await doDeleteQ(path);
  } catch (e) {
    showToast(e.message, 'error');
    console.error('[ACTION_ERR]', act, path, e);
    setLast('❌ Fehler: ' + e.message);
    addLog('ERROR ' + act + ' :: ' + path + ' :: ' + e.message);
  }
});

let _groupsFilterTimer = null;
function _applyGroupsFilter() {
  if (window.__DATA) {
    document.getElementById('groups').innerHTML = renderGroups(window.__DATA);
    if (currentView === 'perfile') renderPerFile(window.__DATA);
  }
}
for (const id of ['q','f_name','f_content','f_similar','g_mod','show_full','keep_ord1','f_show_ignored']) {
  const el = document.getElementById(id);
  if (id === 'q') {
    // Textsuche: debounce 300ms
    el.addEventListener('input', () => {
      clearTimeout(_groupsFilterTimer);
      _groupsFilterTimer = setTimeout(_applyGroupsFilter, 300);
    });
  } else {
    // Checkboxen: sofort anwenden
    el.addEventListener('input', _applyGroupsFilter);
    el.addEventListener('change', _applyGroupsFilter);
  }
}

// initial load
_initCheatFavs().then(() => {
reloadData().then(()=>{
  setLast('✅ Daten geladen');
  addLog('PAGE LOAD');
  updateSelCount();
  // Scan fertig — auf Savegame + Bibliothek warten
  _scanReady = true;
  _checkAllReady();
}).catch(e=>{
  document.getElementById('groups').innerHTML = '<p class="muted">Fehler: ' + esc(e.message) + '</p>';
  setLast('❌ Fehler beim Laden: ' + e.message);
  addLog('LOAD ERROR :: ' + e.message);
  // Scan als fertig markieren trotz Fehler
  _scanReady = true;
  _checkAllReady();
});
}); // end _initCheatFavs

// Fehler-Analyse immer laden (unabhängig von Duplikat-Daten)
loadErrors();

(async function checkForUpdate() {
  try {
    const r = await fetch('/api/update-check?token=' + encodeURIComponent(TOKEN));
    const j = await r.json();
    if (j.ok && j.available) {
      const banner = document.getElementById('update-banner');
      document.getElementById('update-text').textContent =
        '🔔 Neue Version verfügbar: v' + j.latest + '  (du hast v' + j.current + ')';
      const link = document.getElementById('update-link');
      link.href = j.download_url || j.url || '#';
      banner.style.display = 'block';
    }
  } catch(e) { /* silent */ }
})();

async function loadErrors() {
  document.getElementById('error-summary').innerHTML = 'Suche Sims 4 Verzeichnis und lese Fehlerlogs…';
  try {
    const r = await fetch('/api/errors?token=' + encodeURIComponent(TOKEN));
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'unknown');
    if (j.note) {
      document.getElementById('error-summary').innerHTML = '⚠️ ' + esc(j.note);
      return;
    }
    renderErrors(j);
  } catch(e) {
    document.getElementById('error-summary').innerHTML = '<span style="color:#ef4444;">❌ Fehler beim Laden: ' + esc(e.message) + '</span>';
  }
}

function schwereIcon(s) {
  if (s === 'hoch') return '🔴';
  if (s === 'mittel') return '🟡';
  if (s === 'niedrig') return '🟢';
  return '⚪';
}

function schwereLabel(s) {
  if (s === 'hoch') return 'Schwerwiegend';
  if (s === 'mittel') return 'Mittel';
  if (s === 'niedrig') return 'Gering';
  return 'Unbekannt';
}

function renderErrors(data) {
  const errors = data.errors || [];
  const simsDir = data.sims4_dir || '(nicht gefunden)';

  const hoch = errors.filter(e => e.schwere === 'hoch').length;
  const mittel = errors.filter(e => e.schwere === 'mittel').length;
  const niedrig = errors.filter(e => e.schwere === 'niedrig').length;
  const unbekannt = errors.filter(e => e.schwere === 'unbekannt').length;

  // --- Dashboard-Karte für Fehler aktualisieren ---
  const dashErrors = document.getElementById('dash-errors');
  const dashErrorsCount = document.getElementById('dash-errors-count');
  const dashErrorsDesc = document.getElementById('dash-errors-desc');
  if (dashErrors && dashErrorsCount) {
    dashErrorsCount.textContent = errors.length;
    if (errors.length === 0) {
      dashErrors.classList.add('dash-hidden');
    } else {
      dashErrors.classList.remove('dash-hidden');
      // Schweregrad-basiertes Styling
      if (hoch > 0) {
        dashErrors.className = 'dash-card dash-critical';
      } else if (mittel > 0) {
        dashErrors.className = 'dash-card dash-warn';
      } else {
        dashErrors.className = 'dash-card dash-info';
      }
      // Beschreibung mit Schweregrad-Info
      let descParts = [];
      if (hoch > 0) descParts.push(`<b style="color:#ef4444;">${hoch}x Schwerwiegend</b>`);
      if (mittel > 0) descParts.push(`<b style="color:#f59e0b;">${mittel}x Mittel</b>`);
      if (niedrig > 0) descParts.push(`${niedrig}x Gering`);
      if (unbekannt > 0) descParts.push(`${unbekannt}x Unbekannt`);
      dashErrorsDesc.innerHTML = descParts.join(', ') + ' — Klicke für Details und Lösungen.';
    }
    // Fehler-Badge im Nav aktualisieren
    const errBadge = document.getElementById('nav-badge-errors');
    if (errBadge) {
      errBadge.textContent = errors.length;
      errBadge.classList.toggle('badge-zero', errors.length === 0);
    }
  }
  // Globale Variable für Health-Score
  window.__errorData = {total: errors.length, hoch: hoch, mittel: mittel};

  let summaryHtml = '';
  if (errors.length === 0) {
    summaryHtml = '✅ <b>Keine Fehler gefunden!</b> Deine Fehlerlog-Dateien sind sauber.';
  } else {
    summaryHtml = `<b>${errors.length} Fehler</b> gefunden in <code>${esc(simsDir)}</code><br>`;
    if (hoch > 0) summaryHtml += `<span class="err-schwere hoch">${hoch}x Schwerwiegend</span> `;
    if (mittel > 0) summaryHtml += `<span class="err-schwere mittel">${mittel}x Mittel</span> `;
    if (niedrig > 0) summaryHtml += `<span class="err-schwere niedrig">${niedrig}x Gering</span> `;
    if (unbekannt > 0) summaryHtml += `<span class="err-schwere unbekannt">${unbekannt}x Unbekannt</span> `;
  }
  // Snapshot-Info (neu/bekannt/behoben)
  const snap = data.snapshot;
  if (snap && errors.length > 0) {
    summaryHtml += `<br><span style="font-size:12px; color:#94a3b8;">`;
    if (snap.fehler_neu > 0) summaryHtml += `🆕 ${snap.fehler_neu} neu `;
    if (snap.fehler_bekannt > 0) summaryHtml += `🔄 ${snap.fehler_bekannt} bekannt `;
    if (snap.fehler_behoben > 0) summaryHtml += `✅ ${snap.fehler_behoben} seit letztem Mal behoben `;
    summaryHtml += `</span>`;
  }
  document.getElementById('error-summary').innerHTML = summaryHtml;

  // --- Exception-Datei-Übersicht ---
  const excFiles = data.exception_files || [];
  let fileListHtml = '';
  if (excFiles.length > 0) {
    const aktuell = excFiles.filter(f => f.ist_aktuell);
    const alt = excFiles.filter(f => !f.ist_aktuell);
    fileListHtml += '<details style="margin-top:8px;"><summary style="cursor:pointer; font-size:13px; color:#94a3b8;">📁 <b>' + excFiles.length + ' Exception-Dateien</b> gefunden (' + aktuell.length + ' aktuell, ' + alt.length + ' ältere)</summary>';
    fileListHtml += '<table style="width:100%; font-size:12px; margin-top:6px; border-collapse:collapse;">';
    fileListHtml += '<tr style="color:#94a3b8;"><th style="text-align:left; padding:4px 8px;">Datei</th><th style="text-align:left; padding:4px 8px;">Datum</th><th style="text-align:right; padding:4px 8px;">Größe</th><th style="padding:4px 8px;">Status</th></tr>';
    for (const f of excFiles) {
      const style = f.ist_aktuell ? 'color:#4ade80; font-weight:600;' : 'color:#64748b;';
      const badge = f.ist_aktuell ? '<span style="background:#166534; color:#4ade80; padding:1px 6px; border-radius:4px; font-size:11px;">✓ aktuell</span>' : '<span style="background:#1e293b; color:#64748b; padding:1px 6px; border-radius:4px; font-size:11px;">alt</span>';
      fileListHtml += '<tr style="border-top:1px solid #1e293b; ' + style + '"><td style="padding:4px 8px;">' + esc(f.name) + '</td><td style="padding:4px 8px;">' + esc(f.datum) + '</td><td style="text-align:right; padding:4px 8px;">' + f.groesse_kb + ' KB</td><td style="text-align:center; padding:4px 8px;">' + badge + '</td></tr>';
    }
    fileListHtml += '</table></details>';
  }
  document.getElementById('exc-file-list').innerHTML = fileListHtml;

  let html = '';
  for (const err of errors) {
    // --- Betroffene Mods (verbessert) ---
    let modsHtml = '';
    if (err.betroffene_mods && err.betroffene_mods.length > 0) {
      modsHtml = '<div class="err-mods"><span class="muted small">🎯 Beteiligte Mods:</span> ' +
        err.betroffene_mods.map(m => '<span class="err-mod-tag">' + esc(m) + '</span>').join('') +
        '</div>';
    }

    // --- BetterExceptions-Hinweis ---
    let beHtml = '';
    if (err.be_advice && err.be_advice !== 'Not available. More info may be in BE Report.') {
      beHtml = '<div style="background:#1a1a2e; border-left:3px solid #8b5cf6; padding:6px 10px; margin:6px 0; border-radius:4px; font-size:12px;">' +
        '<span style="color:#8b5cf6;">🔮 BetterExceptions:</span> <span style="color:#c4b5fd;">' + esc(err.be_advice) + '</span></div>';
    }

    // --- Anzahl-Badge ---
    let countBadge = '';
    if (err.anzahl && err.anzahl > 1) {
      countBadge = '<span style="background:#7c3aed; color:#fff; padding:1px 8px; border-radius:10px; font-size:11px; font-weight:600;">' + err.anzahl + 'x</span>';
    }

    // --- Raw Snippet (lesbarer Traceback) ---
    const rawHtml = err.raw_snippet
      ? '<details class="err-raw"><summary>📄 Traceback / Log-Auszug anzeigen</summary><pre style="white-space:pre-wrap; word-break:break-all; max-height:300px; overflow-y:auto;">' + esc(err.raw_snippet) + '</pre></details>'
      : '';

    // --- Status-Badge ---
    const statusBadge = err.status === 'neu'
      ? '<span class="err-status neu">🆕 NEU</span>'
      : err.status === 'bekannt'
        ? '<span class="err-status bekannt">🔄 BEKANNT</span>'
        : '';

    // --- Erklärung mit Zeilenumbrüchen ---
    const explainLines = esc(err.erklaerung).split('\n→ ');
    let explainHtml = explainLines[0];
    if (explainLines.length > 1) {
      explainHtml += '<div style="margin-top:4px; padding-left:8px; border-left:2px solid #334155; font-size:12px; color:#94a3b8;">';
      for (let i = 1; i < explainLines.length; i++) {
        explainHtml += '<div style="margin:2px 0;">→ ' + explainLines[i] + '</div>';
      }
      explainHtml += '</div>';
    }

    html += '<div class="err-card ' + err.schwere + '">' +
      '<div class="flex" style="align-items:center; gap:8px; flex-wrap:wrap;">' +
        '<span>' + schwereIcon(err.schwere) + '</span>' +
        '<span class="err-title">' + esc(err.titel) + '</span>' +
        '<span class="err-schwere ' + err.schwere + '">' + schwereLabel(err.schwere) + '</span>' +
        countBadge + statusBadge +
      '</div>' +
      '<div class="err-explain">' + explainHtml + '</div>' +
      '<div class="err-solution">💡 <b>Lösung:</b> ' + esc(err.loesung) + '</div>' +
      modsHtml + beHtml +
      '<div class="err-meta">' +
        '<span>📁 ' + esc(err.datei) + '</span>' +
        '<span>📅 ' + esc(err.datum) + '</span>' +
        '<span>📂 ' + esc(err.kategorie) + '</span>' +
      '</div>' +
      rawHtml +
    '</div>';
  }

  document.getElementById('error-list').innerHTML = html;
}

document.getElementById('btn_reload_errors').addEventListener('click', () => {
  document.getElementById('error-summary').innerHTML = 'Lade Fehler…';
  document.getElementById('error-list').innerHTML = '';
  loadErrors();
});

document.getElementById('btn_save_html').addEventListener('click', () => {
  const html = document.documentElement.outerHTML;
  const blob = new Blob(['<!DOCTYPE html>\n' + html], {type: 'text/html; charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const ts = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
  a.href = url;
  a.download = 'Sims4_Scanner_' + ts + '.html';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  setLast('📄 HTML gespeichert als ' + a.download);
});

loadHistory();
// Tray-Daten aus Scan übernehmen (kein extra Fetch nötig)
if (window.__DATA && window.__DATA.tray) {
  _trayData = window.__DATA.tray;
  renderTrayResults();
  document.getElementById('btn-tray-analyze').textContent = '🔍 Analysieren';
  document.getElementById('btn-tray-refresh').style.display = 'inline-block';
} else {
  setTimeout(() => startTrayAnalysis(), 500);
}

async function loadHistory() {
  try {
    const r = await fetch('/api/history?token=' + encodeURIComponent(TOKEN));
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'unknown');
    renderHistory(j);
  } catch(e) {
    document.getElementById('mod-snapshot-content').innerHTML = '<span style="color:#ef4444;">❌ ' + esc(e.message) + '</span>';
    document.getElementById('scan-history-content').innerHTML = '';
  }
}

function renderHistory(data) {
  // Mod-Snapshot
  const ms = data.mod_snapshot || {};
  if (ms.mods_gesamt > 0) {
    let modsHtml = `<div class="mod-stats">
      <div class="mod-stat"><div class="val">${ms.mods_gesamt}</div><div class="lbl">Mods gesamt</div></div>
      <div class="mod-stat"><div class="val">${ms.mods_package}</div><div class="lbl">.package</div></div>
      <div class="mod-stat"><div class="val">${ms.mods_script}</div><div class="lbl">.ts4script</div></div>
      <div class="mod-stat"><div class="val">${esc(ms.groesse_gesamt_h)}</div><div class="lbl">Gesamtgröße</div></div>
    </div>`;

    // Änderungen anzeigen
    const hasChanges = ms.neue > 0 || ms.entfernt > 0 || ms.geaendert > 0;
    if (hasChanges) {
      const ch = ms.changes || {};
      let changesHtml = '<div style="margin-top:8px;">';
      if (ms.neue > 0) changesHtml += `<span class="change-tag neu">+${ms.neue} neue Mods</span> `;
      if (ms.entfernt > 0) changesHtml += `<span class="change-tag entfernt">-${ms.entfernt} entfernte Mods</span> `;
      if (ms.geaendert > 0) changesHtml += `<span class="change-tag geaendert">~${ms.geaendert} geänderte Mods</span> `;
      changesHtml += '</div>';

      // Details aufklappbar
      if (ch.neue_mods && ch.neue_mods.length > 0) {
        changesHtml += `<details style="margin-top:8px;"><summary style="cursor:pointer; color:#86efac; font-size:12px;">📥 Neue Mods anzeigen (${ch.neue_mods.length})</summary>
          <div style="margin-top:4px;">${ch.neue_mods.map(m => `<span class="change-tag neu">${esc(m)}</span>`).join('')}</div></details>`;
      }
      if (ch.entfernte_mods && ch.entfernte_mods.length > 0) {
        changesHtml += `<details style="margin-top:4px;"><summary style="cursor:pointer; color:#fca5a5; font-size:12px;">📤 Entfernte Mods anzeigen (${ch.entfernte_mods.length})</summary>
          <div style="margin-top:4px;">${ch.entfernte_mods.map(m => `<span class="change-tag entfernt">${esc(m)}</span>`).join('')}</div></details>`;
      }
      if (ch.geaenderte_mods && ch.geaenderte_mods.length > 0) {
        changesHtml += `<details style="margin-top:4px;"><summary style="cursor:pointer; color:#fde68a; font-size:12px;">✏️ Geänderte Mods anzeigen (${ch.geaenderte_mods.length})</summary>
          <div style="margin-top:4px;">${ch.geaenderte_mods.map(m => `<span class="change-tag geaendert">${esc(m)}</span>`).join('')}</div></details>`;
      }

      document.getElementById('mod-changes').style.display = 'block';
      document.getElementById('mod-changes-content').innerHTML = changesHtml;
    }

    document.getElementById('mod-snapshot-content').innerHTML = modsHtml;
  } else {
    document.getElementById('mod-snapshot-content').innerHTML = '<span class="muted">Noch kein Mod-Inventar vorhanden. Starte einen Scan um eines zu erstellen.</span>';
  }

  // Scan-History Tabelle
  const hist = data.scan_history || [];
  if (hist.length === 0) {
    document.getElementById('scan-history-content').innerHTML = '<span class="muted">Noch keine Scan-History vorhanden.</span>';
    return;
  }

  let tableHtml = `<table class="hist-table">
    <thead><tr>
      <th>Datum</th>
      <th>Dateien</th>
      <th>Name-Duplikate</th>
      <th>Inhalt-Duplikate</th>
    </tr></thead><tbody>`;

  for (const h of hist) {
    tableHtml += `<tr>
      <td>${esc(h.timestamp || '')}</td>
      <td>${h.dateien_gesamt || 0}</td>
      <td>${h.duplikate_name_gruppen || 0} Gruppen / ${h.duplikate_name_dateien || 0} Dateien</td>
      <td>${h.duplikate_inhalt_gruppen || 0} Gruppen / ${h.duplikate_inhalt_dateien || 0} Dateien</td>
    </tr>`;
  }
  tableHtml += '</tbody></table>';
  document.getElementById('scan-history-content').innerHTML = tableHtml;

  // Verlaufs-Diagramm rendern
  renderHistoryChart(hist);
}

function renderHistoryChart(hist) {
  const chartArea = document.getElementById('history-chart-area');
  if (!hist || hist.length < 2) {
    chartArea.style.display = 'none';
    return;
  }
  chartArea.style.display = '';

  const canvas = document.getElementById('history-chart');
  const ctx = canvas.getContext('2d');
  const container = canvas.parentElement;

  // Set canvas size
  canvas.width = container.clientWidth - 24;
  canvas.height = 196;
  const W = canvas.width;
  const H = canvas.height;
  const pad = {top: 20, right: 20, bottom: 40, left: 50};

  // Data arrays (reversed since hist is newest-first)
  const data = [...hist].reverse();
  const labels = data.map(h => {
    const ts = h.timestamp || '';
    return ts.substring(0, 10); // YYYY-MM-DD
  });
  const values = data.map(h => h.dateien_gesamt || 0);
  const dupes = data.map(h => (h.duplikate_name_dateien || 0) + (h.duplikate_inhalt_dateien || 0));

  const maxVal = Math.max(...values, ...dupes, 1);
  const minVal = 0;

  const plotW = W - pad.left - pad.right;
  const plotH = H - pad.top - pad.bottom;

  function x(i) { return pad.left + (i / (data.length - 1)) * plotW; }
  function y(v) { return pad.top + plotH - (v / maxVal) * plotH; }

  // Clear
  ctx.clearRect(0, 0, W, H);

  // Grid lines
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 1;
  const gridSteps = 4;
  for (let i = 0; i <= gridSteps; i++) {
    const yy = pad.top + (i / gridSteps) * plotH;
    ctx.beginPath();
    ctx.moveTo(pad.left, yy);
    ctx.lineTo(W - pad.right, yy);
    ctx.stroke();
    // Label
    const val = Math.round(maxVal * (1 - i / gridSteps));
    ctx.fillStyle = '#64748b';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'right';
    ctx.fillText(val.toLocaleString(), pad.left - 6, yy + 3);
  }

  // Draw line: total files
  ctx.strokeStyle = '#6366f1';
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  for (let i = 0; i < data.length; i++) {
    const px = x(i), py = y(values[i]);
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.stroke();

  // Fill area under total
  ctx.fillStyle = 'rgba(99, 102, 241, 0.1)';
  ctx.beginPath();
  ctx.moveTo(x(0), y(values[0]));
  for (let i = 1; i < data.length; i++) ctx.lineTo(x(i), y(values[i]));
  ctx.lineTo(x(data.length - 1), pad.top + plotH);
  ctx.lineTo(x(0), pad.top + plotH);
  ctx.closePath();
  ctx.fill();

  // Draw line: duplicates
  ctx.strokeStyle = '#f59e0b';
  ctx.lineWidth = 2;
  ctx.setLineDash([4, 3]);
  ctx.beginPath();
  for (let i = 0; i < data.length; i++) {
    const px = x(i), py = y(dupes[i]);
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.stroke();
  ctx.setLineDash([]);

  // Dots total
  for (let i = 0; i < data.length; i++) {
    ctx.fillStyle = '#6366f1';
    ctx.beginPath();
    ctx.arc(x(i), y(values[i]), 3.5, 0, Math.PI * 2);
    ctx.fill();
  }

  // Dots dupes
  for (let i = 0; i < data.length; i++) {
    ctx.fillStyle = '#f59e0b';
    ctx.beginPath();
    ctx.arc(x(i), y(dupes[i]), 3, 0, Math.PI * 2);
    ctx.fill();
  }

  // X-axis labels (show max ~6)
  ctx.fillStyle = '#64748b';
  ctx.font = '10px system-ui';
  ctx.textAlign = 'center';
  const step = Math.max(1, Math.floor(data.length / 6));
  for (let i = 0; i < data.length; i += step) {
    const short = labels[i].substring(5); // MM-DD
    ctx.fillText(short, x(i), H - pad.bottom + 16);
  }
  // Always show last
  if ((data.length - 1) % step !== 0) {
    ctx.fillText(labels[data.length - 1].substring(5), x(data.length - 1), H - pad.bottom + 16);
  }

  // Legend
  ctx.font = '11px system-ui';
  const legX = pad.left + 8;
  ctx.fillStyle = '#6366f1';
  ctx.fillRect(legX, pad.top - 14, 12, 3);
  ctx.fillStyle = '#94a3b8';
  ctx.textAlign = 'left';
  ctx.fillText('Mods gesamt', legX + 16, pad.top - 10);

  ctx.fillStyle = '#f59e0b';
  ctx.fillRect(legX + 110, pad.top - 14, 12, 3);
  ctx.fillStyle = '#94a3b8';
  ctx.fillText('Duplikate', legX + 126, pad.top - 10);
}

document.getElementById('btn_export_modlist').addEventListener('click', async () => {
  try {
    const resp = await fetch('/api/mod_export?token=' + encodeURIComponent(TOKEN));
    if (!resp.ok) throw new Error('Export fehlgeschlagen');
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const ts = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
    a.href = url;
    a.download = 'Sims4_ModListe_' + ts + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setLast('📥 Mod-Liste exportiert als ' + a.download);
    addLog('MOD_EXPORT :: ' + a.download);
  } catch(e) {
    alert('Export-Fehler: ' + e.message);
  }
});

document.getElementById('btn_reload_history').addEventListener('click', () => {
  document.getElementById('mod-snapshot-content').innerHTML = 'Lade…';
  document.getElementById('scan-history-content').innerHTML = 'Lade…';
  loadHistory();
});

// ═══════════════════════════════════════════════════
// ═══ TRAY-ANALYSE ═══
// ═══════════════════════════════════════════════════
let _trayData = null;
let _trayPolling = false;

async function startTrayAnalysis(force) {
  if (_trayPolling) return;
  const statusEl = document.getElementById('tray-status');
  const summaryEl = document.getElementById('tray-summary');
  const filtersEl = document.getElementById('tray-filters');
  const itemsEl = document.getElementById('tray-items');
  const mostUsedEl = document.getElementById('tray-most-used');
  const btnAnalyze = document.getElementById('btn-tray-analyze');
  const btnRefresh = document.getElementById('btn-tray-refresh');

  statusEl.innerHTML = _miniLoaderHTML('tray-loader', 'Tray-Analyse wird gestartet', 5);
  _startMiniTipRotation('tray-loader');
  summaryEl.style.display = 'none';
  filtersEl.style.display = 'none';
  itemsEl.style.display = 'none';
  mostUsedEl.style.display = 'none';
  btnAnalyze.disabled = true;
  btnAnalyze.textContent = '⏳ Analysiere…';
  _trayPolling = true;

  const url = `/api/tray?token=${TOKEN}` + (force ? '&force=1' : '');
  try {
    const r = await fetch(url);
    const d = await r.json();
    if (d.status === 'ready') {
      _trayPolling = false;
      _trayData = d.data;
      renderTrayResults();
      btnAnalyze.disabled = false;
      btnAnalyze.textContent = '🔍 Analysieren';
      btnRefresh.style.display = 'inline-block';
      _refreshAfterTray();
      return;
    }
    // Poll until ready
    pollTray();
  } catch(e) {
    statusEl.innerHTML = '<span style="color:#f87171;">❌ Fehler: ' + esc(e.message) + '</span>';
    btnAnalyze.disabled = false;
    btnAnalyze.textContent = '🔍 Analysieren';
    _trayPolling = false;
    _stopMiniTipRotation('tray-loader');
  }
}

async function pollTray() {
  const statusEl = document.getElementById('tray-status');
  const btnAnalyze = document.getElementById('btn-tray-analyze');
  const btnRefresh = document.getElementById('btn-tray-refresh');
  let progress = 10;

  const iv = setInterval(async () => {
    try {
      const r = await fetch(`/api/tray?token=${TOKEN}`);
      const d = await r.json();
      if (d.status === 'ready') {
        clearInterval(iv);
        _trayPolling = false;
        _trayData = d.data;
        renderTrayResults();
        btnAnalyze.disabled = false;
        btnAnalyze.textContent = '🔍 Analysieren';
        btnRefresh.style.display = 'inline-block';
        _refreshAfterTray();
      } else if (d.status === 'analyzing' || d.status === 'started') {
        var p = (d.progress && d.progress.pct) ? d.progress.pct : Math.min(progress + 3, 90);
        var msg = (d.progress && d.progress.msg) ? d.progress.msg : 'Tray wird gescannt…';
        progress = p;
        _setMiniBar('tray-loader', p);
        var txtEl = document.getElementById('tray-loader-text');
        if (txtEl) { txtEl.textContent = msg; }
        else { statusEl.innerHTML = _miniLoaderHTML('tray-loader', msg, p); _startMiniTipRotation('tray-loader'); }
      } else if (d.status === 'error') {
        clearInterval(iv);
        _trayPolling = false;
        statusEl.innerHTML = '<span style="color:#f87171;">❌ Fehler: ' + esc(d.error || 'Unbekannt') + '</span>';
        btnAnalyze.disabled = false;
        btnAnalyze.textContent = '🔍 Analysieren';
        _stopMiniTipRotation('tray-loader');
      }
    } catch(e) {
      clearInterval(iv);
      _trayPolling = false;
      statusEl.innerHTML = '<span style="color:#f87171;">❌ Verbindungsfehler</span>';
      btnAnalyze.disabled = false;
      btnAnalyze.textContent = '🔍 Analysieren';
      _stopMiniTipRotation('tray-loader');
    }
  }, 2000);
}

function renderTrayResults() {
  const statusEl = document.getElementById('tray-status');
  const summaryEl = document.getElementById('tray-summary');
  const filtersEl = document.getElementById('tray-filters');
  const itemsEl = document.getElementById('tray-items');
  const mostUsedEl = document.getElementById('tray-most-used');
  const s = _trayData.summary;

  _stopMiniTipRotation('tray-loader');
  statusEl.innerHTML = '<span style="color:#4ade80;">✅ Analyse abgeschlossen!</span>';

  // Summary grid
  summaryEl.style.display = 'block';
  summaryEl.innerHTML = `<div class="tray-summary-grid">
    <div class="tray-stat"><div class="tray-stat-num">${s.total_items}</div><div class="tray-stat-label">Gesamt</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${s.households}</div><div class="tray-stat-label">🧑 Haushalte</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${s.lots}</div><div class="tray-stat-label">🏠 Grundstücke</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${s.rooms}</div><div class="tray-stat-label">🛋️ Räume</div></div>
    <div class="tray-stat"><div class="tray-stat-num" style="color:#f59e0b;">${s.items_with_cc}</div><div class="tray-stat-label">Mit CC</div></div>
    <div class="tray-stat"><div class="tray-stat-num" style="color:#6366f1;">${s.total_mods_used}</div><div class="tray-stat-label">Mods genutzt</div></div>
  </div>` + (s.max_cc_item ? `<div style="font-size:12px;color:#94a3b8;margin-top:4px;">🏆 Meiste CC: <b style="color:#e2e8f0;">${esc(s.max_cc_item)}</b> (${s.max_cc_count} Mods)</div>` : '');

  // Show filters
  filtersEl.style.display = 'flex';

  // Render items
  filterTrayItems();

  // Most used mods
  renderTrayMostUsed();
}

function filterTrayItems() {
  if (!_trayData) return;
  const search = (document.getElementById('tray-search').value || '').toLowerCase();
  const typeF = document.getElementById('tray-type-filter').value;
  const ccF = document.getElementById('tray-cc-filter').value;
  const sortF = document.getElementById('tray-sort').value;

  let items = _trayData.items.filter(it => {
    if (search && !(it.name || '').toLowerCase().includes(search) && !(it.creator || '').toLowerCase().includes(search)) return false;
    if (typeF !== 'all' && String(it.type) !== typeF) return false;
    if (ccF === 'cc' && it.cc_count === 0) return false;
    if (ccF === 'nocc' && it.cc_count > 0) return false;
    return true;
  });

  // Sort
  if (sortF === 'name') items.sort((a,b) => (a.name||'').localeCompare(b.name||''));
  else if (sortF === 'cc-desc') items.sort((a,b) => b.cc_count - a.cc_count);
  else if (sortF === 'cc-asc') items.sort((a,b) => a.cc_count - b.cc_count);
  else if (sortF === 'type') items.sort((a,b) => a.type - b.type || (a.name||'').localeCompare(b.name||''));

  const itemsEl = document.getElementById('tray-items');
  itemsEl.style.display = 'block';

  if (items.length === 0) {
    itemsEl.innerHTML = '<div class="muted" style="text-align:center;padding:20px;">Keine Einträge gefunden.</div>';
    return;
  }

  const typeIcons = {1:'🧑', 2:'🏠', 3:'🛋️'};
  const typeNames = {1:'Haushalt', 2:'Grundstück', 3:'Raum'};
  const typeClasses = {1:'type-household', 2:'type-lot', 3:'type-room'};
  let html = '<div class="tray-items-grid">';
  for (const it of items) {
    const icon = typeIcons[it.type] || '❓';
    const typeName = typeNames[it.type] || 'Unbekannt';
    const typeClass = typeClasses[it.type] || '';
    const name = esc(it.name || 'Unbenannt');
    const creator = esc(it.creator || '');
    const ccCount = it.cc_count || 0;
    const mods = it.used_mods || [];
    const cardId = 'tray-card-' + it.instance_id;

    html += `<div class="tray-card" id="${cardId}" onclick="toggleTrayCard('${cardId}')">`;
    html += `<div class="tray-card-header"><span class="tray-card-icon ${typeClass}">${icon}</span><div style="min-width:0;flex:1;"><div class="tray-card-name" title="${name}">${name}</div>`;
    if (creator) html += `<div class="tray-card-creator">von ${creator}</div>`;
    html += `</div></div>`;
    html += `<div class="tray-card-body">`;
    html += `<div class="tray-card-badges">`;
    html += `<span class="tray-badge tray-badge-type">${typeName}</span>`;
    if (ccCount > 0) html += `<span class="tray-badge tray-badge-cc">🎨 ${ccCount} CC-Mods</span>`;
    else html += `<span class="tray-badge tray-badge-nocc">✅ Kein CC</span>`;
    html += `</div>`;
    if (mods.length > 0) {
      html += `<div class="tray-card-mods">`;
      const showMods = mods.slice(0, 30);
      for (const m of showMods) {
        const mname = esc((m.name || m.path || '').split(/[/\\\\]/).pop());
        html += `<div class="tray-mod-item"><span class="tray-mod-dot"></span><span class="tray-mod-name" title="${esc(m.path||'')}">${mname}</span><span class="tray-mod-matches">${m.matches} Treffer</span></div>`;
      }
      if (mods.length > 30) html += `<div class="tray-mod-item" style="color:#64748b;">…und ${mods.length - 30} weitere</div>`;
      html += `</div>`;
      html += `<div class="tray-expand-hint">▼ Klicken für Details</div>`;
    }
    html += `</div></div>`;
  }
  html += '</div>';
  html += `<div style="text-align:center;margin-top:8px;font-size:12px;color:#64748b;">${items.length} von ${_trayData.items.length} Einträgen</div>`;
  itemsEl.innerHTML = html;
}

function toggleTrayCard(cardId) {
  const el = document.getElementById(cardId);
  if (el) el.classList.toggle('expanded');
}

function renderTrayMostUsed() {
  const mostUsedEl = document.getElementById('tray-most-used');
  if (!_trayData || !_trayData.mod_usage) { mostUsedEl.style.display='none'; return; }

  const entries = Object.entries(_trayData.mod_usage)
    .sort((a,b) => b[1].used_count - a[1].used_count)
    .slice(0, 50);

  if (entries.length === 0) { mostUsedEl.style.display='none'; return; }

  mostUsedEl.style.display = 'block';
  let html = '<h3 style="color:#e2e8f0;margin-bottom:8px;">📊 Meistgenutzte Mods im Tray</h3>';
  html += '<table class="tray-most-used-table"><thead><tr><th>Mod</th><th>Verwendet von</th><th style="text-align:center;">Anzahl</th></tr></thead><tbody>';
  for (const [path, info] of entries) {
    const name = esc((info.name || path).split(/[/\\\\]/).pop());
    const usedBy = (info.used_by || []).slice(0, 5).map(n => esc(n)).join(', ');
    const more = (info.used_by || []).length > 5 ? ` +${info.used_by.length - 5} mehr` : '';
    html += `<tr><td title="${esc(path)}">${name}</td><td>${usedBy}${more}</td><td style="text-align:center;"><span class="tray-used-count">${info.used_count}×</span></td></tr>`;
  }
  html += '</tbody></table>';
  mostUsedEl.innerHTML = html;
}

</script>
<div id="lightbox-overlay" onclick="if(event.target===this)closeLightbox()"><div id="lightbox-content"></div></div>
<button id="lightbox-close" title="Schließen" onclick="closeLightbox()">✕</button>
<button id="back-to-top" title="Zurück nach oben" onclick="window.scrollTo({top:0,behavior:'smooth'});">⬆</button>
<script>
function openLightbox(src) {
  const ov = document.getElementById('lightbox-overlay');
  document.getElementById('lightbox-content').innerHTML =
    `<img class="lb-single" src="${src}" alt="Vorschau" onclick="event.stopPropagation()" />`;
  ov.classList.add('active');
  document.body.style.overflow = 'hidden';
}
function openCompareGallery(gi) {
  if (!window.__DATA || !window.__DATA.groups || !window.__DATA.groups[gi]) return;
  const g = window.__DATA.groups[gi];
  const items = [];
  for (const f of g.files) {
    const fname = (f.path || '').split(/[\\\/]/).pop();
    const thumb = f.deep && f.deep.thumbnail_b64 ? f.deep.thumbnail_b64 : null;
    const cat = f.deep && f.deep.category ? f.deep.category : '';
    const size = f.size_h || '?';
    const mtime = f.mtime || '?';
    items.push({fname, thumb, cat, size, mtime, path: f.path});
  }
  if (items.filter(i => i.thumb).length === 0) {
    alert('Keine Vorschaubilder in dieser Gruppe vorhanden.');
    return;
  }
  const esc2 = s => s ? s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;') : '';
  let html = `<div class="lb-gallery" onclick="event.stopPropagation()">`;
  html += `<div class="lb-gallery-title">🖼️ Bildvergleich — ${esc2(g.key_short || g.key)} (${items.length} Dateien)</div>`;
  for (const it of items) {
    if (it.thumb) {
      html += `<div class="lb-gallery-card">`;
      html += `<img src="${it.thumb}" alt="${esc2(it.fname)}" onclick="openLightbox(this.src)" style="cursor:zoom-in;" title="Klicken zum Vergrößern" />`;
      html += `<div class="lb-label">${esc2(it.fname)}</div>`;
      html += `<div class="lb-meta">${esc2(it.size)} · ${esc2(it.mtime)}${it.cat ? ' · ' + esc2(it.cat) : ''}</div>`;
      html += `</div>`;
    } else {
      html += `<div class="lb-gallery-card" style="border-color:#475569;opacity:0.5;">`;
      html += `<div style="width:120px;height:120px;background:#0f172a;border-radius:8px;display:flex;align-items:center;justify-content:center;margin:0 auto 8px;color:#475569;font-size:36px;">?</div>`;
      html += `<div class="lb-label">${esc2(it.fname)}</div>`;
      html += `<div class="lb-meta">${esc2(it.size)} · ${esc2(it.mtime)} · Kein Bild</div>`;
      html += `</div>`;
    }
  }
  html += `<div class="lb-gallery-hint">Klicke auf ein Bild zum Vergrößern · ESC oder Hintergrund zum Schließen</div>`;
  html += `</div>`;
  const ov = document.getElementById('lightbox-overlay');
  document.getElementById('lightbox-content').innerHTML = html;
  ov.classList.add('active');
  document.body.style.overflow = 'hidden';
}
function closeLightbox() {
  document.getElementById('lightbox-overlay').classList.remove('active');
  document.body.style.overflow = '';
}
document.addEventListener('keydown', e => {
  // Nicht reagieren wenn Eingabefeld fokussiert ist (außer Escape)
  const active = document.activeElement;
  const inInput = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable);

  // Escape: Lightbox/Modal schließen oder Suchfeld verlassen
  if (e.key === 'Escape') {
    const lb = document.getElementById('lightbox-overlay');
    if (lb && lb.classList.contains('active')) { closeLightbox(); return; }
    const bpo = document.getElementById('batch-progress-overlay');
    if (bpo && bpo.style.display !== 'none') return; // Batch läuft — nicht schließen
    if (inInput) { active.blur(); e.preventDefault(); return; }
    return;
  }

  // Ab hier: Nicht reagieren wenn in Eingabefeld
  if (inInput) return;

  // / oder Ctrl+K → Suche fokussieren
  if (e.key === '/' || (e.ctrlKey && e.key === 'k')) {
    e.preventDefault();
    const search = document.getElementById('global-search');
    if (search) search.focus();
    return;
  }

  // Ctrl+R → Rescan
  if (e.ctrlKey && e.key === 'r') {
    e.preventDefault();
    const btn = document.getElementById('reload');
    if (btn) btn.click();
    return;
  }

  // 1–5 → Tab wechseln (Hauptbereiche)
  const tabMap = {'1':'dashboard','2':'duplicates','3':'outdated','4':'tray','5':'stats'};
  if (tabMap[e.key]) {
    e.preventDefault();
    switchTab(tabMap[e.key]);
    return;
  }

  // ? → Tutorial starten
  if (e.key === '?' && !e.ctrlKey) {
    e.preventDefault();
    if (typeof startTutorial === 'function') startTutorial();
    return;
  }
});

// ═══════════════════════════════════════════════════
// ═══ SAVEGAME-ANALYSE ═══
// ═══════════════════════════════════════════════════
let _savegameData = null;
let _savegamePolling = false;

// Nach Tray-Analyse: Savegame + Bibliothek neu laden für CC-Daten
async function _refreshAfterTray() {
  console.log('[CC] Tray fertig — lade Savegame + Bibliothek neu für CC-Info…');
  if (_savegameData) {
    try {
      const r = await fetch(`/api/savegame?token=${TOKEN}`);
      const d = await r.json();
      if (d.status === 'ready') {
        _savegameData = d.data;
        renderSavegameResults();
        console.log('[CC] Savegame-Karten mit CC-Daten aktualisiert');
      }
    } catch(e) { console.warn('[CC] Savegame-Reload fehlgeschlagen:', e); }
  }
  if (_libraryData) {
    startLibraryAnalysis(true);
  }
}

async function startSavegameAnalysis(force, selectedSave) {
  if (_savegamePolling) return;
  const statusEl = document.getElementById('savegame-status');
  const summaryEl = document.getElementById('savegame-summary');
  const filtersEl = document.getElementById('savegame-filters');
  const listEl = document.getElementById('savegame-list');
  const btnAnalyze = document.getElementById('btn-savegame-analyze');

  statusEl.innerHTML = _miniLoaderHTML('sg-loader', 'Spielstand wird gelesen', 5);
  _startMiniTipRotation('sg-loader');
  summaryEl.style.display = 'none';
  filtersEl.style.display = 'none';
  listEl.style.display = 'none';
  btnAnalyze.disabled = true;
  btnAnalyze.textContent = '⏳ Analysiere…';
  _savegamePolling = true;

  let url = `/api/savegame?token=${TOKEN}`;
  if (force) url += '&force=1';
  if (selectedSave) url += '&save=' + encodeURIComponent(selectedSave);
  try {
    const r = await fetch(url);
    const d = await r.json();
    if (d.status === 'ready') {
      _savegamePolling = false;
      _savegameData = d.data;
      renderSavegameResults();
      checkSaveHealth();
      btnAnalyze.disabled = false;
      btnAnalyze.textContent = '🔍 Analysieren';
      return;
    }
    pollSavegame();
  } catch(e) {
    statusEl.innerHTML = '<span style="color:#f87171;">❌ Fehler: ' + esc(e.message) + '</span>';
    btnAnalyze.disabled = false;
    btnAnalyze.textContent = '🔍 Analysieren';
    _savegamePolling = false;
    _stopMiniTipRotation('sg-loader');
    if (!_savegameReady) { _savegameReady = true; _checkAllReady(); }
  }
}

async function pollSavegame() {
  const statusEl = document.getElementById('savegame-status');
  const btnAnalyze = document.getElementById('btn-savegame-analyze');
  let progress = 10;

  const iv = setInterval(async () => {
    try {
      const r = await fetch(`/api/savegame?token=${TOKEN}`);
      const d = await r.json();
      if (d.status === 'ready') {
        clearInterval(iv);
        _savegamePolling = false;
        _savegameData = d.data;
        renderSavegameResults();
        checkSaveHealth();
        btnAnalyze.disabled = false;
        btnAnalyze.textContent = '🔍 Analysieren';
      } else if (d.status === 'analyzing' || d.status === 'started') {
        var p = (d.progress && d.progress.pct) ? d.progress.pct : Math.min(progress + 5, 90);
        var msg = (d.progress && d.progress.msg) ? d.progress.msg : 'Spielstand wird analysiert…';
        progress = p;
        _setMiniBar('sg-loader', p);
        var txtEl = document.getElementById('sg-loader-text');
        if (txtEl) { txtEl.textContent = msg; }
        else { statusEl.innerHTML = _miniLoaderHTML('sg-loader', msg, p); _startMiniTipRotation('sg-loader'); }
      }
    } catch(e) {
      clearInterval(iv);
      _savegamePolling = false;
      statusEl.innerHTML = '<span style="color:#f87171;">❌ Verbindungsfehler</span>';
      btnAnalyze.disabled = false;
      btnAnalyze.textContent = '🔍 Analysieren';
      _stopMiniTipRotation('sg-loader');
      if (!_savegameReady) { _savegameReady = true; _checkAllReady(); }
    }
  }, 1500);
}

function switchSavegame() {
  const sel = document.getElementById('savegame-select').value;
  if (sel) startSavegameAnalysis(true, sel);
}

function renderSavegameResults() {
  const statusEl = document.getElementById('savegame-status');
  const summaryEl = document.getElementById('savegame-summary');
  const filtersEl = document.getElementById('savegame-filters');
  const listEl = document.getElementById('savegame-list');
  const selectEl = document.getElementById('savegame-select');
  const d = _savegameData;

  // Savegame als geladen markieren (auch bei Fehler)
  if (!_savegameReady) { _savegameReady = true; _checkAllReady(); }
  _stopMiniTipRotation('sg-loader');

  if (d.error) {
    statusEl.innerHTML = '<span style="color:#f87171;">❌ ' + esc(d.error) + '</span>';
    return;
  }

  statusEl.innerHTML = '<span style="color:#4ade80;">✅ Analyse abgeschlossen!</span>';

  // Dropdown
  if (d.available_saves && d.available_saves.length > 0) {
    selectEl.style.display = '';
    selectEl.innerHTML = '';
    for (const sv of d.available_saves) {
      const opt = document.createElement('option');
      opt.value = sv.file;
      opt.textContent = sv.file + ' (' + sv.size_mb + ' MB · ' + sv.date + ')';
      if (sv.file === d.active_save) opt.selected = true;
      selectEl.appendChild(opt);
    }
  }

  const gs = d.gender_stats || {};
  const as = d.age_stats || {};
  const sp = d.species_stats || {};
  const sk = d.skin_stats || {};
  const gameSets = d.game_settings || {};

  // Gesamtvermögen aller Haushalte berechnen
  const allFunds = new Map();
  for (const sim of (d.sims || [])) {
    if (sim.simoleons > 0 && sim.household) allFunds.set(sim.household, sim.simoleons);
  }
  const totalSimoleons = [...allFunds.values()].reduce((a,b)=>a+b, 0);

  summaryEl.style.display = 'block';
  let summaryHtml = `<div class="tray-summary-grid">
    <div class="tray-stat"><div class="tray-stat-num">${d.sim_count}</div><div class="tray-stat-label">🧑 Sims</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${d.household_count}</div><div class="tray-stat-label">👨‍👩‍👧 Haushalte</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${d.world_count}</div><div class="tray-stat-label">🌍 Welten</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${gs['Männlich']||0}</div><div class="tray-stat-label">♂️ Männlich</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${gs['Weiblich']||0}</div><div class="tray-stat-label">♀️ Weiblich</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${d.partner_count||0}</div><div class="tray-stat-label">💑 Paare</div></div>
  </div>
  <div style="margin-top:8px;display:flex;gap:10px;flex-wrap:wrap;font-size:11px;color:#94a3b8;align-items:center;">
    ${gameSets.game_version ? '<span class="game-version-badge">🎮 v' + esc(gameSets.game_version) + '</span>' : ''}
    ${totalSimoleons > 0 ? '<span style="color:#86efac;font-weight:600;">§ ' + totalSimoleons.toLocaleString('de-DE') + ' Gesamt</span>' : ''}
    <span>👶${as['Baby']||0}</span><span>🧒${as['Kleinkind']||0}</span><span>🧒${as['Kind']||0}</span>
    <span>🧑${as['Teen']||0}</span><span>🧑${as['Junger Erwachsener']||0}</span><span>🧑${as['Erwachsener']||0}</span><span>👴${as['Älterer']||0}</span>
    <span style="margin-left:6px;color:#64748b;">|</span>
    ${Object.entries(sp).map(([k,v]) => '<span style="color:#a78bfa;">'+esc(k)+': '+v+'</span>').join('')}
    <span style="margin-left:6px;color:#64748b;">|</span>
    <span>📦 ${d.active_save_size_mb} MB</span>
  </div>`;

  // ── Spieleinstellungen-Panel ──
  if (Object.keys(gameSets).length > 1) {
    summaryHtml += '<div class="game-settings-panel" style="margin-top:12px;"><h3>⚙️ Spieleinstellungen</h3><div class="game-settings-grid">';
    if (gameSets.cc_mods !== undefined) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">🧩</span><div><div class="game-setting-label">CC/Mods</div><div class="game-setting-val">${gameSets.cc_mods ? '✅ Aktiv' : '❌ Aus'}</div></div></div>`;
    if (gameSets.script_mods !== undefined) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">📜</span><div><div class="game-setting-label">Skript-Mods</div><div class="game-setting-val">${gameSets.script_mods ? '✅ Aktiv' : '❌ Aus'}</div></div></div>`;
    if (gameSets.aging !== undefined) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">⏳</span><div><div class="game-setting-label">Alterung</div><div class="game-setting-val">${gameSets.aging ? '✅ An' : '❌ Aus'}</div></div></div>`;
    if (gameSets.lifespan_label) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">⏱️</span><div><div class="game-setting-label">Lebensdauer</div><div class="game-setting-val">${esc(gameSets.lifespan_label)}</div></div></div>`;
    if (gameSets.season_label) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">🍂</span><div><div class="game-setting-label">Jahreszeiten</div><div class="game-setting-val">${esc(gameSets.season_label)}</div></div></div>`;
    if (gameSets.autonomy_label) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">🤖</span><div><div class="game-setting-label">Autonomie</div><div class="game-setting-val">${esc(gameSets.autonomy_label)}</div></div></div>`;
    if (gameSets.language) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">🌐</span><div><div class="game-setting-label">Sprache</div><div class="game-setting-val">${esc(gameSets.language)}</div></div></div>`;
    if (gameSets.resolution) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">🖥️</span><div><div class="game-setting-label">Auflösung</div><div class="game-setting-val">${esc(gameSets.resolution)}</div></div></div>`;
    if (gameSets.online_features !== undefined) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">🌐</span><div><div class="game-setting-label">Online</div><div class="game-setting-val">${gameSets.online_features ? '✅ An' : '❌ Aus'}</div></div></div>`;
    if (gameSets.fullscreen !== undefined) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">🖥️</span><div><div class="game-setting-label">Vollbild</div><div class="game-setting-val">${gameSets.fullscreen ? '✅ An' : '❌ Aus'}</div></div></div>`;
    if (gameSets.fps_limit) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">🎯</span><div><div class="game-setting-label">FPS-Limit</div><div class="game-setting-val">${gameSets.fps_limit}</div></div></div>`;
    if (gameSets.ui_scale && gameSets.ui_scale !== 100) summaryHtml += `<div class="game-setting-item"><span class="game-setting-icon">🔍</span><div><div class="game-setting-label">UI-Skalierung</div><div class="game-setting-val">${gameSets.ui_scale}%</div></div></div>`;
    summaryHtml += '</div></div>';
  }

  summaryHtml += `${(d.duplicate_sims && d.duplicate_sims.length > 0) ? `<div style="margin-top:10px;padding:10px 14px;background:#ef444420;border:1px solid #ef444440;border-radius:8px;">
    <div style="font-weight:700;color:#f87171;font-size:13px;">⚠️ ${d.duplicate_sims.length} doppelte Sim(s) erkannt!</div>
    <div style="font-size:11px;color:#fca5a5;margin-top:4px;">${d.duplicate_sims.map(ds => ds.count + 'x ' + esc(ds.name) + ' (' + ds.households.map(h=>esc(h)).join(', ') + ')').join(' &middot; ')}</div>
    <div style="font-size:10px;color:#94a3b8;margin-top:4px;">Doppelte Sims können durch Bugs oder Mods entstehen und Spielprobleme verursachen.</div>
  </div>` : ''}`;
  summaryEl.innerHTML = summaryHtml;

  filtersEl.style.display = 'flex';
  listEl.style.display = 'block';

  // Portrait-Verfügbarkeit markieren (für Filter)
  const portraitSet = new Set(d.portrait_names || []);
  window._portraitData = d.portrait_data || {};
  const basegameSet = new Set(d.basegame_names || []);
  const townieSet = new Set(d.townie_names || []);
  const dupeSet = new Set((d.duplicate_sims || []).map(ds => ds.name));
  const librarySet = new Set(d.library_sim_names || []);
  const ccByHH = d.cc_by_household || {};
  for (const sim of (d.sims || [])) {
    sim._hasPortrait = portraitSet.has(sim.full_name);
    sim._isBasegame = basegameSet.has(sim.full_name);
    sim._isTownie = townieSet.has(sim.full_name);
    sim._isDuplicate = dupeSet.has(sim.full_name);
    sim._inLibrary = librarySet.has(sim.full_name);
    sim._ccMods = ccByHH[sim.household] || [];
    sim._ccCount = sim._ccMods.length;
  }

  // Welt-Filter dynamisch befüllen
  const worldSelect = document.getElementById('savegame-world-filter');
  if (worldSelect) {
    const worlds = [...new Set((d.sims || []).map(s => s.world || '').filter(w => w))].sort();
    worldSelect.innerHTML = '<option value="all">🏘️ Alle Welten (' + worlds.length + ')</option>';
    for (const w of worlds) {
      const count = (d.sims || []).filter(s => s.world === w).length;
      worldSelect.innerHTML += '<option value="' + esc(w) + '">🏘️ ' + esc(w) + ' (' + count + ')</option>';
    }
  }

  filterSavegameSims();
}

// ── Global sim registry for character sheet ──
if (!window._simRegistry) window._simRegistry = {};
let _simRegIdx = 0;

function _simCard(sim, showHousehold) {
  const isMale = sim.gender === 'Männlich';
  const isFemale = sim.gender === 'Weiblich';
  const genderCls = isMale ? 'male' : isFemale ? 'female' : 'unknown';
  // Register sim for character sheet modal
  const _regId = 'sreg_' + (_simRegIdx++);
  window._simRegistry[_regId] = sim;
  const avatarEmoji = sim.species_emoji ? sim.species_emoji : sim.age === 'Baby' ? '👶' : sim.age === 'Kleinkind' ? '🧒' : sim.age === 'Kind' ? '🧒' : isMale ? '👨' : isFemale ? '👩' : '🧑';

  // Spezies-spezifische CSS-Klasse für Karten  
  const speciesCls = {'Haustier':'pet','Pferd':'horse','Werwolf':'werewolf','Zauberer':'spellcaster','Fee':'fairy','Vampir':'vampire','Meerjungfrau':'mermaid','Alien':'alien'}[sim.species] || '';

  // Portrait: Bild (eingebettetes Base64 oder Emoji-Fallback)
  const simFullName = sim.full_name || '';
  let portraitHtml;
  const embeddedPortrait = (window._portraitData || {})[simFullName] || (window._libPortraitData || {})[simFullName];
  if (embeddedPortrait) {
    portraitHtml = `<div class="sim-portrait-frame"><img src="${embeddedPortrait}" data-simname="${esc(simFullName)}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><div class="sim-emoji-holder ${genderCls}" style="display:none;">${avatarEmoji}</div></div>`;
  } else {
    portraitHtml = `<div class="sim-portrait-frame"><div class="sim-emoji-holder ${genderCls}">${avatarEmoji}</div></div>`;
  }

  // Typ-Badge (Geschlecht)
  const typeBadge = `<span class="sim-type-badge ${genderCls}">${sim.gender_emoji} ${esc(sim.gender)}</span>`;

  // Spezies-Badge (wenn nicht Mensch)
  let speciesBadge = '';
  if (sim.species) speciesBadge = `<span class="sim-type-badge" style="background:#7c3aed33;color:#c4b5fd;border:1px solid #7c3aed55;">${sim.species_emoji || '✨'} ${esc(sim.species)}</span>`;

  // Stats
  let statsHtml = '<div class="sim-card-stats">';
  statsHtml += `<div class="sim-stat"><div class="sim-stat-val">${sim.age_emoji}</div><div class="sim-stat-label">${esc(sim.age)}</div></div>`;
  if (sim.trait_count > 0) statsHtml += `<div class="sim-stat"><div class="sim-stat-val">🎭 ${sim.trait_count}</div><div class="sim-stat-label">Traits</div></div>`;
  if (sim.relationship_count > 0) statsHtml += `<div class="sim-stat"><div class="sim-stat-val">🤝 ${sim.relationship_count}</div><div class="sim-stat-label">Bezieh.</div></div>`;
  if (sim.career_name) statsHtml += `<div class="sim-stat"><div class="sim-stat-val">💼 ${sim.career_level||''}</div><div class="sim-stat-label">${esc(sim.career_name)}</div></div>`;
  else if (sim.career_level > 0) statsHtml += `<div class="sim-stat"><div class="sim-stat-val">💼 ${sim.career_level}</div><div class="sim-stat-label">Karriere</div></div>`;
  const likesCnt = sim.likes ? Object.values(sim.likes).reduce((s,a)=>s+a.length,0) : 0;
  const dislikesCnt = sim.dislikes ? Object.values(sim.dislikes).reduce((s,a)=>s+a.length,0) : 0;
  if (likesCnt > 0 || dislikesCnt > 0) statsHtml += `<div class="sim-stat"><div class="sim-stat-val">❤️ ${likesCnt}</div><div class="sim-stat-label">${dislikesCnt > 0 ? '💔 '+dislikesCnt+' Abneig.' : 'Vorlieben'}</div></div>`;
  statsHtml += '</div>';

  // Badges
  let badges = '';
  if (showHousehold !== false) badges += `<span class="sim-badge sim-badge-hh">👨‍👩‍👧 ${esc(sim.household)}</span>`;
  if (sim.is_played) badges += `<span class="sim-badge" style="background:#a78bfa22;color:#c4b5fd;border:1px solid #a78bfa44;">🎮 Gespielt</span>`;
  if (sim.simoleons > 0) badges += `<span class="sim-badge sim-badge-simoleons">§ ${sim.simoleons.toLocaleString('de-DE')}</span>`;
  if (sim.lot_name) badges += `<span class="sim-badge sim-badge-lot">🏠 ${esc(sim.lot_name)}</span>`;
  if (sim.gallery_username) badges += `<span class="sim-badge sim-badge-username">👤 ${esc(sim.gallery_username)}</span>`;
  if (sim._isBasegame) badges += `<span class="sim-badge sim-badge-basegame">🏠 Basegame</span>`;
  if (sim._isTownie) badges += `<span class="sim-badge sim-badge-townie">🤖 EA-Townie</span>`;
  if (sim._isDuplicate) badges += `<span class="sim-badge sim-badge-dupe">⚠️ Duplikat</span>`;
  if (sim._inLibrary) badges += `<span class="sim-badge" style="background:#22c55e22;color:#86efac;border:1px solid #22c55e44;">📚 In Bibliothek</span>`;
  if (sim.skin_tone) badges += `<span class="sim-badge sim-badge-skin">🎨 ${esc(sim.skin_tone)}</span>`;

  // Trait-Details Aufschlüsselung
  let traitDetailHtml = '';
  if (sim.trait_details) {
    const td = sim.trait_details;
    const parts = [];
    if (td.personality) parts.push('🧠 ' + td.personality + ' Persönl.');
    if (td.bonus) parts.push('⭐ ' + td.bonus + ' Bonus');
    if (td.lifestyle) parts.push('🏃 ' + td.lifestyle + ' Lifestyle');
    if (td.likes) parts.push('❤️ ' + td.likes + ' Likes');
    if (td.aspiration) parts.push('🌟 ' + td.aspiration + ' Aspiration');
    if (parts.length > 0) {
      const items = parts.map(p => `<span class="sim-trait-detail-item">${p}</span>`).join('');
      traitDetailHtml = `<div class="sim-trait-details" style="display:flex;">${items}</div>`;
    }
  }

  // CC-Badge
  let ccHtml = '';
  if (sim._ccCount > 0) {
    const simId = (sim.full_name || '').replace(/[^a-zA-Z0-9]/g, '') + '_' + (sim.sim_id || Math.random().toString(36).slice(2,8));
    const ccModsList = sim._ccMods.map(m =>
      `<div class="lib-cc-item"><span class="lib-cc-item-name">${esc(m.name)}</span><span class="lib-cc-item-count">${m.matches}x</span></div>`
    ).join('');
    ccHtml = `<div style="padding:0 10px 6px;">
      <span class="lib-cc-badge" onclick="document.getElementById('simcc-${simId}').classList.toggle('open');event.stopPropagation();" title="${sim._ccCount} CC-Mods im Haushalt">🧩 ${sim._ccCount} CC</span>
      <div class="lib-cc-list" id="simcc-${simId}" style="margin-top:6px;">${ccModsList}</div>
    </div>`;
  }

  let partnerHtml = '';
  if (sim.partner) partnerHtml = `<div class="sim-partner-line">💕 ${esc(sim.partner)}</div>`;

  // Familien-Rolle Badge
  const roleEmoji = {'Elternteil':'👨‍👧','Kind':'🧒','Partner':'💑','Geschwister':'👫','Mitbewohner':'🏠','Einzelgänger':'🧑'};
  const roleCls = (sim.family_role || '').toLowerCase().replace('ä','ae');
  let roleHtml = '';
  if (sim.family_role && sim.family_role !== 'Einzelgänger') {
    roleHtml = `<span class="sim-role-badge ${roleCls}">${roleEmoji[sim.family_role]||''} ${esc(sim.family_role)}</span>`;
  }

  // Beziehungs-Score Bar
  let relBarHtml = '';
  if (sim.rel_score && sim.rel_score !== 'keine') {
    const barCls = sim.rel_score.replace(' ','-');
    relBarHtml = `<div style="padding:2px 12px 0;"><div class="sim-rel-bar"><div class="sim-rel-bar-fill ${barCls}"></div></div><div style="font-size:9px;color:#64748b;margin-top:2px;">Vernetzung: ${esc(sim.rel_score)}</div></div>`;
  }

  // ── Skills ──
  let skillsHtml = '';
  if (sim.top_skills && sim.top_skills.length > 0) {
    const rows = sim.top_skills.map(sk => {
      const maxLvl = sk.max_level || 10;
      let stars = '';
      for (let i = 1; i <= maxLvl; i++) stars += i <= sk.level ? '★' : '<span class="off">★</span>';
      const isMod = sk.name.startsWith('Mod-Skill');
      const nameCls = isMod ? 'sim-skill-name mod-skill' : 'sim-skill-name';
      return `<div class="sim-skill-row"><span class="${nameCls}">${esc(sk.name)}</span><span class="sim-skill-stars">${stars}</span></div>`;
    }).join('');
    skillsHtml = `<div class="sim-skills-section">${rows}</div>`;
  }

  // ── Bedürfnisse ──
  let needsHtml = '';
  if (sim.needs && sim.needs.length > 0) {
    const needRows = sim.needs.map(n => {
      const pct = Math.max(0, Math.min(100, n.percent));
      let cls = 'high';
      if (pct < 20) cls = 'critical';
      else if (pct < 40) cls = 'low';
      else if (pct < 70) cls = 'medium';
      return `<div class="sim-need-row"><span class="sim-need-emoji">${n.emoji}</span><span class="sim-need-name">${esc(n.name)}</span><div class="sim-need-bar"><div class="sim-need-bar-fill ${cls}" style="width:${pct}%"></div></div><span class="sim-need-val">${pct}%</span></div>`;
    }).join('');
    needsHtml = `<div class="sim-needs-section"><div class="sim-needs-title">Bedürfnisse</div>${needRows}</div>`;
  }

  // ── Mood Bar ──
  let moodHtml = '';
  if (sim.mood_label && sim.mood_label !== 'Unbekannt') {
    const moodMap = {'Sehr glücklich':'very-happy','Glücklich':'happy','Neutral':'neutral','Traurig':'sad','Sehr traurig':'very-sad'};
    const moodCls = moodMap[sim.mood_label] || 'neutral';
    moodHtml = `<div class="sim-detail-row"><span class="detail-icon">${sim.mood_emoji||''}</span><span class="detail-val">${esc(sim.mood_label)}</span><span class="detail-label" style="margin-left:auto;">${sim.mood_value > 0 ? '+' : ''}${sim.mood_value}</span></div>
    <div style="padding:0 12px;"><div class="sim-mood-bar"><div class="sim-mood-bar-fill ${moodCls}"></div></div></div>`;
  }

  // ── Sim-Alter ──
  let ageInfoHtml = '';
  if (sim.sim_age_days && sim.sim_age_days > 0) {
    ageInfoHtml = `<div class="sim-detail-row"><span class="detail-icon">📅</span><span class="detail-label">Spielalter:</span><span class="detail-val">${sim.sim_age_days} Tage</span></div>`;
  }

  // ── Outfits ──
  let outfitHtml = '';
  if (sim.outfit_summary && sim.outfit_summary.length > 0) {
    const ofId = 'outfit-' + (sim.full_name || '').replace(/[^a-zA-Z0-9]/g, '') + '_' + (sim.sim_id || 0);
    const catRows = sim.outfit_summary.map(o => {
      const btTags = (o.body_types || []).map(bt => `<span class="outfit-bt-tag">${esc(bt)}</span>`).join('');
      return `<div class="outfit-cat-row"><span class="outfit-cat-name">${esc(o.category)}</span><span class="outfit-cat-count">${o.part_count} Teile</span><div class="outfit-bt-tags">${btTags}</div></div>`;
    }).join('');
    // CC-Mods die zum Outfit gehören
    let outfitCcHtml = '';
    if (sim.outfit_cc_mods && sim.outfit_cc_mods.length > 0) {
      const ccRows = sim.outfit_cc_mods.map(m =>
        `<div class="lib-cc-item"><span class="lib-cc-item-name">${esc(m.name)}</span><span class="lib-cc-item-count">${m.matches}x</span></div>`
      ).join('');
      outfitCcHtml = `<div style="margin-top:6px;border-top:1px solid #334155;padding-top:6px;"><div style="font-size:10px;color:#a78bfa;font-weight:700;margin-bottom:4px;">🧩 CC-Teile im Outfit (${sim.outfit_cc_mods.length})</div><div style="max-height:200px;overflow-y:auto;">${ccRows}</div></div>`;
    }
    outfitHtml = `<div class="sim-outfit-section">
      <div class="sim-outfit-title" style="cursor:pointer;" onclick="document.getElementById('${ofId}').classList.toggle('open');event.stopPropagation();">👗 ${sim.outfit_total_parts || 0} Outfit-Teile · ${sim.outfit_categories ? sim.outfit_categories.length : 0} Kategorien ▾</div>
      <div class="sim-outfit-detail lib-cc-list" id="${ofId}">${catRows}${outfitCcHtml}</div>
    </div>`;
  }

  // Familienmitglieder (aufklappbar, wenn mehr als 0)
  let familyHtml = '';
  if (sim.family_members && sim.family_members.length > 0) {
    const famId = 'fam-' + (sim.full_name || '').replace(/[^a-zA-Z0-9]/g, '') + '_' + (sim.sim_id || 0);
    const famRows = sim.family_members.map(m => {
      const mEmoji = m.gender === 'Männlich' ? '♂️' : m.gender === 'Weiblich' ? '♀️' : '';
      return `<div class="hh-member-row">${mEmoji} ${esc(m.name)} <span class="hh-m-role">${esc(m.role)}</span></div>`;
    }).join('');
    familyHtml = `<div class="sim-family-section">
      <div class="sim-family-title" style="cursor:pointer;" onclick="document.getElementById('${famId}').classList.toggle('open');event.stopPropagation();">👨‍👩‍👧 Familie & Haushalt ▾</div>
      <div class="sim-hh-detail lib-cc-list" id="${famId}">${famRows}</div>
    </div>`;
  }

  return `<div class="sim-card ${genderCls} ${speciesCls}" data-has-portrait="1" data-reg-id="${_regId}" onclick="openCharSheet('${_regId}')" style="cursor:pointer;">
    <div class="sim-card-topbar">
      <span class="sim-name" title="${esc(sim.full_name)}">${esc(sim.full_name)}</span>
      <div class="sim-badges-row">${roleHtml}${speciesBadge}${typeBadge}</div>
    </div>
    ${portraitHtml}
    <div class="sim-card-info">
      <div class="sim-subtitle"><span class="gender-dot ${genderCls}"></span> ${esc(sim.gender)} · ${esc(sim.age)}</div>
      ${sim.world ? `<div class="sim-world-tag">🏘️ ${esc(sim.world)}</div>` : ''}
    </div>
    ${statsHtml}
    ${traitDetailHtml}
    ${partnerHtml}
    ${relBarHtml}
    ${moodHtml}
    ${ageInfoHtml}
    ${skillsHtml}
    ${needsHtml}
    <div class="sim-card-body"><div class="sim-badges">${badges}</div></div>
    ${ccHtml}
    ${outfitHtml}
    ${familyHtml}
  </div>`;
}

function filterSavegameSims() {
  if (!_savegameData) return;
  const search = (document.getElementById('savegame-search').value || '').toLowerCase();
  const sortBy = document.getElementById('savegame-sort').value;
  const ageFilter = document.getElementById('savegame-age-filter').value;
  const genderFilter = document.getElementById('savegame-gender-filter').value;
  const worldFilter = document.getElementById('savegame-world-filter').value;
  const speciesFilter = document.getElementById('savegame-species-filter').value;
  const groupHH = document.getElementById('savegame-group-hh').checked;
  const playedOnly = document.getElementById('savegame-played-filter').checked;
  const portraitOnly = document.getElementById('savegame-portrait-filter').checked;
  const basegameOnly = document.getElementById('savegame-basegame-filter').checked;
  const townieOnly = document.getElementById('savegame-townie-filter').checked;
  const dupeOnly = document.getElementById('savegame-dupe-filter').checked;
  const ccOnly = document.getElementById('savegame-cc-filter').checked;
  const libraryOnly = document.getElementById('savegame-library-filter').checked;
  const listEl = document.getElementById('savegame-list');

  let sims = [...(_savegameData.sims || [])];

  if (search) {
    sims = sims.filter(s =>
      s.full_name.toLowerCase().includes(search) ||
      s.household.toLowerCase().includes(search) ||
      (s.world && s.world.toLowerCase().includes(search)) ||
      (s.partner && s.partner.toLowerCase().includes(search)) ||
      (s.species && s.species.toLowerCase().includes(search)) ||
      (s.family_role && s.family_role.toLowerCase().includes(search)) ||
      (s.mood_label && s.mood_label.toLowerCase().includes(search)) ||
      (s.lot_name && s.lot_name.toLowerCase().includes(search)) ||
      (s.gallery_username && s.gallery_username.toLowerCase().includes(search)) ||
      (s.top_skills && s.top_skills.some(sk => sk.name.toLowerCase().includes(search))) ||
      (s._ccMods && s._ccMods.some(m => m.name.toLowerCase().includes(search)))
    );
  }
  if (ageFilter !== 'all') sims = sims.filter(s => s.age === ageFilter);
  if (genderFilter !== 'all') sims = sims.filter(s => s.gender === genderFilter);
  if (worldFilter !== 'all') sims = sims.filter(s => (s.world || '') === worldFilter);
  if (speciesFilter === 'human') sims = sims.filter(s => !s.species);
  else if (speciesFilter !== 'all') sims = sims.filter(s => (s.species || '') === speciesFilter);
  if (playedOnly) sims = sims.filter(s => s.is_played);
  if (portraitOnly) sims = sims.filter(s => s._hasPortrait);
  if (basegameOnly) sims = sims.filter(s => s._isBasegame);
  if (townieOnly) sims = sims.filter(s => s._isTownie);
  if (dupeOnly) sims = sims.filter(s => s._isDuplicate);
  if (ccOnly) sims = sims.filter(s => s._ccCount > 0);
  if (libraryOnly) sims = sims.filter(s => s._inLibrary);

  const ageOrder = {'Baby':0,'Kleinkind':1,'Kind':2,'Teen':3,'Junger Erwachsener':4,'Erwachsener':5,'Älterer':6};
  if (sortBy === 'name') sims.sort((a, b) => a.full_name.localeCompare(b.full_name));
  else if (sortBy === 'name-desc') sims.sort((a, b) => b.full_name.localeCompare(a.full_name));
  else if (sortBy === 'household') sims.sort((a, b) => a.household.localeCompare(b.household) || a.full_name.localeCompare(b.full_name));
  else if (sortBy === 'age') sims.sort((a, b) => (ageOrder[a.age]||9) - (ageOrder[b.age]||9) || a.full_name.localeCompare(b.full_name));
  else if (sortBy === 'skills') sims.sort((a, b) => (b.skill_count||0) - (a.skill_count||0) || a.full_name.localeCompare(b.full_name));
  else if (sortBy === 'mood') sims.sort((a, b) => (b.mood_value||0) - (a.mood_value||0) || a.full_name.localeCompare(b.full_name));
  else if (sortBy === 'sim-age') sims.sort((a, b) => (b.sim_age_days||0) - (a.sim_age_days||0) || a.full_name.localeCompare(b.full_name));
  else if (sortBy === 'simoleons') sims.sort((a, b) => (b.simoleons||0) - (a.simoleons||0) || a.full_name.localeCompare(b.full_name));
  else if (sortBy === 'career') sims.sort((a, b) => (b.career_level||0) - (a.career_level||0) || (a.career_name||'').localeCompare(b.career_name||'') || a.full_name.localeCompare(b.full_name));
  else if (sortBy === 'world') sims.sort((a, b) => (a.world||'').localeCompare(b.world||'') || a.household.localeCompare(b.household) || a.full_name.localeCompare(b.full_name));

  let html = '';
  if (sims.length === 0) {
    html = '<div class="muted" style="text-align:center;padding:40px;font-size:15px;">Keine Sims gefunden.</div>';
  } else if (groupHH) {
    const groups = {};
    for (const sim of sims) { if (!groups[sim.household]) groups[sim.household] = []; groups[sim.household].push(sim); }
    const sortedGroups = Object.keys(groups).sort();
    html += `<div class="muted small" style="margin-bottom:10px;">${sims.length} Sims in ${sortedGroups.length} Haushalten</div>`;
    for (const grp of sortedGroups) {
      const members = groups[grp];
      // Familien-Zusammenfassung
      const roles = {};
      let pairs = [];
      for (const m of members) {
        const r = m.family_role || 'Unbekannt';
        roles[r] = (roles[r] || 0) + 1;
        if (m.partner && !pairs.includes(m.partner + ' & ' + m.full_name)) {
          pairs.push(m.full_name + ' & ' + m.partner);
        }
      }
      let hhMeta = '';
      const roleTags = [];
      if (roles['Elternteil']) roleTags.push('👨‍👧 ' + roles['Elternteil'] + ' Eltern');
      if (roles['Kind']) roleTags.push('🧒 ' + roles['Kind'] + ' Kinder');
      if (roles['Partner']) roleTags.push('💑 ' + (roles['Partner']/2|0) + ' Paar(e)');
      if (roles['Geschwister']) roleTags.push('👫 ' + roles['Geschwister'] + ' Geschwister');
      if (roles['Mitbewohner']) roleTags.push('🏠 ' + roles['Mitbewohner'] + ' Mitbewohner');
      if (roleTags.length) hhMeta = `<div style="font-size:11px;color:#94a3b8;margin-top:4px;display:flex;gap:10px;flex-wrap:wrap;">${roleTags.join(' <span style=\\"color:#334155\\">·</span> ')}</div>`;
      if (pairs.length) hhMeta += `<div style="font-size:10px;color:#f472b6;margin-top:2px;">💕 ${pairs.map(p => esc(p)).join(', ')}</div>`;

      html += `<details class="grp" open style="margin-bottom:12px;">`;
      html += `<summary style="cursor:pointer;padding:10px 16px;background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(99,102,241,0.05));border:1px solid #6366f133;border-radius:12px;font-weight:600;font-size:14px;color:#c7d2fe;">`;
      html += `👨‍👩‍👧 ${esc(grp)} <span style="font-weight:400;color:#94a3b8;">(${members.length})</span>${hhMeta}</summary>`;
      html += `<div class="sim-grid" style="padding:12px 0;">`;
      for (const sim of members) html += _simCard(sim, false);
      html += `</div></details>`;
    }
  } else {
    html += `<div class="muted small" style="margin-bottom:10px;">${sims.length} Sims</div>`;
    html += `<div class="sim-grid">`;
    for (const sim of sims) html += _simCard(sim, true);
    html += `</div>`;
  }

  listEl.innerHTML = html;
}

// ═══════════════════════════════════════════════════
// ═══ BIBLIOTHEK (TRAY-HAUSHALTE) ═══
// ═══════════════════════════════════════════════════
let _libraryData = null;
let _libraryPolling = false;

async function startLibraryAnalysis(force) {
  if (_libraryPolling) return;
  const statusEl = document.getElementById('library-status');
  const summaryEl = document.getElementById('library-summary');
  const filtersEl = document.getElementById('library-filters');
  const listEl = document.getElementById('library-list');
  const btnAnalyze = document.getElementById('btn-library-analyze');
  const btnRefresh = document.getElementById('btn-library-refresh');

  statusEl.innerHTML = _miniLoaderHTML('lib-loader', 'Bibliothek wird geladen', 5);
  _startMiniTipRotation('lib-loader');
  summaryEl.style.display = 'none';
  filtersEl.style.display = 'none';
  listEl.style.display = 'none';
  btnAnalyze.disabled = true;
  btnAnalyze.textContent = '⏳ Lade…';
  _libraryPolling = true;

  let url = `/api/library?token=${TOKEN}`;
  if (force) url += '&force=1';
  try {
    const r = await fetch(url);
    const d = await r.json();
    if (d.status === 'ready') {
      _libraryPolling = false;
      _libraryData = d.data;
      renderLibraryResults();
      btnAnalyze.disabled = false;
      btnAnalyze.textContent = '🔍 Laden';
      btnRefresh.style.display = '';
      return;
    }
    pollLibrary();
  } catch(e) {
    statusEl.innerHTML = '<span style="color:#f87171;">❌ Fehler: ' + esc(e.message) + '</span>';
    btnAnalyze.disabled = false;
    btnAnalyze.textContent = '🔍 Laden';
    _libraryPolling = false;
    _stopMiniTipRotation('lib-loader');
    if (!_libraryReady) { _libraryReady = true; _checkAllReady(); }
  }
}

async function pollLibrary() {
  const statusEl = document.getElementById('library-status');
  const btnAnalyze = document.getElementById('btn-library-analyze');
  const btnRefresh = document.getElementById('btn-library-refresh');
  let progress = 10;

  const iv = setInterval(async () => {
    try {
      const r = await fetch(`/api/library?token=${TOKEN}`);
      const d = await r.json();
      if (d.status === 'ready') {
        clearInterval(iv);
        _libraryPolling = false;
        _libraryData = d.data;
        renderLibraryResults();
        btnAnalyze.disabled = false;
        btnAnalyze.textContent = '🔍 Laden';
        btnRefresh.style.display = '';
      } else {
        var p = (d.progress && d.progress.pct) ? d.progress.pct : Math.min(progress + 8, 90);
        var msg = (d.progress && d.progress.msg) ? d.progress.msg : 'Bibliothek wird analysiert…';
        progress = p;
        _setMiniBar('lib-loader', p);
        var txtEl = document.getElementById('lib-loader-text');
        if (txtEl) { txtEl.textContent = msg; }
        else { statusEl.innerHTML = _miniLoaderHTML('lib-loader', msg, p); _startMiniTipRotation('lib-loader'); }
      }
    } catch(e) {
      clearInterval(iv);
      _libraryPolling = false;
      statusEl.innerHTML = '<span style="color:#f87171;">❌ Verbindungsfehler</span>';
      btnAnalyze.disabled = false;
      btnAnalyze.textContent = '🔍 Laden';
      _stopMiniTipRotation('lib-loader');
      if (!_libraryReady) { _libraryReady = true; _checkAllReady(); }
    }
  }, 1200);
}

function renderLibraryResults() {
  const statusEl = document.getElementById('library-status');
  const summaryEl = document.getElementById('library-summary');
  const filtersEl = document.getElementById('library-filters');
  const listEl = document.getElementById('library-list');
  const d = _libraryData;
  window._libPortraitData = d.portrait_data || {};

  // Bibliothek als geladen markieren (auch bei Fehler)
  if (!_libraryReady) { _libraryReady = true; _checkAllReady(); }
  _stopMiniTipRotation('lib-loader');

  if (d.error) {
    statusEl.innerHTML = '<span style="color:#f87171;">❌ ' + esc(d.error) + '</span>';
    return;
  }

  statusEl.innerHTML = '<span style="color:#4ade80;">✅ Bibliothek geladen!</span>';

  summaryEl.style.display = 'block';
  const ccAvailable = !!d.cc_data_available;
  const ccHint = ccAvailable
    ? `<div class="tray-stat"><div class="tray-stat-num" style="color:#fbbf24;">${d.total_cc_households}</div><div class="tray-stat-label">🧩 Mit CC</div></div>`
    : '';
  const ccNote = !ccAvailable
    ? '<div class="muted small" style="margin-top:6px;">💡 CC-Info benötigt eine abgeschlossene <b>Tray &amp; CC</b>-Analyse. Danach <b>🔄 Neu</b> klicken.</div>'
    : '';
  summaryEl.innerHTML = `<div class="tray-summary-grid">
    <div class="tray-stat"><div class="tray-stat-num">${d.total_households}</div><div class="tray-stat-label">👨‍👩‍👧 Haushalte</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${d.total_sims}</div><div class="tray-stat-label">🧑 Sims gesamt</div></div>
    <div class="tray-stat"><div class="tray-stat-num" style="color:#4ade80;">${d.active_sims}</div><div class="tray-stat-label">✅ Im Spiel</div></div>
    <div class="tray-stat"><div class="tray-stat-num" style="color:#c4b5fd;">${d.library_only}</div><div class="tray-stat-label">📚 Nur Bibliothek</div></div>
    ${ccHint}
    ${(d.duplicate_sims && d.duplicate_sims.length > 0) ? `<div class="tray-stat"><div class="tray-stat-num" style="color:#f87171;">${d.duplicate_sims.length}</div><div class="tray-stat-label">⚠️ Duplikate</div></div>` : ''}
    ${(d.safe_to_delete_count > 0) ? `<div class="tray-stat"><div class="tray-stat-num" style="color:#fb923c;">${d.safe_to_delete_count}</div><div class="tray-stat-label">🗑️ Löschbar</div></div>` : ''}
  </div>${ccNote}
  ${(d.duplicate_sims && d.duplicate_sims.length > 0) ? `<div style="margin-top:10px;padding:12px 16px;background:#ef444420;border:1px solid #ef444440;border-radius:10px;">
    <div style="font-weight:700;color:#f87171;font-size:13px;cursor:pointer;display:flex;align-items:center;justify-content:space-between;" onclick="const el=document.getElementById('lib-dupe-list');el.classList.toggle('open');this.querySelector('.dupe-arrow').textContent=el.classList.contains('open')?'▼':'▶';">
      <span>⚠️ ${d.duplicate_sims.length} Sim(s) mehrfach in Bibliothek</span>
      <span class="dupe-arrow" style="font-size:11px;color:#94a3b8;">▶</span>
    </div>
    <div class="lib-cc-list" id="lib-dupe-list" style="margin-top:8px;">
      ${d.duplicate_sims.map(ds => {
        const dsPortrait = (window._libPortraitData || {})[ds.name] || '';
        const hhTags = ds.households.map(h => '<span style=\"display:inline-block;background:#1e293b;color:#c4b5fd;border:1px solid #8b5cf633;border-radius:6px;padding:2px 8px;font-size:11px;margin:2px;\">👨‍👩‍👧 ' + esc(h) + '</span>').join('');
        const statusIcon = ds.in_savegame ? '<span style=\"color:#4ade80;\">✅ Im Spiel aktiv</span>' : '<span style=\"color:#c4b5fd;\">📚 Nur in Bibliothek</span>';
        const imgTag = dsPortrait ? '<img src=\"' + dsPortrait + '\" style=\"width:48px;height:48px;border-radius:8px;object-fit:cover;border:2px solid #ef444466;flex-shrink:0;\">' : '<div style=\"width:48px;height:48px;border-radius:8px;background:#1e1b4b;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;border:2px solid #ef444466;\">🧑</div>';
        return '<div style=\"display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-bottom:1px solid #ffffff0a;\">' +
          imgTag +
          '<div style=\"flex:1;min-width:0;\">' +
            '<div style=\"display:flex;align-items:center;gap:8px;flex-wrap:wrap;\">' +
              '<span style=\"font-weight:700;color:#f1f5f9;font-size:13px;\">' + esc(ds.name) + '</span>' +
              '<span style=\"background:#ef444433;color:#fca5a5;border:1px solid #ef444455;border-radius:8px;padding:1px 8px;font-size:11px;font-weight:600;\">' + ds.count + 'x</span>' +
              statusIcon +
            '</div>' +
            '<div style=\"margin-top:6px;display:flex;flex-wrap:wrap;gap:2px;\">' + hhTags + '</div>' +
          '</div>' +
        '</div>';
      }).join('')}
    </div>
  </div>` : ''}`;

  // Duplikat-Lookup für Karten-Badges
  window._libDupeMap = {};
  if (d.duplicate_sims) {
    for (const ds of d.duplicate_sims) {
      window._libDupeMap[ds.name] = ds;
    }
  }

  filtersEl.style.display = 'flex';
  listEl.style.display = 'block';
  filterLibrary();
}

function _libSimMini(sim) {
  const embeddedSrc = (window._libPortraitData || {})[sim.full_name] || (window._portraitData || {})[sim.full_name];
  const cls = sim.in_savegame ? 'in-game' : 'lib-only';
  const dot = sim.in_savegame
    ? '<span class="lib-sim-dot active" title="Im Spielstand aktiv"></span>'
    : '<span class="lib-sim-dot inactive" title="Nur in Bibliothek"></span>';
  const imgHtml = embeddedSrc
    ? `<img src="${embeddedSrc}" alt="${esc(sim.full_name)}">`
    : `<div class="lib-sim-avatar">🧑</div>`;
  return `<div class="lib-sim-mini ${cls}">
    ${imgHtml}${dot}<span>${esc(sim.full_name)}</span>
  </div>`;
}

function _libSimCard(sim, hh) {
  const embeddedSrc = (window._libPortraitData || {})[sim.full_name] || (window._portraitData || {})[sim.full_name];
  const inGame = sim.in_savegame;
  const genderCls = inGame ? 'unknown' : 'lib-only-card';

  const portraitHtml = embeddedSrc
    ? `<div class="sim-portrait-frame"><img src="${embeddedSrc}" data-simname="${esc(sim.full_name)}"></div>`
    : `<div class="sim-portrait-frame"><div class="sim-emoji-holder ${genderCls}">🧑</div></div>`;

  // Badges
  let badges = '';
  if (inGame) {
    badges += `<span class="sim-badge" style="background:#22c55e22;color:#86efac;border:1px solid #22c55e44;">✅ Im Spiel</span>`;
  } else {
    badges += `<span class="sim-badge" style="background:#8b5cf622;color:#c4b5fd;border:1px solid #8b5cf644;">📚 Nur Bibliothek</span>`;
  }
  if (hh.creator) {
    badges += `<span class="sim-badge sim-badge-creator">🎨 ${esc(hh.creator)}</span>`;
  }
  // Duplikat-Badge
  const dupeInfo = (window._libDupeMap || {})[sim.full_name];
  if (dupeInfo) {
    badges += `<span class="sim-badge" style="background:#ef444422;color:#fca5a5;border:1px solid #ef444444;">⚠️ ${dupeInfo.count}x</span>`;
  }
  // Einzigartig-Badge (Sim nur in diesem HH)
  if (sim.is_unique) {
    badges += `<span class="sim-badge" style="background:#f8717122;color:#fca5a5;border:1px solid #f8717144;">🔒 Einzigartig</span>`;
  }

  // CC-Badge
  let ccHtml = '';
  const ccCount = hh.cc_count || 0;
  const ccMods = hh.used_mods || [];
  if (ccCount > 0) {
    const simId = 'lib_' + (sim.full_name || '').replace(/[^a-zA-Z0-9]/g, '') + '_' + Math.random().toString(36).slice(2,8);
    const ccModsList = ccMods.map(m =>
      `<div class="lib-cc-item"><span class="lib-cc-item-name">${esc(m.name)}</span><span class="lib-cc-item-count">${m.matches}x</span></div>`
    ).join('');
    ccHtml = `<div style="padding:0 10px 6px;">
      <span class="lib-cc-badge" onclick="document.getElementById('${simId}').classList.toggle('open');event.stopPropagation();" title="${ccCount} CC-Mods im Haushalt">🧩 ${ccCount} CC</span>
      <div class="lib-cc-list" id="${simId}" style="margin-top:6px;">${ccModsList}</div>
    </div>`;
  }

  return `<div class="sim-card ${inGame ? 'unknown' : 'lib-only-card'}" data-has-portrait="1">
    <div class="sim-card-topbar">
      <span class="sim-name" title="${esc(sim.full_name)}">${esc(sim.full_name)}</span>
    </div>
    ${portraitHtml}
    <div class="sim-card-info">
      <div class="sim-subtitle">👨‍👩‍👧 ${esc(hh.display_name || hh.name)}</div>
    </div>
    <div class="sim-card-body"><div class="sim-badges">${badges}</div></div>
    ${ccHtml}
  </div>`;
}

function filterLibrary() {
  if (!_libraryData) return;
  const search = (document.getElementById('library-search').value || '').toLowerCase();
  const sortBy = document.getElementById('library-sort').value;
  const statusFilter = document.getElementById('library-status-filter').value;
  const ccFilter = document.getElementById('library-cc-filter').value;
  const creatorOnly = document.getElementById('library-creator-filter').checked;
  const dupeOnly = document.getElementById('library-dupe-filter').checked;
  const safeOnly = document.getElementById('library-safe-filter').checked;
  const listEl = document.getElementById('library-list');

  let households = [...(_libraryData.households || [])];

  // Filter
  if (search) {
    households = households.filter(hh =>
      (hh.display_name || hh.name).toLowerCase().includes(search) ||
      (hh.creator && hh.creator.toLowerCase().includes(search)) ||
      hh.sims.some(s => s.full_name.toLowerCase().includes(search)) ||
      (hh.used_mods || []).some(m => m.name.toLowerCase().includes(search))
    );
  }
  if (statusFilter === 'active') {
    households = households.filter(hh => hh.sims.some(s => s.in_savegame));
  } else if (statusFilter === 'libonly') {
    households = households.filter(hh => hh.sims.every(s => !s.in_savegame));
  } else if (statusFilter === 'mixed') {
    households = households.filter(hh => hh.sims.some(s => s.in_savegame) && hh.sims.some(s => !s.in_savegame));
  }
  if (ccFilter === 'with-cc') {
    households = households.filter(hh => (hh.cc_count || 0) > 0);
  } else if (ccFilter === 'no-cc') {
    households = households.filter(hh => (hh.cc_count || 0) === 0);
  }
  if (creatorOnly) {
    households = households.filter(hh => hh.creator);
  }
  if (dupeOnly) {
    const dupeNames = new Set(Object.keys(window._libDupeMap || {}));
    households = households.filter(hh => hh.sims.some(s => dupeNames.has(s.full_name)));
  }
  if (safeOnly) {
    households = households.filter(hh => hh.safe_to_delete);
  }

  // Sort
  if (sortBy === 'name') households.sort((a, b) => (a.display_name || a.name).localeCompare(b.display_name || b.name));
  else if (sortBy === 'name-desc') households.sort((a, b) => (b.display_name || b.name).localeCompare(a.display_name || a.name));
  else if (sortBy === 'size-desc') households.sort((a, b) => b.sim_count - a.sim_count || (a.display_name || a.name).localeCompare(b.display_name || b.name));
  else if (sortBy === 'size-asc') households.sort((a, b) => a.sim_count - b.sim_count || (a.display_name || a.name).localeCompare(b.display_name || b.name));
  else if (sortBy === 'cc-desc') households.sort((a, b) => (b.cc_count || 0) - (a.cc_count || 0) || (a.display_name || a.name).localeCompare(b.display_name || b.name));

  let html = '';
  const totalSims = households.reduce((s, h) => s + h.sim_count, 0);
  if (households.length === 0) {
    html = '<div class="muted" style="text-align:center;padding:40px;font-size:15px;">Keine Haushalte gefunden.</div>';
  } else {
    html += `<div class="muted small" style="margin-bottom:10px;">${households.length} Haushalte · ${totalSims} Sims</div>`;
    // Alle Sims als flache Liste sammeln für Karten-Ansicht
    const groupHH = document.getElementById('library-group-hh') && document.getElementById('library-group-hh').checked;
    if (groupHH) {
      // Gruppiert nach Haushalt
      for (const hh of households) {
        html += `<details class="grp" open style="margin-bottom:12px;">`;
        html += `<summary style="cursor:pointer;padding:10px 16px;background:linear-gradient(135deg,rgba(139,92,246,0.15),rgba(139,92,246,0.05));border:1px solid #8b5cf633;border-radius:12px;font-weight:600;font-size:14px;color:#c4b5fd;">`;
        const ccTag = (hh.cc_count||0) > 0 ? ` <span style="font-size:11px;color:#fbbf24;">🧩 ${hh.cc_count} CC</span>` : '';
        const creatorTag = hh.creator ? ` <span style="font-size:11px;color:#94a3b8;">🎨 ${esc(hh.creator)}</span>` : '';
        const safeTag = hh.safe_to_delete ? ` <span style="font-size:11px;color:#fb923c;">🗑️ löschbar</span>` : '';
        const uniqueTag = (hh.unique_sims && hh.unique_sims.length > 0) ? ` <span style="font-size:11px;color:#f87171;">🔒 ${hh.unique_sims.length} einzigartig</span>` : '';
        html += `👨‍👩‍👧 ${esc(hh.display_name || hh.name)} <span style="font-weight:400;color:#94a3b8;">(${hh.sim_count})</span>${ccTag}${creatorTag}${safeTag}${uniqueTag}</summary>`;
        html += `<div class="sim-grid" style="padding:12px 0;">`;
        for (const sim of hh.sims) html += _libSimCard(sim, hh);
        html += `</div></details>`;
      }
    } else {
      // Flat: alle Sims als Karten
      html += `<div class="sim-grid">`;
      for (const hh of households) {
        for (const sim of hh.sims) html += _libSimCard(sim, hh);
      }
      html += `</div>`;
    }
  }

  listEl.innerHTML = html;
}

// Auto-Start: Savegame + Bibliothek im Hintergrund analysieren (nach allen Definitionen)
document.addEventListener('DOMContentLoaded', () => {
  startSavegameAnalysis();
  startLibraryAnalysis();
});

</script>

<div id="tutorial-overlay">
  <div id="tutorial-backdrop" onclick="closeTutorial()"></div>
  <div id="tutorial-spotlight"></div>
  <div id="tutorial-tooltip">
    <div class="tut-header">
      <span class="tut-icon" id="tut-step-icon"></span>
      <div class="tut-title" id="tut-step-title"></div>
    </div>
    <div class="tut-body" id="tut-step-body"></div>
    <div class="tut-progress">
      <div class="tut-progress-bar"><div class="tut-progress-fill" id="tut-progress-fill"></div></div>
      <span class="tut-progress-text" id="tut-progress-text"></span>
    </div>
    <div class="tut-footer">
      <button class="tut-btn tut-btn-skip" id="tut-btn-skip" onclick="closeTutorial()">Überspringen</button>
      <div style="display:flex;gap:8px;">
        <button class="tut-btn" id="tut-btn-prev" onclick="tutorialPrev()">← Zurück</button>
        <button class="tut-btn tut-btn-primary" id="tut-btn-next" onclick="tutorialNext()">Weiter →</button>
      </div>
    </div>
    <div class="tut-check">
      <input type="checkbox" id="tut-dont-show">
      <label for="tut-dont-show">Beim nächsten Start nicht mehr anzeigen</label>
    </div>
  </div>
</div>

<!-- ═══ MMO CHARACTER SHEET OVERLAY ═══ -->
<div class="cs-overlay" id="cs-overlay" onclick="if(event.target===this)closeCharSheet()">
  <div class="cs-sheet" id="cs-sheet"></div>
</div>

<script>
window.addEventListener('scroll', () => {
  document.getElementById('back-to-top').classList.toggle('visible', window.scrollY > 400);
});

function openCharSheet(regId) {
  const sim = window._simRegistry[regId];
  if (!sim) return;
  const esc = s => { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; };

  // Portrait
  const simFullName = sim.full_name || '';
  const portraitSrc = (window._portraitData || {})[simFullName] || (window._libPortraitData || {})[simFullName];
  const isMale = sim.gender === 'Männlich';
  const genderCls = isMale ? 'male' : sim.gender === 'Weiblich' ? 'female' : 'unknown';
  const avatarEmoji = sim.species_emoji || (sim.age === 'Baby' ? '👶' : sim.age === 'Kleinkind' ? '🧒' : sim.age === 'Kind' ? '🧒' : isMale ? '👨' : sim.gender === 'Weiblich' ? '👩' : '🧑');
  const portraitHtml = portraitSrc
    ? `<img src="${portraitSrc}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"><div class="cs-emoji" style="display:none;">${avatarEmoji}</div>`
    : `<div class="cs-emoji">${avatarEmoji}</div>`;

  // Tags
  let tags = '';
  if (sim.species) tags += `<span class="cs-tag cs-tag-species">${sim.species_emoji||'✨'} ${esc(sim.species)}</span>`;
  tags += `<span class="cs-tag cs-tag-age">${sim.age_emoji||''} ${esc(sim.age)}</span>`;
  tags += `<span class="cs-tag cs-tag-gender ${isMale?'male':''}">${sim.gender_emoji||''} ${esc(sim.gender)}</span>`;
  if (sim.career_name) tags += `<span class="cs-tag cs-tag-career">💼 ${esc(sim.career_name)}${sim.career_level ? ' Lv.'+sim.career_level : ''}</span>`;
  else if (sim.career_level > 0) tags += `<span class="cs-tag cs-tag-career">💼 Karriere Lv.${sim.career_level}</span>`;
  const moodColors = {'Sehr glücklich':'#22c55e','Glücklich':'#4ade80','Neutral':'#60a5fa','Traurig':'#f59e0b','Sehr traurig':'#ef4444'};
  if (sim.mood_label && sim.mood_label !== 'Unbekannt') {
    const mc = moodColors[sim.mood_label] || '#60a5fa';
    tags += `<span class="cs-tag cs-tag-mood" style="background:${mc}22;color:${mc};border:1px solid ${mc}44;">${sim.mood_emoji||''} ${esc(sim.mood_label)}</span>`;
  }

  // Gold (Simoleons)
  let goldHtml = '';
  if (sim.simoleons > 0) goldHtml = `<div class="cs-gold"><span class="cs-gold-icon">§</span><span class="cs-gold-val">${sim.simoleons.toLocaleString('de-DE')}</span></div>`;

  // ── LEFT COLUMN ──
  let leftCol = '';

  // Skills
  if (sim.top_skills && sim.top_skills.length > 0) {
    leftCol += `<div class="cs-section-title"><span class="cs-st-icon">⚔️</span> Fähigkeiten</div>`;
    for (const sk of sim.top_skills) {
      const maxLvl = sk.max_level || 10;
      const pct = Math.round((sk.level / maxLvl) * 100);
      leftCol += `<div class="cs-skill"><span class="cs-skill-name">${esc(sk.name)}</span><div class="cs-skill-bar"><div class="cs-skill-fill" style="width:${pct}%"></div></div><span class="cs-skill-lvl">${sk.level}/${maxLvl}</span></div>`;
    }
  }

  // Traits
  if (sim.trait_details) {
    const td = sim.trait_details;
    leftCol += `<div class="cs-section-title" style="margin-top:12px;"><span class="cs-st-icon">🧬</span> Eigenschaften</div><div class="cs-traits">`;
    if (td.personality_names) td.personality_names.forEach(n => { leftCol += `<span class="cs-trait cs-trait-person">🧠 ${esc(n)}</span>`; });
    if (td.bonus_names) td.bonus_names.forEach(n => { leftCol += `<span class="cs-trait cs-trait-bonus">⭐ ${esc(n)}</span>`; });
    if (td.aspiration_names) td.aspiration_names.forEach(n => { leftCol += `<span class="cs-trait cs-trait-aspir">🌟 ${esc(n)}</span>`; });
    if (td.likes_names) td.likes_names.forEach(n => { leftCol += `<span class="cs-trait cs-trait-like">❤️ ${esc(n)}</span>`; });
    if (td.lifestyle_names) td.lifestyle_names.forEach(n => { leftCol += `<span class="cs-trait cs-trait-life">🏃 ${esc(n)}</span>`; });
    // Fallback if no _names arrays, show counts
    if (!td.personality_names && !td.bonus_names && !td.aspiration_names && !td.likes_names && !td.lifestyle_names) {
      if (td.personality) leftCol += `<span class="cs-trait cs-trait-person">🧠 ${td.personality} Persönlichkeit</span>`;
      if (td.bonus) leftCol += `<span class="cs-trait cs-trait-bonus">⭐ ${td.bonus} Bonus</span>`;
      if (td.aspiration) leftCol += `<span class="cs-trait cs-trait-aspir">🌟 ${td.aspiration} Aspiration</span>`;
      if (td.likes) leftCol += `<span class="cs-trait cs-trait-like">❤️ ${td.likes} Likes</span>`;
      if (td.lifestyle) leftCol += `<span class="cs-trait cs-trait-life">🏃 ${td.lifestyle} Lifestyle</span>`;
    }
    leftCol += `</div>`;
  }

  // Likes & Dislikes
  const _prefCatOrder = ['Farbe','Deko','Musik','Aktivitäten','Mode','Eigenschaft','Kommunikation'];
  const _prefCatEmoji = {Farbe:'🎨',Deko:'🏠',Musik:'🎵','Aktivitäten':'🎯',Mode:'👗',Eigenschaft:'💭',Kommunikation:'💬'};
  const hasLikes = sim.likes && Object.keys(sim.likes).length > 0;
  const hasDislikes = sim.dislikes && Object.keys(sim.dislikes).length > 0;
  if (hasLikes || hasDislikes) {
    leftCol += `<div class="cs-section-title" style="margin-top:12px;"><span class="cs-st-icon">❤️</span> Vorlieben & Abneigungen</div>`;
    if (hasLikes) {
      for (const cat of _prefCatOrder) {
        const items = sim.likes[cat];
        if (!items) continue;
        const em = _prefCatEmoji[cat] || '';
        leftCol += `<div class="cs-pref-row"><span class="cs-pref-cat">${em} ${esc(cat)}</span>`;
        items.forEach(it => { leftCol += `<span class="cs-trait cs-trait-like">${esc(it)}</span>`; });
        leftCol += `</div>`;
      }
    }
    if (hasDislikes) {
      leftCol += `<div style="margin:4px 0 2px;font-size:10px;color:#64748b;font-weight:600;">💔 Mag nicht</div>`;
      for (const cat of _prefCatOrder) {
        const items = sim.dislikes[cat];
        if (!items) continue;
        const em = _prefCatEmoji[cat] || '';
        leftCol += `<div class="cs-pref-row"><span class="cs-pref-cat">${em} ${esc(cat)}</span>`;
        items.forEach(it => { leftCol += `<span class="cs-trait cs-trait-dislike">${esc(it)}</span>`; });
        leftCol += `</div>`;
      }
    }
  }

  // Relationships / Family
  if (sim.family_members && sim.family_members.length > 0) {
    leftCol += `<div class="cs-section-title" style="margin-top:12px;"><span class="cs-st-icon">👪</span> Familie</div>`;
    for (const m of sim.family_members) {
      const mE = m.gender === 'Männlich' ? '♂️' : m.gender === 'Weiblich' ? '♀️' : '';
      leftCol += `<div class="cs-family-member">${mE} ${esc(m.name)} <span class="cs-fm-role">${esc(m.role)}</span></div>`;
    }
  }

  // Relationship Details
  if (sim.relationships_detail && sim.relationships_detail.length > 0) {
    leftCol += `<div class="cs-section-title" style="margin-top:12px;"><span class="cs-st-icon">🤝</span> Beziehungen (${sim.relationships_detail.length})</div>`;
    leftCol += `<div class="cs-rel-scroll">`;
    for (const r of sim.relationships_detail) {
      let tags = '';
      if (r.family) tags += `<span class="cs-rel-tag cs-rel-fam">👪 ${esc(r.family)}</span>`;
      if (r.romance) tags += `<span class="cs-rel-tag cs-rel-rom">💕 ${esc(r.romance)}</span>`;
      if (r.friendship && r.friendship !== 'Bekannt') tags += `<span class="cs-rel-tag cs-rel-fri">🤝 ${esc(r.friendship)}</span>`;
      if (r.compat) tags += `<span class="cs-rel-tag cs-rel-comp">${r.compat === 'Toll' ? '⭐' : r.compat === 'Schlecht' ? '⚡' : '👍'} ${esc(r.compat)}</span>`;
      if (!tags && r.friendship === 'Bekannt') tags = `<span class="cs-rel-tag" style="opacity:0.5;">👋 Bekannt</span>`;
      leftCol += `<div class="cs-rel-row"><span class="cs-rel-name">${esc(r.name)}</span><span class="cs-rel-tags">${tags}</span></div>`;
    }
    leftCol += `</div>`;
  }

  // ── RIGHT COLUMN ──
  let rightCol = '';

  // Needs
  if (sim.needs && sim.needs.length > 0) {
    rightCol += `<div class="cs-section-title"><span class="cs-st-icon">❤️</span> Vitalwerte</div>`;
    for (const n of sim.needs) {
      const pct = Math.max(0, Math.min(100, n.percent));
      let cls = 'high';
      if (pct < 20) cls = 'crit';
      else if (pct < 40) cls = 'low';
      else if (pct < 70) cls = 'med';
      rightCol += `<div class="cs-need"><span class="cs-need-icon">${n.emoji}</span><span class="cs-need-name">${esc(n.name)}</span><div class="cs-need-bar"><div class="cs-need-fill ${cls}" style="width:${pct}%"></div></div><span class="cs-need-pct">${pct}%</span></div>`;
    }
  }

  // Info rows
  rightCol += `<div class="cs-section-title" style="margin-top:12px;"><span class="cs-st-icon">📋</span> Steckbrief</div>`;
  if (sim.household) rightCol += `<div class="cs-info-row"><span class="cs-info-icon">👨‍👩‍👧</span><span class="cs-info-label">Haushalt</span><span class="cs-info-val">${esc(sim.household)}</span></div>`;
  if (sim.world) rightCol += `<div class="cs-info-row"><span class="cs-info-icon">🏘️</span><span class="cs-info-label">Welt</span><span class="cs-info-val">${esc(sim.world)}</span></div>`;
  if (sim.lot_name) rightCol += `<div class="cs-info-row"><span class="cs-info-icon">🏠</span><span class="cs-info-label">Grundstück</span><span class="cs-info-val">${esc(sim.lot_name)}</span></div>`;
  if (sim.partner) rightCol += `<div class="cs-info-row"><span class="cs-info-icon">💕</span><span class="cs-info-label">Partner</span><span class="cs-info-val">${esc(sim.partner)}</span></div>`;
  if (sim.sim_age_days > 0) rightCol += `<div class="cs-info-row"><span class="cs-info-icon">📅</span><span class="cs-info-label">Alter</span><span class="cs-info-val">${sim.sim_age_days} Sim-Tage</span></div>`;
  if (sim.family_role && sim.family_role !== 'Einzelgänger') rightCol += `<div class="cs-info-row"><span class="cs-info-icon">👤</span><span class="cs-info-label">Rolle</span><span class="cs-info-val">${esc(sim.family_role)}</span></div>`;
  if (sim.is_played) rightCol += `<div class="cs-info-row"><span class="cs-info-icon">🎮</span><span class="cs-info-label">Status</span><span class="cs-info-val" style="color:#a78bfa;">Aktiv gespielt</span></div>`;
  if (sim.gallery_username) rightCol += `<div class="cs-info-row"><span class="cs-info-icon">🌐</span><span class="cs-info-label">Gallery</span><span class="cs-info-val">${esc(sim.gallery_username)}</span></div>`;
  if (sim.skin_tone) rightCol += `<div class="cs-info-row"><span class="cs-info-icon">🎨</span><span class="cs-info-label">Hautton</span><span class="cs-info-val">${esc(sim.skin_tone)}</span></div>`;

  // Equipment / Outfit
  if (sim.outfit_summary && sim.outfit_summary.length > 0) {
    rightCol += `<div class="cs-section-title" style="margin-top:12px;"><span class="cs-st-icon">👗</span> Ausrüstung — ${sim.outfit_total_parts||0} Teile</div>`;
    rightCol += `<div class="cs-equip-grid">`;
    const equipIcons = {'Hut':'🎩','Haare':'💇','Oberteil':'👕','Unterteil':'👖','Schuhe':'👟','Handschuhe':'🧤','Ganzkörper':'👗','Ohrring':'💎','Brille':'👓','Halskette':'📿','Ring':'💍','Armband':'⌚','Tattoo':'🖊️','Strümpfe':'🧦','Socken':'🧦','Makeup':'💄','Lippenstift':'💋','Lidschatten':'👁️','Eyeliner':'✏️','Nagellack':'💅','Augenbrauen':'🤨','Wimpern':'👁️','Gesichtsbehaarung':'🧔','Skindetail':'🎭','Hautfarbe':'🎨','Sommersprossen':'✨','Kopfschmuck':'👑','Mantel':'🧥'};
    for (const o of sim.outfit_summary) {
      if (o.body_types && o.body_types.length > 0) {
        for (const bt of o.body_types) {
          const icon = equipIcons[bt] || '📦';
          rightCol += `<div class="cs-equip-slot"><div class="cs-equip-icon">${icon}</div><div class="cs-equip-info"><div class="cs-equip-label">${esc(o.category)}</div><div class="cs-equip-val">${esc(bt)}</div></div></div>`;
        }
      } else {
        rightCol += `<div class="cs-equip-slot"><div class="cs-equip-icon">👗</div><div class="cs-equip-info"><div class="cs-equip-label">${esc(o.category)}</div><div class="cs-equip-val">${o.part_count} Teile</div></div></div>`;
      }
    }
    rightCol += `</div>`;
  }

  // CC Mods — Equipment grid with thumbnails
  if (sim.outfit_cc_mods && sim.outfit_cc_mods.length > 0) {
    const modsWithThumb = sim.outfit_cc_mods.filter(m => m.thumb);
    const modsNoThumb = sim.outfit_cc_mods.filter(m => !m.thumb);
    rightCol += `<div class="cs-section-title" style="margin-top:12px;"><span class="cs-st-icon">🧩</span> CC-Equipment (${sim.outfit_cc_mods.length})</div>`;
    if (modsWithThumb.length > 0) {
      rightCol += `<div class="cs-equip-grid" style="max-height:320px;overflow-y:auto;">`;
      for (const m of modsWithThumb) {
        const shortName = m.name.replace(/\\.package$/i, '').replace(/_/g, ' ');
        const displayName = shortName.length > 28 ? shortName.slice(0, 26) + '…' : shortName;
        rightCol += `<div class="cs-equip-slot" title="${esc(m.name)}"><div class="cs-equip-icon" style="width:48px;height:48px;border-radius:8px;overflow:hidden;border:1px solid #312e81;"><img src="${m.thumb}" style="width:100%;height:100%;object-fit:cover;" onerror="this.parentElement.innerHTML='🧩';"></div><div class="cs-equip-info"><div class="cs-equip-label">${m.matches}x</div><div class="cs-equip-val">${esc(displayName)}</div></div></div>`;
      }
      rightCol += `</div>`;
    }
    if (modsNoThumb.length > 0) {
      rightCol += `<div class="cs-cc-list" style="margin-top:6px;max-height:200px;overflow-y:auto;">`;
      for (const m of modsNoThumb) {
        rightCol += `<div class="cs-cc-item"><span class="cs-cc-name">${esc(m.name)}</span><span class="cs-cc-count">${m.matches}x</span></div>`;
      }
      rightCol += `</div>`;
    }
  }
  if (sim._ccCount > 0) {
    rightCol += `<div class="cs-section-title" style="margin-top:12px;"><span class="cs-st-icon">📦</span> CC-Mods im Haushalt (${sim._ccCount})</div><div class="cs-cc-list" style="max-height:260px;overflow-y:auto;">`;
    for (const m of (sim._ccMods || [])) {
      rightCol += `<div class="cs-cc-item"><span class="cs-cc-name">${esc(m.name)}</span><span class="cs-cc-count">${m.matches}x</span></div>`;
    }
    rightCol += `</div>`;
  }

  // Build the sheet
  document.getElementById('cs-sheet').innerHTML = `
    <button class="cs-close" onclick="closeCharSheet()" title="Schließen">✕</button>
    <div class="cs-header">
      <div class="cs-portrait">${portraitHtml}</div>
      <div class="cs-header-info">
        <div class="cs-name">${esc(sim.full_name)}</div>
        <div class="cs-subtitle">${tags}</div>
      </div>
      ${goldHtml}
    </div>
    <div class="cs-body">
      <div class="cs-col">${leftCol || '<div style="color:#334155;font-size:11px;">Keine Daten verfügbar</div>'}</div>
      <div class="cs-col">${rightCol || '<div style="color:#334155;font-size:11px;">Keine Daten verfügbar</div>'}</div>
    </div>
    <div class="cs-footer">⚔️ Sims 4 Character Sheet — ${esc(sim.full_name)}</div>
  `;

  const overlay = document.getElementById('cs-overlay');
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeCharSheet() {
  document.getElementById('cs-overlay').classList.remove('open');
  document.body.style.overflow = '';
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeCharSheet(); });
</script>
</body>
</html>
"""

