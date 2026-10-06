const ROWS = [
  { key: 'final_score', label: 'Match' },
  { key: 'visual_score', label: 'Visual' },
  { key: 'text_score', label: 'Text' },
  { key: 'face_score', label: 'Face' },
  { key: 'ocr_score', label: 'OCR / metadata' },
  { key: 'location_score', label: 'Location' },
];

const COLORS = {
  final_score: 'bg-gradient-to-r from-emerald-500 to-teal-500',
  visual_score: 'bg-gradient-to-r from-blue-500 to-indigo-500',
  text_score: 'bg-gradient-to-r from-violet-500 to-purple-500',
  face_score: 'bg-gradient-to-r from-pink-500 to-rose-500',
  ocr_score: 'bg-gradient-to-r from-emerald-500 to-green-500',
  location_score: 'bg-gradient-to-r from-amber-500 to-orange-500',
};

function scoreNum(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export default function ScoreBars({ result }) {
  const rows = ROWS.map(({ key, label }) => {
    const value = scoreNum(result?.[key]);
    return value === null ? null : { key, label, value };
  }).filter(Boolean);

  if (rows.length === 0) return null;

  return (
    <div className="space-y-1.5">
      {rows.map(({ key, label, value }) => (
        <div key={key}>
          <div className="flex justify-between text-xs text-slate-500">
            <span>{label}</span>
            <span className="font-mono">{value.toFixed(2)}</span>
          </div>
          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${COLORS[key]}`}
              style={{ width: `${Math.min(100, Math.max(0, Math.round(value * 100)))}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}