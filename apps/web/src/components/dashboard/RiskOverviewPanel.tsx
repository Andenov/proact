"use client";

import { useQuery } from "@tanstack/react-query";
import { DistrictWithRisk, getRiskHorizons } from "@/lib/api";

type RiskType = "flood" | "landslide" | "food_stress";

interface Props {
  districts: DistrictWithRisk[];
  riskType: RiskType;
  selectedId: number | null;
  onRiskTypeChange: (t: RiskType) => void;
  onSelect: (id: number) => void;
}

const TABS: { key: RiskType; label: string }[] = [
  { key: "flood", label: "Flood Risk" },
  { key: "landslide", label: "Landslide Risk" },
  { key: "food_stress", label: "Food Stress" },
];

const LEVEL_COLOR: Record<string, string> = {
  High: "text-red-400",
  Medium: "text-amber-400",
  Low: "text-emerald-400",
};

const LEVEL_BG: Record<string, string> = {
  High: "bg-red-100 text-red-700",
  Medium: "bg-amber-100 text-amber-700",
  Low: "bg-emerald-100 text-emerald-700",
};

const LEVEL_ICON: Record<string, string> = {
  High: "⚠",
  Medium: "△",
  Low: "✓",
};

const LEVEL_ORDER: Record<string, number> = { Low: 0, Medium: 1, High: 2 };

function Forecast7dBadge({ districtId, riskType }: { districtId: number; riskType: RiskType }) {
  const { data: horizons = [] } = useQuery({
    queryKey: ["riskHorizons", districtId],
    queryFn: () => getRiskHorizons(districtId),
    staleTime: 5 * 60 * 1000,
  });
  const h7d = horizons.find((h) => h.key === "7d");
  if (!h7d) return null;
  const item = h7d[riskType] as { level: string };
  if (!item) return null;
  return (
    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full ${LEVEL_BG[item.level] ?? ""}`}>
      {item.level} in 7d
    </span>
  );
}

// Short contextual bullets shown in the list (before full detail is loaded)
const QUICK_DRIVERS: Record<RiskType, Record<string, string[]>> = {
  flood: {
    High: ["Heavy rainfall events", "High floodplain exposure"],
    Medium: ["Moderate rainfall anomaly", "River proximity"],
    Low: ["Normal rainfall levels"],
  },
  landslide: {
    High: ["Heavy rainfall, steep slopes", "Saturated soil conditions"],
    Medium: ["Elevated soil moisture", "Moderate slope gradient"],
    Low: ["Stable soil conditions"],
  },
  food_stress: {
    High: ["Severe rainfall deficit", "Prolonged heat stress"],
    Medium: ["Rainfall below average", "Seasonal vulnerability"],
    Low: ["Normal crop conditions"],
  },
};

function getLevel(d: DistrictWithRisk, type: RiskType): string | null {
  if (type === "flood") return d.flood_level;
  if (type === "landslide") return d.landslide_level;
  return d.food_stress_level;
}

export default function RiskOverviewPanel({
  districts,
  riskType,
  selectedId,
  onRiskTypeChange,
  onSelect,
}: Props) {
  // Group by region
  const byRegion: Record<string, DistrictWithRisk[]> = {};
  for (const d of districts) {
    const region = d.region ?? "Other";
    if (!byRegion[region]) byRegion[region] = [];
    byRegion[region].push(d);
  }

  // Sort regions so High-risk districts surface to top within each group
  const levelOrder = { High: 0, Medium: 1, Low: 2 };
  for (const region of Object.keys(byRegion)) {
    byRegion[region].sort((a, b) => {
      const la = getLevel(a, riskType) ?? "Low";
      const lb = getLevel(b, riskType) ?? "Low";
      return (levelOrder[la as keyof typeof levelOrder] ?? 2) -
             (levelOrder[lb as keyof typeof levelOrder] ?? 2);
    });
  }

  return (
    <div className="flex flex-col h-full bg-[#132240] border-r border-white/10">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 border-b border-white/10">
        <h2 className="text-sm font-bold text-white tracking-wide uppercase">Risk Overview</h2>
      </div>

      {/* Risk type tabs */}
      <div className="px-3 pt-3 pb-2 flex flex-col gap-1">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => onRiskTypeChange(tab.key)}
            className={`text-left px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              riskType === tab.key
                ? "bg-emerald-600 text-white"
                : "text-slate-400 hover:text-white hover:bg-white/10"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* District list by region */}
      <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-4 mt-1">
        {Object.entries(byRegion).map(([region, dists]) => (
          <div key={region}>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 px-1">
              {region} Region
            </div>
            <div className="space-y-1">
              {dists.map((d) => {
                const level = getLevel(d, riskType) ?? "Low";
                const isSelected = d.id === selectedId;
                const drivers = QUICK_DRIVERS[riskType][level] ?? [];

                return (
                  <button
                    key={d.id}
                    onClick={() => onSelect(d.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors ${
                      isSelected
                        ? "bg-white/15 ring-1 ring-white/20"
                        : "hover:bg-white/8"
                    }`}
                  >
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-sm ${LEVEL_COLOR[level] ?? "text-slate-400"}`}>
                        {LEVEL_ICON[level] ?? "·"}
                      </span>
                      <span className="text-sm font-semibold text-white">{d.name}:</span>
                      <span className={`text-sm font-bold ${LEVEL_COLOR[level] ?? "text-slate-400"}`}>
                        {level.toUpperCase()}
                      </span>
                      <Forecast7dBadge districtId={d.id} riskType={riskType} />
                    </div>
                    <ul className="mt-1 ml-5 space-y-0.5">
                      {drivers.map((bullet, i) => (
                        <li key={i} className="text-xs text-slate-400 flex gap-1">
                          <span className="text-slate-600">•</span>
                          {bullet}
                        </li>
                      ))}
                    </ul>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
