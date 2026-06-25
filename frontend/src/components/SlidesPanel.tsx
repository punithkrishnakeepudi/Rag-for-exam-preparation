import { ChevronLeft, ChevronRight, Download, Loader2, Presentation } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import * as api from '../api'
import type { Document, Slide, SlidesDeck } from '../api'
import ProgressBar from './ProgressBar'

interface Props { documents: Document[] }

// ── Layout Engine ──────────────────────────────────────────────────────────────

function GradientPlaceholder({ spinning }: { spinning?: boolean }) {
  return (
    <div className="w-full h-full rounded-xl bg-gradient-to-br from-indigo-900/60 to-purple-900/40 flex items-center justify-center">
      <div className={`w-16 h-16 rounded-full bg-indigo-500/20 border border-indigo-500/30 ${spinning ? 'animate-pulse' : ''}`} />
    </div>
  )
}

function SlideAsset({ path }: { path?: string }) {
  const [attempt, setAttempt] = useState(0)
  const [ok, setOk] = useState(false)

  // reset when path changes (new deck generated)
  useEffect(() => { setAttempt(0); setOk(false) }, [path])

  if (!path) return <GradientPlaceholder />

  return (
    <>
      {/* hidden img that retries every 3s until loaded */}
      <img
        key={attempt}
        src={`/assets/${path}?v=${attempt}`}
        alt=""
        className={`w-full h-full object-cover rounded-xl ${ok ? 'block' : 'hidden'}`}
        onLoad={() => setOk(true)}
        onError={() => {
          if (attempt < 20) setTimeout(() => setAttempt((a) => a + 1), 3000)
        }}
      />
      {!ok && <GradientPlaceholder spinning />}
    </>
  )
}

