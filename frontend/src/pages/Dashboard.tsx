import { AlertTriangle, Bookmark, CheckCircle2, Play, RefreshCw, Search } from 'lucide-react';
import type { ScrapeRun, Stats } from '../types';

type Props = {
  stats: Stats | null;
  runs: ScrapeRun[];
  onRunScrape: (fresh?: boolean) => Promise<void>;
  scrapeMessage: string | null;
  isScraping: boolean;
};

export function Dashboard({ stats, runs, onRunScrape, scrapeMessage, isScraping }: Props) {
  const cards = [
    { label: 'Jobs found', value: stats?.jobs_found_today ?? 0, icon: Search },
    { label: 'New high-fit', value: stats?.new_high_fit_jobs ?? 0, icon: AlertTriangle },
    { label: 'Saved', value: stats?.saved_jobs ?? 0, icon: Bookmark },
    { label: 'Applied', value: stats?.applied_jobs ?? 0, icon: CheckCircle2 },
    { label: 'Source errors', value: stats?.sources_with_errors ?? 0, icon: AlertTriangle },
  ];
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">Daily Discovery</h2>
          <p className="text-sm text-slate-600">Ranked remote-friendly strategic roles, without auto-applying.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button disabled={isScraping} onClick={() => onRunScrape(false)} className="flex items-center gap-2 rounded bg-fern px-4 py-2 text-sm font-medium text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60">
            <Play size={16} /> {isScraping ? 'Running...' : 'Run incremental'}
          </button>
          <button disabled={isScraping} onClick={() => onRunScrape(true)} className="flex items-center gap-2 rounded border border-fern px-4 py-2 text-sm font-medium text-fern hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-60">
            <RefreshCw size={16} /> Fresh overwrite
          </button>
        </div>
      </div>
      {scrapeMessage && (
        <div className="rounded border border-fern/30 bg-emerald-50 px-4 py-3 text-sm text-emerald-950">
          <div className="flex items-center gap-2">
            <RefreshCw size={16} className={isScraping ? 'animate-spin' : ''} />
            <span>{scrapeMessage}</span>
          </div>
        </div>
      )}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.label} className="rounded border border-line bg-white p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">{card.label}</span>
                <Icon size={18} className="text-fern" />
              </div>
              <div className="mt-3 text-3xl font-semibold">{card.value}</div>
            </div>
          );
        })}
      </section>
      <section className="rounded border border-line bg-white">
        <div className="border-b border-line px-4 py-3">
          <h3 className="font-semibold">Scrape Status</h3>
        </div>
        <div className="divide-y divide-line">
          {runs.slice(0, 8).map((run) => (
            <div key={run.id} className="grid gap-3 px-4 py-3 text-sm md:grid-cols-5">
              <span className="font-medium">Run #{run.id}</span>
              <span>{new Date(run.started_at).toLocaleString()}</span>
              <span className={run.status === 'error' ? 'text-red-700' : 'text-fern'}>{run.status}</span>
              <span>{run.jobs_found} found, {run.jobs_new} new</span>
              <span className="truncate text-slate-600">{run.error_message ?? 'OK'}</span>
            </div>
          ))}
          {runs.length === 0 && <div className="px-4 py-6 text-sm text-slate-600">No scrape runs yet.</div>}
        </div>
      </section>
    </div>
  );
}
