import { BarChart3, BriefcaseBusiness, Building2, ClipboardEdit, Settings, Sparkles } from 'lucide-react';

type Props = {
  active: string;
  setActive: (page: string) => void;
  children: React.ReactNode;
};

const nav = [
  { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { id: 'jobs', label: 'Jobs', icon: BriefcaseBusiness },
  { id: 'sources', label: 'Sources', icon: Building2 },
  { id: 'manual', label: 'Manual Capture', icon: ClipboardEdit },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export function Layout({ active, setActive, children }: Props) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded bg-fern text-white">
              <Sparkles size={20} />
            </div>
            <div>
              <h1 className="text-lg font-semibold leading-tight">Job Intel Agent</h1>
              <p className="text-sm text-slate-600">Local-first strategic job discovery for Brian</p>
            </div>
          </div>
          <nav className="flex flex-wrap gap-2">
            {nav.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  className={`flex items-center gap-2 rounded border px-3 py-2 text-sm ${active === item.id ? 'border-fern bg-mist text-fern' : 'border-line bg-white text-slate-700 hover:border-fern'}`}
                  onClick={() => setActive(item.id)}
                  title={item.label}
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-5 py-6">{children}</main>
    </div>
  );
}
