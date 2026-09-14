"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useUser } from "@clerk/nextjs";
import { PipelineResponse, JobItem, CVProfile } from "@/types/job";
import { API_BASE_URL } from "@/config/api";
import { useJobPilotApi } from "@/hooks/useJobPilotApi";

import Header from "@/components/Header";
import ProfileSummary from "@/components/ProfileSummary";
import JobGrid from "@/components/JobGrid";
import LoadingState from "@/components/LoadingState";
import CoverLetterModal from "@/components/CoverLetterModal";
import FilterBar from "@/components/FilterBar";
import SocialSearchLinks from "@/components/SocialSearchLinks";
import ApplyStudioModal from "@/components/ApplyStudioModal";
import LandingHero from "@/components/LandingHero";
import Footer from "@/components/Footer";
import Pagination from "@/components/Pagination";

const STORAGE_KEY_PROFILE = "jobpilot_saved_profile";
const STORAGE_KEY_JOBS = "jobpilot_saved_jobs";
const STORAGE_KEY_APPLIED = "jobpilot_applied_jobs";
const STORAGE_KEY_SYNC_TIME = "jobpilot_last_synced";

const ITEMS_PER_PAGE = 6;

export default function DashboardPage() {
  const { isSignedIn, isLoaded } = useUser();
  const { fetchSavedPipeline, savePipeline } = useJobPilotApi();

  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [profile, setProfile] = useState<CVProfile | null>(null);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [selectedTab, setSelectedTab] = useState<string>("ALL");
  const [selectedJobForModal, setSelectedJobForModal] = useState<JobItem | null>(null);
  const [appliedJobs, setAppliedJobs] = useState<Record<string, boolean>>({});
  const [lastSynced, setLastSynced] = useState<string | null>(null);
  const [districts, setDistricts] = useState<string[]>([]);
  const [selectedDistrict, setSelectedDistrict] = useState<string>("ALL");
  const [searchKeyword, setSearchKeyword] = useState<string>("");
  const [selectedJobForStudio, setSelectedJobForStudio] = useState<JobItem | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);

  // ১. ইউজার ডেটা লোড
  useEffect(() => {
    if (!isLoaded) return;

    if (isSignedIn) {
      fetchSavedPipeline()
        .then((data) => {
          if (data && data.profile) {
            setProfile(data.profile);
            setJobs(data.matched_jobs || []);
            setLastSynced(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
          }
        })
        .catch((err) => {
          console.log("Database fetch info:", err);
        });
    } else {
      try {
        const savedProfile = localStorage.getItem(STORAGE_KEY_PROFILE);
        const savedJobs = localStorage.getItem(STORAGE_KEY_JOBS);
        const savedApplied = localStorage.getItem(STORAGE_KEY_APPLIED);
        const savedTime = localStorage.getItem(STORAGE_KEY_SYNC_TIME);

        // eslint-disable-next-line react-hooks/set-state-in-effect
        if (savedProfile) setProfile(JSON.parse(savedProfile));
        if (savedJobs) setJobs(JSON.parse(savedJobs));
        if (savedApplied) setAppliedJobs(JSON.parse(savedApplied));
        if (savedTime) setLastSynced(savedTime);
      } catch (e) {
        console.error("Local storage load error:", e);
      }
    }
  }, [isSignedIn, isLoaded, fetchSavedPipeline]);

  // ২. জেলা তালিকা লোড
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/districts`)
      .then((res) => res.json())
      .then((data) => {
        if (data.districts && Array.isArray(data.districts)) {
          setDistricts(data.districts);
        }
      })
      .catch((err) => console.error("District fetch error:", err));
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentPage(1);
  }, [selectedTab, selectedDistrict, searchKeyword]);

  // ৩. রেজুমে আপলোড ও পাইপলাইন রান
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE_URL}/api/pipeline/run`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Pipeline execution failed");
      }

      const result: PipelineResponse = await res.json();
      const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      setProfile(result.profile);
      setJobs(result.matched_jobs);
      setLastSynced(timeStr);
      setCurrentPage(1);

      if (isSignedIn) {
        try {
          await savePipeline(result);
        } catch (dbErr) {
          console.error("Database save error:", dbErr);
        }
      }

      localStorage.setItem(STORAGE_KEY_PROFILE, JSON.stringify(result.profile));
      localStorage.setItem(STORAGE_KEY_JOBS, JSON.stringify(result.matched_jobs));
      localStorage.setItem(STORAGE_KEY_SYNC_TIME, timeStr);
    } catch (err: unknown) {
      const errorMessage =
        typeof err === "object" && err !== null && "message" in err
          ? err.message
          : "Error parsing resume and aggregating jobs. Ensure backend is running.";
      alert(errorMessage);
      console.error(err);
    } finally {
      setLoading(false);
      e.target.value = "";
    }
  };

  // ৪. জব রিফ্রেশ
  const handleRefreshJobs = async () => {
    if (!profile) return;

    setRefreshing(true);
    try {
      const searchKeywords = profile.preferred_job_titles?.length
        ? profile.preferred_job_titles
        : profile.skills.slice(0, 4);

      const res = await fetch(`${API_BASE_URL}/api/pipeline/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          keywords: searchKeywords,
          districts: [profile.district || "Cumilla", "Dhaka"],
          include_remote: true,
          include_gov: true,
        }),
      });

      if (!res.ok) throw new Error("Job search failed");
      const searchData = await res.json();

      const matchRes = await fetch(`${API_BASE_URL}/api/pipeline/match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile: profile,
          jobs: searchData.jobs,
          generate_cover_letters_for_top: 3,
        }),
      });

      if (!matchRes.ok) throw new Error("Job matching failed");
      const matchData = await matchRes.json();

      const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      setJobs(matchData.matched_jobs);
      setLastSynced(timeStr);
      setCurrentPage(1);

      if (isSignedIn) {
        savePipeline({
          profile: profile,
          total_found: matchData.matched_jobs.length,
          matched_jobs: matchData.matched_jobs,
        }).catch((err) => console.error("Auto-sync to DB error:", err));
      }

      localStorage.setItem(STORAGE_KEY_JOBS, JSON.stringify(matchData.matched_jobs));
      localStorage.setItem(STORAGE_KEY_SYNC_TIME, timeStr);
    } catch (err) {
      alert("Failed to refresh live vacancies. Please try again.");
      console.error(err);
    } finally {
      setRefreshing(false);
    }
  };

  const toggleApplied = (id: string) => {
    setAppliedJobs((prev) => {
      const updated = { ...prev, [id]: !prev[id] };
      localStorage.setItem(STORAGE_KEY_APPLIED, JSON.stringify(updated));
      return updated;
    });
  };

  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      let matchesTab = true;
      if (selectedTab === "APPLIED") matchesTab = !!appliedJobs[job.id];
      else if (selectedTab === "REMOTE") matchesTab = job.is_remote;
      else if (selectedTab === "LOCAL") matchesTab = !job.is_remote;
      else if (selectedTab === "HIGH_MATCH") matchesTab = (job.match_score || 0) >= 50;
      else if (selectedTab !== "ALL") matchesTab = job.source.toUpperCase() === selectedTab;

      const kw = searchKeyword.toLowerCase();
      const matchesKeyword =
        !searchKeyword ||
        job.title.toLowerCase().includes(kw) ||
        job.company.toLowerCase().includes(kw) ||
        (job.tags && job.tags.some((t) => t.toLowerCase().includes(kw)));

      const matchesDistrict =
        selectedDistrict === "ALL" ||
        (job.district && job.district.toLowerCase() === selectedDistrict.toLowerCase()) ||
        (job.location && job.location.toLowerCase().includes(selectedDistrict.toLowerCase()));

      return matchesTab && matchesKeyword && matchesDistrict;
    });
  }, [jobs, selectedTab, appliedJobs, searchKeyword, selectedDistrict]);

  const totalPages = Math.ceil(filteredJobs.length / ITEMS_PER_PAGE) || 1;
  const paginatedJobs = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredJobs.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [filteredJobs, currentPage]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 320, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-[#090D16] text-slate-100 font-sans selection:bg-cyan-500 selection:text-slate-950 flex flex-col justify-between w-full">
      {/* 1. Header (পুরো স্ক্রিন জুড়ে বর্ডার ও গ্লাস ইফেক্ট পাবে) */}
      <Header
        loading={loading}
        refreshing={refreshing}
        hasProfile={!!profile}
        lastSynced={lastSynced}
        onFileUpload={handleFileUpload}
        onRefreshJobs={handleRefreshJobs}
      />

      {/* 2. Main Content Container (প্রশস্ত ও স্ট্যান্ডার্ড 7xl উইডথ) */}
      <main className="flex-1 w-full py-8 md:py-10 space-y-8">
        {loading && <LoadingState />}

        {!loading && !profile && (
          <LandingHero onFileUpload={handleFileUpload} loading={loading} />
        )}

        {!loading && profile && (
          <div className="space-y-6">
            <ProfileSummary profile={profile} totalFound={jobs.length} />

            <FilterBar
              selectedTab={selectedTab}
              onSelectTab={setSelectedTab}
              totalCount={filteredJobs.length}
              districts={districts}
              selectedDistrict={selectedDistrict}
              onSelectDistrict={setSelectedDistrict}
              searchKeyword={searchKeyword}
              onSearchKeywordChange={setSearchKeyword}
            />

            <SocialSearchLinks
              keyword={searchKeyword || profile.preferred_job_titles?.[0] || "React Developer"}
              location={selectedDistrict !== "ALL" ? selectedDistrict : profile.district || "Bangladesh"}
            />

            <JobGrid
              jobs={paginatedJobs}
              profile={profile}
              appliedJobs={appliedJobs}
              onToggleApply={toggleApplied}
              onOpenCoverLetter={(job) => setSelectedJobForModal(job)}
              onOpenApplyStudio={(job) => setSelectedJobForStudio(job)}
            />

            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={filteredJobs.length}
              itemsPerPage={ITEMS_PER_PAGE}
              onPageChange={handlePageChange}
            />
          </div>
        )}
      </main>

      {/* 3. Footer (পুরো স্ক্রিন জুড়ে বিস্তৃত থাকবে) */}
      <Footer />

      {/* Modals */}
      <CoverLetterModal
        job={selectedJobForModal}
        onClose={() => setSelectedJobForModal(null)}
      />

      <ApplyStudioModal
        job={selectedJobForStudio}
        profile={profile}
        isOpen={!!selectedJobForStudio}
        onClose={() => setSelectedJobForStudio(null)}
        onConfirmApply={(jobId) => toggleApplied(jobId)}
      />
    </div>
  );
}