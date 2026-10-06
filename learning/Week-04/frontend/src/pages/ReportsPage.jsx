import { useEffect, useMemo, useState } from 'react';
import { LoaderCircle } from 'lucide-react';
import { fetchReports } from '../api';
import CaseCard from '../components/CaseCard';

const FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'lost_pet', label: 'Lost Pet' },
  { value: 'lost_item', label: 'Lost Item' },
  { value: 'lost_person', label: 'Lost Person' },
];

export default function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchReports(500);
        if (!cancelled) setReports(data.data ?? []);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(
    () => (filter === 'all' ? reports : reports.filter((r) => r.case_type === filter)),
    [reports, filter],
  );

  return (
    <div className="max-w-5xl mx-auto">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">All reports</h1>
          <p className="mt-1 text-slate-500">
            Every report in the database ({reports.length}) — the dataset seed plus new submissions.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                filter === f.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </header>

      {loading && (
        <div className="flex items-center justify-center py-16 text-slate-400">
          <LoaderCircle size={24} className="animate-spin mr-2" />
          Loading reports…
        </div>
      )}

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-2xl p-6 text-center">
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          {filtered.length === 0 ? (
            <p className="text-slate-500 text-center py-16">No reports of this type yet.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((r) => (
                <CaseCard key={r.case_id} report={r} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}