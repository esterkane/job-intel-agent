type Props = {
  profile: Record<string, unknown> | null;
};

export function Settings({ profile }: Props) {
  const positive = (profile?.positive_keywords as string[] | undefined) ?? [];
  const negative = (profile?.negative_keywords as string[] | undefined) ?? [];
  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <section className="rounded border border-line bg-white p-5">
        <h2 className="mb-3 text-xl font-semibold">Target Profile</h2>
        <p className="text-sm text-slate-700">{String(profile?.headline ?? 'Profile loads from config/profile.yaml.')}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {((profile?.target_role_families as string[] | undefined) ?? []).map((role) => (
            <span key={role} className="rounded border border-line px-2 py-1 text-xs">{role}</span>
          ))}
        </div>
      </section>
      <section className="rounded border border-line bg-white p-5">
        <h2 className="mb-3 text-xl font-semibold">LLM Providers</h2>
        <p className="text-sm text-slate-700">Core ranking uses deterministic scoring and local config. Ollama and OpenAI are disabled unless configured through environment variables.</p>
        <div className="mt-4 rounded bg-mist p-3 text-sm text-slate-700">Set <code>LLM_PROVIDER=ollama</code> for local summaries or <code>LLM_PROVIDER=openai</code> with <code>OPENAI_API_KEY</code> if you intentionally accept separate API billing.</div>
      </section>
      <section className="rounded border border-line bg-white p-5">
        <h2 className="mb-3 text-xl font-semibold">Positive Keywords</h2>
        <div className="flex flex-wrap gap-2">{positive.map((kw) => <span key={kw} className="rounded bg-emerald-50 px-2 py-1 text-xs text-fern">{kw}</span>)}</div>
      </section>
      <section className="rounded border border-line bg-white p-5">
        <h2 className="mb-3 text-xl font-semibold">Excluded Keywords</h2>
        <div className="flex flex-wrap gap-2">{negative.map((kw) => <span key={kw} className="rounded bg-orange-50 px-2 py-1 text-xs text-signal">{kw}</span>)}</div>
      </section>
      <section className="rounded border border-line bg-white p-5 lg:col-span-2">
        <h2 className="mb-3 text-xl font-semibold">Notifications</h2>
        <p className="text-sm text-slate-700">Placeholder for local email, desktop, or webhook notifications. No outbound notification service is configured in this MVP.</p>
      </section>
    </div>
  );
}
