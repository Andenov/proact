"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { getAlerts, getDistricts } from "@/lib/api";
import RiskOverviewPanel from "@/components/dashboard/RiskOverviewPanel";
import DistrictAlertPanel from "@/components/dashboard/DistrictAlertPanel";
import RainfallChart from "@/components/charts/RainfallChart";
import MapLegend from "@/components/map/MapLegend";

const RiskMap = dynamic(() => import("@/components/map/RiskMap"), { ssr: false });

type RiskType = "flood" | "landslide" | "food_stress";

export default function DashboardPage() {
  const [riskType, setRiskType] = useState<RiskType>("flood");
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: districts = [] } = useQuery({
    queryKey: ["districts"],
    queryFn: getDistricts,
  });

  const { data: alerts = [] } = useQuery({
    queryKey: ["alerts"],
    queryFn: () => getAlerts({ status: "active" }),
  });

  const selectedDistrict = districts.find((d) => d.id === selectedId) ?? null;
  const activeAlerts = alerts.filter((a) => a.status === "active").length;
  const highRisk = districts.filter(
    (d) => d.flood_level === "High" || d.landslide_level === "High" || d.food_stress_level === "High"
  ).length;

  const handleSelect = (id: number) => setSelectedId(id === selectedId ? null : id);

  return (
    <div className="flex flex-col h-full bg-[#0d1929] text-white">
      {/* Top bar */}
      <div className="flex items-center justify-between px-5 py-3 bg-[#0a1520] border-b border-white/10 shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-lg font-black tracking-wider">
            <span className="text-white">PRO</span>
            <span className="text-emerald-400">ACT</span>
          </span>
          <span className="text-slate-500 text-sm">|</span>
          <span className="text-slate-400 text-sm">Anticipatory Action Platform</span>
        </div>
        {/* Quick stats */}
        <div className="flex items-center gap-5 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="text-slate-400">{districts.length} Districts</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${highRisk > 0 ? "bg-red-400" : "bg-slate-600"}`} />
            <span className="text-slate-400">{highRisk} High Risk</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${activeAlerts > 0 ? "bg-amber-400" : "bg-slate-600"}`} />
            <span className="text-slate-400">{activeAlerts} Active Alerts</span>
          </div>
        </div>
      </div>

      {/* Main 3-panel content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Risk Overview */}
        <div className="w-60 shrink-0 overflow-hidden">
          <RiskOverviewPanel
            districts={districts}
            riskType={riskType}
            selectedId={selectedId}
            onRiskTypeChange={setRiskType}
            onSelect={handleSelect}
          />
        </div>

        {/* Center: Map + bottom chart */}
        <div className="flex-1 flex flex-col overflow-hidden border-x border-white/10">
          {/* Map */}
          <div className="relative flex-1 min-h-0">
            <RiskMap
              districts={districts}
              riskType={riskType}
              selectedId={selectedId}
              onSelect={handleSelect}
            />
            <MapLegend />
          </div>

          {/* Bottom: Rainfall chart */}
          <div className="h-52 shrink-0 border-t border-white/10 bg-[#0f1e35] px-5 py-3">
            {selectedDistrict ? (
              <RainfallChart
                districtId={selectedDistrict.id}
                districtName={selectedDistrict.name}
              />
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 text-sm gap-1">
                <span className="text-2xl">📍</span>
                <span>Select a district to view risk trend</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Alert Detail */}
        <div className="w-72 shrink-0 overflow-hidden">
          {selectedDistrict ? (
            <DistrictAlertPanel
              district={selectedDistrict}
              riskType={riskType}
              onClose={() => setSelectedId(null)}
            />
          ) : (
            <div className="h-full bg-[#132240] flex flex-col items-center justify-center text-slate-600 text-sm gap-2 px-6 text-center">
              <span className="text-3xl">🗺</span>
              <span className="font-medium text-slate-500">No district selected</span>
              <span className="text-xs text-slate-600">Click a district on the map or in the list to view alerts and recommendations</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
