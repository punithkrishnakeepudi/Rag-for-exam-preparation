export interface Notebook {
  id: number
  name: string
  created_at: string
}

export interface Document {
  id: number
  notebook_id: number
  name: string
  source_type: 'pdf' | 'docx' | 'txt' | 'url'
  source_ref: string
  summary: string | null
  chunk_count: number
  created_at: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: { doc_name: string; chunk_idx: number }[]
}

export interface MindMapData {
  nodes: { id: string; label: string }[]
  edges: { source: string; target: string; label: string }[]
  parse_error?: boolean
}

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(path, opts)
  if (!r.ok) {
    const msg = await r.text().catch(() => `HTTP ${r.status}`)
    throw new Error(msg)
  }
  return r.json()
}

// Notebooks
export const getNotebooks = () => req<Notebook[]>('/api/notebooks')
export const createNotebook = (name: string) =>
  req<Notebook>('/api/notebooks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
export const renameNotebook = (id: number, name: string) =>
  req<Notebook>(`/api/notebooks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
export const deleteNotebook = (id: number) =>
  req<void>(`/api/notebooks/${id}`, { method: 'DELETE' })

// Documents
export const getDocuments = (nbId: number) =>
  req<Document[]>(`/api/notebooks/${nbId}/documents`)

export const uploadFile = (nbId: number, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return req<Document>(`/api/notebooks/${nbId}/documents`, { method: 'POST', body: form })
}

export const uploadUrl = (nbId: number, url: string) => {
  const form = new FormData()
  form.append('url', url)
  return req<Document>(`/api/notebooks/${nbId}/documents`, { method: 'POST', body: form })
}

export const deleteDocument = (nbId: number, docId: number) =>
  req<void>(`/api/notebooks/${nbId}/documents/${docId}`, { method: 'DELETE' })

// Chat (streaming SSE over POST)
export async function* streamChat(
  nbId: number,
  question: string,
  history: ChatMessage[]
): AsyncGenerator<{ type: string; token?: string; sources?: ChatMessage['sources']; done?: boolean }> {
  const response = await fetch(`/api/notebooks/${nbId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, history: history.slice(-4) }),
  })

  if (!response.ok) {
    const text = await response.text().catch(() => `HTTP ${response.status}`)
    throw new Error(text)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop()!
      for (const part of parts) {
        const line = part.trim()
        if (line.startsWith('data: ')) {
          yield JSON.parse(line.slice(6))
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

// Chat history persistence
export const getMessages = (nbId: number) =>
  req<ChatMessage[]>(`/api/notebooks/${nbId}/messages`)

export const saveMessage = (nbId: number, msg: { role: string; content: string; sources?: ChatMessage['sources'] }) =>
  req<{ ok: boolean }>(`/api/notebooks/${nbId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role: msg.role, content: msg.content, sources: msg.sources ?? [] }),
  })

export const clearMessages = (nbId: number) =>
  req<void>(`/api/notebooks/${nbId}/messages`, { method: 'DELETE' })

// SSE helper (shared by quiz / mindmap / slides)
async function* ssePost(
  path: string,
  body?: object
): AsyncGenerator<{ type: string; token?: string; [key: string]: unknown }> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    const text = await response.text().catch(() => `HTTP ${response.status}`)
    throw new Error(text)
  }
  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop()!
      for (const part of parts) {
        const line = part.trim()
        if (line.startsWith('data: ')) yield JSON.parse(line.slice(6))
      }
    }
  } finally {
    reader.releaseLock()
  }
}

// Quiz & Mind Map & Slides (all SSE-streamed now for real-time progress)
export const streamQuiz = (docId: number, n = 5) =>
  ssePost(`/api/documents/${docId}/quiz`, { n })

export const streamMindmap = (docId: number) =>
  ssePost(`/api/documents/${docId}/mindmap`)

export type LayoutType = 'Title_Slide' | 'Standard_Bullets' | 'Split_Metrics' | 'Visual_Hero'

export interface Slide {
  slide_number: number
  layout_type: LayoutType
  title: string
  bullets: string[]
  speaker_notes?: string
  asset_generation_prompt?: string
  asset_path?: string
}

export interface SlidesDeck {
  slideshow_title: string
  slides: Slide[]
}

export const streamSlides = (docId: number) =>
  ssePost(`/api/documents/${docId}/slides`)
