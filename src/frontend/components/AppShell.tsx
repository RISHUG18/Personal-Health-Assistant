/* Week 6 – Client shell wrapping sidebar + toast provider */
"use client";

import { ToastProvider } from "@/components/ui/toast";
import { Sidebar, BottomNav } from "@/components/nav/Navigation";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 overflow-auto pb-20 md:pb-0">{children}</main>
      </div>
      <BottomNav />
    </ToastProvider>
  );
}
