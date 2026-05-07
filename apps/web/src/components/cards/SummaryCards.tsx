"use client";

import { useQuery } from "@tanstack/react-query";
import { getAlerts, getDistricts, getFarmers, type DistrictWithRisk } from "@/lib/api";

interface CardProps {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}

function Card({ label, value, sub, color = "bg-white" }: CardProps) {
  return (
    <div className={`${color} rounded-xl shadow-sm border border-slate-200 p-5`}>
      <div className="text-sm text-slate-500 font-medium">{label}</div>
      <div className="text-3xl font-bold mt-1 text-slate-900">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  );
}

export default function SummaryCards() {
  const { data: districts = [] } = useQuery<DistrictWithRisk[]>({
    queryKey: ["districts"],
    queryFn: getDistricts,
  });
  const { data: alerts = [] } = useQuery({
    queryKey: ["alerts"],
    queryFn: () => getAlerts(),
  });
  const { data: farmers = [] } = useQuery({
    queryKey: ["farmers"],
    queryFn: () => getFarmers(),
  });

  const highRisk = districts.filter(
    (d) =>
      d.flood_level === "High" ||
      d.landslide_level === "High" ||
      d.food_stress_level === "High"
  ).length;

  const activeAlerts = alerts.filter((a) => a.status === "active").length;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card
        label="Districts Monitored"
        value={districts.length}
        sub="Pilot districts"
      />
      <Card
        label="High Risk Districts"
        value={highRisk}
        sub="Requires attention"
        color={highRisk > 0 ? "bg-red-50" : "bg-white"}
      />
      <Card label="Active Alerts" value={activeAlerts} sub="Today" />
      <Card label="Enrolled Farmers" value={farmers.length} sub="SMS recipients" />
    </div>
  );
}
