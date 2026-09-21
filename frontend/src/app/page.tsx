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
import Footer from "@/components/Footer";
import Pagination from "@/components/Pagination";
import Container from "@/components/Container";
import LandingBanner from "@/components/LandingHero";
import SupportedPlatforms from "@/components/SupportedPlatforms";
import HowItWorks from "@/components/HowItWorks";

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
    const rawSource = (job.source || "").toUpperCase();
    const rawUrl = (job.url || "").toLowerCase();
    const rawTags = (job.tags || []).map((t: string) => (t || "").toLowerCase());
    const rawTitle = (job.title || "").toLowerCase();
    const rawMatchReason = (job.match_reason || "").toLowerCase();

    // ১. বিডিজবস শনাক্তকরণ (URL বা Source বা Tag)
    const isBdjobs = 
      rawUrl.includes("bdjobs.com") || 
      rawSource.includes("BDJOBS") || 
      rawTags.includes("bdjobs");

    // ২. সরকারি জব শনাক্তকরণ (বিডিজবস কখনোই সরকারি ট্যাবে ঢুকবে না)
    const isGovt = 
      !isBdjobs && (
        rawUrl.includes("bdgovtjob.net") ||
        rawSource.includes("GOV") || 
        rawTags.includes("govt") || 
        rawTags.includes("সরকারি চাকরি") ||
        rawMatchReason.includes("government") ||
        rawTitle.includes("নিয়োগ") ||
        rawTitle.includes("বিজ্ঞপ্তি")
      );

    // ৩. ট্যাব ফিল্টার লজিক
    let matchesTab = true;
    if (selectedTab === "APPLIED") {
      matchesTab = !!appliedJobs[job.id];
    } else if (selectedTab === "REMOTE") {
      matchesTab = Boolean(job.is_remote);
    } else if (selectedTab === "LOCAL") {
      matchesTab = !job.is_remote;
    } else if (selectedTab === "HIGH_MATCH") {
      matchesTab = (job.match_score || 0) >= 50;
    } else if (selectedTab === "BDJOBS") {
      matchesTab = isBdjobs;
    } else if (selectedTab === "GOVT") {
      matchesTab = isGovt;
    } else if (selectedTab === "LINKEDIN") {
      matchesTab = rawSource.includes("LINKEDIN") || rawUrl.includes("linkedin.com");
    } else if (selectedTab === "REMOTIVE") {
      matchesTab = rawSource.includes("REMOTIVE") || rawUrl.includes("remotive.com");
    } else if (selectedTab === "ARBEITNOW") {
      matchesTab = rawSource.includes("ARBEITNOW") || rawUrl.includes("arbeitnow.com");
    } else if (selectedTab !== "ALL") {
      matchesTab = rawSource === selectedTab;
    }

    if (!matchesTab) return false;

    // ৪. কি-ওয়ার্ড সার্চ ফিল্টার (Title, Company, Tags)
    const kw = (searchKeyword || "").toLowerCase().trim();
    if (kw) {
      const titleMatch = rawTitle.includes(kw);
      const compMatch = (job.company || "").toLowerCase().includes(kw);
      const tagMatch = rawTags.some((t: string) => t.includes(kw));
      if (!titleMatch && !compMatch && !tagMatch) return false;
    }

    // ৫. জেলা ফিল্টার (দেশব্যাপী বা রিমোট জব হলে সব জেলাতেই ডিসপ্লে করবে)
    if (selectedDistrict && selectedDistrict !== "ALL") {
      const targetDist = selectedDistrict.toLowerCase().trim();
      const jDist = (job.district || "").toLowerCase().trim();
      const jLoc = (job.location || "").toLowerCase().trim();

      const isCountryWide = 
        jDist.includes("bangladesh") || 
        jLoc.includes("bangladesh") || 
        jLoc.includes("anywhere") ||
        job.is_remote || 
        isGovt;

      const matchesDistrictName = 
        jDist.includes(targetDist) || 
        jLoc.includes(targetDist);

      if (!isCountryWide && !matchesDistrictName) {
        return false;
      }
    }

    return true;
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
    <div className="bg-[#090D16] text-slate-100 font-sans selection:bg-cyan-500 selection:text-slate-950 flex flex-col justify-between w-full">
      {/* 1. Header (Inside it uses <Container>) */}
      <Header
        loading={loading}
        refreshing={refreshing}
        hasProfile={!!profile}
        lastSynced={lastSynced}
        onFileUpload={handleFileUpload}
        onRefreshJobs={handleRefreshJobs}
      />

      {/* 2. Main Content Area */}
      <main className="flex-1 w-full">
        {loading && (
          <Container className="py-12">
            <LoadingState />
          </Container>
        )}

        {/* Guest View: Landing Banner handles its own <Container> internally */}
        {!loading && !profile && (
          <>
            <LandingBanner onFileUpload={handleFileUpload} loading={loading} />
            <SupportedPlatforms />
            <HowItWorks />
          </>
        )}

        {/* Dashboard View: Wrapped in identical <Container> */}
        {!loading && profile && (
          <Container className="py-8 space-y-6">
            <ProfileSummary profile={profile} totalFound={jobs.length} />

            <FilterBar
              selectedTab={selectedTab}
              onSelectTab={setSelectedTab}
              totalCount={jobs.length}
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
          </Container>
        )}
      </main>

      {/* 3. Footer (Inside it uses <Container>) */}
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