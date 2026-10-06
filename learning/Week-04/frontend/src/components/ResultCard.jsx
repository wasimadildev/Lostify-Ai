import { MapPin } from 'lucide-react';
import { assetUrl } from '../api';
import StatusBadge from './StatusBadge';
import ScoreBars from './ScoreBars';

export default function ResultCard({ result, rank }) {
  const imgSrc = assetUrl(result.image_path);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 flex gap-4 hover:shadow-md transition-shadow">
      {imgSrc ? (
        <img
          src={imgSrc}
          alt={result.title}
          className="w-24 h-24 object-cover rounded-xl shrink-0"
          onError={(e) => {
            e.currentTarget.style.visibility = 'hidden';
          }}
        />
      ) : (
        <div className="w-24 h-24 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 shrink-0">
          no image
        </div>
      )}

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-400 text-sm font-mono">
            #{rank} · {result.case_id}
          </span>
          <StatusBadge type={result.case_type} status={result.status} />
        </div>
        <h3 className="font-semibold text-slate-900 mt-1 leading-snug">{result.title}</h3>
        <p className="text-sm text-slate-500 flex items-center gap-1">
          <MapPin size={14} className="shrink-0" />
          {result.location || 'Unknown'} · lost {result.date_lost || '—'}
        </p>
        {result.description ? (
          <p className="mt-1 text-sm text-slate-500 line-clamp-2">{result.description}</p>
        ) : null}
        <div className="mt-2">
          <ScoreBars result={result} />
        </div>
      </div>
    </div>
  );
}