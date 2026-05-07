"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getDistricts, getSMSLogs, sendSMS } from "@/lib/api";
import { alertTypeLabel, formatDateTime, levelBadge } from "@/lib/utils";

const ALERT_TYPES = ["flood", "landslide", "food_stress"];
const SEVERITIES = ["Low", "Medium", "High"];

export default function SMSPage() {
  const queryClient = useQueryClient();
  const [districtFilter, setDistrictFilter] = useState<number | undefined>();
  const [form, setForm] = useState({
    district_id: "",
    alert_type: "flood",
    severity: "High",
  });
  const [preview, setPreview] = useState<string | null>(null);

  const { data: districts = [] } = useQuery({
    queryKey: ["districts"],
    queryFn: getDistricts,
  });

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ["smsLogs", districtFilter],
    queryFn: () => getSMSLogs(districtFilter),
  });

  const sendMutation = useMutation({
    mutationFn: sendSMS,
    onSuccess: (data) => {
      setPreview(data.message_preview);
      queryClient.invalidateQueries({ queryKey: ["smsLogs"] });
    },
  });

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.district_id) return;
    sendMutation.mutate({
      district_id: Number(form.district_id),
      alert_type: form.alert_type,
      severity: form.severity,
    });
  };

  const deliveryColor = (status: string | null) => {
    if (status === "delivered") return "text-green-600 bg-green-50";
    if (status === "failed") return "text-red-600 bg-red-50";
    return "text-slate-500 bg-slate-50";
  };

  return (
    <div className="space-y-5 p-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">SMS Module</h1>
        <p className="text-sm text-slate-500">Send alerts and view delivery logs</p>
      </div>

      {/* SMS Composer */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
        <h2 className="font-semibold text-slate-800">Send Alert SMS</h2>
        <form onSubmit={handleSend} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">District *</label>
              <select
                required
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
              <label className="block text-xs font-medium text-slate-600 mb-1">Alert Type</label>
              <select
                value={form.alert_type}
                onChange={(e) => setForm({ ...form, alert_type: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white"
              >
                {ALERT_TYPES.map((t) => (
                  <option key={t} value={t}>{alertTypeLabel(t)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Severity</label>
              <select
                value={form.severity}
                onChange={(e) => setForm({ ...form, severity: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white"
              >
                {SEVERITIES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          {preview && (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm text-slate-700 font-mono">
              <div className="text-xs text-slate-400 mb-1">Last message sent:</div>
              {preview}
            </div>
          )}

          {sendMutation.isSuccess && (
            <div className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-2">
              Sent to {sendMutation.data?.sent} farmers in {sendMutation.data?.district}.
            </div>
          )}

          <button
            type="submit"
            disabled={sendMutation.isPending || !form.district_id}
            className="bg-emerald-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            {sendMutation.isPending ? "Sending..." : "Send SMS to District"}
          </button>
        </form>
      </div>

      {/* Log filter */}
      <div className="flex items-center gap-3">
        <h2 className="font-semibold text-slate-800">Delivery Log</h2>
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

      {/* Logs table */}
      {isLoading ? (
        <div className="text-sm text-slate-400">Loading logs...</div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-xs font-medium text-slate-500 uppercase tracking-wide">
                <th className="px-4 py-3 text-left">Phone</th>
                <th className="px-4 py-3 text-left">District</th>
                <th className="px-4 py-3 text-left">Message</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Sent</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-slate-600">{log.phone_number}</td>
                  <td className="px-4 py-3 text-slate-600">{log.district_name ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-500 text-xs max-w-xs truncate">
                    {log.message}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${deliveryColor(
                        log.delivery_status
                      )}`}
                    >
                      {log.delivery_status ?? "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{formatDateTime(log.sent_at)}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-slate-400">
                    No SMS logs yet
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
