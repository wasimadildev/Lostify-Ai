import { useEffect, useRef, useState } from 'react';
import {
  Activity,
  ArrowUpRight,
  BadgeAlert,
  Bike,
  Check,
  ChevronRight,
  CircleHelp,
  FilePlus2,
  ImagePlus,
  LoaderCircle,
  MapPin,
  PackageSearch,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

const emptyReport = {
  title: '',
  category: 'Bag',
  location: '',
  description: '',
  contact_name: '',
  contact_email: '',
};

function App() {
  const [activeView, setActiveView] = useState('search');
  const [query, setQuery] = useState('');
  const [queryImage, setQueryImage] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [weights, setWeights] = useState({ image: 0.5, text: 0.5 });
  const [topK, setTopK] = useState(5);
  const [results, setResults] = useState([]);
  const [reports, setReports] = useState([]);
  const [status, setStatus] = useState({ loading: true, healthy: false, ai: null });
  const [searchState, setSearchState] = useState({ loading: false, error: '', ran: false });
  const [reportState, setReportState] = useState({ ...emptyReport });
  const [reportImage, setReportImage] = useState(null);
  const [reportPreview, setReportPreview] = useState('');
  const [reportFeedback, setReportFeedback] = useState({ loading: false, error: '', success: '' });
  const fileInputRef = useRef(null);
  const reportInputRef = useRef(null);

  useEffect(() => {
    refreshDashboard();
  }, []);

  async function refreshDashboard() {
    const [healthResponse, reportsResponse] = await Promise.allSettled([
      fetch(`${API_URL}/api/health`),
      fetch(`${API_URL}/api/reports`),
    ]);

    if (healthResponse.status === 'fulfilled') {
      const payload = await healthResponse.value.json();
      setStatus({ loading: false, healthy: healthResponse.value.ok, ai: payload });
    } else {
      setStatus({ loading: false, healthy: false, ai: null });
    }

    if (reportsResponse.status === 'fulfilled' && reportsResponse.value.ok) {
      const payload = await reportsResponse.value.json();
      setReports(payload.data || []);
    }
  }

  function handleImageChange(event, target) {
    const file = event.target.files?.[0];
    if (!file) return;
    const preview = URL.createObjectURL(file);
    if (target === 'query') {
      setQueryImage(file);
      setImagePreview(preview);
    } else {
      setReportImage(file);
      setReportPreview(preview);
    }
  }

  function clearQueryImage() {
    setQueryImage(null);
    setImagePreview('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  async function runSearch(event) {
    event.preventDefault();
    if (!query.trim() && !queryImage) {
      setSearchState({ loading: false, ran: false, error: 'Add a photo or describe the item first.' });
      return;
    }

    const form = new FormData();
    if (queryImage) form.append('image', queryImage);
    if (query.trim()) form.append('text', query.trim());
    form.append('weight_image', queryImage ? weights.image : '0');
    form.append('weight_text', query.trim() ? weights.text : '0');
    form.append('top_k', String(topK));

    setSearchState({ loading: true, ran: false, error: '' });
    try {
      const response = await fetch(`${API_URL}/api/search`, { method: 'POST', body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Search failed.');
      setResults(payload.data?.results || []);
      setSearchState({ loading: false, ran: true, error: '' });
    } catch (error) {
      setSearchState({ loading: false, ran: false, error: error.message });
    }
  }

  async function submitReport(event) {
    event.preventDefault();
    setReportFeedback({ loading: true, error: '', success: '' });
    const form = new FormData();
    Object.entries(reportState).forEach(([key, value]) => form.append(key, value));
    if (reportImage) form.append('image', reportImage);

    try {
      const response = await fetch(`${API_URL}/api/reports`, { method: 'POST', body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Could not create report.');
      setReports((current) => [payload.data, ...current]);
      setReportState({ ...emptyReport });
      setReportImage(null);
      setReportPreview('');
      if (reportInputRef.current) reportInputRef.current.value = '';
      setReportFeedback({ loading: false, error: '', success: 'Report added to the lost-item registry.' });
    } catch (error) {
      setReportFeedback({ loading: false, error: error.message, success: '' });
    }
  }

  function updateReport(field, value) {
    setReportState((current) => ({ ...current, [field]: value }));
  }

  const hasBothQueries = Boolean(query.trim() && queryImage);
  const currentMode = hasBothQueries ? 'Image + text' : queryImage ? 'Image search' : 'Text search';

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark"><Sparkles size={18} /></div>
          <div>
            <strong>lostify</strong>
            <span>match desk</span>
          </div>
        </div>

        <div className="side-label">Workspace</div>
        <nav className="nav-list" aria-label="Primary navigation">
          <button className={activeView === 'search' ? 'nav-item active' : 'nav-item'} onClick={() => setActiveView('search')}>
            <Search size={18} />
            <span>Find an item</span>
            <ChevronRight size={15} className="nav-chevron" />
          </button>
          <button className={activeView === 'report' ? 'nav-item active' : 'nav-item'} onClick={() => setActiveView('report')}>
            <FilePlus2 size={18} />
            <span>Report lost item</span>
            <ChevronRight size={15} className="nav-chevron" />
          </button>
          <button className={activeView === 'reports' ? 'nav-item active' : 'nav-item'} onClick={() => setActiveView('reports')}>
            <PackageSearch size={18} />
            <span>Report registry</span>
            <span className="nav-count">{reports.length}</span>
          </button>
        </nav>

        <div className="sidebar-spacer" />
        <div className="side-status">
          <div className="status-row"><span className={status.healthy ? 'status-dot online' : 'status-dot'} /> <span>AI service</span><b>{status.loading ? 'checking' : status.healthy ? 'online' : 'offline'}</b></div>
          <div className="status-row"><span className="status-dot online" /> <span>Node API</span><b>online</b></div>
          <p>Search is powered by CLIP embeddings and FAISS ranking.</p>
        </div>
        <div className="side-footer">WEEK 02 / OPERATIONS</div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Lostify AI <span>/</span> {activeView === 'search' ? 'Match desk' : activeView === 'report' ? 'New report' : 'Registry'}</p>
            <h1>{activeView === 'search' ? 'Find what went missing.' : activeView === 'report' ? 'Put the details on record.' : 'Every report, in one place.'}</h1>
          </div>
          <div className="topbar-meta">
            <div className="service-pill"><span className={status.healthy ? 'status-dot online' : 'status-dot'} /> {status.healthy ? 'AI connected' : 'AI needs attention'}</div>
            <div className="avatar">LD</div>
          </div>
        </header>

        {activeView === 'search' && (
          <SearchView
            query={query}
            setQuery={setQuery}
            queryImage={queryImage}
            imagePreview={imagePreview}
            fileInputRef={fileInputRef}
            handleImageChange={handleImageChange}
            clearQueryImage={clearQueryImage}
            weights={weights}
            setWeights={setWeights}
            topK={topK}
            setTopK={setTopK}
            runSearch={runSearch}
            searchState={searchState}
            results={results}
            currentMode={currentMode}
            reports={reports}
            onNewReport={() => setActiveView('report')}
          />
        )}

        {activeView === 'report' && (
          <ReportView
            reportState={reportState}
            updateReport={updateReport}
            reportImage={reportImage}
            reportPreview={reportPreview}
            reportInputRef={reportInputRef}
            handleImageChange={handleImageChange}
            submitReport={submitReport}
            feedback={reportFeedback}
          />
        )}

        {activeView === 'reports' && (
          <RegistryView reports={reports} onNewReport={() => setActiveView('report')} />
        )}
      </main>
    </div>
  );
}

function SearchView({ query, setQuery, queryImage, imagePreview, fileInputRef, handleImageChange, clearQueryImage, weights, setWeights, topK, setTopK, runSearch, searchState, results, currentMode, reports, onNewReport }) {
  return (
    <>
      <section className="search-grid">
        <form className="query-panel" onSubmit={runSearch}>
          <div className="panel-heading">
            <div><span className="section-kicker">01 / Query</span><h2>Describe the missing item</h2></div>
            <div className="mode-chip"><Activity size={14} /> {currentMode}</div>
          </div>
          <label className="field-label" htmlFor="query">What should we look for?</label>
          <textarea id="query" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="e.g. black backpack with a silver zipper, last seen near the station" rows="4" />
          <div className="query-divider"><span>and / or add a photo</span></div>
          {imagePreview ? (
            <div className="image-preview">
              <img src={imagePreview} alt="Selected search query" />
              <button type="button" className="remove-image" onClick={clearQueryImage} aria-label="Remove selected image"><X size={16} /></button>
              <div className="preview-caption"><Check size={14} /> {queryImage?.name}</div>
            </div>
          ) : (
            <button type="button" className="dropzone" onClick={() => fileInputRef.current?.click()}>
              <span className="drop-icon"><ImagePlus size={20} /></span>
              <span><b>Upload a reference image</b><small>JPEG, PNG, WEBP · up to 10MB</small></span>
              <Upload size={17} className="drop-arrow" />
            </button>
          )}
          <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp,image/gif" onChange={(event) => handleImageChange(event, 'query')} hidden />
          <div className="search-controls">
            <label>Results <select value={topK} onChange={(event) => setTopK(event.target.value)}><option value="3">Top 3</option><option value="5">Top 5</option><option value="10">Top 10</option></select></label>
            {queryImage && query.trim() && <label>Image weight <input type="range" min="0" max="1" step="0.1" value={weights.image} onChange={(event) => setWeights({ image: Number(event.target.value), text: 1 - Number(event.target.value) })} /></label>}
          </div>
          <button className="primary-button" type="submit" disabled={searchState.loading}>{searchState.loading ? <LoaderCircle className="spin" size={18} /> : <Search size={18} />} {searchState.loading ? 'Searching the index' : 'Search lost-item index'} <ArrowUpRight size={17} /></button>
          {searchState.error && <div className="inline-error"><BadgeAlert size={16} /> {searchState.error}</div>}
        </form>

        <div className="signal-panel">
          <div className="signal-orbit"><div className="orbit-dot"><Sparkles size={17} /></div><span className="orbit-ring ring-one" /><span className="orbit-ring ring-two" /></div>
          <span className="section-kicker">How it works</span>
          <h2>One clear lead can change the search.</h2>
          <p>CLIP turns your image and words into a shared visual language. FAISS compares that signal against every known case.</p>
          <div className="pipeline"><span>query</span><i /><span>embedding</span><i /><span>ranked leads</span></div>
          <div className="signal-foot"><ShieldCheck size={16} /> Similarity is a lead, not proof of ownership.</div>
        </div>
      </section>

      <section className="results-section">
        <div className="section-header"><div><span className="section-kicker">02 / Results</span><h2>{searchState.ran ? `${results.length} strongest matches` : 'Your strongest matches will appear here'}</h2></div><span className="result-note">{searchState.ran ? 'Sorted by combined similarity' : 'Ready when you are'}</span></div>
        {searchState.ran && results.length > 0 ? <div className="result-list">{results.map((result, index) => <ResultCard key={result.case_id} result={result} rank={index + 1} />)}</div> : <EmptyResults onNewReport={onNewReport} ran={searchState.ran} />}
      </section>

      <section className="bottom-strip"><div><span className="section-kicker">Registry snapshot</span><strong>{reports.length} lost-item report{reports.length === 1 ? '' : 's'} on file</strong></div><button className="text-button" onClick={onNewReport}>Add a report <ArrowUpRight size={15} /></button></section>
    </>
  );
}

function ResultCard({ result, rank }) {
  const score = Math.round((result.similarity_score || 0) * 100);
  return <article className="result-card"><div className="rank">{String(rank).padStart(2, '0')}</div><div className="result-main"><div className="result-title-row"><h3>{result.title}</h3><span className="score">{score}% match</span></div><div className="result-tags"><span>{result.category}</span><span><MapPin size={13} /> {result.location}</span></div><p>{result.description}</p></div><div className="result-side"><span className="score-bar"><i style={{ width: `${score}%` }} /></span><span className="score-decimal">{Number(result.similarity_score || 0).toFixed(4)}</span></div></article>;
}

function EmptyResults({ onNewReport, ran }) {
  return <div className="empty-results"><div className="empty-icon"><PackageSearch size={24} /></div><div><h3>{ran ? 'No matches came back.' : 'The index is waiting.'}</h3><p>{ran ? 'Try a broader description or a different image.' : 'Add a photo, a few identifying words, or both to begin.'}</p></div><button className="outline-button" onClick={onNewReport}><FilePlus2 size={16} /> Report an item</button></div>;
}

function ReportView({ reportState, updateReport, reportImage, reportPreview, reportInputRef, handleImageChange, submitReport, feedback }) {
  return <section className="report-layout"><form className="report-form" onSubmit={submitReport}><div className="panel-heading"><div><span className="section-kicker">01 / New report</span><h2>Tell us what went missing</h2></div><div className="required-note">All marked fields required</div></div><div className="form-grid"><label>Item title <input required value={reportState.title} onChange={(event) => updateReport('title', event.target.value)} placeholder="Black leather wallet" /></label><label>Category <select value={reportState.category} onChange={(event) => updateReport('category', event.target.value)}><option>Bag</option><option>Electronics</option><option>Personal item</option><option>Clothing</option><option>Pet</option><option>Keys</option><option>Other</option></select></label><label>Where was it lost? <input required value={reportState.location} onChange={(event) => updateReport('location', event.target.value)} placeholder="Central bus station" /></label><label>Contact email <input type="email" value={reportState.contact_email} onChange={(event) => updateReport('contact_email', event.target.value)} placeholder="you@example.com" /></label><label className="full-field">Description <textarea required value={reportState.description} onChange={(event) => updateReport('description', event.target.value)} placeholder="Color, brand, marks, what was inside, and when you noticed it missing..." rows="5" /></label><label>Contact name <input value={reportState.contact_name} onChange={(event) => updateReport('contact_name', event.target.value)} placeholder="Your name" /></label></div><div className="report-upload"><div><span className="section-kicker">Optional evidence</span><h3>Attach an image of the item</h3><p>A clear photo makes later matching more useful.</p></div>{reportPreview ? <div className="report-preview"><img src={reportPreview} alt="Report item preview" /><button type="button" onClick={() => { reportInputRef.current.value = ''; }}><X size={15} /></button></div> : <button type="button" className="mini-upload" onClick={() => reportInputRef.current?.click()}><ImagePlus size={19} /><span>Choose image</span></button>}<input ref={reportInputRef} type="file" accept="image/jpeg,image/png,image/webp,image/gif" onChange={(event) => handleImageChange(event, 'report')} hidden /></div><button className="primary-button report-submit" disabled={feedback.loading} type="submit">{feedback.loading ? <LoaderCircle className="spin" size={18} /> : <Send size={18} />} {feedback.loading ? 'Saving report' : 'Save lost-item report'} <ArrowUpRight size={17} /></button>{feedback.error && <div className="inline-error"><BadgeAlert size={16} /> {feedback.error}</div>}{feedback.success && <div className="inline-success"><Check size={16} /> {feedback.success}</div>}</form><aside className="report-aside"><div className="aside-number">02</div><span className="section-kicker">Good to know</span><h2>Details make better matches.</h2><p>Your report is stored in the Node API registry. The image search index contains the current known cases; adding this report to FAISS is a separate indexing step.</p><div className="aside-list"><span><Check size={14} /> Use specific colors and brands</span><span><Check size={14} /> Add the last known location</span><span><Check size={14} /> Keep contact details current</span></div></aside></section>;
}

function RegistryView({ reports, onNewReport }) {
  return <section className="registry-section"><div className="section-header"><div><span className="section-kicker">Report registry</span><h2>{reports.length ? `${reports.length} report${reports.length === 1 ? '' : 's'} on file` : 'No reports yet'}</h2></div><button className="primary-button compact" onClick={onNewReport}><FilePlus2 size={16} /> New report</button></div>{reports.length ? <div className="registry-list">{reports.map((report) => <article className="registry-card" key={report.id}><div className="registry-icon"><PackageSearch size={20} /></div><div><h3>{report.title}</h3><p>{report.description}</p><div className="result-tags"><span>{report.category}</span><span><MapPin size={13} /> {report.location}</span></div></div><time>{new Date(report.createdAt).toLocaleDateString()}</time></article>)}</div> : <EmptyResults onNewReport={onNewReport} ran />}</section>;
}

export default App;
