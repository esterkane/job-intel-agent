import { Copy, ExternalLink } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { SearchQueryVariant } from '../types';

type Props = {
  queries: SearchQueryVariant[];
};

const modeLabels: Record<string, string> = {
  api_filter_locally: 'API, filter locally',
  public_scrape_or_manual: 'Public/manual',
  manual_only: 'Manual-only',
};

export function SearchStrategy({ queries }: Props) {
  const [enabled, setEnabled] = useState<Record<string, boolean>>({});
  const [platformFilter, setPlatformFilter] = useState('');

  const hydrated = useMemo(() => queries.map((query) => ({
    ...query,
    enabled: enabled[query.id] ?? query.enabled,
  })), [enabled, queries]);

  const platforms = useMemo(() => [...new Set(queries.map((query) => query.platform))].sort(), [queries]);
  const visible = hydrated.filter((query) => !platformFilter || query.platform === platformFilter);
  const grouped = useMemo(() => {
    const map = new Map<string, SearchQueryVariant[]>();
    visible.forEach((query) => {
      map.set(query.platform, [...(map.get(query.platform) ?? []), query]);
    });
    return [...map.entries()];
  }, [visible]);

  async function copy(text: string) {
    await navigator.clipboard.writeText(text);
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Search Strategy</h2>
          <p className="text-sm text-slate-600">Generated platform queries for Brian's AI search, RAG, knowledge systems, automation, and advisory targets.</p>
        </div>
        <label className="grid gap-1 text-sm">
          Platform
          <select className="rounded border border-line px-3 py-2" value={platformFilter} onChange={(event) => setPlatformFilter(event.target.value)}>
            <option value="">All</option>
            {platforms.map((platform) => <option key={platform} value={platform}>{platform}</option>)}
          </select>
        </label>
      </div>

      <div className="grid gap-4">
        {grouped.map(([platform, items]) => (
          <section key={platform} className="rounded border border-line bg-white">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
              <h3 className="font-semibold">{platform}</h3>
              <span className="text-sm text-slate-500">{items.length} queries</span>
            </div>
            <div className="divide-y divide-line">
              {items.map((item) => (
                <div key={item.id} className={`grid gap-3 px-4 py-3 ${item.enabled ? '' : 'opacity-55'}`}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <label className="inline-flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={item.enabled}
                            onChange={(event) => setEnabled((current) => ({ ...current, [item.id]: event.target.checked }))}
                          />
                          <span className="font-medium">{item.query_name}</span>
                        </label>
                        <span className="rounded bg-mist px-2 py-1 text-xs text-fern">{modeLabels[item.mode] ?? item.mode}</span>
                        <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">{item.language}</span>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">{item.role_family} · {item.query_type}</p>
                    </div>
                    <div className="flex gap-2">
                      <button className="inline-flex items-center gap-1 rounded border border-line px-3 py-2 text-sm hover:border-fern" onClick={() => copy(item.query)}>
                        <Copy size={14} /> Copy
                      </button>
                      {item.url && (
                        <button className="inline-flex items-center gap-1 rounded border border-fern px-3 py-2 text-sm text-fern hover:bg-mist" onClick={() => window.open(item.url ?? '', '_blank', 'noopener,noreferrer')}>
                          <ExternalLink size={14} /> Open
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="rounded bg-slate-50 p-3 font-mono text-xs text-slate-700">{item.query}</div>
                  <div className="flex flex-wrap gap-2 text-xs">
                    {item.supported_features.map((feature) => <span key={feature} className="rounded bg-slate-100 px-2 py-1 text-slate-600">{feature.replaceAll('_', ' ')}</span>)}
                    {item.negative_keywords.length > 0 && <span className="rounded bg-rose-50 px-2 py-1 text-rose-700">negative filters: {item.negative_keywords.join(', ')}</span>}
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
