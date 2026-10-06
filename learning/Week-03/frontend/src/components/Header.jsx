import { NavLink, Outlet, Link } from 'react-router-dom';

const NAV = [
  { to: '/', label: 'Search' },
  { to: '/new-report', label: 'New report' },
  { to: '/reports', label: 'All reports' },
];

export default function Header() {
  return (
    <header className="bg-slate-900 text-white">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-500 grid place-items-center font-bold">
            L
          </span>
          <span className="font-semibold tracking-tight">Lostify AI</span>
        </Link>

        <nav className="flex gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  isActive ? 'bg-white/15 text-white' : 'text-slate-300 hover:text-white hover:bg-white/10'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}