import type { CSSProperties } from 'react';
import { ExternalLink, Eye, Search } from 'lucide-react';
import type { Job } from '../types';

type Props = {
  jobs: Job[];
  selected: Job | null;
  setSelected: (job: Job) => void;
  onUpdate: (id: number, payload: Partial<Job>) => Promise<void>;
  filters: { minScore: string; status: string; company: string };
  setFilters: (filters: { minScore: string; status: string; company: string }) => void;
};

export function Jobs({ jobs, selected, setSelected, onUpdate, filters, setFilters }: Props) {
  const companies = Array.from(new Set(jobs.map((job) => job.company))).sort();
  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
      <section className="space-y-4">
        <div className="rounded border border-line bg-white p-4">
          <div className="grid gap-3 md:grid-cols-4">
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Minimum score</span>
              <input className="w-full rounded border border-line px-3 py-2" value={filters.minScore} onChange={(e) => setFilters({ ...filters, minScore: e.target.value })} placeholder="70" />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Company</span>
              <select className="w-full rounded border border-line px-3 py-2" value={filters.company} onChange={(e) => setFilters({ ...filters, company: e.target.value })}>
                <option value="">All</option>
                {companies.map((company) => <option key={company}>{company}</option>)}
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-slate-600">Status</span>
              <select className="w-full rounded border border-line px-3 py-2" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
                <option value="">All</option>
                {['new', 'seen', 'saved', 'ignored', 'applied', 'expired'].map((status) => <option key={status}>{status}</option>)}
              </select>
            </label>
            <div className="flex items-end">
              <div className="flex h-10 items-center gap-2 text-sm text-slate-600"><Search size={16} /> {jobs.length} roles loaded</div>
            </div>
          </div>
        </div>
        <div className="overflow-hidden rounded border border-line bg-white">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-mist text-xs uppercase text-slate-600">
              <tr>
                <th className="px-3 py-3">Score</th>
                <th className="px-3 py-3">Title</th>
                <th className="px-3 py-3">Company</th>
                <th className="px-3 py-3">Remote</th>
                <th className="px-3 py-3">Role family</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {jobs.map((job) => (
                <tr key={job.id} className={selected?.id === job.id ? 'bg-emerald-50' : ''}>
                  <td className="px-3 py-3 font-semibold text-fern">{job.final_score}</td>
                  <td className="max-w-sm px-3 py-3">
                    <button className="text-left font-medium hover:text-fern" onClick={() => setSelected(job)}>{job.title}</button>
                    <div className="text-xs text-slate-500">{job.location ?? 'Location unclear'}</div>
                  </td>
                  <td className="px-3 py-3">{job.company}</td>
                  <td className="px-3 py-3">{job.remote_type ?? job.region ?? 'Check'}</td>
                  <td className="px-3 py-3">{job.role_family}</td>
                  <td className="px-3 py-3">{job.status}</td>
                  <td className="px-3 py-3">
                    <div className="flex gap-2">
                      <button title="View" onClick={() => setSelected(job)} className="rounded border border-line p-2 hover:border-fern"><Eye size={15} /></button>
                      <a title="Open original" href={job.job_url} target="_blank" rel="noreferrer" className="rounded border border-line p-2 hover:border-fern"><ExternalLink size={15} /></a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {jobs.length === 0 && <div className="p-6 text-sm text-slate-600">No jobs yet. Run a scrape from the dashboard or sources page.</div>}
        </div>
      </section>
      <JobDetail job={selected} onUpdate={onUpdate} />
    </div>
  );
}

function JobDetail({ job, onUpdate }: { job: Job | null; onUpdate: (id: number, payload: Partial<Job>) => Promise<void> }) {
  if (!job) {
    return <aside className="rounded border border-line bg-white p-5 text-sm text-slate-600">Select a job to inspect score breakdown, concerns, and application angle.</aside>;
  }
  return (
    <aside className="space-y-4 rounded border border-line bg-white p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold">{job.title}</h3>
          <p className="text-sm text-slate-600">{job.company} - {job.location ?? 'Location unclear'}</p>
        </div>
        <div className="score-ring grid h-16 w-16 shrink-0 place-items-center rounded-full" style={{ '--score': job.final_score } as CSSProperties}>
          <div className="grid h-12 w-12 place-items-center rounded-full bg-white text-sm font-semibold">{job.final_score}</div>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {['saved', 'ignored', 'applied', 'seen'].map((status) => (
          <button key={status} onClick={() => onUpdate(job.id, { status })} className="rounded border border-line px-3 py-2 text-sm hover:border-fern">{status}</button>
        ))}
      </div>
      <Info title="Why this matches" body={job.why_this_matches} />
      <Info title="Concerns" body={job.concerns} />
      <Info title="Application angle" body={job.suggested_application_angle} />
      <Info title="CV emphasis" body={job.suggested_cv_emphasis} />
      <div>
        <h4 className="mb-2 text-sm font-semibold">Score breakdown</h4>
        <div className="space-y-2">
          {Object.entries(job.score_breakdown).map(([key, value]) => (
            <div key={key}>
              <div className="mb-1 flex justify-between text-xs text-slate-600"><span>{key.split('_').join(' ')}</span><span>{Math.round(value)}</span></div>
              <div className="h-2 rounded bg-mist"><div className="h-2 rounded bg-fern" style={{ width: `${Math.min(value, 100)}%` }} /></div>
            </div>
          ))}
        </div>
      </div>
      <label className="block text-sm">
        <span className="mb-1 block font-semibold">Notes</span>
        <textarea className="min-h-24 w-full rounded border border-line p-3" defaultValue={job.notes ?? ''} onBlur={(e) => onUpdate(job.id, { notes: e.target.value })} />
      </label>
      <Info title="Original description" body={job.description} long />
    </aside>
  );
}

function Info({ title, body, long = false }: { title: string; body: string | null; long?: boolean }) {
  return (
    <div>
      <h4 className="mb-1 text-sm font-semibold">{title}</h4>
      <p className={`text-sm text-slate-700 ${long ? 'max-h-72 overflow-auto whitespace-pre-wrap rounded border border-line bg-slate-50 p-3' : ''}`}>{body ?? 'No data yet.'}</p>
    </div>
  );
}

