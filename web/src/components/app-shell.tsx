"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import {
  IconLayoutDashboard,
  IconFileText,
  IconChecklist,
  IconDatabase,
  IconAdjustmentsHorizontal,
  IconMenu2,
  IconX,
  IconDeviceDesktop,
  IconSun,
  IconMoon,
} from "@tabler/icons-react";
import { reviewCount } from "@/lib/sample-data";

const nav = [
  { href: "/", label: "Overview", icon: IconLayoutDashboard },
  { href: "/documents", label: "Documents", icon: IconFileText },
  { href: "/review", label: "Review", icon: IconChecklist, count: reviewCount },
  { href: "/factors", label: "Emission factors", icon: IconDatabase },
  { href: "/simulator", label: "What-if simulator", icon: IconAdjustmentsHorizontal },
];

function Mark() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
      <rect x="1" y="1" width="20" height="20" rx="6" fill="var(--pine)" />
      <path d="M6 8h10M6 12h5" stroke="var(--on-pine)" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M12.5 14.5l1.8 1.8 3.2-3.6" stroke="var(--on-pine)" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ThemeSwitch() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const options = [
    { value: "system", label: "System", icon: IconDeviceDesktop },
    { value: "light", label: "Light", icon: IconSun },
    { value: "dark", label: "Dark", icon: IconMoon },
  ];
  return (
    <div role="radiogroup" aria-label="Theme" className="flex rounded-full border border-rule bg-canvas p-0.5">
      {options.map((o) => {
        const active = mounted && theme === o.value;
        return (
          <button
            key={o.value}
            role="radio"
            aria-checked={active}
            aria-label={o.label}
            title={o.label}
            onClick={() => setTheme(o.value)}
            className={`flex h-8 flex-1 items-center justify-center rounded-full transition-colors ${
              active ? "bg-surface text-ink shadow-[0_0_0_1px_var(--rule)]" : "text-ink-2 hover:text-ink"
            }`}
          >
            <o.icon size={16} stroke={1.75} aria-hidden="true" />
          </button>
        );
      })}
    </div>
  );
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <ul className="space-y-0.5">
      {nav.map((item) => {
        const active = pathname === item.href;
        return (
          <li key={item.href}>
            <Link
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={`flex h-9 items-center gap-2.5 rounded-md px-2.5 text-sm font-medium transition-colors ${
                active ? "bg-pine-wash text-pine" : "text-ink-2 hover:bg-canvas hover:text-ink"
              }`}
            >
              <item.icon size={18} stroke={1.75} aria-hidden="true" />
              <span className="flex-1">{item.label}</span>
              {item.count ? (
                <span className="num rounded-full bg-review-wash px-2 text-xs leading-5 text-review-ink">
                  {item.count}
                </span>
              ) : null}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[248px_minmax(0,1fr)]">
      <aside className="hidden border-r border-rule bg-surface lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col">
        <div className="flex h-16 items-center gap-2.5 px-5">
          <Mark />
          <span className="text-[15px] font-semibold tracking-tight">CarbonTrace</span>
        </div>
        <nav aria-label="Main" className="flex-1 px-3 pt-2">
          <NavList />
        </nav>
        <div className="space-y-3 border-t border-rule p-4">
          <div className="text-xs text-ink-2">Acme Components Pvt Ltd</div>
          <ThemeSwitch />
        </div>
      </aside>

      <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-rule bg-surface px-4 lg:hidden">
        <div className="flex items-center gap-2">
          <Mark />
          <span className="text-[15px] font-semibold tracking-tight">CarbonTrace</span>
        </div>
        <button
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="mobile-nav"
          aria-label={open ? "Close menu" : "Open menu"}
          className="flex h-10 w-10 items-center justify-center rounded-md text-ink hover:bg-canvas"
        >
          {open ? <IconX size={20} aria-hidden="true" /> : <IconMenu2 size={20} aria-hidden="true" />}
        </button>
      </header>
      {open ? (
        <div id="mobile-nav" className="sticky top-14 z-10 space-y-4 border-b border-rule bg-surface p-4 lg:hidden">
          <nav aria-label="Main">
            <NavList onNavigate={() => setOpen(false)} />
          </nav>
          <ThemeSwitch />
        </div>
      ) : null}

      <main id="main" tabIndex={-1} className="min-w-0 scroll-mt-16 outline-none">
        {children}
      </main>
    </div>
  );
}
