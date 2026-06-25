import { Loader2, Send, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import * as api from '../api'
import type { ChatMessage } from '../api'
import ProgressBar from './ProgressBar'

interface Props {
  notebookId: number
}

// ~300 tokens expected per answer; cap display at 95% until done
const EXPECTED_TOKENS = 300

export default function ChatPanel({ notebookId }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [tokenCount, setTokenCount] = useState(0)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  // Load persisted history on mount / notebook switch
  useEffect(() => {
    api.getMessages(notebookId).then(setMessages).catch(() => {})
  }, [notebookId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!input.trim() || streaming) return
    const question = input.trim()
    setInput('')
    setError('')
    setTokenCount(0)

    const userMsg: ChatMessage = { role: 'user', content: question }
    const assistantMsg: ChatMessage = { role: 'assistant', content: '', sources: [] }

    setMessages((prev) => [...prev, userMsg, assistantMsg])
    const assistantIdx = messages.length + 1
    setStreaming(true)

    let answer = ''
    let sources: ChatMessage['sources'] = []
    let toks = 0

    try {
      for await (const event of api.streamChat(notebookId, question, [...messages, userMsg])) {
        if (event.type === 'sources') {
          sources = event.sources ?? []
          setMessages((prev) =>
            prev.map((m, i) => (i === assistantIdx ? { ...m, sources } : m))
          )
        } else if (event.type === 'token') {
          answer += event.token
          toks++
          setTokenCount(toks)
          setMessages((prev) =>
            prev.map((m, i) => (i === assistantIdx ? { ...m, content: answer } : m))
          )
        }
      }
      // persist both messages
      await api.saveMessage(notebookId, { role: 'user', content: question })
      await api.saveMessage(notebookId, { role: 'assistant', content: answer, sources })
    } catch (err: any) {
      setError(err.message || 'Something went wrong')
      setMessages((prev) => prev.slice(0, -1))
    } finally {
      setStreaming(false)
      setTokenCount(0)
    }
  }

  const clearHistory = async () => {
    await api.clearMessages(notebookId)
    setMessages([])
  }

  const pct = Math.min(95, Math.round((tokenCount / EXPECTED_TOKENS) * 100))

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-700 pt-16">
            <p className="text-sm">Ask a question about your sources</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-sm'
                  : 'bg-gray-800 text-gray-100 rounded-bl-sm'
              }`}
            >
              {msg.role === 'assistant' ? (
                <>
                  {msg.content ? (
                    <div className="prose prose-invert prose-sm max-w-none">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                  )}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-700">
                      <p className="text-xs text-gray-500 mb-1">Sources:</p>
                      <div className="flex flex-wrap gap-1">
                        {msg.sources.map((s, j) => (
                          <span
                            key={j}
                            className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full truncate max-w-[200px]"
                            title={s.doc_name}
                          >
                            {s.doc_name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}

        {error && (
          <div className="text-red-400 text-sm text-center bg-red-400/10 rounded-lg py-2 px-4">
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {streaming && (
        <div className="px-4 pb-1">
          <ProgressBar pct={pct} label="Generating answer..." />
        </div>
      )}

      <div className="p-4 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask about your documents..."
            disabled={streaming}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
          />
          <button
            onClick={send}
            disabled={streaming || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white p-2.5 rounded-xl transition-colors"
          >
            {streaming ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
          {messages.length > 0 && !streaming && (
            <button
              onClick={clearHistory}
              title="Clear history"
              className="text-gray-600 hover:text-red-400 p-2.5 rounded-xl transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
