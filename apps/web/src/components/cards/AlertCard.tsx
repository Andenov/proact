import { Alert } from "@/lib/api";
import { alertTypeLabel, formatDateTime, levelBadge } from "@/lib/utils";

export default function AlertCard({ alert }: { alert: Alert }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full ${levelBadge(
                alert.severity as "Low" | "Medium" | "High"
              )}`}
            >
              {alert.severity}
            </span>
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
              {alertTypeLabel(alert.alert_type)}
            </span>
          </div>
          <div className="font-semibold text-sm mt-2 text-slate-800">{alert.title}</div>
          <div className="text-xs text-slate-500 mt-0.5">{alert.district_name}</div>
        </div>
        <div className="text-xs text-slate-400 shrink-0">{formatDateTime(alert.issued_at)}</div>
      </div>
      {alert.recommended_action && (
        <div className="mt-3 text-xs text-slate-600 bg-slate-50 rounded-md p-2 border border-slate-100">
          <span className="font-medium">Action: </span>
          {alert.recommended_action.split(";")[0]}
        </div>
      )}
    </div>
  );
}
