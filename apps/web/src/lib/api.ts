const API_BASE =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    : "/api";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

// Districts
export const getDistricts = () => apiFetch<DistrictWithRisk[]>("/districts");
export const getDistrict = (id: number) => apiFetch<DistrictWithRisk>(`/districts/${id}`);

// Risk
export const getLatestRisk = (params?: { type?: string; district_id?: number }) => {
  const q = new URLSearchParams();
  if (params?.type) q.set("type", params.type);
  if (params?.district_id) q.set("district_id", String(params.district_id));
  return apiFetch<RiskScore[]>(`/risk/latest${q.toString() ? "?" + q : ""}`);
};
export const getRiskHistory = (district_id: number, limit = 30) =>
  apiFetch<RiskScore[]>(`/risk/history?district_id=${district_id}&limit=${limit}`);
export const getRiskHorizons = (district_id: number) =>
  apiFetch<RiskHorizon[]>(`/risk/horizons/${district_id}`);

// Alerts
export const getAlerts = (params?: { severity?: string; alert_type?: string; district_id?: number; status?: string }) => {
  const q = new URLSearchParams();
  if (params?.severity) q.set("severity", params.severity);
  if (params?.alert_type) q.set("alert_type", params.alert_type);
  if (params?.district_id) q.set("district_id", String(params.district_id));
  if (params?.status) q.set("status", params.status);
  return apiFetch<Alert[]>(`/alerts${q.toString() ? "?" + q : ""}`);
};
export const generateAlerts = () =>
  apiFetch<{ generated: number }>("/alerts/generate", { method: "POST" });

// Farmers
export const getFarmers = (district_id?: number) =>
  apiFetch<Farmer[]>(`/farmers${district_id ? "?district_id=" + district_id : ""}`);
export const registerFarmer = (data: FarmerCreate) =>
  apiFetch<Farmer>("/farmers", { method: "POST", body: JSON.stringify(data) });

// SMS
export const sendSMS = (data: SMSSendRequest) =>
  apiFetch<SMSSendResult>("/sms/send", { method: "POST", body: JSON.stringify(data) });
export const getSMSLogs = (district_id?: number) =>
  apiFetch<SMSLog[]>(`/sms/logs${district_id ? "?district_id=" + district_id : ""}`);

// Ingest
export const triggerIngest = () =>
  apiFetch<unknown>("/ingest/weather", { method: "POST" });
export const triggerComputeRisk = () =>
  apiFetch<unknown>("/ingest/compute-risk", { method: "POST" });

// Storage
export const getStorageUnits = (params?: { farmer_id?: number; district_id?: number }) => {
  const q = new URLSearchParams();
  if (params?.farmer_id) q.set("farmer_id", String(params.farmer_id));
  if (params?.district_id) q.set("district_id", String(params.district_id));
  return apiFetch<StorageUnit[]>(`/storage/units${q.toString() ? "?" + q : ""}`);
};
export const registerStorageUnit = (data: StorageUnitCreate) =>
  apiFetch<StorageUnit>("/storage/units", { method: "POST", body: JSON.stringify(data) });
export const getStorageUnit = (id: number) =>
  apiFetch<StorageUnit>(`/storage/units/${id}`);
export const submitSiloReading = (unit_id: number, data: SiloReadingCreate) =>
  apiFetch<{ reading_id: number; risk: StorageReadingRisk }>(`/storage/units/${unit_id}/readings`, {
    method: "POST",
    body: JSON.stringify(data),
  });
export const getSiloReadings = (unit_id: number) =>
  apiFetch<SiloReading[]>(`/storage/units/${unit_id}/readings`);
export const getStorageRisk = (unit_id: number) =>
  apiFetch<StorageRisk>(`/storage/units/${unit_id}/risk`);
export const computeStorageRisks = () =>
  apiFetch<{ computed: number }>("/storage/compute-risk", { method: "POST" });

// Auth
export const login = (email: string, password: string) =>
  apiFetch<{ access_token: string; user: User }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

// Types
export interface District {
  id: number;
  name: string;
  region: string | null;
  country: string;
  centroid_lat: number | null;
  centroid_lon: number | null;
  slope_index: number;
  flood_exposure_index: number;
  created_at: string;
}

