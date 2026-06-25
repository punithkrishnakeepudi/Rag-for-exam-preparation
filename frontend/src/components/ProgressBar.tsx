interface Props {
  pct: number   // 0-100
  label?: string
}

export default function ProgressBar({ pct, label }: Props) {
  const clamped = Math.min(100, Math.max(0, pct))
  return (
    <div className="space-y-1">
      {label && <p className="text-xs text-gray-500">{label}</p>}
      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-indigo-500 rounded-full transition-all duration-300"
          style={{ width: `${clamped}%` }}
        />
      </div>
      <p className="text-xs text-gray-600 text-right">{Math.round(clamped)}%</p>
    </div>
  )
}
