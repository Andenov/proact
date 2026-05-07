"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getRiskHistory } from "@/lib/api";

interface Props {
  districtId: number;
  districtName: string;
}

export default function RainfallChart({ districtId, districtName }: Props) {
  const { data = [], isLoading } = useQuery({
    queryKey: ["riskHistory", districtId],
    queryFn: () => getRiskHistory(districtId, 30),
    enabled: !!districtId,
  });

  const chartData = data.map((r) => ({
    date: r.date.slice(5), // MM-DD
    flood: r.flood_score ?? 0,
    landslide: r.landslide_score ?? 0,
    food_stress: r.food_stress_score ?? 0,
  }));

  if (isLoading)
    return (
      <div className="h-full flex items-center justify-center text-slate-500 text-sm">
        Loading chart...
      </div>
    );

  if (!chartData.length)
    return (
      <div className="h-full flex items-center justify-center text-slate-500 text-sm">
        No history data
      </div>
    );

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-1">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
          Risk Trend — {districtName}
        </div>
        <div className="flex gap-3 text-xs text-slate-500">
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-blue-400 inline-block" />Flood</span>
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-amber-400 inline-block" />Landslide</span>
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-emerald-400 inline-block" />Food Stress</span>
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
            <defs>
              <linearGradient id="flood" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#60a5fa" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="landslide" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#fbbf24" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="food" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#34d399" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="date" tick={{ fontSize: 9, fill: "#64748b" }} interval="preserveStartEnd" />
            <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: "#64748b" }} />
            <Tooltip
              contentStyle={{ fontSize: 11, borderRadius: 6, backgroundColor: "#1e3555", border: "1px solid rgba(255,255,255,0.1)", color: "#fff" }}
              formatter={(v, name) => [
                `${Number(v).toFixed(0)}/100`,
                String(name) === "food_stress" ? "Food Stress" : String(name).charAt(0).toUpperCase() + String(name).slice(1),
              ]}
            />
            <Area type="monotone" dataKey="flood" stroke="#60a5fa" fill="url(#flood)" strokeWidth={1.5} />
            <Area type="monotone" dataKey="landslide" stroke="#fbbf24" fill="url(#landslide)" strokeWidth={1.5} />
            <Area type="monotone" dataKey="food_stress" stroke="#34d399" fill="url(#food)" strokeWidth={1.5} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
