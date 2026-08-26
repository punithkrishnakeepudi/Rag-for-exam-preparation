import { CheckCircle, HelpCircle, Loader2, XCircle } from 'lucide-react'
import { useState } from 'react'
import * as api from '../api'
import type { Document } from '../api'
import ProgressBar from './ProgressBar'

interface Props {
  documents: Document[]
}

interface Question {
  question: string
  options: Record<string, string>
  answer: string
}

function parseQuiz(text: string): Question[] {
  const questions: Question[] = []
  const blocks = text.split(/(?=Q\d*[:.]\s|Question\s*\d+[:.]\s)/i).filter((b) => b.trim())

  for (const block of blocks) {
    const qMatch = block.match(/Q[\d]*[:.]\s*(.+?)(?=\n[A-D][.)]\s)/is)
    if (!qMatch) continue
    const question = qMatch[1].replace(/\n/g, ' ').trim()
    const opts: Record<string, string> = {}
    for (const letter of ['A', 'B', 'C', 'D']) {
      // Anchor to line start so a stray "a " inside the question text can't match.
      const m = block.match(new RegExp(`^[ \\t]*${letter}[.)][ \\t]*(.+)$`, 'm'))
      if (m) opts[letter] = m[1].trim()
    }
    const ansMatch = block.match(/Answer[:.]\s*([A-D])/i)
    if (Object.keys(opts).length === 4 && ansMatch) {
      questions.push({ question, options: opts, answer: ansMatch[1].toUpperCase() })
    }
  }
  return questions
}

// ~600 tokens for 5 questions
const EXPECTED_TOKENS = 600

export default function QuizPanel({ documents }: Props) {
  const [selectedDoc, setSelectedDoc] = useState<number | ''>('')
  const [count, setCount] = useState(5)
  const [loading, setLoading] = useState(false)
  const [tokenCount, setTokenCount] = useState(0)
  const [questions, setQuestions] = useState<Question[]>([])
  const [rawText, setRawText] = useState('')
  const [selected, setSelected] = useState<Record<number, string>>({})
  const [revealed, setRevealed] = useState<Record<number, boolean>>({})
  const [error, setError] = useState('')

  const generate = async () => {
    if (!selectedDoc) return
    setLoading(true)
    setError('')
    setQuestions([])
    setRawText('')
    setSelected({})
    setRevealed({})
    setTokenCount(0)

    try {
      let toks = 0
      for await (const event of api.streamQuiz(Number(selectedDoc), count)) {
        if (event.type === 'token') {
          toks++
          setTokenCount(toks)
        } else if (event.type === 'done') {
          const quizText = (event.quiz_text as string) ?? ''
          const parsed = parseQuiz(quizText)
          if (parsed.length > 0) setQuestions(parsed)
          else setRawText(quizText)
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

  const pick = (qi: number, letter: string) => {
    if (revealed[qi]) return
    setSelected((prev) => ({ ...prev, [qi]: letter }))
    setRevealed((prev) => ({ ...prev, [qi]: true }))
  }

  const score = questions.filter((q, i) => selected[i] === q.answer).length
  const readyDocs = documents.filter((d) => d.chunk_count > 0)
  const pct = Math.min(95, Math.round((tokenCount / (EXPECTED_TOKENS * (count / 5))) * 100))

  return (
    <div className="flex flex-col h-full p-4 gap-4">
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <label className="text-xs text-gray-500 block mb-1">Document</label>
          <select
            value={selectedDoc}
            onChange={(e) => setSelectedDoc(e.target.value ? Number(e.target.value) : '')}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">Select a document...</option>
            {readyDocs.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Questions</label>
          <select
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-indigo-500"
          >
            {[3, 5, 8, 10].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
        <button
          onClick={generate}
          disabled={!selectedDoc || loading}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <HelpCircle className="w-4 h-4" />}
          Generate
        </button>
      </div>

      {loading && <ProgressBar pct={pct} label="Generating quiz..." />}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {questions.length > 0 && (
        <div className="text-sm text-gray-400 flex items-center gap-2">
          Score: <span className="text-white font-semibold">{score} / {questions.length}</span>
          <span className="text-gray-600">({Object.keys(revealed).length} answered)</span>
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-4">
        {questions.map((q, qi) => (
          <div key={qi} className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-sm font-medium text-gray-100 mb-3">
              <span className="text-indigo-400 mr-2">Q{qi + 1}.</span>
              {q.question}
            </p>
            <div className="space-y-2">
              {Object.entries(q.options).map(([letter, text]) => {
                const isSelected = selected[qi] === letter
                const isCorrect = q.answer === letter
                const isRevealed = revealed[qi]
                let cls = 'border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-300'
                if (isRevealed && isCorrect) cls = 'border-green-500 text-green-400 bg-green-500/10'
                else if (isRevealed && isSelected) cls = 'border-red-500 text-red-400 bg-red-500/10'
                return (
                  <button
                    key={letter}
                    onClick={() => pick(qi, letter)}
                    disabled={isRevealed}
                    className={`w-full text-left border rounded-lg px-3 py-2 text-sm transition-colors flex items-center gap-2 ${cls}`}
                  >
                    <span className="font-mono text-xs shrink-0">{letter})</span>
                    <span className="flex-1">{text}</span>
                    {isRevealed && isCorrect && <CheckCircle className="w-4 h-4 shrink-0" />}
                    {isRevealed && isSelected && !isCorrect && <XCircle className="w-4 h-4 shrink-0" />}
                  </button>
                )
              })}
            </div>
          </div>
        ))}

        {rawText && (
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-xs text-gray-500 mb-2">Raw quiz output:</p>
            <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">{rawText}</pre>
          </div>
        )}
      </div>
    </div>
  )
}
