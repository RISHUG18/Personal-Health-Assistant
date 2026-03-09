import { cn } from "@/lib/utils";
import { Severity } from "@/lib/demo-data";

// ── Badge ─────────────────────────────────────
interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "outline" | "success" | "warning" | "danger" | "info";
  className?: string;
}
export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold",
        {
          "bg-slate-700 text-slate-200": variant === "default",
          "border border-slate-600 text-slate-300 bg-transparent": variant === "outline",
          "bg-emerald-600/20 text-emerald-300 border border-emerald-600/40": variant === "success",
          "bg-amber-600/20 text-amber-300 border border-amber-600/40": variant === "warning",
          "bg-red-600/20 text-red-300 border border-red-600/40": variant === "danger",
          "bg-blue-600/20 text-blue-300 border border-blue-600/40": variant === "info",
        },
        className
      )}
    >
      {children}
    </span>
  );
}

// ── SeverityBadge ─────────────────────────────
export function SeverityBadge({ severity }: { severity: Severity }) {
  if (severity === "critical") {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-600/30 text-red-300 border border-red-500/60 shadow-sm shadow-red-900/40">
        <span className="h-1.5 w-1.5 rounded-full bg-red-400 animate-pulse" />
        Critical
      </span>
    );
  }
  const map: Record<Exclude<Severity, "critical">, { label: string; variant: BadgeProps["variant"] }> = {
    low: { label: "Low", variant: "success" },
    medium: { label: "Medium", variant: "warning" },
    high: { label: "High", variant: "danger" },
  };
  const { label, variant } = map[severity];
  return <Badge variant={variant}>{label}</Badge>;
}

// ── Card ──────────────────────────────────────
interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}
export function Card({ children, className, onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "bg-slate-800/80 border border-slate-700/80 rounded-2xl p-4",
        "backdrop-blur-sm",
        onClick && "cursor-pointer card-hover hover:border-slate-600",
        className
      )}
    >
      {children}
    </div>
  );
}

// ── StatCard ──────────────────────────────────
interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "neutral";
  trendBad?: boolean; // if up is bad (e.g., LDL)
}
export function StatCard({ label, value, sub, icon, trend, trendBad }: StatCardProps) {
  const trendColor =
    trend === "neutral" || !trend
      ? "text-slate-400"
      : trend === "up"
      ? trendBad
        ? "text-red-400"
        : "text-emerald-400"
      : trendBad
      ? "text-emerald-400"
      : "text-red-400";

  const trendArrow = trend === "up" ? "↑" : trend === "down" ? "↓" : "—";

  return (
    <Card className="card-hover">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs text-slate-400 truncate font-medium uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-white mt-1 stat-value">{value}</p>
          {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
        </div>
        <div className="flex flex-col items-end gap-1.5">
          {icon && (
            <span className="text-slate-400 p-1.5 bg-slate-700/60 rounded-lg">{icon}</span>
          )}
          {trend && (
            <span className={cn("text-sm font-bold", trendColor)}>{trendArrow}</span>
          )}
        </div>
      </div>
    </Card>
  );
}

// ── Section ───────────────────────────────────
interface SectionProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}
export function Section({ title, subtitle, children, action }: SectionProps) {
  return (
    <section className="space-y-3 animate-fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white tracking-tight">{title}</h2>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
        {action && <div>{action}</div>}
      </div>
      {children}
    </section>
  );
}

// ── Empty State ───────────────────────────────
export function EmptyState({ message, icon }: { message: string; icon?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-14 text-slate-600">
      {icon && (
        <span className="text-4xl opacity-30 p-4 bg-slate-800/60 rounded-2xl">{icon}</span>
      )}
      <p className="text-sm text-slate-500">{message}</p>
    </div>
  );
}

// ── Spinner ───────────────────────────────────
export function Spinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  return (
    <span
      className={cn("inline-block animate-spin rounded-full border-2 border-slate-600 border-t-blue-400", {
        "h-4 w-4": size === "sm",
        "h-6 w-6": size === "md",
        "h-8 w-8": size === "lg",
      })}
    />
  );
}

// ── Lab Status colour helper ──────────────────
export function labStatusColor(status: "normal" | "low" | "high" | "critical") {
  return {
    normal: "text-emerald-400",
    low: "text-amber-400",
    high: "text-orange-400",
    critical: "text-red-400",
  }[status];
}

// ── AQI colour helper ─────────────────────────
export function aqiColor(aqi: number) {
  if (aqi <= 50) return "text-emerald-400";
  if (aqi <= 100) return "text-yellow-400";
  if (aqi <= 150) return "text-orange-400";
  if (aqi <= 200) return "text-red-400";
  return "text-purple-400";
}

export function aqiLabel(aqi: number) {
  if (aqi <= 50) return "Good";
  if (aqi <= 100) return "Moderate";
  if (aqi <= 150) return "Unhealthy (Sensitive)";
  if (aqi <= 200) return "Unhealthy";
  return "Very Unhealthy";
}

// ── AQI Badge (coloured pill with label) ─────
export function AqiBadge({ aqi }: { aqi: number }) {
  const color = aqiColor(aqi);
  const label = aqiLabel(aqi);
  // border colour mirrors text colour class
  const border =
    aqi <= 50  ? "border-emerald-500/40 bg-emerald-500/10" :
    aqi <= 100 ? "border-yellow-500/40 bg-yellow-500/10"  :
    aqi <= 150 ? "border-orange-500/40 bg-orange-500/10"  :
    aqi <= 200 ? "border-red-500/40 bg-red-500/10"        :
                 "border-purple-500/40 bg-purple-500/10";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border",
        border, color
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full",
        aqi <= 50  ? "bg-emerald-400" :
        aqi <= 100 ? "bg-yellow-400"  :
        aqi <= 150 ? "bg-orange-400"  :
        aqi <= 200 ? "bg-red-400"     : "bg-purple-400"
      )} />
      AQI {aqi} — {label}
    </span>
  );
}
