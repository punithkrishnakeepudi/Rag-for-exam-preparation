import { ChevronDown, ChevronRight, FileText, Globe, Loader2, Plus, Trash2, X } from 'lucide-react'
import { useRef, useState } from 'react'
import * as api from '../api'
import type { Document } from '../api'

interface Props {
  notebookId: number
  documents: Document[]
  onDocsChange: (docs: Document[]) => void
}

const typeIcon = (t: string) =>
  t === 'url' ? <Globe className="w-4 h-4 text-blue-400 shrink-0" /> : <FileText className="w-4 h-4 text-indigo-400 shrink-0" />

export default function DocumentPanel({ notebookId, documents, onDocsChange }: Props) {
  const [mode, setMode] = useState<'file' | 'url'>('file')
  const [urlInput, setUrlInput] = useState('')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const fileRef = useRef<HTMLInputElement>(null)

  const toggleExpand = (id: number) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      const doc = await api.uploadFile(notebookId, file)
      onDocsChange([...documents, doc])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const handleUrl = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!urlInput.trim()) return
    setUploading(true)
    setError('')
    try {
      const doc = await api.uploadUrl(notebookId, urlInput.trim())
      onDocsChange([...documents, doc])
      setUrlInput('')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const remove = async (docId: number) => {
    await api.deleteDocument(notebookId, docId)
    onDocsChange(documents.filter((d) => d.id !== docId))
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-800">
        <h2 className="text-xs uppercase tracking-wider text-gray-500 mb-3">Sources</h2>

        <div className="flex gap-1 mb-3 bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setMode('file')}
            className={`flex-1 text-xs py-1 rounded-md transition-colors ${mode === 'file' ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'}`}
          >
            Upload file
          </button>
          <button
            onClick={() => setMode('url')}
            className={`flex-1 text-xs py-1 rounded-md transition-colors ${mode === 'url' ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'}`}
          >
            Add URL
          </button>
        </div>

        {mode === 'file' ? (
          <label className="flex items-center justify-center gap-2 border-2 border-dashed border-gray-700 hover:border-indigo-500 rounded-lg p-3 cursor-pointer transition-colors text-sm text-gray-500 hover:text-gray-300">
            {uploading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Plus className="w-4 h-4" />
                <span>PDF, DOCX, TXT, MD</span>
              </>
            )}
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.docx,.txt,.md"
              className="hidden"
              onChange={handleFile}
              disabled={uploading}
            />
          </label>
        ) : (
          <form onSubmit={handleUrl} className="flex gap-2">
            <input
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://..."
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={uploading}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs px-3 py-1.5 rounded-lg transition-colors"
            >
              {uploading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Add'}
            </button>
          </form>
        )}

        {error && (
          <div className="mt-2 flex items-start gap-1.5 text-red-400 text-xs">
            <X className="w-3 h-3 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {documents.length === 0 && (
          <p className="text-center text-gray-700 text-sm py-8">No sources yet</p>
        )}
        {documents.map((doc) => (
          <div key={doc.id} className="bg-gray-900 rounded-lg overflow-hidden">
            <div className="flex items-center gap-2 px-3 py-2 group">
              {typeIcon(doc.source_type)}
              <span
                className="flex-1 text-sm text-gray-300 truncate"
                title={doc.name}
              >
                {doc.name}
              </span>
              {doc.chunk_count === 0 ? (
                <span className="text-xs text-yellow-500 flex items-center gap-1">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Indexing
                </span>
              ) : (
                <span className="text-xs text-green-600">{doc.chunk_count} chunks</span>
              )}
              {doc.summary && (
                <button
                  onClick={() => toggleExpand(doc.id)}
                  className="text-gray-600 hover:text-gray-400"
                >
                  {expanded.has(doc.id) ? (
                    <ChevronDown className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5" />
                  )}
                </button>
              )}
              <button
                onClick={() => remove(doc.id)}
                className="opacity-0 group-hover:opacity-100 text-gray-700 hover:text-red-400 transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
            {expanded.has(doc.id) && doc.summary && (
              <div className="px-3 pb-3 pt-1 border-t border-gray-800">
                <p className="text-xs text-gray-400 leading-relaxed">{doc.summary}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
