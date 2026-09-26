"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { API_BASE_URL } from "@/config/api";

export type AppStatus =
  | "SAVED"
  | "APPLIED"
  | "EXAM"
  | "INTERVIEW"
  | "OFFER"
  | "REJECTED";

export interface ApplicationItem {
  id: string;
  job_id: string;
  status: AppStatus;
  tracking_id?: string | null;
  fee_paid: boolean;
  admit_downloaded: boolean;
  exam_date?: string | null;
  notes: string;
  applied_at?: string | null;
  updated_at?: string | null;
  title: string;
  company: string;
  url: string;
  source: string;
  district: string;
  deadline?: string | null;
  days_left?: number | null;
  urgency?: string;
}

export interface AppStats {
  total: number;
  by_status: Record<string, number>;
  upcoming_exams: number;
}

export function useApplications() {
  const { getToken, isSignedIn, isLoaded } = useAuth();

  const [apps, setApps] = useState<ApplicationItem[]>([]);
  const [stats, setStats] = useState<AppStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const authFetch = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const token = await getToken();
      if (!token) throw new Error("লগইন প্রয়োজন");

      const res = await fetch(`${API_BASE_URL}/api${path}`, {
        ...init,
        headers: {
          ...(init.headers || {}),
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `রিকোয়েস্ট ব্যর্থ (${res.status})`);
      }
      return res.json();
    },
    [getToken]
  );

  const refresh = useCallback(async () => {
    if (!isSignedIn) return;
    setLoading(true);
    setError(null);
    try {
      const [list, s] = await Promise.all([
        authFetch("/applications"),
        authFetch("/applications/stats"),
      ]);
      setApps(list);
      setStats(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "লোড করা যায়নি");
    } finally {
      setLoading(false);
    }
  }, [authFetch, isSignedIn]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (isLoaded && isSignedIn) refresh();
  }, [isLoaded, isSignedIn, refresh]);

  /** জব ট্র্যাকারে যোগ করা বা স্ট্যাটাস বদলানো */
  const saveApplication = useCallback(
    async (jobId: string, status: AppStatus = "APPLIED") => {
      const saved = await authFetch("/applications", {
        method: "POST",
        body: JSON.stringify({ job_id: jobId, status }),
      });
      setApps((prev) => {
        const rest = prev.filter((a) => a.job_id !== jobId);
        return [saved, ...rest];
      });
      return saved as ApplicationItem;
    },
    [authFetch]
  );

  const updateApplication = useCallback(
    async (id: string, patch: Partial<ApplicationItem>) => {
      const updated = await authFetch(`/applications/${id}`, {
        method: "PATCH",
        body: JSON.stringify(patch),
      });
      setApps((prev) => prev.map((a) => (a.id === id ? updated : a)));
      return updated as ApplicationItem;
    },
    [authFetch]
  );

  const removeApplication = useCallback(
    async (id: string) => {
      await authFetch(`/applications/${id}`, { method: "DELETE" });
      setApps((prev) => prev.filter((a) => a.id !== id));
    },
    [authFetch]
  );

  /** job_id → status, JobCard-এ দ্রুত দেখার জন্য */
  const statusByJobId = apps.reduce<Record<string, AppStatus>>((acc, a) => {
    acc[a.job_id] = a.status;
    return acc;
  }, {});

  return {
    apps,
    stats,
    loading,
    error,
    refresh,
    saveApplication,
    updateApplication,
    removeApplication,
    statusByJobId,
  };
}