"use client";

import { useEffect, useRef } from "react";
import { DistrictWithRisk } from "@/lib/api";
import { levelColor } from "@/lib/utils";

interface Props {
  districts: DistrictWithRisk[];
  riskType: "flood" | "landslide" | "food_stress";
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export default function RiskMap({ districts, riskType, selectedId, onSelect }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<unknown>(null);
  const markersRef = useRef<unknown[]>([]);

  const getLevel = (d: DistrictWithRisk) => {
    if (riskType === "flood") return d.flood_level;
    if (riskType === "landslide") return d.landslide_level;
    return d.food_stress_level;
  };

  useEffect(() => {
    if (typeof window === "undefined" || !mapRef.current) return;

    import("leaflet").then((L) => {
      // Fix default icon paths
      delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      if (!mapInstanceRef.current) {
        const map = L.map(mapRef.current!, {
          center: [1.5, 34.3],
          zoom: 7,
          zoomControl: true,
        });

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap contributors",
          opacity: 0.6,
        }).addTo(map);

        mapInstanceRef.current = map;
      }

      const map = mapInstanceRef.current as ReturnType<typeof L.map>;

      // Clear old markers
      (markersRef.current as ReturnType<typeof L.circleMarker>[]).forEach((m) => m.remove());
      markersRef.current = [];

      // Add district markers
      districts.forEach((d) => {
        if (!d.centroid_lat || !d.centroid_lon) return;
        const level = getLevel(d);
        const color = levelColor(level as "Low" | "Medium" | "High");
        const isSelected = d.id === selectedId;

        const marker = L.circleMarker([d.centroid_lat, d.centroid_lon], {
          radius: isSelected ? 18 : 14,
          fillColor: color,
          color: isSelected ? "#1e293b" : "#fff",
          weight: isSelected ? 3 : 2,
          opacity: 1,
          fillOpacity: 0.85,
        })
          .bindTooltip(
            `<strong>${d.name}</strong><br/>${riskType.replace("_", " ")} risk: ${level ?? "No data"}`,
            { permanent: false, direction: "top" }
          )
          .addTo(map);

        marker.on("click", () => onSelect(d.id));
        markersRef.current.push(marker);
      });
    });
  }, [districts, riskType, selectedId]);

  return (
    <div className="relative w-full h-full">
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      />
      <div ref={mapRef} className="w-full h-full rounded-lg" />
    </div>
  );
}
