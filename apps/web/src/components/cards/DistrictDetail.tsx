"use client";

import { useQuery } from "@tanstack/react-query";
import { getLatestRisk, getRiskHorizons, RiskHorizon } from "@/lib/api";
import { alertTypeLabel, levelBadge, levelColor } from "@/lib/utils";
import RainfallChart from "@/components/charts/RainfallChart";

interface Props {
  districtId: number;
  districtName: string;
  onClose: () => void;
}

const LEVEL_ORDER: Record<string, number> = { Low: 0, Medium: 1, High: 2 };

function trendArrow(from: string | null, to: string): string {
  const a = LEVEL_ORDER[from ?? "Low"] ?? 0;
  const b = LEVEL_ORDER[to] ?? 0;
  if (b > a) return "↑";
  if (b < a) return "↓";
  return "→";
}

function trendColor(from: string | null, to: string): string {
  const a = LEVEL_ORDER[from ?? "Low"] ?? 0;
  const b = LEVEL_ORDER[to] ?? 0;
  if (b > a) return "text-red-500";
  if (b < a) return "text-emerald-500";
  return "text-slate-400";
}

function ScoreBar({ score, level }: { score: number | null; level: string | null }) {
  const color = levelColor(level as "Low" | "Medium" | "High");
  return (
    <div className="w-full bg-slate-100 rounded-full h-2">
      <div
        className="h-2 rounded-full transition-all"
        style={{ width: `${score ?? 0}%`, backgroundColor: color }}
      />
    </div>
  );
}

const HAZARD_KEYS: Array<{ key: keyof RiskHorizon; label: string }> = [
  { key: "flood",       label: "Flood" },
  { key: "landslide",   label: "Landslide" },
  { key: "food_stress", label: "Food Stress" },
];

