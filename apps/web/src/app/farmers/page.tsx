"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getFarmers, getDistricts, registerFarmer } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function FarmersPage() {
  const queryClient = useQueryClient();
  const [districtFilter, setDistrictFilter] = useState<number | undefined>();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    full_name: "",
    phone_number: "",
    district_id: "",
    preferred_language: "en",
  });

  const { data: farmers = [], isLoading } = useQuery({
    queryKey: ["farmers", districtFilter],
    queryFn: () => getFarmers(districtFilter),
  });

  const { data: districts = [] } = useQuery({
    queryKey: ["districts"],
    queryFn: getDistricts,
  });

  const registerMutation = useMutation({
    mutationFn: registerFarmer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["farmers"] });
      setShowForm(false);
      setForm({ full_name: "", phone_number: "", district_id: "", preferred_language: "en" });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    registerMutation.mutate({
      full_name: form.full_name || undefined,
      phone_number: form.phone_number,
      district_id: form.district_id ? Number(form.district_id) : undefined,
      preferred_language: form.preferred_language,
      consent_status: true,
    });
  };

  return (
    <div className="space-y-5 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Farmers</h1>
          <p className="text-sm text-slate-500">SMS alert recipients</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"
        >
          {showForm ? "Cancel" : "+ Register Farmer"}
        </button>
      </div>

      {/* Registration form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4"
        >
          <h2 className="font-semibold text-slate-800">Register New Farmer</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Full Name</label>
              <input
                type="text"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                placeholder="Optional"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">
                Phone Number *
              </label>
              <input
                type="text"
                required
                value={form.phone_number}
                onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                placeholder="+256700..."
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">District</label>
              <select
                value={form.district_id}
                onChange={(e) => setForm({ ...form, district_id: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white"
              >
                <option value="">Select district</option>
                {districts.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Language</label>
              <select
                value={form.preferred_language}
                onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white"
              >
                <option value="en">English</option>
                <option value="lg">Luganda</option>
                <option value="ach">Acholi</option>
              </select>
            </div>
          </div>
          <button
            type="submit"
            disabled={registerMutation.isPending}
            className="bg-emerald-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            {registerMutation.isPending ? "Registering..." : "Register"}
          </button>
          {registerMutation.isError && (
            <p className="text-xs text-red-600">{(registerMutation.error as Error).message}</p>
          )}
        </form>
      )}

      {/* Filter */}
      <div>
        <select
          value={districtFilter ?? ""}
          onChange={(e) =>
            setDistrictFilter(e.target.value ? Number(e.target.value) : undefined)
          }
          className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 bg-white text-slate-700"
        >
          <option value="">All Districts</option>
          {districts.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
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
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left">Phone</th>
                <th className="px-4 py-3 text-left">District</th>
                <th className="px-4 py-3 text-left">Language</th>
                <th className="px-4 py-3 text-left">Registered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {farmers.map((f) => (
                <tr key={f.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 text-slate-800">{f.full_name ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-600 font-mono text-xs">{f.phone_number}</td>
                  <td className="px-4 py-3 text-slate-600">{f.district_name ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-500 uppercase text-xs">{f.preferred_language}</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{formatDate(f.created_at)}</td>
                </tr>
              ))}
              {farmers.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-slate-400">
                    No farmers registered
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