function SlideView({ slide, showNotes }: { slide: Slide; showNotes: boolean }) {
  const layout = slide.layout_type ?? 'Standard_Bullets'

  const TitleSlide = (
    <div className="flex flex-col items-center justify-center h-full text-center px-16 gap-6">
      <div className="w-12 h-1 bg-indigo-500 rounded-full" />
      <h1 className="text-4xl font-bold text-white leading-tight">{slide.title}</h1>
      {slide.bullets?.[0] && (
        <p className="text-xl text-indigo-300 max-w-lg">{slide.bullets[0]}</p>
      )}
      <div className="w-12 h-1 bg-indigo-500/40 rounded-full" />
    </div>
  )

  const StandardBullets = (
    <div className="flex flex-col justify-center h-full px-12 gap-8">
      <h2 className="text-2xl font-bold text-indigo-200 border-b border-indigo-900 pb-3">
        {slide.title}
      </h2>
      <ul className="space-y-4 flex-1">
        {slide.bullets?.map((b, i) => (
          <li key={i} className="flex items-start gap-3 text-gray-200 text-base">
            <span className="text-indigo-500 mt-1 shrink-0 text-sm">→</span>
            <span>{b}</span>
          </li>
        ))}
      </ul>
      {slide.asset_path && (
        <div className="absolute right-8 bottom-16 w-32 h-32 opacity-60">
          <SlideAsset path={slide.asset_path} />
        </div>
      )}
    </div>
  )

  const SplitMetrics = (
    <div className="grid grid-cols-2 gap-6 h-full p-10">
      <div className="flex flex-col justify-center gap-6">
        <h2 className="text-2xl font-bold text-indigo-200">{slide.title}</h2>
        <div className="space-y-3">
          {slide.bullets?.map((b, i) => (
            <div key={i} className="bg-indigo-900/40 border border-indigo-800/50 rounded-xl p-3">
              <span className="text-gray-200 text-sm">{b}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-center justify-center">
        <div className="w-full h-full max-h-56">
          <SlideAsset path={slide.asset_path} />
        </div>
      </div>
    </div>
  )

  const VisualHero = (
    <div className="relative h-full overflow-hidden rounded-none">
      {slide.asset_path ? (
        <div className="absolute inset-0">
          <SlideAsset path={slide.asset_path} />
        </div>
      ) : (
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-950 via-purple-950 to-slate-900" />
      )}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
      <div className="relative flex flex-col justify-end h-full p-12 gap-4">
        <h2 className="text-3xl font-bold text-white leading-snug">{slide.title}</h2>
        {slide.bullets?.slice(0, 2).map((b, i) => (
          <p key={i} className="text-indigo-200 text-lg">{b}</p>
        ))}
      </div>
    </div>
  )

  const content = {
    Title_Slide: TitleSlide,
    Standard_Bullets: StandardBullets,
    Split_Metrics: SplitMetrics,
    Visual_Hero: VisualHero,
  }[layout] ?? StandardBullets

  return (
    <div className="relative flex flex-col h-full overflow-hidden">
      <div className="flex-1 overflow-hidden">{content}</div>
      {showNotes && slide.speaker_notes && (
        <div className="shrink-0 border-t border-indigo-900/50 bg-slate-900/80 px-8 py-3">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Speaker Notes</p>
          <p className="text-sm text-gray-400 italic">{slide.speaker_notes}</p>
        </div>
      )}
    </div>
  )
}

// ── Offline Export Engine ──────────────────────────────────────────────────────

async function toBase64(url: string): Promise<string | null> {
  try {
    const r = await fetch(url)
    if (!r.ok) return null
    const blob = await r.blob()
    return new Promise((res) => {
      const reader = new FileReader()
      reader.onloadend = () => res(reader.result as string)
      reader.readAsDataURL(blob)
    })
  } catch { return null }
}

async function exportOfflineHTML(deck: SlidesDeck) {
  // embed images as base64 so the file works fully offline
  const slides = await Promise.all(
    deck.slides.map(async (s) => ({
      ...s,
      _b64: s.asset_path ? await toBase64(`/assets/${s.asset_path}`) : null,
    }))
  )

  const slidesJson = JSON.stringify(slides)

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>${deck.slideshow_title}</title>
<style>
:root{--bg:#030712;--surface:#0f172a;--border:#1e3a5f;--accent:#6366f1;--text:#f1f5f9;--sub:#94a3b8;--muted:#475569}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:system-ui,sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{display:flex;align-items:center;justify-content:space-between;padding:12px 24px;border-bottom:1px solid var(--border);flex-shrink:0}
header h1{font-size:.9rem;color:var(--accent);font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.progress-bar{height:3px;background:var(--border)}
.progress-fill{height:100%;background:var(--accent);transition:width .3s}
.slide-wrap{flex:1;position:relative;overflow:hidden}
.slide{display:none;position:absolute;inset:0}
.slide.active{display:flex;flex-direction:column}
/* Title_Slide */
.layout-Title_Slide{align-items:center;justify-content:center;text-align:center;padding:4rem}
.layout-Title_Slide h2{font-size:2.5rem;font-weight:700;color:#fff;line-height:1.2;margin:.75rem 0}
.layout-Title_Slide .sub{font-size:1.2rem;color:var(--accent)}
.layout-Title_Slide .bar{width:3rem;height:.25rem;background:var(--accent);border-radius:9px;margin:.5rem auto}
/* Standard_Bullets */
.layout-Standard_Bullets{padding:3rem 3.5rem;gap:2rem}
.layout-Standard_Bullets h2{font-size:1.6rem;font-weight:700;color:#c7d2fe;border-bottom:1px solid var(--border);padding-bottom:.75rem}
.layout-Standard_Bullets ul{list-style:none;display:flex;flex-direction:column;gap:.9rem;flex:1}
.layout-Standard_Bullets li{display:flex;gap:.75rem;font-size:1rem;color:#e2e8f0}
.layout-Standard_Bullets li::before{content:"→";color:var(--accent);flex-shrink:0}
/* Split_Metrics */
.layout-Split_Metrics{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;padding:2.5rem}
.split-left{display:flex;flex-direction:column;gap:1.25rem}
.split-left h2{font-size:1.5rem;font-weight:700;color:#c7d2fe}
.metric-card{background:rgba(99,102,241,.12);border:1px solid rgba(99,102,241,.3);border-radius:.75rem;padding:.75rem 1rem;font-size:.9rem;color:#e2e8f0}
.split-right{display:flex;align-items:center;justify-content:center}
.asset-img{width:100%;max-height:240px;object-fit:cover;border-radius:.75rem}
.asset-placeholder{width:100%;height:200px;border-radius:.75rem;background:linear-gradient(135deg,#1e1b4b,#312e81);border:1px solid var(--border)}
/* Visual_Hero */
.layout-Visual_Hero{position:relative;overflow:hidden}
.hero-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.3}
.hero-grad{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.85) 0%,rgba(0,0,0,.2) 60%,transparent 100%)}
.hero-content{position:relative;display:flex;flex-direction:column;justify-content:flex-end;height:100%;padding:3rem;gap:1rem}
.hero-content h2{font-size:2rem;font-weight:700;color:#fff;line-height:1.2}
.hero-content p{font-size:1.1rem;color:#c7d2fe}
/* Notes */
.notes-bar{flex-shrink:0;border-top:1px solid var(--border);background:rgba(15,23,42,.9);padding:.75rem 1.5rem;display:none}
.notes-bar.visible{display:block}
.notes-bar p{font-size:.8rem;color:var(--sub);font-style:italic}
.notes-label{font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.25rem}
/* Nav */
nav{display:flex;align-items:center;justify-content:space-between;padding:10px 24px;border-top:1px solid var(--border);flex-shrink:0}
nav button{background:rgba(99,102,241,.15);border:1px solid var(--accent);color:#c7d2fe;padding:6px 18px;border-radius:8px;cursor:pointer;font-size:.85rem;transition:background .2s}
nav button:hover{background:rgba(99,102,241,.35)}
nav button:disabled{opacity:.3;cursor:default}
.dots{display:flex;gap:6px;align-items:center}
.dot{width:6px;height:6px;border-radius:50%;background:var(--muted);cursor:pointer;border:none;transition:background .2s}
.dot.active{background:var(--accent)}
.key-hint{font-size:.65rem;color:var(--muted)}
</style>
</head>
<body>
<header>
  <h1>${deck.slideshow_title}</h1>
  <span class="key-hint">← → navigate · N toggle notes</span>
</header>
<div class="progress-bar"><div class="progress-fill" id="prog"></div></div>
<div class="slide-wrap" id="wrap"></div>
<nav>
  <button id="prevBtn" onclick="go(-1)">◀ Prev</button>
  <div class="dots" id="dots"></div>
  <button id="nextBtn" onclick="go(1)">Next ▶</button>
</nav>
<script>
const SLIDES=${slidesJson};
let cur=0,notesOn=false;
const wrap=document.getElementById('wrap');
const dots=document.getElementById('dots');
const prog=document.getElementById('prog');

function buildSlide(s,i){
  const div=document.createElement('div');
  div.className='slide'+(i===0?' active':'');
  div.id='s'+i;
  const layout=s.layout_type||'Standard_Bullets';
  const img=s._b64?'<img class="asset-img" src="'+s._b64+'" alt="">':'<div class="asset-placeholder"></div>';
  let inner='';
  if(layout==='Title_Slide'){
    inner='<div class="layout-Title_Slide"><div class="bar"></div><h2>'+s.title+'</h2>'+(s.bullets&&s.bullets[0]?'<p class="sub">'+s.bullets[0]+'</p>':'')+'<div class="bar"></div></div>';
  }else if(layout==='Split_Metrics'){
    const cards=(s.bullets||[]).map(b=>'<div class="metric-card">'+b+'</div>').join('');
    inner='<div class="layout-Split_Metrics"><div class="split-left"><h2>'+s.title+'</h2>'+cards+'</div><div class="split-right">'+img+'</div></div>';
  }else if(layout==='Visual_Hero'){
    const ps=(s.bullets||[]).slice(0,2).map(b=>'<p>'+b+'</p>').join('');
    const bg=s._b64?'<img class="hero-bg" src="'+s._b64+'" alt="">':'';
    inner='<div class="layout-Visual_Hero">'+bg+'<div class="hero-grad"></div><div class="hero-content"><h2>'+s.title+'</h2>'+ps+'</div></div>';
  }else{
    const lis=(s.bullets||[]).map(b=>'<li>'+b+'</li>').join('');
    inner='<div class="layout-Standard_Bullets"><h2>'+s.title+'</h2><ul>'+lis+'</ul></div>';
  }
  const notes=s.speaker_notes?'<div class="notes-bar" id="n'+i+'"><div class="notes-label">Speaker Notes</div><p>'+s.speaker_notes+'</p></div>':'';
  div.innerHTML=inner+notes;
  return div;
}

SLIDES.forEach((s,i)=>{
  wrap.appendChild(buildSlide(s,i));
  const d=document.createElement('button');
  d.className='dot'+(i===0?' active':'');
  d.onclick=()=>jump(i);
  dots.appendChild(d);
});

function render(){
  document.querySelectorAll('.slide').forEach((el,i)=>el.classList.toggle('active',i===cur));
  document.querySelectorAll('.dot').forEach((d,i)=>d.classList.toggle('active',i===cur));
  prog.style.width=((cur+1)/SLIDES.length*100)+'%';
  document.getElementById('prevBtn').disabled=cur===0;
  document.getElementById('nextBtn').disabled=cur===SLIDES.length-1;
  document.querySelectorAll('.notes-bar').forEach(nb=>nb.classList.toggle('visible',notesOn));
}

function go(d){cur=Math.max(0,Math.min(SLIDES.length-1,cur+d));render();}
function jump(i){cur=i;render();}

document.addEventListener('keydown',e=>{
  if(e.key==='ArrowRight'||e.key==='ArrowDown')go(1);
  else if(e.key==='ArrowLeft'||e.key==='ArrowUp')go(-1);
  else if(e.key==='n'||e.key==='N'){notesOn=!notesOn;render();}
});
render();
</script>
</body>
</html>`

  const blob = new Blob([html], { type: 'text/html' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${deck.slideshow_title.replace(/\s+/g, '_')}.html`
  a.click()
  URL.revokeObjectURL(a.href)
}

// ── Panel ──────────────────────────────────────────────────────────────────────

// ~1500 tokens for a 10-slide deck
const EXPECTED_TOKENS = 1500

export default function SlidesPanel({ documents }: Props) {
  const [selectedDoc, setSelectedDoc] = useState<number | ''>('')
  const [loading, setLoading] = useState(false)
  const [tokenCount, setTokenCount] = useState(0)
  const [deck, setDeck] = useState<SlidesDeck | null>(null)
  const [current, setCurrent] = useState(0)
  const [showNotes, setShowNotes] = useState(false)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(false)

  const readyDocs = documents.filter((d) => d.chunk_count > 0)
  const slide = deck?.slides[current]
  const total = deck?.slides.length ?? 0

  const go = (dir: number) => setCurrent((c) => Math.max(0, Math.min(total - 1, c + dir)))

  useEffect(() => {
    if (!deck) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') go(1)
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') go(-1)
      else if (e.key === 'n' || e.key === 'N') setShowNotes((v) => !v)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [deck, total])

  const generate = async () => {
    if (!selectedDoc) return
    setLoading(true)
    setError('')
    setDeck(null)
    setCurrent(0)
    setTokenCount(0)
    try {
      let toks = 0
      for await (const event of api.streamSlides(Number(selectedDoc))) {
        if (event.type === 'token') {
          toks++
          setTokenCount(toks)
        } else if (event.type === 'done') {
          const result = event as unknown as SlidesDeck
          if (!result.slides?.length) { setError('Model returned empty slides — try again'); return }
          setDeck(result)
        } else if (event.type === 'error') {
          setError((event.message as string) ?? 'Generation failed')
        }
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
      setTokenCount(0)
    }
  }

  const doExport = async () => {
    if (!deck) return
    setExporting(true)
    await exportOfflineHTML(deck)
    setExporting(false)
  }

  const layoutBadgeColor: Record<string, string> = {
    Title_Slide: 'bg-violet-900/60 text-violet-300',
    Standard_Bullets: 'bg-indigo-900/60 text-indigo-300',
    Split_Metrics: 'bg-blue-900/60 text-blue-300',
    Visual_Hero: 'bg-purple-900/60 text-purple-300',
  }

  return (
    <div className="flex flex-col h-full">
      {/* Controls */}
      <div className="p-4 border-b border-gray-800 flex items-end gap-3 shrink-0">
        <div className="flex-1">
          <label className="text-xs text-gray-500 block mb-1">Document</label>
          <select
            value={selectedDoc}
            onChange={(e) => setSelectedDoc(e.target.value ? Number(e.target.value) : '')}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">Select a document...</option>
            {readyDocs.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <button
          onClick={generate}
          disabled={!selectedDoc || loading}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Presentation className="w-4 h-4" />}
          Generate
        </button>
        {deck && (
          <button
            onClick={doExport}
            disabled={exporting}
            className="border border-gray-700 hover:border-indigo-500 text-gray-400 hover:text-indigo-400 text-sm px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
            title="Export standalone offline HTML"
          >
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Export
          </button>
        )}
      </div>

      {error && <p className="text-red-400 text-sm px-4 py-2 shrink-0">{error}</p>}

      {loading && (
        <div className="px-4 pt-2 shrink-0">
          <ProgressBar pct={Math.min(95, Math.round((tokenCount / EXPECTED_TOKENS) * 100))} label="Generating slides..." />
        </div>
      )}

      {!deck && !loading && (
        <div className="flex-1 flex items-center justify-center text-gray-700 text-sm">
          Select a document and click Generate
        </div>
      )}

      {deck && slide && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Deck title + layout badge + counter */}
          <div className="flex items-center gap-3 px-5 py-2 border-b border-gray-800 shrink-0">
            <span className="text-xs text-indigo-400 font-medium truncate flex-1">{deck.slideshow_title}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${layoutBadgeColor[slide.layout_type] ?? 'bg-gray-800 text-gray-400'}`}>
              {slide.layout_type?.replace('_', ' ')}
            </span>
            <span className="text-xs text-gray-600 shrink-0">{current + 1} / {total}</span>
          </div>

          {/* Progress bar */}
          <div className="h-0.5 bg-gray-800 shrink-0">
            <div className="h-full bg-indigo-600 transition-all" style={{ width: `${((current + 1) / total) * 100}%` }} />
          </div>

          {/* Slide */}
          <div className="flex-1 overflow-hidden bg-gray-950 m-4 rounded-xl border border-gray-800">
            <SlideView slide={slide} showNotes={showNotes} />
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between px-5 py-2 border-t border-gray-800 shrink-0">
            <button
              onClick={() => go(-1)}
              disabled={current === 0}
              className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-300 disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" /> Prev
            </button>

            {/* Dot strip */}
            <div className="flex gap-1.5 items-center overflow-hidden max-w-xs">
              {deck.slides.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setCurrent(i)}
                  className={`shrink-0 rounded-full transition-all ${i === current ? 'w-4 h-2 bg-indigo-500' : 'w-1.5 h-1.5 bg-gray-700 hover:bg-gray-500'}`}
                />
              ))}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowNotes((v) => !v)}
                className={`text-xs px-2 py-1 rounded-md transition-colors ${showNotes ? 'bg-indigo-900/60 text-indigo-400' : 'text-gray-600 hover:text-gray-400'}`}
                title="Toggle notes (N)"
              >
                Notes
              </button>
              <button
                onClick={() => go(1)}
                disabled={current === total - 1}
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-300 disabled:opacity-30 transition-colors"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
