import { CalendarDays, MapPin } from 'lucide-react';
import { assetUrl } from '../api';
import StatusBadge from './StatusBadge';

export default function CaseCard({ report }) {
  const imgSrc = assetUrl(report.image_path);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow">
      {imgSrc ? (
        <img
          src={imgSrc}
          alt={report.title}
          className="h-40 w-full object-cover"
          onError={(e) => {
            e.currentTarget.style.visibility = 'hidden';
          }}
        />
      ) : (
        <div className="h-40 w-full bg-slate-100 flex items-center justify-center text-slate-400">
          no image
        </div>
      )}

      <div className="p-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-400 text-xs font-mono">{report.case_id}</span>
          <StatusBadge type={report.case_type} status={report.status} />
          {report.source === 'user' && (
            <span className="rounded-full bg-amber-100 text-amber-700 px-2.5 py-0.5 text-xs font-semibold">
              New report
            </span>
          )}
        </div>
        <h3 className="font-semibold text-slate-900 mt-2 leading-snug">{report.title}</h3>
        <div className="mt-2 text-sm text-slate-500 space-y-1">
          <p className="flex items-center gap-1.5">
            <MapPin size={14} className="shrink-0" />
            {report.location || 'Unknown'}
          </p>
          <p className="flex items-center gap-1.5">
            <CalendarDays size={14} className="shrink-0" />
            Lost {report.date_lost || '—'}
          </p>
        </div>
      </div>
    </div>
  );
}