function HorizonTimeline({
  horizons,
  currentLevels,
}: {
  horizons: RiskHorizon[];
  currentLevels: Record<string, string | null>;
}) {
  return (
    <div>
      <div className="text-sm font-semibold text-slate-700 mb-3">Risk Outlook</div>

      {/* Column headers */}
      <div className="grid grid-cols-4 gap-1 mb-2">
        {horizons.map((h) => (
          <div key={h.key} className="text-center">
            <div className="text-xs font-semibold text-slate-700">{h.label}</div>
            <div className="text-xs text-slate-400">{h.target_date}</div>
            {h.note && (
              <div className="text-xs text-slate-400 italic">{h.note}</div>
            )}
          </div>
        ))}
      </div>

      {/* One row per hazard type */}
      {HAZARD_KEYS.map(({ key, label }) => (
        <div key={key} className="mb-3">
          <div className="text-xs font-medium text-slate-500 mb-1">{label}</div>
          <div className="grid grid-cols-4 gap-1">
            {horizons.map((h, i) => {
              const item = h[key] as { score: number; level: string };
              const prevLevel = i === 0 ? currentLevels[key] : (horizons[i - 1][key] as { level: string }).level;
              const arrow = i === 0 ? null : trendArrow(prevLevel, item.level);
              const arrowCls = i === 0 ? "" : trendColor(prevLevel, item.level);
              return (
                <div key={h.key} className="flex flex-col items-center gap-0.5">
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full w-full text-center ${levelBadge(
                      item.level as "Low" | "Medium" | "High"
                    )}`}
                  >
                    {item.level}
                  </span>
                  <span className="text-xs text-slate-400">{item.score.toFixed(0)}/100</span>
                  {arrow && (
                    <span className={`text-sm font-bold ${arrowCls}`}>{arrow}</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {/* Connector line */}
      <div className="relative mt-1 mb-3">
        <div className="absolute top-1/2 left-0 right-0 h-px bg-slate-200" />
        <div className="grid grid-cols-4 gap-1 relative">
          {horizons.map((h) => (
            <div key={h.key} className="flex justify-center">
              <div className="w-2 h-2 rounded-full bg-slate-300" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function DistrictDetail({ districtId, districtName, onClose }: Props) {
  const { data: scores = [], isLoading } = useQuery({
    queryKey: ["latestRisk", districtId],
    queryFn: () => getLatestRisk({ district_id: districtId }),
  });

  const { data: horizons = [] } = useQuery({
    queryKey: ["riskHorizons", districtId],
    queryFn: () => getRiskHorizons(districtId),
  });

  const score = scores[0];

  const risks = score
    ? [
        { type: "flood",       label: "Flood",       score: score.flood_score,       level: score.flood_level },
        { type: "landslide",   label: "Landslide",   score: score.landslide_score,   level: score.landslide_level },
        { type: "food_stress", label: "Food Stress", score: score.food_stress_score, level: score.food_stress_level },
      ]
    : [];

  const currentLevels: Record<string, string | null> = {
    flood:       score?.flood_level ?? null,
    landslide:   score?.landslide_level ?? null,
    food_stress: score?.food_stress_level ?? null,
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="font-bold text-lg text-slate-800">{districtName}</div>
          <div className="text-xs text-slate-400">District detail · {score?.date ?? "—"}</div>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-lg font-light">✕</button>
      </div>

      {isLoading && <div className="text-sm text-slate-400">Loading risk data...</div>}

      {/* Current risk scores */}
      {risks.map((r) => (
        <div key={r.type}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-slate-700">{r.label}</span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">{(r.score ?? 0).toFixed(0)}/100</span>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${levelBadge(r.level as "Low" | "Medium" | "High")}`}>
                {r.level ?? "—"}
              </span>
            </div>
          </div>
          <ScoreBar score={r.score} level={r.level} />
          {score?.top_drivers_json?.[r.type]?.length ? (
            <div className="mt-2 space-y-1">
              {score.top_drivers_json[r.type].slice(0, 2).map((d) => (
                <div key={d.factor} className="flex items-center justify-between text-xs text-slate-500">
                  <span>{d.factor}</span>
                  <span className="text-slate-400">{d.contribution.toFixed(1)} pts</span>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ))}

      {/* Forecast timeline */}
      {horizons.length > 0 && (
        <div className="border-t border-slate-100 pt-4">
          <HorizonTimeline horizons={horizons} currentLevels={currentLevels} />
        </div>
      )}

      {/* Recommendations — scoped to the worst upcoming horizon */}
      {score?.recommendations_json && (
        <div className="border-t border-slate-100 pt-4">
          <div className="text-sm font-semibold text-slate-700 mb-2">Recommended Actions</div>
          {Object.entries(score.recommendations_json).map(([type, recs]) => {
            // Find worst upcoming level for this hazard type across horizons
            const upcomingLevels = horizons
              .filter((h) => h.key !== "current")
              .map((h) => (h[type as keyof RiskHorizon] as { level: string })?.level)
              .filter(Boolean);
            const worstUpcoming = upcomingLevels.sort(
              (a, b) => (LEVEL_ORDER[b] ?? 0) - (LEVEL_ORDER[a] ?? 0)
            )[0];
            const horizon7d = horizons.find((h) => h.key === "7d");
            const level7d = horizon7d
              ? (horizon7d[type as keyof RiskHorizon] as { level: string })?.level
              : null;

            return (
              <div key={type} className="mb-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium text-slate-500 uppercase">
                    {alertTypeLabel(type)}
                  </span>
                  {level7d && (
                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full ${levelBadge(level7d as "Low" | "Medium" | "High")}`}>
                      {level7d} in 7 days
                    </span>
                  )}
                  {worstUpcoming && worstUpcoming !== level7d && (
                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full ${levelBadge(worstUpcoming as "Low" | "Medium" | "High")}`}>
                      {worstUpcoming} by 30 days
                    </span>
                  )}
                </div>
                <ul className="space-y-1">
                  {recs.slice(0, 2).map((rec, i) => (
                    <li key={i} className="text-xs text-slate-600 flex gap-1">
                      <span className="text-emerald-500 shrink-0">›</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      )}

      {/* Chart */}
      <div className="pt-2 border-t border-slate-100">
        <RainfallChart districtId={districtId} districtName={districtName} />
      </div>
    </div>
  );
}