export interface DistrictWithRisk extends District {
  flood_score: number | null;
  flood_level: string | null;
  landslide_score: number | null;
  landslide_level: string | null;
  food_stress_score: number | null;
  food_stress_level: string | null;
}

export interface TopDriversJson {
  flood?: Driver[];
  landslide?: Driver[];
  food_stress?: Driver[];
  descriptions?: Record<string, string>;
  [key: string]: Driver[] | Record<string, string> | undefined;
}

export interface RiskScore {
  id: number;
  district_id: number;
  district_name: string | null;
  date: string;
  flood_score: number | null;
  flood_level: string | null;
  landslide_score: number | null;
  landslide_level: string | null;
  food_stress_score: number | null;
  food_stress_level: string | null;
  top_drivers_json: TopDriversJson | null;
  recommendations_json: Record<string, string[]> | null;
  created_at: string;
}

export interface RiskLevelScore {
  score: number;
  level: string;
  description?: string;
}

export interface RiskHorizon {
  key: string;
  label: string;
  target_date: string;
  note?: string;
  flood: RiskLevelScore;
  landslide: RiskLevelScore;
  food_stress: RiskLevelScore;
}

export interface Driver {
  factor: string;
  contribution: number;
  value: number;
}

export interface Alert {
  id: number;
  district_id: number;
  district_name: string | null;
  alert_type: string | null;
  severity: string | null;
  title: string | null;
  message: string | null;
  recommended_action: string | null;
  issued_at: string;
  status: string | null;
}

export interface Farmer {
  id: number;
  full_name: string | null;
  phone_number: string;
  district_id: number | null;
  district_name: string | null;
  preferred_language: string;
  consent_status: boolean;
  created_at: string;
}

export interface FarmerCreate {
  full_name?: string;
  phone_number: string;
  district_id?: number;
  preferred_language?: string;
  consent_status?: boolean;
}

export interface SMSSendRequest {
  district_id: number;
  alert_type: string;
  severity: string;
  alert_id?: number;
}

export interface SMSSendResult {
  sent: number;
  district: string;
  message_preview: string;
}

export interface SMSLog {
  id: number;
  farmer_id: number | null;
  district_id: number | null;
  district_name: string | null;
  alert_id: number | null;
  phone_number: string;
  message: string | null;
  provider: string | null;
  delivery_status: string | null;
  sent_at: string;
}

export interface User {
  id: number;
  full_name: string | null;
  email: string;
  role: string;
  organization: string | null;
  created_at: string;
}

export interface StorageLatestRisk {
  score: number;
  level: string;
  predicted_days_safe: number;
  recommendation: string | null;
}

export interface StorageLatestReading {
  timestamp: string;
  moisture_pct: number | null;
  temp_c: number | null;
  humidity_pct: number | null;
  co2_ppm: number | null;
}

export interface StorageUnit {
  id: number;
  farmer_id: number;
  farmer_name: string | null;
  district_id: number | null;
  district_name: string | null;
  unit_name: string;
  hermetic_type: string;
  capacity_kg: number | null;
  grain_type: string;
  subscription_tier: string;
  install_date: string | null;
  is_active: boolean;
  created_at: string;
  latest_risk: StorageLatestRisk | null;
  latest_reading: StorageLatestReading | null;
}

export interface StorageUnitCreate {
  farmer_id: number;
  district_id?: number;
  unit_name: string;
  hermetic_type?: string;
  capacity_kg?: number;
  grain_type?: string;
  subscription_tier?: string;
  install_date?: string;
}

export interface SiloReadingCreate {
  temp_c?: number;
  moisture_pct?: number;
  humidity_pct?: number;
  co2_ppm?: number;
}

export interface SiloReading {
  id: number;
  timestamp: string;
  temp_c: number | null;
  moisture_pct: number | null;
  humidity_pct: number | null;
  co2_ppm: number | null;
}

export interface StorageDriver {
  factor: string;
  contribution: number;
  value: number;
  raw: string;
}

export interface StorageReadingRisk {
  score: number;
  level: string;
  predicted_days_safe: number;
  description: string;
  recommendations: string[];
}

export interface StorageRisk {
  unit_id: number;
  date: string;
  score: number;
  level: string;
  predicted_days_safe: number;
  top_drivers: StorageDriver[];
  recommendation: string | null;
}
