"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  getSiloReadings,
  getStorageRisk,
  submitSiloReading,
  StorageUnit,
  SiloReadingCreate,
} from "@/lib/api";

interface Props {
  unit: StorageUnit;
  onClose: () => void;
}

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

const TYPE_LABEL: Record<string, string> = {
  metal_silo: "Metal Silo",
  pics_bag: "PICS Bag",
  sealed_drum: "Sealed Drum",
};

function MetricCard({ label, value, unit, warn }: { label: string; value: number | null; unit: string; warn?: boolean }) {
  return (
    <div className={`rounded-lg border px-3 py-2.5 ${warn ? "border-amber-500/30 bg-amber-500/10" : "border-white/10 bg-white/5"}`}>
      <div className="text-xs text-slate-400 mb-0.5">{label}</div>
      <div className={`text-lg font-bold ${warn ? "text-amber-300" : "text-white"}`}>
        {value != null ? value.toFixed(1) : "—"}
        <span className="text-xs font-normal text-slate-400 ml-1">{unit}</span>
      </div>
    </div>
  );
}

export default function StorageUnitPanel({ unit, onClose }: Props) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<SiloReadingCreate>({
    moisture_pct: undefined,
    temp_c: undefined,
    humidity_pct: undefined,
    co2_ppm: undefined,
  });

  const { data: risk } = useQuery({
    queryKey: ["storageRisk", unit.id],
    queryFn: () => getStorageRisk(unit.id),
    retry: false,
  });

  const { data: readings = [] } = useQuery({
    queryKey: ["siloReadings", unit.id],
    queryFn: () => getSiloReadings(unit.id),
  });

  const submitMutation = useMutation({
    mutationFn: (data: SiloReadingCreate) => submitSiloReading(unit.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["storageRisk", unit.id] });
      queryClient.invalidateQueries({ queryKey: ["siloReadings", unit.id] });
      queryClient.invalidateQueries({ queryKey: ["storageUnits"] });
      setShowForm(false);
      setForm({ moisture_pct: undefined, temp_c: undefined, humidity_pct: undefined, co2_ppm: undefined });
    },
  });

  const level = risk?.level ?? unit.latest_risk?.level ?? "Low";
  const reading = unit.latest_reading;

  const chartData = [...readings]
    .reverse()
    .slice(-14)
    .map((r) => ({
      time: r.timestamp.slice(5, 16).replace("T", " "),
      moisture: r.moisture_pct,
      temp: r.temp_c,
    }));

  return (
    <div className="flex flex-col h-full bg-[#132240] border-l border-white/10">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 border-b border-white/10 flex items-start justify-between">
        <div>
          <div className="text-xs text-slate-400 uppercase tracking-wide mb-0.5">Storage Unit</div>
          <h2 className="text-sm font-bold text-white">{unit.unit_name}</h2>
          <div className="text-xs text-slate-400 mt-0.5">
            {TYPE_LABEL[unit.hermetic_type] ?? unit.hermetic_type} · {unit.grain_type}
          </div>
        </div>
        <button onClick={onClose} className="text-slate-500 hover:text-white text-lg leading-none mt-0.5">✕</button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {/* Risk badge */}
        <div className={`rounded-lg border px-3 py-2.5 ${LEVEL_BG[level] ?? LEVEL_BG.Low}`}>
          <div className="text-xs text-slate-400 mb-0.5">AFLATOXIN RISK</div>
          <div className={`text-lg font-black tracking-wide ${LEVEL_COLOR[level] ?? "text-slate-300"}`}>
            {level.toUpperCase()}
          </div>
          {(risk?.score ?? unit.latest_risk?.score) != null && (
            <div className="text-xs text-slate-500 mt-0.5">
              Score: {(risk?.score ?? unit.latest_risk?.score)!.toFixed(0)}/100
            </div>
          )}
          {(risk?.predicted_days_safe ?? unit.latest_risk?.predicted_days_safe) != null && (
            <div className="text-xs text-slate-400 mt-1">
              Estimated safe for{" "}
              <span className={`font-semibold ${LEVEL_COLOR[level]}`}>
                {risk?.predicted_days_safe ?? unit.latest_risk?.predicted_days_safe} days
              </span>
            </div>
          )}
        </div>

        {/* Current sensor readings */}
        {reading && (
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Latest Sensor Readings
            </div>
            <div className="grid grid-cols-2 gap-2">
              <MetricCard label="Grain Moisture" value={reading.moisture_pct} unit="%" warn={(reading.moisture_pct ?? 0) > 13.5} />
              <MetricCard label="Temperature" value={reading.temp_c} unit="°C" warn={(reading.temp_c ?? 0) > 28} />
              <MetricCard label="Humidity" value={reading.humidity_pct} unit="%" warn={(reading.humidity_pct ?? 0) > 70} />
              <MetricCard label="CO₂" value={reading.co2_ppm} unit="ppm" warn={(reading.co2_ppm ?? 0) > 1500} />
            </div>
            <div className="text-xs text-slate-600 mt-1.5">
              Reading: {reading.timestamp.slice(0, 16).replace("T", " ")} UTC
            </div>
          </div>
        )}

        {/* Risk drivers */}
        {risk?.top_drivers && risk.top_drivers.length > 0 && (
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Risk Drivers
            </div>
            <ul className="space-y-2">
              {risk.top_drivers.map((d, i) => (
                <li key={i} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300">{d.factor}</span>
                    <span className="text-slate-500">{d.raw}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.min(d.contribution / 40 * 100, 100)}%`,
                        backgroundColor: d.contribution > 20 ? "#f87171" : d.contribution > 10 ? "#fbbf24" : "#34d399",
                      }}
                    />
                  </div>
                  <div className="text-xs text-slate-600">{d.contribution.toFixed(1)} pts</div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {unit.latest_risk?.recommendation && (
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Recommendation
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {unit.latest_risk.recommendation}
            </p>
          </div>
        )}

        {/* Trend chart */}
        {chartData.length > 1 && (
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Moisture &amp; Temp Trend
            </div>
            <div className="h-28">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 2, right: 4, bottom: 0, left: -24 }}>
                  <defs>
                    <linearGradient id="sm" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#60a5fa" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="tm" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#fbbf24" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="time" tick={{ fontSize: 8, fill: "#64748b" }} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 8, fill: "#64748b" }} />
                  <Tooltip
                    contentStyle={{ fontSize: 10, borderRadius: 6, backgroundColor: "#1e3555", border: "1px solid rgba(255,255,255,0.1)", color: "#fff" }}
                    formatter={(v, name) => [Number(v).toFixed(1), name === "moisture" ? "Moisture %" : "Temp °C"]}
                  />
                  <Area type="monotone" dataKey="moisture" stroke="#60a5fa" fill="url(#sm)" strokeWidth={1.5} dot={false} />
                  <Area type="monotone" dataKey="temp" stroke="#fbbf24" fill="url(#tm)" strokeWidth={1.5} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex gap-3 text-xs text-slate-500 mt-1">
              <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-blue-400 inline-block" />Moisture %</span>
              <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-amber-400 inline-block" />Temp °C</span>
            </div>
          </div>
        )}

        {/* Submit reading */}
        <div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="w-full text-xs font-medium py-2 px-3 rounded-lg border border-white/10 text-slate-400 hover:text-white hover:border-white/20 transition-colors"
          >
            {showForm ? "Cancel" : "+ Submit Sensor Reading"}
          </button>

          {showForm && (
            <form
              onSubmit={(e) => { e.preventDefault(); submitMutation.mutate(form); }}
              className="mt-3 space-y-3 bg-white/5 rounded-lg p-3 border border-white/10"
            >
              <div className="grid grid-cols-2 gap-2">
                {[
                  { key: "moisture_pct" as const, label: "Moisture %", placeholder: "12.5" },
                  { key: "temp_c" as const, label: "Temp °C", placeholder: "26.0" },
                  { key: "humidity_pct" as const, label: "Humidity %", placeholder: "65.0" },
                  { key: "co2_ppm" as const, label: "CO₂ ppm", placeholder: "600" },
                ].map(({ key, label, placeholder }) => (
                  <div key={key}>
                    <label className="block text-xs text-slate-400 mb-1">{label}</label>
                    <input
                      type="number"
                      step="0.1"
                      value={form[key] ?? ""}
                      onChange={(e) => setForm({ ...form, [key]: e.target.value ? Number(e.target.value) : undefined })}
                      placeholder={placeholder}
                      className="w-full bg-white/5 border border-white/10 rounded px-2 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                    />
                  </div>
                ))}
              </div>
              <button
                type="submit"
                disabled={submitMutation.isPending}
                className="w-full bg-emerald-600 text-white py-1.5 rounded text-xs font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
              >
                {submitMutation.isPending ? "Submitting..." : "Submit & Recompute Risk"}
              </button>
              {submitMutation.isError && (
                <p className="text-xs text-red-400">{(submitMutation.error as Error).message}</p>
              )}
            </form>
          )}
        </div>

        {/* Unit info footer */}
        <div className="pt-3 border-t border-white/10 space-y-1 text-xs text-slate-500">
          <div className="flex justify-between">
            <span>Farmer</span>
            <span className="text-slate-400">{unit.farmer_name ?? "—"}</span>
          </div>
          <div className="flex justify-between">
            <span>District</span>
            <span className="text-slate-400">{unit.district_name ?? "—"}</span>
          </div>
          {unit.capacity_kg && (
            <div className="flex justify-between">
              <span>Capacity</span>
              <span className="text-slate-400">{unit.capacity_kg} kg</span>
            </div>
          )}
          {unit.install_date && (
            <div className="flex justify-between">
              <span>Installed</span>
              <span className="text-slate-400">{unit.install_date}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span>Subscription</span>
            <span className="text-slate-400 capitalize">{unit.subscription_tier}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
