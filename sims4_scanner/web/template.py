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
  #batchbar { position:sticky; top:56px; z-index:5; }
  #section-nav { position:sticky; top:0; z-index:10; background:#0f172a; border-bottom:2px solid #334155; padding:0 16px; display:flex; gap:0; flex-wrap:nowrap; align-items:stretch; margin:0 -20px; padding-left:20px; padding-right:20px; overflow-x:auto; scrollbar-width:thin; }
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

  /* ---- Tutorial Overlay ---- */
  #tutorial-overlay { display:none; position:fixed; inset:0; z-index:10000; background:rgba(0,0,0,0.75); backdrop-filter:blur(4px); justify-content:center; align-items:center; }
  #tutorial-overlay.active { display:flex; }
  #tutorial-card { background:linear-gradient(145deg,#0f172a,#1e1b4b); border:1px solid #4f46e5; border-radius:20px; padding:36px 40px 28px; max-width:600px; width:92vw; box-shadow:0 20px 60px rgba(0,0,0,0.6); position:relative; animation:tutorialIn 0.35s ease-out; }
  @keyframes tutorialIn { from { opacity:0; transform:translateY(30px) scale(0.95); } to { opacity:1; transform:translateY(0) scale(1); } }
  #tutorial-card .tut-header { text-align:center; margin-bottom:20px; }
  #tutorial-card .tut-icon { font-size:48px; margin-bottom:8px; display:block; }
  #tutorial-card .tut-title { font-size:22px; font-weight:bold; color:#e2e8f0; margin-bottom:4px; }
  #tutorial-card .tut-body { color:#cbd5e1; font-size:14px; line-height:1.7; min-height:100px; }
  #tutorial-card .tut-body b { color:#a5b4fc; }
  #tutorial-card .tut-body ul { margin:8px 0 0 18px; padding:0; }
  #tutorial-card .tut-body li { margin-bottom:4px; }
  .tut-footer { display:flex; justify-content:space-between; align-items:center; margin-top:24px; gap:12px; flex-wrap:wrap; }
  .tut-dots { display:flex; gap:6px; justify-content:center; flex:1; }
  .tut-dot { width:10px; height:10px; border-radius:50%; background:#334155; transition:all 0.2s; cursor:pointer; }
  .tut-dot.active { background:#6366f1; transform:scale(1.3); }
  .tut-dot.done { background:#4f46e5; }
  .tut-btn { border:1px solid #4f46e5; background:#1e1b4b; color:#c7d2fe; padding:8px 20px; border-radius:10px; cursor:pointer; font-size:13px; transition:all 0.15s; white-space:nowrap; }
  .tut-btn:hover { background:#312e81; color:#e0e7ff; }
  .tut-btn-primary { background:#6366f1; color:#fff; border-color:#6366f1; font-weight:bold; }
  .tut-btn-primary:hover { background:#818cf8; }
  .tut-btn-skip { background:transparent; border-color:#334155; color:#64748b; font-size:12px; }
  .tut-btn-skip:hover { color:#94a3b8; border-color:#475569; }
  .tut-check { display:flex; align-items:center; gap:8px; margin-top:16px; justify-content:center; }
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
  .sim-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:14px; }
  .tray-most-used-table { width:100%; border-collapse:collapse; margin-top:10px; }
  .tray-most-used-table th { text-align:left; font-size:11px; color:#64748b; padding:6px 10px; border-bottom:1px solid #334155; }
  .tray-most-used-table td { font-size:12px; color:#cbd5e1; padding:8px 10px; border-bottom:1px solid #1e293b; }
  .tray-most-used-table tr:hover { background:#1e293b; }
  .tray-used-count { background:#6366f133; color:#a5b4fc; padding:2px 8px; border-radius:6px; font-size:11px; font-weight:600; }
  .tray-progress { background:#1e293b; border-radius:8px; height:8px; margin:10px 0; overflow:hidden; }
  .tray-progress-bar { height:100%; background:linear-gradient(90deg,#6366f1,#a78bfa); border-radius:8px; transition:width 0.3s; }
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
</style>
</head>
<body>
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
  <button class="nav-tab" onclick="switchTab('duplicates')" id="nav-groups">📂 Duplikate <span class="nav-badge badge-zero" id="nav-badge-groups">0</span><span class="nav-sub">Gruppen · Korrupte · Addons · Enthaltene · Konflikte</span></button>
  <button class="nav-tab" onclick="switchTab('analysis')" id="nav-analysis">🔍 Analyse <span class="nav-badge badge-zero" id="nav-badge-analysis">0</span><span class="nav-sub">Veraltet · Abhängigkeiten · Fehler</span></button>
  <button class="nav-tab" onclick="switchTab('traycc')" id="nav-tray">🎭 Tray &amp; CC<span class="nav-sub">Sims · Häuser · CC-Galerie · Savegames</span></button>
  <button class="nav-tab" onclick="switchTab('overview')" id="nav-overview">📊 Übersicht<span class="nav-sub">Statistik · Creators · Alle Mods</span></button>
  <button class="nav-tab" onclick="switchTab('tools')" id="nav-tools">🛠 Werkzeuge<span class="nav-sub">Import · Quarantäne · Log</span></button>
  <button class="nav-tab" onclick="switchTab('history')" id="nav-history">📚 Verlauf<span class="nav-sub">Mod-Inventar · Änderungen</span></button>
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
<div class="dashboard" id="dashboard" data-tab="dashboard">
  <div class="dash-card dash-critical dash-hidden" id="dash-corrupt" onclick="switchTab('duplicates')">
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
  <div class="dash-card dash-warn dash-hidden" id="dash-conflicts" onclick="switchTab('duplicates')">
    <div class="dash-icon">⚔️</div>
    <div class="dash-count" id="dash-conflicts-count">0</div>
    <div class="dash-label">Konflikte</div>
    <div class="dash-desc">Mods die sich gegenseitig überschreiben — nur einer kann funktionieren.</div>
    <span class="dash-action">Prüfen →</span>
  </div>
  <div class="dash-card dash-info dash-hidden" id="dash-outdated" onclick="switchTab('analysis')">
    <div class="dash-icon">⏰</div>
    <div class="dash-count" id="dash-outdated-count">0</div>
    <div class="dash-label">Veraltete Mods</div>
    <div class="dash-desc">Vor dem letzten Spiel-Patch erstellt — könnten nicht mehr funktionieren.</div>
    <span class="dash-action">Prüfen →</span>
  </div>
  <div class="dash-card dash-ok dash-hidden" id="dash-addons" onclick="switchTab('duplicates')">
    <div class="dash-icon">🧩</div>
    <div class="dash-count" id="dash-addons-count">0</div>
    <div class="dash-label">Addons erkannt</div>
    <div class="dash-desc">Erweiterungen die zusammengehören — <b>kein Handlungsbedarf!</b></div>
    <span class="dash-action">Details →</span>
  </div>
  <div class="dash-card dash-warn dash-hidden" id="dash-contained" onclick="switchTab('duplicates')">
    <div class="dash-icon">📦</div>
    <div class="dash-count" id="dash-contained-count">0</div>
    <div class="dash-label">Enthaltene Mods</div>
    <div class="dash-desc">Ein Mod steckt komplett in einem Bundle — der Einzelne ist <b>redundant</b> und kann entfernt werden.</div>
    <span class="dash-action">Prüfen →</span>
  </div>
  <div class="dash-card dash-critical dash-hidden" id="dash-missingdeps" onclick="switchTab('analysis')">
    <div class="dash-icon">❌</div>
    <div class="dash-count" id="dash-missingdeps-count">0</div>
    <div class="dash-label">Fehlende Abhängigkeiten</div>
    <div class="dash-desc">Mods importieren Bibliotheken die nicht installiert sind — werden nicht funktionieren!</div>
    <span class="dash-action">Prüfen →</span>
  </div>
  <div class="dash-card dash-info dash-hidden" id="dash-nonmod" onclick="switchTab('overview')">
    <div class="dash-icon">📄</div>
    <div class="dash-count" id="dash-nonmod-count">0</div>
    <div class="dash-label">Sonstige Dateien</div>
    <div class="dash-desc">Nicht-Mod-Dateien (txt, png, html…) im Mods-Ordner — können aufgeräumt werden.</div>
    <span class="dash-action">Anzeigen →</span>
  </div>
  <div class="dash-card dash-ok" id="dash-total" onclick="switchTab('overview')">
    <div class="dash-icon">📦</div>
    <div class="dash-count" id="dash-total-count">…</div>
    <div class="dash-label">Mods gescannt</div>
    <div class="dash-desc">Deine gesamte Mod-Sammlung wurde analysiert.</div>
    <span class="dash-action">Statistik →</span>
  </div>
</div>

<div class="box" id="help-section" data-tab="dashboard" style="margin-bottom:12px;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:15px;font-weight:bold;">📖 Erste Schritte — So funktioniert der Scanner</span>
    <button class="help-toggle" id="help-toggle" onclick="document.getElementById('help-panel').classList.toggle('open'); this.textContent = document.getElementById('help-panel').classList.contains('open') ? '▲ Hilfe zuklappen' : '▼ Hilfe aufklappen';">▲ Hilfe zuklappen</button>
  </div>
  <div class="help-panel open" id="help-panel">
    <div style="margin-bottom:16px;">
      <p class="muted" style="margin:0 0 10px;"><b>Keine Sorge, es ist einfacher als es aussieht!</b> Hier die wichtigsten Schritte:</p>
      <div class="help-step">
        <span class="help-num">1</span>
        <div class="help-text">Oben siehst du die <b>Tab-Leiste</b>. Das <b>Dashboard</b> zeigt dir auf einen Blick, was der Scanner gefunden hat. Klicke auf eine Karte oder auf den Tab <b>📂 Duplikate</b> um zu den Ergebnissen zu gelangen.</div>
      </div>
      <div class="help-step">
        <span class="help-num">2</span>
        <div class="help-text">Im Tab <b>📂 Duplikate</b> siehst du alle Duplikat-Gruppen, Korrupte Dateien, Addons, Enthaltene Mods und Konflikte. Setze ein <b>Häkchen ☑️</b> bei den Dateien, die du <b>nicht mehr brauchst</b> (z.B. die ältere Version).</div>
      </div>
      <div class="help-step">
        <span class="help-num">3</span>
        <div class="help-text">Im Tab <b>🛠 Werkzeuge</b> findest du die <b>📦 Quarantäne</b> — dort werden markierte Dateien sicher verschoben. <b>Nichts wird gelöscht!</b> Du kannst sie jederzeit wiederherstellen.</div>
      </div>
      <div class="help-step">
        <span class="help-num">4</span>
        <div class="help-text">Der Tab <b>🔍 Analyse</b> zeigt dir veraltete Mods, fehlende Abhängigkeiten und Fehler-Logs. <b>⏰ Veraltet</b> = vor dem letzten Patch erstellt.</div>
      </div>
      <div class="help-step">
        <span class="help-num">5</span>
        <div class="help-text">Starte dein Spiel und teste ob alles funktioniert. Falls nicht, gehe zu <b>🛠 Werkzeuge → Quarantäne</b> und stelle Dateien wieder her.</div>
      </div>
    </div>

    <div class="hr"></div>
    <p style="font-weight:bold;font-size:13px;margin:12px 0 8px;color:#e2e8f0;">🧭 Die Tabs im Überblick</p>
    <div class="legend-grid">
      <span class="legend-icon" style="min-width:100px;">🏠 Dashboard</span>
      <span class="muted">Übersicht aller Ergebnisse — <b>dein Startpunkt</b>. Zeigt auf einen Blick was los ist.</span>
      <span class="legend-icon" style="min-width:100px;">📂 Duplikate</span>
      <span class="muted">Duplikat-Gruppen, <b>Korrupte Dateien, Addons, Enthaltene Mods, Konflikte</b> — alles was mit doppelten Dateien zu tun hat.</span>
      <span class="legend-icon" style="min-width:100px;">🔍 Analyse</span>
      <span class="muted"><b>Veraltete Mods, Abhängigkeiten, Fehler-Logs</b> — tiefe Analyse deiner Mod-Gesundheit.</span>
      <span class="legend-icon" style="min-width:100px;">🎭 Tray & CC</span>
      <span class="muted"><b>Sims, Häuser, CC-Galerie</b> — welche Mods deine gespeicherten Sims/Häuser brauchen.</span>
      <span class="legend-icon" style="min-width:100px;">📊 Übersicht</span>
      <span class="muted"><b>Statistiken, Creators, Alle Mods</b> — deine komplette Mod-Sammlung durchsuchen.</span>
      <span class="legend-icon" style="min-width:100px;">🛠 Werkzeuge</span>
      <span class="muted"><b>Import, Quarantäne, Batch-Aktionen, Log</b> — Werkzeuge zum Aufräumen.</span>
      <span class="legend-icon" style="min-width:100px;">📚 Verlauf</span>
      <span class="muted"><b>Mod-Inventar, Änderungen</b> — was sich seit dem letzten Scan geändert hat.</span>
    </div>

    <div class="hr"></div>
    <p style="font-weight:bold;font-size:13px;margin:12px 0 8px;color:#e2e8f0;">🎨 Konflikte — Farbcode auf einen Blick</p>
    <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:12px;">
      <div style="display:flex;align-items:center;gap:12px;padding:8px 12px;border-radius:8px;background:rgba(239,68,68,0.15);border-left:4px solid #ef4444;">
        <span style="background:#ef4444;color:#000;padding:2px 10px;border-radius:6px;font-size:11px;font-weight:bold;white-space:nowrap;">⚠️ Kritisch</span>
        <span style="color:#fca5a5;font-size:12px;">3+ Tuning-Konflikte — <b>kann Gameplay brechen</b>, aufräumen!</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px;padding:8px 12px;border-radius:8px;background:rgba(251,191,36,0.12);border-left:4px solid #fbbf24;">
        <span style="background:#fbbf24;color:#000;padding:2px 10px;border-radius:6px;font-size:11px;font-weight:bold;white-space:nowrap;">⚡ Mittel</span>
        <span style="color:#fde68a;font-size:12px;">CAS/Sim-Data betroffen — <b>könnte Darstellungsfehler</b> verursachen</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px;padding:8px 12px;border-radius:8px;background:rgba(34,197,94,0.12);border-left:4px solid #22c55e;">
        <span style="background:#22c55e;color:#000;padding:2px 10px;border-radius:6px;font-size:11px;font-weight:bold;white-space:nowrap;">✅ Niedrig</span>
        <span style="color:#86efac;font-size:12px;">Nur Texturen/Meshes — <b>meistens gewollt</b>, behalten</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px;padding:8px 12px;border-radius:8px;background:rgba(148,163,184,0.12);border-left:4px solid #94a3b8;">
        <span style="background:#94a3b8;color:#000;padding:2px 10px;border-radius:6px;font-size:11px;font-weight:bold;white-space:nowrap;">💤 Harmlos</span>
        <span style="color:#cbd5e1;font-size:12px;">1-2 geteilte Keys — <b>Mods teilen einzelne Assets</b>, kein Problem</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px;padding:8px 12px;border-radius:8px;background:rgba(96,165,250,0.12);border-left:4px solid #60a5fa;">
        <span style="background:#60a5fa;color:#000;padding:2px 10px;border-radius:6px;font-size:11px;font-weight:bold;white-space:nowrap;">✅ Gewollt</span>
        <span style="color:#93c5fd;font-size:12px;">Zusammengehörige Dateien — <b>gleicher Mod, behalten!</b></span>
      </div>
    </div>

    <div style="margin:8px 0 12px;padding:10px 14px;background:#0f172a;border:1px solid #334155;border-radius:8px;display:flex;align-items:flex-start;gap:10px;">
      <span style="font-size:16px;margin-top:1px;">💡</span>
      <div style="font-size:12px;color:#94a3b8;line-height:1.5;">
        <b style="color:#cbd5e1;">Hinweis zu den Hintergrundfarben:</b> Die wechselnden Hintergrundfarben
        (<span style="color:#4a7fff;">blau</span>,
        <span style="color:#a855f7;">lila</span>,
        <span style="color:#22c55e;">grün</span>,
        <span style="color:#f97316;">orange</span>,
        <span style="color:#ef4444;">rot</span>,
        <span style="color:#06b6d4;">cyan</span>)
        bei den Einträgen dienen <b style="color:#e2e8f0;">nur zur visuellen Unterscheidung</b> der einzelnen Gruppen — sie haben <b style="color:#e2e8f0;">nichts mit Fehlern oder Schweregrad</b> zu tun. Der Schweregrad wird ausschließlich über das <b style="color:#e2e8f0;">Badge</b> (Kritisch, Mittel, usw.) angezeigt.
      </div>
    </div>

    <div class="hr"></div>
    <p style="font-weight:bold;font-size:13px;margin:12px 0 8px;color:#e2e8f0;">🛡️ Sicherheits-Tipps</p>
    <div class="muted" style="font-size:12px;line-height:1.6;">
      ✅ Immer zuerst <b>Quarantäne</b> nutzen statt direkt zu löschen<br>
      ✅ Nach dem Aufräumen das Spiel <b>testen</b> bevor du Quarantäne-Dateien endgültig löschst<br>
      ✅ Im Zweifel: <b>lieber behalten!</b> — doppelte CAS-Teile (Haare, Kleidung) sind harmlos<br>
      ✅ <b>💤 Harmlose</b> und <b>✅ Gewollte</b> Konflikte kannst du bedenkenlos ignorieren<br>
      ⚠️ <b>Script-Mods</b> (.ts4script) sind nach Patches am problematischsten — bei Problemen zuerst die deaktivieren<br>
      ⚠️ <b>⚠️ Kritische Konflikte</b> bei Tuning-Mods können zu Abstürzen führen — da konsequent aufräumen
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

<div class="box notice" data-tab="tools">
  <b>🛡️ Sicherheitshinweis:</b> Nutze immer <b>📦 Quarantäne</b> statt Löschen! Quarantäne = Dateien werden nur verschoben, du kannst sie jederzeit zurückholen. <b>🗑 Löschen</b> ist endgültig und nicht rückgängig zu machen!
</div>

<div class="box" id="import-section" data-tab="tools" style="border:1px solid #2563eb;background:linear-gradient(135deg,#0f172a 60%,#1e1b4b);">
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

<div id="last" class="muted" data-tab="tools">Letzte Aktion: –</div>
<div id="watcher-banner" data-tab="tools" style="display:none;padding:8px 16px;margin:4px 0;border-radius:8px;background:linear-gradient(90deg,#1e3a5f,#1e293b);border:1px solid #334155;color:#94a3b8;font-size:0.95em;display:flex;align-items:center;gap:8px;" class="muted small">
  <span id="watcher-dot" style="width:8px;height:8px;border-radius:50%;background:#22c55e;display:inline-block;animation:watcherPulse 2s ease-in-out infinite;"></span>
  <span>👁️ Datei-Watcher aktiv — <span id="watcher-files">0</span> Dateien überwacht</span>
  <span id="watcher-event" style="margin-left:auto;opacity:0.7;"></span>
</div>
<style>
@keyframes watcherPulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
</style>

<div class="box" id="batchbar" data-tab="tools">
  <div class="flex" style="justify-content:space-between;">
    <div>
      <b>📋 Sammel-Aktionen</b>
      <span class="pill" id="selcount">0 ausgewählt</span><br>
      <span class="muted small">Hier kannst du alle Dateien, bei denen du ein <b>Häkchen ☑️</b> gesetzt hast, auf einmal verarbeiten.</span><br>
      <span class="muted small" style="opacity:0.6;">Log-Datei: <code id="logfile"></code></span>
    </div>
    <div class="flex">
      <button class="btn btn-ok" id="btn_q_sel" title="SICHER: Verschiebt alle markierten Dateien in einen Quarantäne-Ordner. Du kannst sie jederzeit wiederherstellen!">📦 In Quarantäne verschieben</button>
      <button class="btn btn-danger" id="btn_d_sel" title="ACHTUNG: Löscht alle markierten Dateien ENDGÜLTIG vom PC! Nicht rückgängig machbar!">🗑 Endgültig löschen</button>
      <button class="btn btn-ghost" id="btn_clear_sel" title="Entfernt alle Häkchen — keine Dateien werden verändert">✖ Auswahl leeren</button>
      <button class="btn btn-ghost" id="reload" title="Scannt alle Mod-Ordner komplett neu — kann bei vielen Mods ein paar Minuten dauern">↻ Neu scannen</button>
      <button class="btn btn-ghost" id="btn_save_html" title="Speichert eine Kopie dieser Seite als HTML-Datei auf dem Desktop — praktisch zum Teilen oder Archivieren">📄 Bericht speichern</button>
    </div>
  </div>
  <div class="hr"></div>
  <div id="batchstatus" class="muted small">Bereit.</div>
</div>

<div class="box" id="log-section" data-tab="tools">
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
  <div class="info-hint" style="margin-top:8px;">💡 <b>So funktioniert es:</b> Jede Gruppe zeigt Dateien die zusammengehören (z.B. Duplikate). Setze ein <b>Häkchen ☑️</b> bei der Datei, die du <b>nicht brauchst</b>, und nutze dann oben <b>📦 Quarantäne</b>. Die Buttons <b>"🗑 Rest in Quarantäne"</b> helfen dir: sie markieren automatisch alle außer der besten Datei.</div>
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

<div class="box" id="corrupt-section" data-tab="duplicates" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>⚠️ Korrupte / Verdächtige .package-Dateien</h2>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Diese .package-Dateien sind beschädigt oder haben ein ungültiges Format. Sie verursachen möglicherweise Fehler im Spiel. <b>Empfehlung:</b> Lösche sie oder lade sie neu vom Ersteller herunter.</div>
  <div id="corrupt-summary" class="muted"></div>
  <div id="corrupt-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="addon-section" data-tab="duplicates" style="display:none;">
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

<div class="box" id="contained-section" data-tab="duplicates" style="display:none;">
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

<div class="box" id="conflict-section" data-tab="duplicates" style="display:none;">
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

<div class="box" id="outdated-section" data-tab="analysis" style="display:none;">
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

<div class="box" id="deps-section" data-tab="analysis" style="display:none;">
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

<div class="box" id="error-section" data-tab="analysis">
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

<div class="box" id="stats-section" data-tab="overview">
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
<div class="box" id="gallery-section" data-tab="traycc" style="display:none;">
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
<div class="box" id="savegame-section" data-tab="traycc">
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
<div class="box" id="library-section" data-tab="traycc">
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
<div class="box" id="tray-section" data-tab="traycc">
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

<div class="box" id="creators-section" data-tab="overview">
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

<div class="box" id="allmods-section" data-tab="overview">
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

<div class="box" id="nonmod-section" data-tab="overview" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📄 Sonstige Dateien im Mods-Ordner</h2>
    <span class="muted" id="nonmod-summary">Warte auf Scan…</span>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Diese Dateien liegen in deinem Mods-Ordner, sind aber <b>keine Mods</b> (.package/.ts4script). Das Spiel ignoriert sie — sie stören nicht, nehmen aber Platz weg. Typisch: Readmes, Vorschau-Bilder, alte Archive.</div>
  <div id="nonmod-list" style="margin-top:8px;"></div>
</div>

<div class="box" id="quarantine-section" data-tab="tools" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📦 Quarantäne-Manager</h2>
    <button class="btn btn-ghost" id="btn_reload_quarantine">↻ Aktualisieren</button>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier siehst du alle Dateien, die du in Quarantäne verschoben hast. Du kannst sie einzeln <b>zurückholen</b> (zurück in den Mods-Ordner) oder <b>endgültig löschen</b>.</div>
  <div id="quarantine-summary" class="muted">Lade…</div>
  <div id="quarantine-list" style="margin-top:12px;"></div>
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
  'corrupt-section','addon-section','contained-section','conflict-section','outdated-section',
  'deps-section','nonmod-section','quarantine-section','gallery-section',
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
    <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben">📦 Quarantäne</button>
    <button class="btn btn-danger" data-act="delete" data-path="${esc(f.path)}" title="Unwiderruflich löschen!">🗑 Löschen</button>
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
        <button class="btn btn-ok" data-gact="quarantine_rest" data-gi="${gi}" title="Verschiebt alle bis auf die beste Datei sicher in Quarantäne">📦 Rest in Quarantäne</button>
        <button class="btn btn-danger" data-gact="delete_rest" data-gi="${gi}" title="Löscht alle bis auf die beste — kann nicht rückgängig gemacht werden!">🗑 Rest löschen</button>
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
  const ignoredGrp = countIgnoredGroups(data);
  const ignoredLabel = ignoredGrp ? ` <span style="color:#6ee7b7;">(${ignoredGrp} ignoriert)</span>` : '';
  return `
    Erstellt: <b>${esc(data.created_at)}</b><br>
    Gruppen: <b>${s.groups_name}</b> Name / <b>${s.groups_content}</b> Inhalt / <b>${s.groups_similar || 0}</b> Ähnlich${ignoredLabel}<br>
    Einträge: <b>${s.entries_total}</b><br>
    Verschwendeter Speicher (identische Duplikate): <b>${esc(s.wasted_h)}</b>
    ${corruptInfo}
    ${conflictInfo}
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
    showConditionalSection('corrupt-section', false);
    return;
  }
  showConditionalSection('corrupt-section', true);

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
    showConditionalSection('addon-section', false);
    return;
  }
  showConditionalSection('addon-section', true);

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
          <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben">📦 Quarantäne</button>
          <button class="btn btn-danger" data-act="delete" data-path="${esc(f.path)}" title="Unwiderruflich löschen!">🗑 Löschen</button>
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
    showConditionalSection('contained-section', false);
    return;
  }
  showConditionalSection('contained-section', true);

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
          <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben">📦 Quarantäne</button>
          <button class="btn btn-danger" data-act="delete" data-path="${esc(f.path)}" title="Unwiderruflich löschen!">🗑 Löschen</button>
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
    showConditionalSection('conflict-section', false);
    return;
  }
  showConditionalSection('conflict-section', true);

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
          <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben">📦 Quarantäne</button>
          <button class="btn btn-danger" data-act="delete" data-path="${esc(f.path)}" title="Unwiderruflich löschen!">🗑 Löschen</button>
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
  {icon:'🎮',title:'Willkommen beim Sims 4 Mod-Scanner!',body:'<b>Schön, dass du da bist!</b> Dieses Tool hilft dir, deine Mods-Sammlung sauber und organisiert zu halten.<br><br>In diesem kurzen Tutorial zeigen wir dir alle wichtigen Funktionen.<br><br><b>💡 Tipp:</b> Du kannst das Tutorial jederzeit über den <b>❓ Tutorial</b>-Button in der Tab-Leiste erneut starten.'},
  {icon:'🧭',title:'Die Tab-Navigation',body:'Oben findest du die <b>Tab-Leiste</b> mit allen Bereichen. Klicke auf einen Tab um den Bereich zu öffnen:<br><ul><li><b>🏠 Dashboard</b> — Übersicht aller Ergebnisse auf einen Blick</li><li><b>📂 Duplikate</b> — Duplikat-Gruppen, Korrupte, Addons, Konflikte</li><li><b>🔍 Analyse</b> — Veraltete Mods, Abhängigkeiten, Fehler-Logs</li><li><b>🎭 Tray & CC</b> — Sim/Haus-Analyse und CC-Galerie</li><li><b>📊 Übersicht</b> — Statistiken, Creators, Alle Mods</li><li><b>🛠 Werkzeuge</b> — Import, Quarantäne, Batch-Aktionen</li><li><b>📚 Verlauf</b> — Mod-Inventar und Änderungen</li></ul>Die <b>Badges</b> hinter den Tabs zeigen die Anzahl der Funde an.'},
  {icon:'🏠',title:'Das Dashboard',body:'Das <b>Dashboard</b> ist dein Startpunkt. Hier siehst du auf einen Blick:<br><ul><li>💀 <b>Korrupte Dateien</b> — Sofort entfernen!</li><li>📂 <b>Duplikate</b> — Doppelte Mod-Dateien</li><li>⚔️ <b>Konflikte</b> — Mods die sich überschreiben</li><li>📦 <b>Enthaltene Mods</b> — Mods in Bundles enthalten</li><li>⏰ <b>Veraltete Mods</b> — Vor letztem Patch erstellt</li><li>❌ <b>Fehlende Abhängigkeiten</b> — Mods ohne Voraussetzungen</li></ul>Klicke auf eine <b>Karte</b> um direkt zum passenden Tab zu springen!'},
  {icon:'📂',title:'Tab: Duplikate',body:'Im Tab <b>📂 Duplikate</b> findest du alles zu doppelten Dateien:<br><ul><li><b>📦 Inhalt-Duplikate</b> — 100% identische Kopien</li><li><b>📛 Name-Duplikate</b> — Gleicher Name, verschiedene Ordner</li><li><b>🔤 Ähnliche Namen</b> — Wahrscheinlich verschiedene Versionen</li></ul>Außerdem findest du hier:<br><ul><li><b>💀 Korrupte Dateien</b> — Beschädigte .package-Dateien</li><li><b>🧩 Addons</b> — Zusammengehörige Mods (kein Handlungsbedarf)</li><li><b>📦 Enthaltene Mods</b> — Ein Mod ist komplett in einem Bundle enthalten</li><li><b>⚔️ Konflikte</b> — Sich überschreibende Mods</li></ul>Setze <b>Häkchen ☑️</b> bei Dateien die du entfernen willst.'},
  {icon:'⚔️',title:'Konflikte & Schweregrade',body:'Konflikte werden nach <b>Schweregrad</b> farblich markiert:<br><br><span style="background:#ef4444;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;">⚠️ Kritisch</span> <span style="color:#ef4444;">3+ Tuning-Ressourcen</span> — Kann Gameplay-Fehler verursachen, aufräumen!<br><br><span style="background:#fbbf24;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;">⚡ Mittel</span> <span style="color:#fbbf24;">CAS/Sim-Data betroffen</span> — Könnte Darstellungsfehler verursachen<br><br><span style="background:#22c55e;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;">✅ Niedrig</span> <span style="color:#22c55e;">Nur Texturen/Meshes</span> — Meistens gewollt, behalten<br><br><span style="background:#94a3b8;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;">💤 Harmlos</span> <span style="color:#94a3b8;">1-2 geteilte Keys</span> — Mods teilen einzelne Assets, kein Problem<br><br><span style="background:#60a5fa;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;">✅ Gewollt</span> <span style="color:#60a5fa;">Zusammengehörige Dateien</span> — Gleicher Mod, behalten!'},
  {icon:'🔍',title:'Tab: Analyse',body:'Der Tab <b>🔍 Analyse</b> zeigt dir die Gesundheit deiner Mods:<br><ul><li><b>⏰ Veraltete Mods</b> — Vor dem letzten Spiel-Patch erstellt, könnten Probleme machen</li><li><b>🔗 Abhängigkeiten</b> — Welche Mods andere Mods brauchen</li><li><b>📋 Fehler-Analyse</b> — Ausgewertete Fehlerlogs (lastException.txt)</li></ul>Hier erkennst du auf einen Blick, welche Mods Probleme verursachen könnten!'},
  {icon:'🎭',title:'Tab: Tray & CC',body:'Der Tab <b>🎭 Tray & CC</b> analysiert deine gespeicherten Inhalte:<br><ul><li><b>Tray-Analyse</b> — Welche Mods deine Sims und Häuser brauchen</li><li><b>CC-Galerie</b> — Alle Custom Content Vorschaubilder in einer Galerie</li></ul>⚠️ Wenn du einen Mod löschen willst, der von einem gespeicherten Sim benutzt wird, wirst du <b>gewarnt</b>!'},
  {icon:'⚡',title:'Aktionen & Quarantäne',body:'Für jede Datei stehen dir Aktionen zur Verfügung:<br><ul><li><b>📦 Quarantäne</b> — Verschiebt die Datei sicher (rückgängig machbar!)</li><li><b>🗑️ Löschen</b> — Löscht die Datei endgültig</li><li><b>📂 Öffnen</b> — Zeigt den Ordner im Explorer</li></ul><b>🛡️ Tipp:</b> Nutze immer Quarantäne statt Löschen! Im Tab <b>🛠 Werkzeuge</b> findest du die Quarantäne-Verwaltung zum Wiederherstellen.'},
  {icon:'🛠',title:'Tab: Werkzeuge',body:'Im Tab <b>🛠 Werkzeuge</b> findest du praktische Helfer:<br><ul><li><b>📥 Import-Manager</b> — Neue Mods sicher importieren</li><li><b>📦 Quarantäne</b> — Verschobene Dateien verwalten/wiederherstellen</li><li><b>🎛️ Batch-Aktionen</b> — Alle markierten Dateien auf einmal verarbeiten</li><li><b>📋 Log</b> — Alle durchgeführten Aktionen nachverfolgen</li></ul>Über die <b>Checkboxen</b> bei jeder Datei und dann <b>Batch-Quarantäne</b> kannst du schnell aufräumen.'},
  {icon:'🔎',title:'Globale Suche',body:'Die <b>Globale Suche</b> unterhalb der Tab-Leiste durchsucht <b>ALLES</b> auf einmal:<br><ul><li>Dateinamen und Pfade</li><li>Notizen und Tags</li><li>Creator-Informationen</li><li>CurseForge-Daten</li></ul>Einfach eintippen — die Ergebnisse erscheinen sofort!'},
  {icon:'🏷️',title:'Notizen & Tags',body:'Du kannst zu jeder Mod <b>persönliche Notizen</b> und <b>Tags</b> hinzufügen:<br><br><b>📝 Notizen</b> — Freitext, z.B. "Funktioniert super mit XY Mod"<br><b>🏷️ Tags</b> — Kategorie-Labels wie "Favorit", "Testen", "Behalten"<br><br>Alles wird gespeichert und überlebt Rescans! Nutze Tags um deine Mods zu organisieren.'},
  {icon:'📚',title:'Tab: Verlauf & Übersicht',body:'<b>📚 Verlauf:</b><br><ul><li><b>📸 Mod-Snapshot</b> — Ein Foto deiner Mod-Sammlung bei jedem Scan</li><li><b>📋 Scan-Historie</b> — Alle Aktionen nachvollziehen</li></ul><b>📊 Übersicht:</b><br><ul><li><b>Statistiken</b> — Gesamtzahlen und Analyse</li><li><b>Creators</b> — Mod-Ersteller verwalten</li><li><b>Alle Mods</b> — Komplette Liste durchsuchen</li></ul>'},
  {icon:'🎉',title:'Fertig! Viel Spaß!',body:'Du kennst jetzt alle <b>wichtigen Funktionen</b>!<br><br><b>Noch ein paar Tipps:</b><ul><li>Der <b>🔄 Auto-Watcher</b> erkennt Änderungen automatisch</li><li>Erstelle <b>Creator-Verknüpfungen</b> unter 📊 Übersicht</li><li>Nutze den <b>📥 Import-Manager</b> unter 🛠 Werkzeuge</li><li>Schau regelmäßig im Tab <b>🔍 Analyse</b> nach Problemen</li></ul><b>🎮 Happy Simming!</b>'}
];

let tutorialStep = 0;

function renderTutorialStep() {
  const step = TUTORIAL_STEPS[tutorialStep];
  document.getElementById('tut-step-icon').textContent = step.icon;
  document.getElementById('tut-step-title').textContent = step.title;
  document.getElementById('tut-step-body').innerHTML = step.body;

  // Dots
  const dotsEl = document.getElementById('tut-dots');
  dotsEl.innerHTML = TUTORIAL_STEPS.map((_, i) =>
    `<div class="tut-dot ${i === tutorialStep ? 'active' : (i < tutorialStep ? 'done' : '')}" onclick="tutorialGoTo(${i})"></div>`
  ).join('');

  // Buttons
  document.getElementById('tut-btn-prev').style.display = tutorialStep === 0 ? 'none' : '';
  const isLast = tutorialStep === TUTORIAL_STEPS.length - 1;
  document.getElementById('tut-btn-next').textContent = isLast ? '✅ Fertig!' : 'Weiter →';
  document.getElementById('tut-btn-skip').style.display = isLast ? 'none' : '';
}

function startTutorial() {
  tutorialStep = 0;
  renderTutorialStep();
  document.getElementById('tutorial-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeTutorial() {
  document.getElementById('tutorial-overlay').classList.remove('active');
  document.body.style.overflow = '';
  if (document.getElementById('tut-dont-show').checked) {
    markTutorialSeen();
  }
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

// Tutorial-Keyboard Navigation
document.addEventListener('keydown', function(e) {
  const overlay = document.getElementById('tutorial-overlay');
  if (!overlay.classList.contains('active')) return;
  if (e.key === 'ArrowRight' || e.key === 'Enter') { e.preventDefault(); tutorialNext(); }
  if (e.key === 'ArrowLeft') { e.preventDefault(); tutorialPrev(); }
  if (e.key === 'Escape') { e.preventDefault(); closeTutorial(); }
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
  const hasProblems = groups > 0 || s.corrupt_count > 0 || s.conflict_count > 0 || (s.missing_dep_count||0) > 0;
  showConditionalSection('all-ok-banner', !hasProblems);
}

function renderDependencies(data) {
  const section = document.getElementById('deps-section');
  const deps = data.dependencies || [];
  if (deps.length === 0) {
    showConditionalSection('deps-section', false);
    return;
  }
  showConditionalSection('deps-section', true);

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
    showConditionalSection('gallery-section', false);
    return;
  }
  showConditionalSection('gallery-section', true);

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
  _galleryShown = 60;

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
  moreBtn.style.display = _galleryShown < _galleryFiltered.length ? '' : 'none';
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
    showConditionalSection('outdated-section', false);
    return;
  }
  showConditionalSection('outdated-section', true);
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
        <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben">📦 Quarantäne</button>
        <button class="btn btn-danger" data-act="delete" data-path="${esc(f.path)}" title="Unwiderruflich löschen!">🗑 Löschen</button>
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
    showConditionalSection('corrupt-section', !!(window.__DATA && window.__DATA.corrupt && window.__DATA.corrupt.length));
    showConditionalSection('addon-section', !!(window.__DATA && window.__DATA.addon_pairs && window.__DATA.addon_pairs.length));
    showConditionalSection('contained-section', !!(window.__DATA && window.__DATA.contained_in && window.__DATA.contained_in.length));
    showConditionalSection('conflict-section', !!(window.__DATA && window.__DATA.conflicts && window.__DATA.conflicts.length));
    title.textContent = 'Gruppen';
  } else {
    groupsView.style.display = 'none';
    perfileView.style.display = 'block';
    showConditionalSection('corrupt-section', false);
    showConditionalSection('addon-section', false);
    showConditionalSection('contained-section', false);
    showConditionalSection('conflict-section', false);
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
  renderOutdated(data);
  renderDependencies(data);
  updateNavBadges(data);
  checkAllOK(data);
  renderStats(data);
  loadQuarantine();
  renderAllMods(data);
  renderGallery(data);
  renderNonModFiles(data);
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
  // Tray-warning check
  if (_trayData && _trayData.mod_usage) {
    const np = path.toLowerCase().replace(/\\\\/g, '/');
    for (const [mp, info] of Object.entries(_trayData.mod_usage)) {
      const nmp = mp.toLowerCase().replace(/\\\\/g, '/');
      if (np === nmp || np.endsWith('/' + nmp.split('/').pop())) {
        const names = (info.used_by || []).slice(0, 5).join(', ');
        if (!confirm(`⚠️ ACHTUNG: Dieser Mod wird von ${info.used_count} gespeicherten Sims/Häusern verwendet!\\n\\nVerwendet von: ${names}\\n\\nTrotzdem in Quarantäne verschieben?`)) return;
        break;
      }
    }
  }
  const res = await postAction('quarantine', path, {});
  console.log('[QUARANTINE]', path, res);
  setLast('📦 Quarantäne: ' + path);
  addLog('QUARANTINE ' + (res.moved ? 'OK' : 'NOTE') + ' :: ' + path + (res.to ? (' -> ' + res.to) : ''));
  removeRowsForPath(path);
  await reloadData();
}

async function doDelete(path) {
  // Tray-warning check
  let trayMsg = '';
  if (_trayData && _trayData.mod_usage) {
    const np = path.toLowerCase().replace(/\\\\/g, '/');
    for (const [mp, info] of Object.entries(_trayData.mod_usage)) {
      const nmp = mp.toLowerCase().replace(/\\\\/g, '/');
      if (np === nmp || np.endsWith('/' + nmp.split('/').pop())) {
        const names = (info.used_by || []).slice(0, 5).join(', ');
        trayMsg = `\\n\\n⚠️ ACHTUNG: Dieser Mod wird von ${info.used_count} Sims/Häusern verwendet!\\nVerwendet von: ${names}`;
        break;
      }
    }
  }
  if (!confirm('Wirklich löschen?\\n\\n' + path + trayMsg)) return;
  const res = await postAction('delete', path, {});
  console.log('[DELETE]', path, res);
  setLast('🗑 Löschen: ' + path + ' (deleted=' + String(res.deleted) + ')');
  addLog('DELETE ' + (res.deleted ? 'OK' : 'NOTE') + ' :: ' + path + (res.note ? (' :: ' + res.note) : ''));
  removeRowsForPath(path);
  await reloadData();
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
  title.textContent = (action === 'quarantine' ? '📦 Quarantäne' : '🗑 Löschen') + '…';
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
        if (action === 'delete') {
          const res = await postAction('delete', p, {});
          console.log('[BATCH_DELETE]', p, res);
          addLog(`BATCH DELETE ${res.deleted ? 'OK' : 'NOTE'} :: ${p}` + (res.note ? (' :: ' + res.note) : ''));
        } else if (action === 'quarantine') {
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
  await batchAction('quarantine', Array.from(selected), `📦 ${selected.size} Dateien in Quarantäne verschieben?`);
});

document.getElementById('btn_d_sel').addEventListener('click', async () => {
  await batchAction('delete', Array.from(selected), `🗑 ${selected.size} Dateien WIRKLICH löschen?\n\nDas kann man nicht rückgängig machen!`);
});

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
      await batchAction('delete', rest, `🗑 Rest der Gruppe WIRKLICH löschen?\n\nBehalte:\n${keep}\n\nAnzahl: ${rest.length}`);
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
reloadData().then(()=>{
  setLast('✅ Daten geladen');
  addLog('PAGE LOAD');
  updateSelCount();
}).catch(e=>{
  document.getElementById('groups').innerHTML = '<p class="muted">Fehler: ' + esc(e.message) + '</p>';
  setLast('❌ Fehler beim Laden: ' + e.message);
  addLog('LOAD ERROR :: ' + e.message);
});

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
    const modsHtml = (err.betroffene_mods && err.betroffene_mods.length > 0)
      ? `<div class="err-mods"><span class="muted small">Betroffene Mod-Dateien:</span> ${err.betroffene_mods.map(m => `<span class="err-mod-tag">${esc(m)}</span>`).join('')}</div>`
      : '';

    const rawHtml = err.raw_snippet
      ? `<details class="err-raw"><summary>📄 Originaler Log-Auszug anzeigen</summary><pre>${esc(err.raw_snippet)}</pre></details>`
      : '';

    const statusBadge = err.status === 'neu'
      ? '<span class="err-status neu">🆕 NEU</span>'
      : err.status === 'bekannt'
        ? '<span class="err-status bekannt">🔄 BEKANNT</span>'
        : '';

    html += `
    <div class="err-card ${err.schwere}">
      <div class="flex" style="align-items:center; gap:8px; flex-wrap:wrap;">
        <span>${schwereIcon(err.schwere)}</span>
        <span class="err-title">${esc(err.titel)}</span>
        <span class="err-schwere ${err.schwere}">${schwereLabel(err.schwere)}</span>
        ${statusBadge}
      </div>
      <div class="err-explain">${esc(err.erklaerung)}</div>
      <div class="err-solution">💡 <b>Lösung:</b> ${esc(err.loesung)}</div>
      ${modsHtml}
      <div class="err-meta">
        <span>📁 ${esc(err.datei)}</span>
        <span>📅 ${esc(err.datum)}</span>
        <span>📂 ${esc(err.kategorie)}</span>
      </div>
      ${rawHtml}
    </div>`;
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

  statusEl.innerHTML = '<div class="tray-progress"><div class="tray-progress-bar" style="width:5%"></div></div><span>Starte Tray-Analyse… Mod-Index wird aufgebaut…</span>';
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
        progress = Math.min(progress + 3, 90);
        statusEl.innerHTML = '<div class="tray-progress"><div class="tray-progress-bar" style="width:' + progress + '%"></div></div><span>⏳ Analyse läuft… Tray-Dateien werden gescannt…</span>';
      } else if (d.status === 'error') {
        clearInterval(iv);
        _trayPolling = false;
        statusEl.innerHTML = '<span style="color:#f87171;">❌ Fehler: ' + esc(d.error || 'Unbekannt') + '</span>';
        btnAnalyze.disabled = false;
        btnAnalyze.textContent = '🔍 Analysieren';
      }
    } catch(e) {
      clearInterval(iv);
      _trayPolling = false;
      statusEl.innerHTML = '<span style="color:#f87171;">❌ Verbindungsfehler</span>';
      btnAnalyze.disabled = false;
      btnAnalyze.textContent = '🔍 Analysieren';
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

  // 1–7 → Tab wechseln
  const tabMap = {'1':'dashboard','2':'duplicates','3':'analysis','4':'traycc','5':'overview','6':'tools','7':'history'};
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

  statusEl.innerHTML = '<div class="tray-progress"><div class="tray-progress-bar" style="width:5%"></div></div><span>⏳ Spielstand wird gelesen…</span>';
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
        btnAnalyze.disabled = false;
        btnAnalyze.textContent = '🔍 Analysieren';
      } else if (d.status === 'analyzing' || d.status === 'started') {
        progress = Math.min(progress + 5, 90);
        statusEl.innerHTML = '<div class="tray-progress"><div class="tray-progress-bar" style="width:' + progress + '%"></div></div><span>⏳ Spielstand wird analysiert…</span>';
      }
    } catch(e) {
      clearInterval(iv);
      _savegamePolling = false;
      statusEl.innerHTML = '<span style="color:#f87171;">❌ Verbindungsfehler</span>';
      btnAnalyze.disabled = false;
      btnAnalyze.textContent = '🔍 Analysieren';
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

  summaryEl.style.display = 'block';
  summaryEl.innerHTML = `<div class="tray-summary-grid">
    <div class="tray-stat"><div class="tray-stat-num">${d.sim_count}</div><div class="tray-stat-label">🧑 Sims</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${d.household_count}</div><div class="tray-stat-label">👨‍👩‍👧 Haushalte</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${d.world_count}</div><div class="tray-stat-label">🌍 Welten</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${gs['Männlich']||0}</div><div class="tray-stat-label">♂️ Männlich</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${gs['Weiblich']||0}</div><div class="tray-stat-label">♀️ Weiblich</div></div>
    <div class="tray-stat"><div class="tray-stat-num">${d.partner_count||0}</div><div class="tray-stat-label">💑 Paare</div></div>
  </div>
  <div style="margin-top:8px;display:flex;gap:10px;flex-wrap:wrap;font-size:11px;color:#94a3b8;">
    <span>👶${as['Baby']||0}</span><span>🧒${as['Kleinkind']||0}</span><span>🧒${as['Kind']||0}</span>
    <span>🧑${as['Teen']||0}</span><span>🧑${as['Junger Erwachsener']||0}</span><span>🧑${as['Erwachsener']||0}</span><span>👴${as['Älterer']||0}</span>
    <span style="margin-left:6px;color:#64748b;">|</span>
    ${Object.entries(sp).map(([k,v]) => '<span style="color:#a78bfa;">'+esc(k)+': '+v+'</span>').join('')}
    <span style="margin-left:6px;color:#64748b;">|</span>
    <span>📦 ${d.active_save_size_mb} MB</span>
  </div>
  ${(d.duplicate_sims && d.duplicate_sims.length > 0) ? `<div style="margin-top:10px;padding:10px 14px;background:#ef444420;border:1px solid #ef444440;border-radius:8px;">
    <div style="font-weight:700;color:#f87171;font-size:13px;">⚠️ ${d.duplicate_sims.length} doppelte Sim(s) erkannt!</div>
    <div style="font-size:11px;color:#fca5a5;margin-top:4px;">${d.duplicate_sims.map(ds => ds.count + 'x ' + esc(ds.name) + ' (' + ds.households.map(h=>esc(h)).join(', ') + ')').join(' &middot; ')}</div>
    <div style="font-size:10px;color:#94a3b8;margin-top:4px;">Doppelte Sims können durch Bugs oder Mods entstehen und Spielprobleme verursachen.</div>
  </div>` : ''}`;

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

function _simCard(sim, showHousehold) {
  const isMale = sim.gender === 'Männlich';
  const isFemale = sim.gender === 'Weiblich';
  const genderCls = isMale ? 'male' : isFemale ? 'female' : 'unknown';
  const avatarEmoji = sim.age === 'Baby' ? '👶' : sim.age === 'Kleinkind' ? '🧒' : sim.age === 'Kind' ? '🧒' : sim.species === 'Vampir' ? '🧛' : sim.species === 'Zauberer' ? '🧙' : isMale ? '👨' : isFemale ? '👩' : '🧑';

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

  // Stats
  let statsHtml = '<div class="sim-card-stats">';
  statsHtml += `<div class="sim-stat"><div class="sim-stat-val">${sim.age_emoji}</div><div class="sim-stat-label">${esc(sim.age)}</div></div>`;
  if (sim.trait_count > 0) statsHtml += `<div class="sim-stat"><div class="sim-stat-val">🎭 ${sim.trait_count}</div><div class="sim-stat-label">Traits</div></div>`;
  if (sim.relationship_count > 0) statsHtml += `<div class="sim-stat"><div class="sim-stat-val">🤝 ${sim.relationship_count}</div><div class="sim-stat-label">Bezieh.</div></div>`;
  if (sim.species) statsHtml += `<div class="sim-stat"><div class="sim-stat-val">${sim.species === 'Vampir' ? '🧛' : '🧙'}</div><div class="sim-stat-label">${esc(sim.species)}</div></div>`;
  statsHtml += '</div>';

  // Badges
  let badges = '';
  if (showHousehold !== false) badges += `<span class="sim-badge sim-badge-hh">👨‍👩‍👧 ${esc(sim.household)}</span>`;
  if (sim.is_played) badges += `<span class="sim-badge" style="background:#a78bfa22;color:#c4b5fd;border:1px solid #a78bfa44;">🎮 Gespielt</span>`;
  if (sim._isBasegame) badges += `<span class="sim-badge sim-badge-basegame">🏠 Basegame</span>`;
  if (sim._isTownie) badges += `<span class="sim-badge sim-badge-townie">🤖 EA-Townie</span>`;
  if (sim._isDuplicate) badges += `<span class="sim-badge sim-badge-dupe">⚠️ Duplikat</span>`;
  if (sim._inLibrary) badges += `<span class="sim-badge" style="background:#22c55e22;color:#86efac;border:1px solid #22c55e44;">📚 In Bibliothek</span>`;
  if (sim.skin_tone) badges += `<span class="sim-badge sim-badge-skin">🎨 ${esc(sim.skin_tone)}</span>`;

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

  return `<div class="sim-card ${genderCls}" data-has-portrait="1">
    <div class="sim-card-topbar">
      <span class="sim-name" title="${esc(sim.full_name)}">${esc(sim.full_name)}</span>
      <div class="sim-badges-row">${roleHtml}${typeBadge}</div>
    </div>
    ${portraitHtml}
    <div class="sim-card-info">
      <div class="sim-subtitle"><span class="gender-dot ${genderCls}"></span> ${esc(sim.gender)} · ${esc(sim.age)}</div>
      ${sim.world ? `<div class="sim-world-tag">🏘️ ${esc(sim.world)}</div>` : ''}
    </div>
    ${statsHtml}
    ${partnerHtml}
    ${relBarHtml}
    ${moodHtml}
    ${ageInfoHtml}
    ${skillsHtml}
    ${needsHtml}
    <div class="sim-card-body"><div class="sim-badges">${badges}</div></div>
    ${ccHtml}
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
      (s.top_skills && s.top_skills.some(sk => sk.name.toLowerCase().includes(search))) ||
      (s._ccMods && s._ccMods.some(m => m.name.toLowerCase().includes(search)))
    );
  }
  if (ageFilter !== 'all') sims = sims.filter(s => s.age === ageFilter);
  if (genderFilter !== 'all') sims = sims.filter(s => s.gender === genderFilter);
  if (worldFilter !== 'all') sims = sims.filter(s => (s.world || '') === worldFilter);
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

  statusEl.innerHTML = '<div class="tray-progress"><div class="tray-progress-bar" style="width:5%"></div></div><span>⏳ Bibliothek wird geladen…</span>';
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
        progress = Math.min(progress + 8, 90);
        statusEl.innerHTML = '<div class="tray-progress"><div class="tray-progress-bar" style="width:' + progress + '%"></div></div><span>⏳ Bibliothek wird analysiert…</span>';
      }
    } catch(e) {
      clearInterval(iv);
      _libraryPolling = false;
      statusEl.innerHTML = '<span style="color:#f87171;">❌ Verbindungsfehler</span>';
      btnAnalyze.disabled = false;
      btnAnalyze.textContent = '🔍 Laden';
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
  <div id="tutorial-card">
    <div class="tut-header">
      <span class="tut-icon" id="tut-step-icon"></span>
      <div class="tut-title" id="tut-step-title"></div>
    </div>
    <div class="tut-body" id="tut-step-body"></div>
    <div class="tut-dots" id="tut-dots"></div>
    <div class="tut-footer">
      <button class="tut-btn tut-btn-skip" id="tut-btn-skip" onclick="closeTutorial()">Überspringen</button>
      <button class="tut-btn" id="tut-btn-prev" onclick="tutorialPrev()">← Zurück</button>
      <button class="tut-btn tut-btn-primary" id="tut-btn-next" onclick="tutorialNext()">Weiter →</button>
    </div>
    <div class="tut-check">
      <input type="checkbox" id="tut-dont-show" checked>
      <label for="tut-dont-show">Beim nächsten Start nicht mehr anzeigen</label>
    </div>
  </div>
</div>

<script>
window.addEventListener('scroll', () => {
  document.getElementById('back-to-top').classList.toggle('visible', window.scrollY > 400);
});
</script>
</body>
</html>
"""

