"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { generateAlerts, getAlerts } from "@/lib/api";
import AlertCard from "@/components/cards/AlertCard";
import { alertTypeLabel, formatDateTime, levelBadge } from "@/lib/utils";

const TYPES = ["", "flood", "landslide", "food_stress"];
const SEVERITIES = ["", "Low", "Medium", "High"];

export default function AlertsPage() {
  const [severity, setSeverity] = useState("");
  const [alertType, setAlertType] = useState("");
  const queryClient = useQueryClient();

  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ["alerts", severity, alertType],
    queryFn: () =>
      getAlerts({
        severity: severity || undefined,
        alert_type: alertType || undefined,
      }),
  });

  const generateMutation = useMutation({
    mutationFn: generateAlerts,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  return (
    <div className="space-y-5 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Alerts</h1>
          <p className="text-sm text-slate-500">All district risk alerts</p>
        </div>
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
        >
          {generateMutation.isPending ? "Generating..." : "Generate Alerts"}
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 bg-white text-slate-700"
        >
          <option value="">All Severities</option>
          {SEVERITIES.slice(1).map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={alertType}
          onChange={(e) => setAlertType(e.target.value)}
          className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 bg-white text-slate-700"
        >
          <option value="">All Types</option>
          {TYPES.slice(1).map((t) => (
            <option key={t} value={t}>{alertTypeLabel(t)}</option>
          ))}
        </select>
      </div>

      {generateMutation.isSuccess && (
        <div className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-2">
          Generated {generateMutation.data?.generated ?? 0} new alerts.
        </div>
      )}

      {isLoading && (
        <div className="text-sm text-slate-400">Loading alerts...</div>
      )}

      <div className="space-y-3">
        {alerts.map((alert) => (
          <AlertCard key={alert.id} alert={alert} />
        ))}
        {!isLoading && alerts.length === 0 && (
          <div className="text-center text-slate-400 py-12">No alerts found</div>
        )}
      </div>
    </div>
  );
}
