import { useEffect, useMemo, useState } from 'react'

type DocumentRow = {
  id: string
  filename: string
  title?: string | null
  source_type: string
  status: string
  created_at: string
}

type Citation = {
  chunk_id: string
  document_id: string
  page_start?: number | null
  page_end?: number | null
  quote: string
  score: number
}

const answerModes = [
  'one-line',
  'short',
  'long',
  'bullets',
  '2-mark',
  '5-mark',
  '10-mark',
  '15-mark',
  'definition',
  'comparison',
  'notes',
  'flowchart',
  'mindmap',
  'memorize',
] as const

export default function App() {
  const [documents, setDocuments] = useState<DocumentRow[]>([])
  const [question, setQuestion] = useState('Explain photosynthesis for 5 marks')
  const [answerMode, setAnswerMode] = useState<typeof answerModes[number]>('5-mark')
  const [answer, setAnswer] = useState('')
  const [citations, setCitations] = useState<Citation[]>([])
  const [notes, setNotes] = useState('')
  const [diagram, setDiagram] = useState('')
  const [activeDocumentId, setActiveDocumentId] = useState<string>('')
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    void refreshDocuments()
  }, [])

  async function refreshDocuments() {
    const response = await fetch('/api/v1/documents')
    const data = await response.json()
    setDocuments(data.documents || [])
    if (!activeDocumentId && data.documents?.[0]?.id) {
      setActiveDocumentId(data.documents[0].id)
    }
  }

  async function upload(event: React.ChangeEvent<HTMLInputElement>) {
    const files = event.target.files
    if (!files?.length) return
    setUploading(true)
    const form = new FormData()
    form.append('session_id', 'default')
    form.append('source_type', 'mixed')
    Array.from(files).forEach((file) => form.append('files', file))
    await fetch('/api/v1/documents/upload', { method: 'POST', body: form })
    await refreshDocuments()
    setUploading(false)
    event.target.value = ''
  }

  async function ask() {
    setBusy(true)
    const payload = {
      session_id: 'default',
      question,
      answer_mode: answerMode,
      document_scope: activeDocumentId ? [activeDocumentId] : undefined,
      citation_mode: 'inline',
      temperature: 0.1,
    }
    const response = await fetch('/api/v1/qa/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = await response.json()
    setAnswer(data.answer || '')
    setCitations(data.citations || [])
    setBusy(false)
  }

  async function generateNotes() {
    if (!activeDocumentId) return
    setBusy(true)
    const response = await fetch('/api/v1/notes/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'default',
        document_id: activeDocumentId,
        topic: question,
        style: 'chapter-wise',
      }),
    })
    const data = await response.json()
    setNotes(data.markdown || '')
    setBusy(false)
  }

  async function generateDiagram(type: 'flowchart' | 'mindmap') {
    if (!activeDocumentId) return
    setBusy(true)
    const response = await fetch('/api/v1/flowcharts/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'default',
        document_id: activeDocumentId,
        topic: question,
        diagram_type: type,
      }),
    })
    const data = await response.json()
    setDiagram(data.mermaid || '')
    setBusy(false)
  }

  const activeLabel = useMemo(() => {
    const doc = documents.find((item) => item.id === activeDocumentId)
    return doc ? doc.filename : 'No document selected'
  }, [documents, activeDocumentId])

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandMark">EL</div>
          <div>
            <div className="brandName">ExamLens Local</div>
            <div className="brandTag">Grounded study workspace</div>
          </div>
        </div>

        <label className="uploadCard">
          <input type="file" multiple onChange={upload} />
          <span>{uploading ? 'Indexing documents...' : 'Upload PDF, DOCX, TXT, MD'}</span>
        </label>

        <div className="sectionTitle">Library</div>
        <div className="docList">
          {documents.length === 0 ? (
            <div className="empty">No documents yet.</div>
          ) : (
            documents.map((doc) => (
              <button
                key={doc.id}
                className={`docCard ${doc.id === activeDocumentId ? 'active' : ''}`}
                onClick={() => setActiveDocumentId(doc.id)}
              >
                <strong>{doc.filename}</strong>
                <span>{doc.source_type}</span>
              </button>
            ))
          )}
        </div>
      </aside>

      <main className="main">
        <header className="hero">
          <div>
            <p className="eyebrow">Local-first exam answer generation</p>
            <h1>Study from your own sources, in exam format.</h1>
            <p className="lede">
              Upload notes or textbooks, ask a question, and get grounded answers with citations,
              notes, and Mermaid diagrams.
            </p>
          </div>
          <div className="statusCard">
            <div className="statusLabel">Active source</div>
            <div className="statusValue">{activeLabel}</div>
          </div>
        </header>

        <section className="workspace">
          <div className="panel chatPanel">
            <div className="panelHeader">
              <h2>Ask</h2>
              <div className="modeRow">
                {answerModes.map((mode) => (
                  <button
                    key={mode}
                    className={`modeChip ${answerMode === mode ? 'selected' : ''}`}
                    onClick={() => setAnswerMode(mode)}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>

            <textarea
              className="questionBox"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask something about the uploaded documents..."
            />

            <div className="actionRow">
              <button className="primaryBtn" onClick={ask} disabled={busy}>
                {busy ? 'Working...' : 'Ask from sources'}
              </button>
              <button className="secondaryBtn" onClick={generateNotes} disabled={busy || !activeDocumentId}>
                Generate notes
              </button>
              <button className="secondaryBtn" onClick={() => generateDiagram('flowchart')} disabled={busy || !activeDocumentId}>
                Flowchart
              </button>
              <button className="secondaryBtn" onClick={() => generateDiagram('mindmap')} disabled={busy || !activeDocumentId}>
                Mind map
              </button>
            </div>

            <div className="answerCard">
              <div className="answerTitle">{answerMode}</div>
              <pre>{answer || 'Your grounded answer will appear here.'}</pre>
            </div>
          </div>

          <div className="panel evidencePanel">
            <div className="panelHeader">
              <h2>Evidence</h2>
              <span className="muted">{citations.length} citations</span>
            </div>
            {citations.length === 0 ? (
              <div className="empty">Citations will appear after asking a question.</div>
            ) : (
              <div className="citationList">
                {citations.map((citation) => (
                  <article key={citation.chunk_id} className="citationCard">
                    <div className="citationMeta">
                      <span>{citation.document_id}</span>
                      <span>p. {citation.page_start ?? '?'}</span>
                      <span>{citation.score.toFixed(3)}</span>
                    </div>
                    <p>{citation.quote}</p>
                  </article>
                ))}
              </div>
            )}
          </div>

          <div className="panel notesPanel">
            <div className="panelHeader">
              <h2>Notes / Diagram</h2>
            </div>
            <div className="stack">
              <div>
                <div className="subTitle">Notes</div>
                <pre className="notesBox">{notes || 'Generated notes will appear here.'}</pre>
              </div>
              <div>
                <div className="subTitle">Mermaid</div>
                <pre className="diagramBox">{diagram || 'Generated Mermaid diagram will appear here.'}</pre>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
