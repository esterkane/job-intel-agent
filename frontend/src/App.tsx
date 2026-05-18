import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from './api/client';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Jobs } from './pages/Jobs';
import { Settings } from './pages/Settings';
import { Sources } from './pages/Sources';
import type { Job, ScrapeRun, Source, Stats } from './types';

export default function App() {
  const [active, setActive] = useState('dashboard');
  const [stats, setStats] = useState<Stats | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [runs, setRuns] = useState<ScrapeRun[]>([]);
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [selected, setSelected] = useState<Job | null>(null);
  const [filters, setFilters] = useState({ minScore: '', status: '', company: '' });
  const [scrapeMessage, setScrapeMessage] = useState<string | null>(null);
  const [isScraping, setIsScraping] = useState(false);
  const [busySourceId, setBusySourceId] = useState<number | null>(null);
  const [pollUntil, setPollUntil] = useState<number | null>(null);

  const load = useCallback(async () => {
    const [statsData, jobsData, sourcesData, runsData, profileData] = await Promise.all([
      api.stats(),
      api.jobs(),
      api.sources(),
      api.runs(),
      api.profile(),
    ]);
    setStats(statsData);
    setJobs(jobsData);
    setSources(sourcesData);
    setRuns(runsData);
    setProfile(profileData);
    setSelected((current) => current ?? jobsData[0] ?? null);
  }, []);

  useEffect(() => {
    load().catch(console.error);
  }, [load]);

  useEffect(() => {
    if (!pollUntil) return;
    const timer = window.setInterval(() => {
      load().catch(console.error);
      if (Date.now() > pollUntil) {
        window.clearInterval(timer);
        setPollUntil(null);
        setIsScraping(false);
        setScrapeMessage('Scrape finished. Results are refreshed.');
      }
    }, 2500);
    return () => window.clearInterval(timer);
  }, [load, pollUntil]);

  const visibleJobs = useMemo(() => jobs.filter((job) => {
    if (filters.minScore && job.final_score < Number(filters.minScore)) return false;
    if (filters.status && job.status !== filters.status) return false;
    if (filters.company && job.company !== filters.company) return false;
    return true;
  }), [jobs, filters]);

  async function updateJob(id: number, payload: Partial<Job>) {
    const updated = await api.updateJob(id, payload);
    setJobs((items) => items.map((item) => item.id === id ? updated : item));
    setSelected(updated);
    setStats(await api.stats());
  }

  async function runScrape(fresh = false) {
    setIsScraping(true);
    setScrapeMessage(fresh ? 'Fresh overwrite queued. Old unsaved results are being replaced.' : 'Incremental scrape queued. Checking enabled sources.');
    const result = await api.runScrape(fresh);
    setScrapeMessage(`${fresh ? 'Fresh overwrite' : 'Incremental scrape'} running: ${result.queued} sources queued${fresh ? `, ${result.deleted} old rows removed` : ''}.`);
    setPollUntil(Date.now() + 60000);
    await load();
  }

  async function runSource(id: number, fresh = false) {
    setBusySourceId(id);
    setScrapeMessage(fresh ? 'Fresh source overwrite running.' : 'Source scrape running.');
    try {
      const run = await api.runSource(id, fresh);
      setScrapeMessage(`${fresh ? 'Fresh source overwrite' : 'Source scrape'} finished: ${run.jobs_found} found, ${run.jobs_new} new, ${run.jobs_updated} updated.`);
      await load();
    } finally {
      setBusySourceId(null);
    }
  }

  async function toggleSource(source: Source) {
    await api.updateSource(source.id, { enabled: !source.enabled });
    await load();
  }

  return (
    <Layout active={active} setActive={setActive}>
      {active === 'dashboard' && <Dashboard stats={stats} runs={runs} onRunScrape={runScrape} scrapeMessage={scrapeMessage} isScraping={isScraping} />}
      {active === 'jobs' && <Jobs jobs={visibleJobs} selected={selected} setSelected={setSelected} onUpdate={updateJob} filters={filters} setFilters={setFilters} />}
      {active === 'sources' && <Sources sources={sources} onToggle={toggleSource} onRunSource={runSource} busySourceId={busySourceId} scrapeMessage={scrapeMessage} />}
      {active === 'settings' && <Settings profile={profile} />}
    </Layout>
  );
}
