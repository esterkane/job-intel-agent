import { useState, type FormEvent } from 'react';
import type { Job, ManualCapturePayload } from '../types';

type Props = {
  onSubmit: (payload: ManualCapturePayload) => Promise<Job>;
};

const emptyForm: ManualCapturePayload = {
  url: '',
  title: '',
  company: '',
  location: '',
  description: '',
  notes: '',
};

export function ManualCapture({ onSubmit }: Props) {
  const [form, setForm] = useState<ManualCapturePayload>(emptyForm);
  const [result, setResult] = useState<Job | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const job = await onSubmit({
        ...form,
        company: form.company || 'Manual',
        url: form.url || undefined,
        location: form.location || undefined,
      });
      setResult(job);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Manual capture failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold">Manual Capture</h2>
        <p className="text-sm text-slate-600">Paste a role from LinkedIn, Indeed, Glassdoor, Wellfound, or another manual-only source and score it locally.</p>
      </div>
      <form onSubmit={submit} className="grid gap-4 rounded border border-line bg-white p-4">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="grid gap-1 text-sm font-medium">
            Title
            <input required className="rounded border border-line px-3 py-2 font-normal" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Company
            <input className="rounded border border-line px-3 py-2 font-normal" value={form.company} onChange={(event) => setForm({ ...form, company: event.target.value })} />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Location / remote policy
            <input className="rounded border border-line px-3 py-2 font-normal" placeholder="Remote Germany, Remote EU, EMEA..." value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Job URL
            <input className="rounded border border-line px-3 py-2 font-normal" value={form.url} onChange={(event) => setForm({ ...form, url: event.target.value })} />
          </label>
        </div>
        <label className="grid gap-1 text-sm font-medium">
          Description
          <textarea required className="min-h-56 rounded border border-line px-3 py-2 font-normal" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
        </label>
        <label className="grid gap-1 text-sm font-medium">
          Notes
          <textarea className="min-h-24 rounded border border-line px-3 py-2 font-normal" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
        </label>
        {error && <div className="rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
        <button disabled={busy} className="w-fit rounded bg-fern px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
          {busy ? 'Scoring...' : 'Score and save'}
        </button>
      </form>
      {result && (
        <section className="rounded border border-line bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="font-semibold">{result.title}</h3>
              <p className="text-sm text-slate-600">{result.company} · {result.location ?? 'Location unclear'}</p>
            </div>
            <div className="rounded bg-mist px-3 py-2 text-lg font-semibold text-fern">{result.final_score}</div>
          </div>
          <p className="mt-3 text-sm">{result.why_this_matches}</p>
          <p className="mt-2 text-sm text-slate-600">{result.concerns}</p>
        </section>
      )}
    </div>
  );
}
