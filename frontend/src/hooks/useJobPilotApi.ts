import { useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { API_BASE_URL } from "@/config/api";

export function useJobPilotApi() {
  const { getToken } = useAuth();

  const fetchSavedPipeline = useCallback(async () => {
    const token = await getToken();
    const res = await fetch(`${API_BASE_URL}/api/pipeline/saved`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch saved pipeline");
    return await res.json();
  }, [getToken]);

  const savePipeline = useCallback(async (pipelineData: unknown) => {
    const token = await getToken();
    const res = await fetch(`${API_BASE_URL}/api/pipeline/save`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(pipelineData),
    });
    if (!res.ok) throw new Error("Failed to save pipeline");
    return await res.json();
  }, [getToken]);

  return { fetchSavedPipeline, savePipeline };
}