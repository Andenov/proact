import { RISK_COLORS } from "@/lib/utils";

export default function MapLegend() {
  return (
    <div className="absolute bottom-4 right-4 bg-[#132240]/90 backdrop-blur-sm rounded-lg border border-white/10 p-3 z-[1000] text-xs">
      <div className="font-semibold mb-2 text-slate-300">Risk Level</div>
      {(["High", "Medium", "Low"] as const).map((level) => (
        <div key={level} className="flex items-center gap-2 mb-1">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: RISK_COLORS[level] }}
          />
          <span className="text-slate-400">{level}</span>
        </div>
      ))}
    </div>
  );
}
