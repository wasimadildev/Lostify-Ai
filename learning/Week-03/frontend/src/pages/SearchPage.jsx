import { useEffect, useState } from 'react';
import { LoaderCircle, Search } from 'lucide-react';
import { searchReport } from '../api';
import Dropzone from '../components/Dropzone';
import ResultCard from '../components/ResultCard';

const TYPES = [
  { value: 'lost_pet', label: 'Lost Pet' },
  { value: 'lost_item', label: 'Lost Item' },
  { value: 'lost_person', label: 'Lost Person' },
];

export default function SearchPage() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState('');
  const [text, setText] = useState('');
  const [queryType, setQueryType] = useState('lost_pet');
  const [location, setLocation] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [response, setResponse] = useState(null);

  useEffect(() => {
    if (!image) {
      setPreview('');
      return undefined;
    }
    const url = URL.createObjectURL(image);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [image]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!image && !text.trim()) {
      setError('Add a photo or a description — the search needs at least one.');
      return;
    }

    setLoading(true);
    setError('');
    setResponse(null);
    try {
      const data = await searchReport({
        image,
        text: text.trim(),
        queryType,
        location: location.trim(),
        topK: 5,
      });
      setResponse(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const results = response?.results ?? [];

  return (
    <div className="max-w-3xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Report a loss</h1>
        <p className="mt-1 text-slate-500">
          Upload a photo and/or describe what went missing. The engine finds the most similar cases in the
          dataset and explains its match with a score.
        </p>
      </header>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-4"
      >
        <Dropzone file={image} preview={preview} onChange={setImage} />

        <div>
          <label htmlFor="text" className="block text-sm font-medium text-slate-700 mb-1">
            Description
          </label>
          <textarea
            id="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            placeholder="e.g. white persian cat with a blue collar, lost near the park"
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <fieldset>
            <legend className="block text-sm font-medium text-slate-700 mb-1">What was lost?</legend>
            <div className="flex flex-wrap gap-2">
              {TYPES.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setQueryType(t.value)}
                  className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                    queryType === t.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </fieldset>

          <div>
            <label htmlFor="location" className="block text-sm font-medium text-slate-700 mb-1">
              City / area (optional)
            </label>
            <input
              id="location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Islamabad"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex items-center gap-3 pt-1">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition-colors"
          >
            {loading ? <LoaderCircle size={16} className="animate-spin" /> : <Search size={16} />}
            {loading ? 'Matching…' : 'Find top 5 matches'}
          </button>
          {error && <p className="text-sm text-rose-600 font-medium">{error}</p>}
        </div>
      </form>

      {response && (
        <section className="mt-8">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-lg font-semibold text-slate-900">Top {results.length} matches</h2>
            <span className="text-xs text-slate-400 font-mono">
              {response.count} results · {response.latency_ms.toFixed(0)} ms
            </span>
          </div>

          {results.length === 0 ? (
            <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-500">
              No cases matched those filters. Try without filtering or add a photo.
            </div>
          ) : (
            <div className="space-y-3">
              {results.map((r, i) => (
                <ResultCard key={r.case_id} result={r} rank={i + 1} />
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}