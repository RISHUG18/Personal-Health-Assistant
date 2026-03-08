/* Navigation sidebar for desktop; bottom bar for mobile */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  Bell,
  MessageCircle,
  User,
  Stethoscope,
  Leaf,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/trends", label: "Trends", icon: TrendingUp },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/chat", label: "AI Chat", icon: MessageCircle },
  { href: "/environment", label: "Environment", icon: Leaf },
  { href: "/doctor", label: "Doctor View", icon: Stethoscope },
  { href: "/profile", label: "Profile", icon: User },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden md:flex flex-col w-60 bg-slate-900/95 border-r border-slate-800/80 min-h-screen py-6 px-3 gap-1 backdrop-blur-sm">
      <AppLogo />
      <div className="divider mt-5 mb-4 mx-1" />
      <nav className="flex flex-col gap-0.5">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
                active
                  ? "nav-active text-white shadow-md"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/70"
              )}
            >
              <Icon size={16} className={active ? "text-white" : "text-slate-500"} />
              {label}
              {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-white/60" />}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto pt-4">
        <div className="mx-1 divider mb-4" />
        <div className="px-3 py-2 rounded-xl bg-blue-950/40 border border-blue-800/30">
          <p className="text-[10px] text-blue-400 font-semibold uppercase tracking-wider mb-0.5">v1.0 MVP</p>
          <p className="text-[10px] text-slate-500">Gemini 2.5 Flash · pgvector</p>
        </div>
      </div>
    </aside>
  );
}

export function BottomNav() {
  const pathname = usePathname();
  const mobileItems = NAV_ITEMS.slice(0, 5);
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex md:hidden bg-slate-900/95 border-t border-slate-800/80 backdrop-blur-sm">
      {mobileItems.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex-1 flex flex-col items-center gap-0.5 py-2.5 text-[10px] font-medium transition-all",
              active ? "text-blue-400" : "text-slate-500 hover:text-slate-200"
            )}
          >
            <span className={cn(
              "p-1.5 rounded-lg transition-all",
              active ? "bg-blue-600/20" : ""
            )}>
              <Icon size={17} />
            </span>
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppLogo() {
  return (
    <div className="flex items-center gap-2.5 px-3">
      <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-900/40">
        <span className="text-white font-bold text-sm">H</span>
      </div>
      <div>
        <p className="font-bold text-white text-sm leading-none">HealthCompanion</p>
        <p className="text-[10px] text-slate-500 mt-0.5">Personal Health AI</p>
      </div>
    </div>
  );
}
