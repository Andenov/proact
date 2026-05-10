"use client";

import { useQuery } from "@tanstack/react-query";
import { getLatestRisk, getRiskHorizons, DistrictWithRisk, RiskHorizon } from "@/lib/api";

type RiskType = "flood" | "landslide" | "food_stress";

interface Props {
  district: DistrictWithRisk;
  riskType: RiskType;
  onClose: () => void;
}

const RISK_TYPE_LABEL: Record<RiskType, string> = {
  flood: "FLOOD RISK",
  landslide: "LANDSLIDE RISK",
  food_stress: "FOOD STRESS",
};

const LEVEL_COLOR: Record<string, string> = {
  High: "text-red-400",
  Medium: "text-amber-400",
  Low: "text-emerald-400",
};

const LEVEL_BG: Record<string, string> = {
  High: "bg-red-500/20 border-red-500/30",
  Medium: "bg-amber-500/20 border-amber-500/30",
  Low: "bg-emerald-500/20 border-emerald-500/30",
};


export default function DistrictAlertPanel({ district, riskType, onClose }: Props) {
  const { data: scores = [], isLoading } = useQuery({
    queryKey: ["latestRisk", district.id],
    queryFn: () => getLatestRisk({ district_id: district.id }),
  });

  const score = scores[0] ?? null;
  const riskInfo = score
    ? (() => {
        if (riskType === "flood") return { level: score.flood_level, scoreVal: score.flood_score };
        if (riskType === "landslide") return { level: score.landslide_level, scoreVal: score.landslide_score };
        return { level: score.food_stress_level, scoreVal: score.food_stress_score };
      })()
    : null;

  const level = riskInfo?.level ?? "Low";
  const drivers = score?.top_drivers_json?.[riskType] ?? [];
  const recommendations = score?.recommendations_json?.[riskType] ?? [];

  const { data: horizons = [] } = useQuery({
    queryKey: ["riskHorizons", district.id],
    queryFn: () => getRiskHorizons(district.id),
  });

  const actionIcons: Record<string, string> = {
    High: "🔴",
    Medium: "🟡",
    Low: "🟢",
  };

  const LEVEL_ORDER: Record<string, number> = { Low: 0, Medium: 1, High: 2 };

  function trendArrow(from: string, to: string) {
    const diff = (LEVEL_ORDER[to] ?? 0) - (LEVEL_ORDER[from] ?? 0);
    if (diff > 0) return { arrow: "↑", color: "text-red-400" };
    if (diff < 0) return { arrow: "↓", color: "text-emerald-400" };
    return { arrow: "→", color: "text-slate-500" };
  }

  const HORIZON_LEVEL_COLOR: Record<string, string> = {
    High:   "bg-red-500/20 text-red-300 border border-red-500/30",
    Medium: "bg-amber-500/20 text-amber-300 border border-amber-500/30",
    Low:    "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30",
  };

  return (
    <div className="flex flex-col h-full bg-[#132240] border-l border-white/10">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 border-b border-white/10 flex items-start justify-between">
        <div>
          <div className="text-xs text-slate-400 uppercase tracking-wide mb-0.5">Alert</div>
          <h2 className="text-sm font-bold text-white">{district.name} District</h2>
        </div>
        <button
          onClick={onClose}
          className="text-slate-500 hover:text-white text-lg leading-none mt-0.5"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {isLoading && (
          <div className="text-xs text-slate-500">Loading risk data...</div>
        )}

        {/* Risk level badge */}
        {riskInfo && (
          <div className={`rounded-lg border px-3 py-2.5 ${LEVEL_BG[level] ?? LEVEL_BG.Low}`}>
            <div className="text-xs text-slate-400 mb-0.5">{RISK_TYPE_LABEL[riskType]}</div>
            <div className={`text-lg font-black tracking-wide ${LEVEL_COLOR[level] ?? "text-slate-300"}`}>
              {level.toUpperCase()}
            </div>
            {riskInfo.scoreVal != null && (
              <div className="text-xs text-slate-500 mt-0.5">
                Score: {riskInfo.scoreVal.toFixed(0)}/100
              </div>
            )}
            {/* Plain-language description */}
            {score?.top_drivers_json?.descriptions?.[riskType] && (
              <div className="mt-2 pt-2 border-t border-white/10 text-xs text-slate-300 leading-relaxed">
                {score.top_drivers_json.descriptions[riskType]}
              </div>
            )}
          </div>
        )}

        {/* Risk Outlook Timeline */}
        {horizons.length > 0 && (
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Risk Outlook — {RISK_TYPE_LABEL[riskType]}
            </div>

            {/* Timeline row */}
            <div className="relative mb-1">
              {/* Connector line */}
              <div className="absolute top-4 left-4 right-4 h-px bg-white/10" />
              <div className="grid grid-cols-4 gap-1 relative">
                {horizons.map((h, i) => {
                  const item = h[riskType] as { score: number; level: string };
                  const prev = i > 0 ? (horizons[i - 1][riskType] as { level: string }).level : null;
                  const trend = prev ? trendArrow(prev, item.level) : null;
                  return (
                    <div key={h.key} className="flex flex-col items-center gap-1">
                      {/* Dot */}
                      <div className={`w-2.5 h-2.5 rounded-full border-2 z-10 ${
                        item.level === "High"   ? "bg-red-400 border-red-500" :
                        item.level === "Medium" ? "bg-amber-400 border-amber-500" :
                                                  "bg-emerald-400 border-emerald-500"
                      }`} />
                      {/* Level badge */}
                      <span className={`text-xs font-bold px-1.5 py-0.5 rounded-full text-center w-full ${HORIZON_LEVEL_COLOR[item.level] ?? ""}`}>
                        {item.level}
                      </span>
                      {/* Label */}
                      <span className="text-xs text-slate-500 text-center leading-tight">{h.label}</span>
                      {/* Trend arrow */}
                      {trend && (
                        <span className={`text-sm font-bold ${trend.color}`}>{trend.arrow}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 30d note */}
            {horizons.find(h => h.key === "30d")?.note && (
              <div className="text-xs text-slate-600 italic mt-1">
                30d: {horizons.find(h => h.key === "30d")!.note}
              </div>
            )}
          </div>
        )}

        {/* Risk Drivers */}
        {drivers.length > 0 && (
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Risk Drivers
            </div>
            <ul className="space-y-2">
              {drivers.map((d, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                  <div>
                    <span className="text-sm text-white">{d.factor}</span>
                    <span className="text-xs text-slate-500 ml-1">({d.contribution.toFixed(0)} pts)</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommended Actions */}
        {recommendations.length > 0 && (
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Recommended Actions
            </div>
            <ul className="space-y-2">
              {recommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-sm shrink-0">{actionIcons[level] ?? "•"}</span>
                  <span className="text-sm text-slate-300">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* All risk types summary */}
        {score && (
          <div className="pt-3 border-t border-white/10">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              All Hazards
            </div>
            <div className="space-y-1.5">
              {[
                { key: "flood",       label: "Flood",       level: score.flood_level,       score: score.flood_score },
                { key: "landslide",   label: "Landslide",   level: score.landslide_level,   score: score.landslide_score },
                { key: "food_stress", label: "Food Stress", level: score.food_stress_level, score: score.food_stress_score },
              ].map((r) => (
                <div key={r.label} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400">{r.label}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-white/10 rounded-full h-1.5">
                        <div
                          className="h-1.5 rounded-full"
                          style={{
                            width: `${r.score ?? 0}%`,
                            backgroundColor:
                              r.level === "High" ? "#f87171" :
                              r.level === "Medium" ? "#fbbf24" : "#34d399",
                          }}
                        />
                      </div>
                      <span className={`text-xs font-semibold w-12 text-right ${LEVEL_COLOR[r.level ?? "Low"] ?? "text-slate-400"}`}>
                        {r.level ?? "—"}
                      </span>
                    </div>
                  </div>
                  {score?.top_drivers_json?.descriptions?.[r.key] && (
                    <p className="text-xs text-slate-500 leading-relaxed pl-0.5">
                      {score.top_drivers_json.descriptions[r.key]}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
