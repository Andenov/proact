"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Dashboard", icon: "⬛" },
  { href: "/alerts", label: "Alerts", icon: "🔔" },
  { href: "/farmers", label: "Farmers", icon: "🌾" },
  { href: "/storage", label: "Grain Storage", icon: "🏚" },
  { href: "/sms", label: "SMS Logs", icon: "💬" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-slate-900 text-white flex flex-col shrink-0">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-slate-700">
        <div className="text-xl font-bold tracking-wide text-emerald-400">PROACT</div>
        <div className="text-xs text-slate-400 mt-0.5">Anticipatory Action Platform</div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1 px-3">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? "bg-emerald-600 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-slate-700 text-xs text-slate-500">
        Uganda Pilot · v0.1.0
      </div>
    </aside>
  );
}
