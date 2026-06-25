import {
  Background,
  Controls,
  type Edge,
  type Node,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Loader2, Network } from 'lucide-react'
import { useState } from 'react'
import * as api from '../api'
import type { Document } from '../api'
import ProgressBar from './ProgressBar'

interface Props {
  documents: Document[]
}

function radialLayout(rawNodes: { id: string; label: string }[]): Node[] {
  const n = rawNodes.length
  if (n === 0) return []
  const cx = 400
  const cy = 300
  const r = Math.min(220, n * 30 + 60)
  return rawNodes.map((node, i) => ({
    id: node.id,
    position: {
      x: cx + r * Math.cos((2 * Math.PI * i) / n) - 60,
      y: cy + r * Math.sin((2 * Math.PI * i) / n) - 20,
    },
    data: { label: node.label },
    style: {
      background: '#1e1b4b',
      border: '1px solid #4f46e5',
      borderRadius: '8px',
      color: '#c7d2fe',
      fontSize: '12px',
      padding: '6px 10px',
    },
  }))
}

// ~400 tokens for 10-15 nodes
const EXPECTED_TOKENS = 400

export default function MindMapPanel({ documents }: Props) {
  const [selectedDoc, setSelectedDoc] = useState<number | ''>('')
  const [loading, setLoading] = useState(false)
  const [tokenCount, setTokenCount] = useState(0)
  const [error, setError] = useState('')
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  const generate = async () => {
    if (!selectedDoc) return
    setLoading(true)
    setError('')
    setTokenCount(0)

    try {
      let toks = 0
      for await (const event of api.streamMindmap(Number(selectedDoc))) {
        if (event.type === 'token') {
          toks++
          setTokenCount(toks)
        } else if (event.type === 'done') {
          const data = event as { nodes?: { id: string; label: string }[]; edges?: { source: string; target: string; label: string }[]; parse_error?: boolean }
          if (data.parse_error || !data.nodes?.length) {
            setError('Model returned invalid JSON. Try again or pick a different document.')
            return
          }
          setNodes(radialLayout(data.nodes))
          setEdges(
            (data.edges || []).map((e, i): Edge => ({
              id: `e${i}`,
              source: e.source,
              target: e.target,
              label: e.label,
              style: { stroke: '#4f46e5' },
              labelStyle: { fill: '#94a3b8', fontSize: 10 },
            }))
          )
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

  const readyDocs = documents.filter((d) => d.chunk_count > 0)
  const pct = Math.min(95, Math.round((tokenCount / EXPECTED_TOKENS) * 100))

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-800 flex flex-col gap-3">
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
          <button
            onClick={generate}
            disabled={!selectedDoc || loading}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Network className="w-4 h-4" />}
            Generate
          </button>
        </div>
        {loading && <ProgressBar pct={pct} label="Generating mind map..." />}
      </div>

      {error && <p className="text-red-400 text-sm px-4 py-2">{error}</p>}

      <div className="flex-1 bg-gray-950">
        {nodes.length === 0 && !loading ? (
          <div className="h-full flex items-center justify-center text-gray-700 text-sm">
            Select a document and click Generate
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            style={{ background: '#030712' }}
          >
            <Background color="#1f2937" gap={24} />
            <Controls />
          </ReactFlow>
        )}
      </div>
    </div>
  )
}
