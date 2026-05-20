import { ExternalLink, Plus, Trash2 } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';
import type { Job, ManualCapturePayload, SavedSearch, SavedSearchPayload, Source } from '../types';

type Props = {
  savedSearches: SavedSearch[];
  sources: Source[];
  onOpenSavedSearch: (id: number) => Promise<void>;
  onCreateSavedSearch: (payload: SavedSearchPayload) => Promise<void>;
  onDeleteSavedSearch: (id: number) => Promise<void>;
  onManualCapture: (payload: ManualCapturePayload) => Promise<Job>;
};

const emptyCapture: ManualCapturePayload = {
  url: '',
  title: '',
  company: '',
  location: '',
  description: '',
  notes: '',
};

const emptySavedSearch: SavedSearchPayload = {
  platform: '',
  query_name: '',
  role_family: '',
  url: '',
  region: 'Germany/EU',
  remote_filter: 'remote/manual',
  enabled: true,
  notes: '',
};

export function BrowserAssistant({ savedSearches, sources, onOpenSavedSearch, onCreateSavedSearch, onDeleteSavedSearch, onManualCapture }: Props) {
  const [capture, setCapture] = useState<ManualCapturePayload>(emptyCapture);
  const [savedForm, setSavedForm] = useState<SavedSearchPayload>(emptySavedSearch);
  const [result, setResult] = useState<Job | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const browserAllowedSources = useMemo(() => sources.filter((source) => source.source_type === 'browser_allowed' && source.enabled), [sources]);
  const grouped = useMemo(() => {
    const map = new Map<string, SavedSearch[]>();
    savedSearches.filter((item) => item.enabled).forEach((item) => {
      map.set(item.platform, [...(map.get(item.platform) ?? []), item]);
    });
    return [...map.entries()];
  }, [savedSearches]);

  async function submitCapture(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy('capture');
    setMessage(null);
    try {
      const job = await onManualCapture({
        ...capture,
        company: capture.company || 'Manual',
        url: capture.url || undefined,
        location: capture.location || undefined,
      });
      setResult(job);
      setMessage('Manual capture saved and scored locally.');
    } finally {
      setBusy(null);
    }
  }

  async function submitSavedSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy('saved-search');
    try {
      await onCreateSavedSearch(savedForm);
      setSavedForm(emptySavedSearch);
      setMessage('Saved search added.');
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Browser Assistant</h2>
        <p className="text-sm text-slate-600">Open saved searches, review manually, then paste promising jobs for local scoring. No logged-in scraping or auto-apply.</p>
      </div>

      {message && <div className="rounded border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div>}

      <section className="rounded border border-line bg-white p-4">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold">Saved Searches</h3>
            <p className="text-sm text-slate-600">Buttons open the saved-search URL in your browser. The app does not scrape the results page.</p>
          </div>
        </div>
        <div className="grid gap-4">
          {grouped.map(([platform, items]) => (
            <div key={platform} className="rounded border border-line p-3">
              <h4 className="mb-2 text-sm font-semibold text-slate-700">{platform}</h4>
              <div className="grid gap-2">
                {items.map((item) => (
                  <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded bg-slate-50 px-3 py-2">
                    <div className="min-w-0">
                      <p className="font-medium">{item.query_name}</p>
                      <p className="text-xs text-slate-600">{item.role_family ?? 'Role family unset'} · {item.region ?? 'Region unset'} · {item.remote_filter ?? 'Filter unset'}</p>
                      {item.notes && <p className="mt-1 text-xs text-slate-500">{item.notes}</p>}
                    </div>
                    <div className="flex gap-2">
                      <button className="inline-flex items-center gap-2 rounded border border-fern px-3 py-2 text-sm text-fern hover:bg-mist" onClick={() => onOpenSavedSearch(item.id)}>
                        <ExternalLink size={15} /> Open
                      </button>
                      <button className="rounded border border-line p-2 text-slate-500 hover:border-rose-300 hover:text-rose-700" title="Delete saved search" onClick={() => onDeleteSavedSearch(item.id)}>
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <form onSubmit={submitSavedSearch} className="mt-4 grid gap-3 rounded border border-dashed border-line p-3">
          <div className="grid gap-3 md:grid-cols-3">
            <input required className="rounded border border-line px-3 py-2 text-sm" placeholder="Platform" value={savedForm.platform} onChange={(event) => setSavedForm({ ...savedForm, platform: event.target.value })} />
            <input required className="rounded border border-line px-3 py-2 text-sm" placeholder="Query name" value={savedForm.query_name} onChange={(event) => setSavedForm({ ...savedForm, query_name: event.target.value })} />
            <input className="rounded border border-line px-3 py-2 text-sm" placeholder="Role family" value={savedForm.role_family ?? ''} onChange={(event) => setSavedForm({ ...savedForm, role_family: event.target.value })} />
          </div>
          <input required className="rounded border border-line px-3 py-2 text-sm" placeholder="https://..." value={savedForm.url} onChange={(event) => setSavedForm({ ...savedForm, url: event.target.value })} />
          <div className="grid gap-3 md:grid-cols-3">
            <input className="rounded border border-line px-3 py-2 text-sm" placeholder="Region" value={savedForm.region ?? ''} onChange={(event) => setSavedForm({ ...savedForm, region: event.target.value })} />
            <input className="rounded border border-line px-3 py-2 text-sm" placeholder="Remote filter" value={savedForm.remote_filter ?? ''} onChange={(event) => setSavedForm({ ...savedForm, remote_filter: event.target.value })} />
            <input className="rounded border border-line px-3 py-2 text-sm" placeholder="Notes" value={savedForm.notes ?? ''} onChange={(event) => setSavedForm({ ...savedForm, notes: event.target.value })} />
          </div>
          <button disabled={busy === 'saved-search'} className="inline-flex w-fit items-center gap-2 rounded bg-fern px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
            <Plus size={15} /> {busy === 'saved-search' ? 'Adding...' : 'Add saved search'}
          </button>
        </form>
      </section>

      <section className="rounded border border-line bg-white p-4">
        <h3 className="font-semibold">Manual Capture</h3>
        <form onSubmit={submitCapture} className="mt-4 grid gap-4">
          <div className="grid gap-4 md:grid-cols-2">
            <input required className="rounded border border-line px-3 py-2" placeholder="Title" value={capture.title} onChange={(event) => setCapture({ ...capture, title: event.target.value })} />
            <input className="rounded border border-line px-3 py-2" placeholder="Company" value={capture.company} onChange={(event) => setCapture({ ...capture, company: event.target.value })} />
            <input className="rounded border border-line px-3 py-2" placeholder="Location / remote policy" value={capture.location} onChange={(event) => setCapture({ ...capture, location: event.target.value })} />
            <input className="rounded border border-line px-3 py-2" placeholder="Job URL" value={capture.url} onChange={(event) => setCapture({ ...capture, url: event.target.value })} />
          </div>
          <textarea required className="min-h-48 rounded border border-line px-3 py-2" placeholder="Paste job description" value={capture.description} onChange={(event) => setCapture({ ...capture, description: event.target.value })} />
          <textarea className="min-h-20 rounded border border-line px-3 py-2" placeholder="Notes" value={capture.notes} onChange={(event) => setCapture({ ...capture, notes: event.target.value })} />
          <button disabled={busy === 'capture'} className="w-fit rounded bg-fern px-4 py-2 text-sm font-medium text-white disabled:opacity-60">{busy === 'capture' ? 'Scoring...' : 'Submit and score'}</button>
        </form>
        {result && (
          <div className="mt-4 rounded border border-line bg-slate-50 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="font-semibold">{result.title}</p>
                <p className="text-sm text-slate-600">{result.company} - {result.location ?? 'Location unclear'} - {result.role_family}</p>
              </div>
              <span className="rounded bg-mist px-3 py-2 font-semibold text-fern">{result.final_score}</span>
            </div>
            <p className="mt-2 text-sm">{result.why_this_matches}</p>
          </div>
        )}
      </section>

      {browserAllowedSources.length > 0 && (
        <section className="rounded border border-amber-200 bg-amber-50 p-4">
          <h3 className="font-semibold text-amber-900">Optional Browser Session</h3>
          <p className="mt-1 text-sm text-amber-900">Only sources explicitly marked `browser_allowed` appear here. Login is manual, credentials are not stored by the app, and extraction must be limited to permitted current/public pages.</p>
          <div className="mt-3 grid gap-2">
            {browserAllowedSources.map((source) => (
              <div key={source.id} className="rounded border border-amber-200 bg-white px-3 py-2 text-sm">
                {source.company_name}: {source.remote_policy_notes ?? 'Review terms before use.'}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
