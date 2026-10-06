import { useEffect, useState } from 'react';
import { CheckCircle2, LoaderCircle, Save, Search } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createReport, assetUrl } from '../api';
import Dropzone from '../components/Dropzone';
import StatusBadge from '../components/StatusBadge';

const TYPES = [
  { value: 'lost_pet', label: 'Lost Pet' },
  { value: 'lost_item', label: 'Lost Item' },
  { value: 'lost_person', label: 'Lost Person' },
];

const emptyForm = {
  title: '',
  description: '',
  caseType: 'lost_pet',
  category: '',
  location: '',
  dateLost: '',
  latitude: '',
  longitude: '',
};

export default function NewReportPage() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState('');
  const [form, setForm] = useState(emptyForm);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(null);

  useEffect(() => {
    if (!image) {
      setPreview('');
      return undefined;
    }
    const url = URL.createObjectURL(image);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [image]);

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!image && !form.description.trim() && !form.title.trim()) {
      setError('Add a photo, a description, or a title.');
      return;
    }

    setLoading(true);
    setError('');
    setSaved(null);
    try {
      const data = await createReport({
        image,
        title: form.title.trim(),
        description: form.description.trim(),
        caseType: form.caseType,
        category: form.category.trim().toLowerCase(),
        location: form.location.trim(),
        dateLost: form.dateLost,
        latitude: form.latitude ? Number(form.latitude) : undefined,
        longitude: form.longitude ? Number(form.longitude) : undefined,
      });
      setSaved(data);
      setForm(emptyForm);
      setImage(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">New lost report</h1>
        <p className="mt-1 text-slate-500">
          Save a new case to the database. It is embedded by CLIP and added to the FAISS index on the spot, so a
          search can find it immediately afterwards.
        </p>
      </header>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 space-y-4"
      >
        <Dropzone file={image} preview={preview} onChange={setImage} />

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-slate-700 mb-1">
              Title
            </label>
            <input
              id="title"
              value={form.title}
              onChange={set('title')}
              placeholder="e.g. White Persian Cat with Blue Collar"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <fieldset>
            <legend className="block text-sm font-medium text-slate-700 mb-1">What was lost?</legend>
            <div className="flex flex-wrap gap-2">
              {TYPES.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setForm((f) => ({ ...f, caseType: t.value }))}
                  className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                    form.caseType === t.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </fieldset>
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-slate-700 mb-1">
            Description
          </label>
          <textarea
            id="description"
            value={form.description}
            onChange={set('description')}
            rows={3}
            placeholder="e.g. white persian cat with a blue collar, lost near the park yesterday evening"
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-slate-700 mb-1">
              Category{' '}
              <span className="text-xs font-normal text-slate-400">(cat, dog, bicycle, …)</span>
            </label>
            <input
              id="category"
              value={form.category}
              onChange={set('category')}
              placeholder="e.g. cat"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="location" className="block text-sm font-medium text-slate-700 mb-1">
              City / area
            </label>
            <input
              id="location"
              value={form.location}
              onChange={set('location')}
              placeholder="e.g. Islamabad"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="dateLost" className="block text-sm font-medium text-slate-700 mb-1">
              Date lost
            </label>
            <input
              id="dateLost"
              type="date"
              value={form.dateLost}
              onChange={set('dateLost')}
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="latitude" className="block text-sm font-medium text-slate-700 mb-1">
                Latitude
              </label>
              <input
                id="latitude"
                value={form.latitude}
                onChange={set('latitude')}
                placeholder="33.68"
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label htmlFor="longitude" className="block text-sm font-medium text-slate-700 mb-1">
                Longitude
              </label>
              <input
                id="longitude"
                value={form.longitude}
                onChange={set('longitude')}
                placeholder="73.05"
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 pt-1">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60 transition-colors"
          >
            {loading ? <LoaderCircle size={16} className="animate-spin" /> : <Save size={16} />}
            {loading ? 'Saving…' : 'Save report'}
          </button>
          {error && <p className="text-sm text-rose-600 font-medium">{error}</p>}
        </div>
      </form>

      {saved && (
        <div className="mt-8 bg-emerald-50 border border-emerald-200 rounded-2xl p-5">
          <div className="flex items-center gap-2 text-emerald-700 font-semibold">
            <CheckCircle2 size={18} />
            Report saved & added to the search index
          </div>
          <p className="mt-1 text-sm text-emerald-700/80">{saved.message}</p>

          <div className="mt-4 bg-white rounded-2xl border border-emerald-200 p-4 flex gap-4">
            {saved.case.image_path ? (
              <img
                src={assetUrl(saved.case.image_path)}
                alt={saved.case.title}
                className="w-24 h-24 object-cover rounded-xl shrink-0"
              />
            ) : (
              <div className="w-24 h-24 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-600 shrink-0">
                {saved.case.case_id}
              </div>
            )}
            <div>
              <div className="flex items-center gap-2">
                <span className="text-slate-400 text-sm font-mono">{saved.case.case_id}</span>
                <StatusBadge type={saved.case.case_type} status={saved.case.status} />
              </div>
              <h3 className="font-semibold text-slate-900 mt-1">{saved.case.title}</h3>
              <p className="text-sm text-slate-500">📍 {saved.case.location || 'Unknown'}</p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              to="/reports"
              className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-300 bg-white px-4 py-2 text-sm font-medium text-emerald-700 hover:bg-emerald-100 transition-colors"
            >
              View all reports
            </Link>
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors"
            >
              <Search size={14} />
              Search for it now
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}