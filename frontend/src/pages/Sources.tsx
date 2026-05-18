import { ExternalLink, Play, Power, RefreshCw } from 'lucide-react';
import type { Source } from '../types';

type Props = {
  sources: Source[];
  onToggle: (source: Source) => Promise<void>;
  onRunSource: (id: number, fresh?: boolean) => Promise<void>;
  busySourceId: number | null;
  scrapeMessage: string | null;
};

export function Sources({ sources, onToggle, onRunSource, busySourceId, scrapeMessage }: Props) {
  return (
    <div className="space-y-3">
      {scrapeMessage && (
        <div className="rounded border border-fern/30 bg-emerald-50 px-4 py-3 text-sm text-emerald-950">
          {scrapeMessage}
        </div>
      )}
      <div className="overflow-hidden rounded border border-line bg-white">
        <table className="w-full text-left text-sm">
        <thead className="bg-mist text-xs uppercase text-slate-600">
          <tr>
            <th className="px-3 py-3">Enabled</th>
            <th className="px-3 py-3">Source</th>
            <th className="px-3 py-3">Adapter</th>
            <th className="px-3 py-3">Priority</th>
            <th className="px-3 py-3">Last status</th>
            <th className="px-3 py-3">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {sources.map((source) => {
            const isBusy = busySourceId === source.id;
            return (
            <tr key={source.id} className={isBusy ? 'bg-emerald-50/60' : ''}>
              <td className="px-3 py-3">
                <button title="Toggle source" onClick={() => onToggle(source)} className={`rounded border p-2 ${source.enabled ? 'border-fern text-fern' : 'border-line text-slate-500'}`}>
                  <Power size={16} />
                </button>
              </td>
              <td className="px-3 py-3">
                <div className="font-medium">{source.company_name}</div>
                <div className="max-w-xl truncate text-xs text-slate-500">{source.remote_policy_notes}</div>
                {source.last_error && <div className="max-w-xl truncate text-xs text-red-700">{source.last_error}</div>}
              </td>
              <td className="px-3 py-3">{source.adapter_type}</td>
              <td className="px-3 py-3">{source.priority}</td>
              <td className="px-3 py-3">{source.last_status ?? 'never'}</td>
              <td className="px-3 py-3">
                <div className="flex gap-2">
                  <button disabled={isBusy} title="Run incremental scrape" onClick={() => onRunSource(source.id, false)} className="rounded border border-line p-2 hover:border-fern disabled:cursor-not-allowed disabled:opacity-60"><Play size={16} /></button>
                  <button disabled={isBusy} title="Fresh overwrite this source" onClick={() => onRunSource(source.id, true)} className="rounded border border-line p-2 text-fern hover:border-fern disabled:cursor-not-allowed disabled:opacity-60"><RefreshCw size={16} className={isBusy ? 'animate-spin' : ''} /></button>
                  <a title="Open source" href={source.career_url} target="_blank" rel="noreferrer" className="rounded border border-line p-2 hover:border-fern"><ExternalLink size={16} /></a>
                </div>
              </td>
            </tr>
          );})}
        </tbody>
      </table>
      </div>
    </div>
  );
}
