import { ArrowLeft, HelpCircle, MessageSquare, Network, Presentation, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import * as api from '../api'
import type { Document, Notebook } from '../api'
import ChatPanel from '../components/ChatPanel'
import DocumentPanel from '../components/DocumentPanel'
import MindMapPanel from '../components/MindMapPanel'
import QuizPanel from '../components/QuizPanel'
import SlidesPanel from '../components/SlidesPanel'

type Tab = 'chat' | 'quiz' | 'mindmap' | 'slides'

const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'chat', label: 'Chat', icon: <MessageSquare className="w-4 h-4" /> },
  { id: 'quiz', label: 'Quiz', icon: <HelpCircle className="w-4 h-4" /> },
  { id: 'mindmap', label: 'Mind Map', icon: <Network className="w-4 h-4" /> },
  { id: 'slides', label: 'Slides', icon: <Presentation className="w-4 h-4" /> },
]

export default function Notebook() {
  const { id } = useParams<{ id: string }>()
  const nbId = Number(id)

  const [notebook, setNotebook] = useState<Notebook | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [tab, setTab] = useState<Tab>('chat')
  const [refreshing, setRefreshing] = useState(false)

  const fetchDocs = async () => {
    const docs = await api.getDocuments(nbId)
    setDocuments(docs)
  }

  useEffect(() => {
    api.getNotebooks().then((nbs) => {
      const found = nbs.find((n) => n.id === nbId)
      setNotebook(found ?? null)
    })
    fetchDocs()
  }, [nbId])

  // poll while any document is still indexing
  useEffect(() => {
    const hasIndexing = documents.some((d) => d.chunk_count === 0)
    if (!hasIndexing) return
    const timer = setInterval(fetchDocs, 3000)
    return () => clearInterval(timer)
  }, [documents])

  const refresh = async () => {
    setRefreshing(true)
    await fetchDocs()
    setRefreshing(false)
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex items-center gap-3 px-4 py-3 border-b border-gray-800 shrink-0">
        <Link to="/" className="text-gray-500 hover:text-gray-300 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="font-semibold text-gray-100 flex-1 truncate">
          {notebook?.name ?? 'Loading...'}
        </h1>
        <button
          onClick={refresh}
          title="Refresh document status"
          className="text-gray-600 hover:text-gray-400 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </header>

      {/* Main layout: documents left, content right */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: document sources */}
        <aside className="w-72 shrink-0 border-r border-gray-800 overflow-hidden flex flex-col">
          <DocumentPanel
            notebookId={nbId}
            documents={documents}
            onDocsChange={setDocuments}
          />
        </aside>

        {/* Right: tabbed content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Tabs */}
          <div className="flex gap-1 px-4 pt-3 pb-0 border-b border-gray-800 shrink-0">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-4 py-2 text-sm rounded-t-lg border-b-2 transition-colors ${
                  tab === t.id
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-gray-500 hover:text-gray-300'
                }`}
              >
                {t.icon}
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-hidden">
            {tab === 'chat' && <ChatPanel notebookId={nbId} />}
            {tab === 'quiz' && <QuizPanel documents={documents} />}
            {tab === 'mindmap' && <MindMapPanel documents={documents} />}
            {tab === 'slides' && <SlidesPanel documents={documents} />}
          </div>
        </main>
      </div>
    </div>
  )
}
