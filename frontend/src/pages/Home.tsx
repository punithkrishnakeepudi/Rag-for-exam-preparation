import { BookOpen, Plus, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as api from '../api'
import type { Notebook } from '../api'

export default function Home() {
  const [notebooks, setNotebooks] = useState<Notebook[]>([])
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    api.getNotebooks().then(setNotebooks).catch(console.error)
  }, [])

  const create = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    const nb = await api.createNotebook(newName.trim())
    setNotebooks((prev) => [nb, ...prev])
    setNewName('')
    setCreating(false)
    navigate(`/notebook/${nb.id}`)
  }

  const remove = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation()
    if (!confirm('Delete this notebook and all its documents?')) return
    await api.deleteNotebook(id)
    setNotebooks((prev) => prev.filter((n) => n.id !== id))
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-start pt-20 px-4">
      <div className="w-full max-w-2xl">
        <div className="flex items-center gap-3 mb-10">
          <BookOpen className="w-8 h-8 text-indigo-400" />
          <h1 className="text-3xl font-bold text-white">StudyLens</h1>
          <span className="text-sm text-gray-500 mt-1">Local AI Study Assistant</span>
        </div>

        <div className="flex items-center justify-between mb-4">
          <h2 className="text-gray-400 text-sm uppercase tracking-wider">Your Notebooks</h2>
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-3 py-1.5 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            New notebook
          </button>
        </div>

        {creating && (
          <form onSubmit={create} className="mb-4 flex gap-2">
            <input
              autoFocus
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Notebook name..."
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-lg transition-colors"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => setCreating(false)}
              className="text-gray-500 hover:text-gray-300 text-sm px-3 py-2 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </form>
        )}

        {notebooks.length === 0 && !creating && (
          <div className="text-center py-16 text-gray-600">
            <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No notebooks yet. Create one to get started.</p>
          </div>
        )}

        <div className="space-y-2">
          {notebooks.map((nb) => (
            <div
              key={nb.id}
              onClick={() => navigate(`/notebook/${nb.id}`)}
              className="flex items-center justify-between bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-gray-700 rounded-xl px-4 py-3 cursor-pointer transition-all group"
            >
              <div className="flex items-center gap-3">
                <BookOpen className="w-5 h-5 text-indigo-400" />
                <span className="font-medium text-gray-100">{nb.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-600">
                  {new Date(nb.created_at).toLocaleDateString()}
                </span>
                <button
                  onClick={(e) => remove(e, nb.id)}
                  className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
