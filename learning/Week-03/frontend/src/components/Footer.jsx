import { useEffect, useState } from 'react';
import { apiBase, fetchHealth } from '../api';

export default function Footer() {
  const [status, setStatus] = useState({ state: 'checking', detail: '' });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const h = await fetchHealth();
        if (!cancelled)
          setStatus({ state: 'ok', detail: `${h.model} · index ${h.index_size} cases · ${h.device}` });
      } catch {
        if (!cancelled) setStatus({ state: 'down', detail: apiBase });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="max-w-5xl mx-auto px-4 py-4 flex flex-wrap items-center justify-between gap-2 text-sm text-slate-500">
        <span>Lostify AI · Week 03 matching engine</span>
        <span className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              status.state === 'ok' ? 'bg-emerald-500' : status.state === 'down' ? 'bg-rose-500' : 'bg-slate-400 animate-pulse'
            }`}
          />
          {status.state === 'ok'
            ? `API online — ${status.detail}`
            : status.state === 'down'
              ? `API unreachable at ${status.detail}`
              : 'Checking API…'}
        </span>
      </div>
    </footer>
  );
}