const TYPE_STYLES = {
  lost_pet: 'bg-emerald-100 text-emerald-700',
  lost_person: 'bg-violet-100 text-violet-700',
  lost_item: 'bg-blue-100 text-blue-700',
};

const TYPE_LABELS = {
  lost_pet: 'Lost Pet',
  lost_person: 'Lost Person',
  lost_item: 'Lost Item',
};

export const caseTypeLabel = (type) => TYPE_LABELS[type] ?? type ?? 'Case';
export const caseTypeStyles = (type) => TYPE_STYLES[type] ?? 'bg-slate-100 text-slate-600';

export default function StatusBadge({ type, status }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${caseTypeStyles(type)}`}>
      {caseTypeLabel(type)}
      {status ? ' · ' : ''}
      {status}
    </span>
  );
}