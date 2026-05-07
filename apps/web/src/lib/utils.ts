export type RiskLevel = "Low" | "Medium" | "High" | null | undefined;

export const RISK_COLORS: Record<string, string> = {
  Low: "#22c55e",
  Medium: "#f59e0b",
  High: "#ef4444",
};

export const RISK_BG: Record<string, string> = {
  Low: "bg-green-100 text-green-800",
  Medium: "bg-amber-100 text-amber-800",
  High: "bg-red-100 text-red-800",
};

export const RISK_BORDER: Record<string, string> = {
  Low: "border-green-400",
  Medium: "border-amber-400",
  High: "border-red-500",
};

export function levelColor(level: RiskLevel): string {
  if (!level) return "#94a3b8";
  return RISK_COLORS[level] ?? "#94a3b8";
}

export function levelBadge(level: RiskLevel): string {
  if (!level) return "bg-slate-100 text-slate-600";
  return RISK_BG[level] ?? "bg-slate-100 text-slate-600";
}

export function alertTypeLabel(type: string | null | undefined): string {
  const map: Record<string, string> = {
    flood: "Flood",
    landslide: "Landslide",
    food_stress: "Food Stress",
  };
  return type ? (map[type] ?? type) : "—";
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function scoreBar(score: number | null | undefined): string {
  if (score == null) return "w-0";
  const pct = Math.round(score);
  return `w-[${pct}%]`;
}
