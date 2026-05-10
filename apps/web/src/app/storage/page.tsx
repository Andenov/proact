"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getStorageUnits,
  registerStorageUnit,
  getFarmers,
  getDistricts,
  StorageUnit,
  StorageUnitCreate,
} from "@/lib/api";
import StorageUnitPanel from "@/components/storage/StorageUnitPanel";

const LEVEL_COLOR: Record<string, string> = {
  High: "text-red-600",
  Medium: "text-amber-600",
  Low: "text-emerald-600",
};

const LEVEL_DOT: Record<string, string> = {
  High: "bg-red-500",
  Medium: "bg-amber-500",
  Low: "bg-emerald-500",
};

const HERMETIC_TYPES = [
  { value: "metal_silo", label: "Metal Silo" },
  { value: "pics_bag", label: "PICS Bag" },
  { value: "sealed_drum", label: "Sealed Drum" },
];

const GRAIN_TYPES = ["maize", "sorghum", "beans", "millet", "cassava"];

export default function StoragePage() {
  const queryClient = useQueryClient();
  const [selectedUnit, setSelectedUnit] = useState<StorageUnit | null>(null);
  const [districtFilter, setDistrictFilter] = useState<number | undefined>();
  const [levelFilter, setLevelFilter] = useState<string>("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<Partial<StorageUnitCreate>>({
    hermetic_type: "metal_silo",
    grain_type: "maize",
    subscription_tier: "basic",
  });

  const { data: units = [], isLoading } = useQuery({
    queryKey: ["storageUnits", districtFilter],
    queryFn: () => getStorageUnits({ district_id: districtFilter }),
  });

  const { data: farmers = [] } = useQuery({
    queryKey: ["farmers"],
    queryFn: () => getFarmers(),
  });

  const { data: districts = [] } = useQuery({
    queryKey: ["districts"],
    queryFn: getDistricts,
  });

  const registerMutation = useMutation({
    mutationFn: (data: StorageUnitCreate) => registerStorageUnit(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["storageUnits"] });
      setShowForm(false);
      setForm({ hermetic_type: "metal_silo", grain_type: "maize", subscription_tier: "basic" });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.farmer_id || !form.unit_name) return;
    registerMutation.mutate(form as StorageUnitCreate);
  };

  const filtered = levelFilter
    ? units.filter((u) => u.latest_risk?.level === levelFilter)
    : units;

  const highCount = units.filter((u) => u.latest_risk?.level === "High").length;
  const medCount = units.filter((u) => u.latest_risk?.level === "Medium").length;

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main content */}
      <div className={`flex-1 flex flex-col overflow-hidden transition-all ${selectedUnit ? "mr-72" : ""}`}>
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Smart Grain Storage</h1>
              <p className="text-sm text-slate-500 mt-0.5">Hermetic silo monitoring · Aflatoxin risk prediction</p>
            </div>
            <button
              onClick={() => setShowForm(!showForm)}
              className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"
            >
              {showForm ? "Cancel" : "+ Register Unit"}
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Total Units</div>
              <div className="text-2xl font-bold text-slate-900">{units.length}</div>
            </div>
            <div className="bg-white border border-red-100 rounded-xl p-4 shadow-sm">
              <div className="text-xs text-red-500 uppercase tracking-wide mb-1">High Risk</div>
              <div className="text-2xl font-bold text-red-600">{highCount}</div>
            </div>
            <div className="bg-white border border-amber-100 rounded-xl p-4 shadow-sm">
              <div className="text-xs text-amber-500 uppercase tracking-wide mb-1">Medium Risk</div>
              <div className="text-2xl font-bold text-amber-600">{medCount}</div>
            </div>
          </div>

          {/* Register form */}
          {showForm && (
            <form
              onSubmit={handleSubmit}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4"
            >
              <h2 className="font-semibold text-slate-800">Register New Storage Unit</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Unit Name *</label>
                  <input
                    type="text"
                    required
                    value={form.unit_name ?? ""}
                    onChange={(e) => setForm({ ...form, unit_name: e.target.value })}
                    placeholder="e.g. Silo A"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Farmer *</label>
                  <select
                    required
                    value={form.farmer_id ?? ""}
                    onChange={(e) => setForm({ ...form, farmer_id: Number(e.target.value) })}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white"
                  >
                    <option value="">Select farmer</option>
                    {farmers.map((f) => (
                      <option key={f.id} value={f.id}>{f.full_name ?? f.phone_number}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">District</label>
                  <select
                    value={form.district_id ?? ""}
                    onChange={(e) => setForm({ ...form, district_id: e.target.value ? Number(e.target.value) : undefined })}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white"
                  >
                    <option value="">Select district</option>
                    {districts.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Storage Type</label>
                  <select
                    value={form.hermetic_type}
                    onChange={(e) => setForm({ ...form, hermetic_type: e.target.value })}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white"
                  >
                    {HERMETIC_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Grain Type</label>
                  <select
                    value={form.grain_type}
                    onChange={(e) => setForm({ ...form, grain_type: e.target.value })}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white"
                  >
                    {GRAIN_TYPES.map((g) => (
                      <option key={g} value={g} className="capitalize">{g.charAt(0).toUpperCase() + g.slice(1)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Capacity (kg)</label>
                  <input
                    type="number"
                    value={form.capacity_kg ?? ""}
                    onChange={(e) => setForm({ ...form, capacity_kg: e.target.value ? Number(e.target.value) : undefined })}
                    placeholder="e.g. 500"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Subscription</label>
                  <select
                    value={form.subscription_tier}
                    onChange={(e) => setForm({ ...form, subscription_tier: e.target.value })}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white"
                  >
                    <option value="basic">Basic</option>
                    <option value="premium">Premium</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Install Date</label>
                  <input
                    type="date"
                    value={form.install_date ?? ""}
                    onChange={(e) => setForm({ ...form, install_date: e.target.value || undefined })}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={registerMutation.isPending}
                className="bg-emerald-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
              >
                {registerMutation.isPending ? "Registering..." : "Register Unit"}
              </button>
              {registerMutation.isError && (
                <p className="text-xs text-red-600">{(registerMutation.error as Error).message}</p>
              )}
            </form>
          )}

          {/* Filters */}
          <div className="flex gap-3">
            <select
              value={districtFilter ?? ""}
              onChange={(e) => setDistrictFilter(e.target.value ? Number(e.target.value) : undefined)}
              className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 bg-white text-slate-700"
            >
              <option value="">All Districts</option>
              {districts.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 bg-white text-slate-700"
            >
              <option value="">All Risk Levels</option>
              <option value="High">High Risk</option>
              <option value="Medium">Medium Risk</option>
              <option value="Low">Low Risk</option>
            </select>
          </div>

          {/* Table */}
          {isLoading ? (
            <div className="text-sm text-slate-400">Loading...</div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100 text-xs font-medium text-slate-500 uppercase tracking-wide">
                    <th className="px-4 py-3 text-left">Unit</th>
                    <th className="px-4 py-3 text-left">Farmer</th>
                    <th className="px-4 py-3 text-left">District</th>
                    <th className="px-4 py-3 text-left">Grain</th>
                    <th className="px-4 py-3 text-left">Risk</th>
                    <th className="px-4 py-3 text-left">Score</th>
                    <th className="px-4 py-3 text-left">Safe For</th>
                    <th className="px-4 py-3 text-left">Moisture</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {filtered.map((u) => (
                    <tr
                      key={u.id}
                      onClick={() => setSelectedUnit(selectedUnit?.id === u.id ? null : u)}
                      className={`cursor-pointer hover:bg-slate-50 transition-colors ${selectedUnit?.id === u.id ? "bg-emerald-50" : ""}`}
                    >
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-800">{u.unit_name}</div>
                        <div className="text-xs text-slate-400 capitalize">{u.hermetic_type.replace("_", " ")}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{u.farmer_name ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-600">{u.district_name ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-500 capitalize">{u.grain_type}</td>
                      <td className="px-4 py-3">
                        {u.latest_risk ? (
                          <div className="flex items-center gap-1.5">
                            <span className={`w-2 h-2 rounded-full ${LEVEL_DOT[u.latest_risk.level] ?? "bg-slate-400"}`} />
                            <span className={`font-semibold text-xs ${LEVEL_COLOR[u.latest_risk.level] ?? "text-slate-500"}`}>
                              {u.latest_risk.level}
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400">No data</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {u.latest_risk ? (
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 rounded-full bg-slate-200 overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${u.latest_risk.score}%`,
                                  backgroundColor:
                                    u.latest_risk.level === "High" ? "#ef4444" :
                                    u.latest_risk.level === "Medium" ? "#f59e0b" : "#10b981",
                                }}
                              />
                            </div>
                            <span className="text-xs text-slate-500">{u.latest_risk.score.toFixed(0)}</span>
                          </div>
                        ) : "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-600 text-xs">
                        {u.latest_risk?.predicted_days_safe != null
                          ? `${u.latest_risk.predicted_days_safe}d`
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-600 text-xs">
                        {u.latest_reading?.moisture_pct != null
                          ? `${u.latest_reading.moisture_pct.toFixed(1)}%`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr>
                      <td colSpan={8} className="px-4 py-12 text-center text-slate-400">
                        {units.length === 0
                          ? "No storage units registered yet. Click + Register Unit to get started."
                          : "No units match the current filter."}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Detail panel */}
      {selectedUnit && (
        <div className="w-72 fixed right-0 top-0 h-full z-10">
          <StorageUnitPanel
            unit={selectedUnit}
            onClose={() => setSelectedUnit(null)}
          />
        </div>
      )}
    </div>
  );
}
