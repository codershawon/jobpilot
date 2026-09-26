"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useUser } from "@clerk/nextjs";
import { PipelineResponse, JobItem, CVProfile } from "@/types/job";
import { API_BASE_URL } from "@/config/api";
import { useJobPilotApi } from "@/hooks/useJobPilotApi";
import { useApplications } from "@/hooks/useApplications";

import Header from "@/components/Header";
import ProfileSummary from "@/components/ProfileSummary";
import JobGrid from "@/components/JobGrid";
import LoadingState from "@/components/LoadingState";
import CoverLetterModal from "@/components/CoverLetterModal";
import FilterBar, { Category } from "@/components/FilterBar";
import SocialSearchLinks from "@/components/SocialSearchLinks";
import ApplyStudioModal from "@/components/ApplyStudioModal";
import Footer from "@/components/Footer";
import Pagination from "@/components/Pagination";
import Container from "@/components/Container";
import LandingBanner from "@/components/LandingHero";
import SupportedPlatforms from "@/components/SupportedPlatforms";
import HowItWorks from "@/components/HowItWorks";
import UrgentDeadlines from "@/components/UrgentDeadlines";
import OfficialPortals from "@/components/OfficialPortals";

const STORAGE_KEY_PROFILE = "jobpilot_saved_profile";
const STORAGE_KEY_JOBS = "jobpilot_saved_jobs";
const STORAGE_KEY_APPLIED = "jobpilot_applied_jobs";
const STORAGE_KEY_SYNC_TIME = "jobpilot_last_synced";

const ITEMS_PER_PAGE = 6;

export default function DashboardPage() {
  const { isSignedIn, isLoaded } = useUser();
  const { fetchSavedPipeline, savePipeline } = useJobPilotApi();
  const { statusByJobId, saveApplication } = useApplications();

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
  const [selectedSectors, setSelectedSectors] = useState<string[]>([]);
  const [selectedFunction, setSelectedFunction] = useState("ALL");
  const [selectedSource, setSelectedSource] = useState("ALL");
  const [categories, setCategories] = useState<{sectors: Category[]; functions: Category[]; sources: Category[]}>({ sectors: [], functions: [], sources: [] });
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

  // ২.১ ক্যাটাগরি তালিকা লোড
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/categories`)
      .then((res) => res.json())
      .then((data) => {
        if (data.sectors) setCategories(data);
      })
      .catch(() => {
        setTimeout(() => {
          fetch(`${API_BASE_URL}/api/categories`)
            .then((r) => r.json())
            .then((d) => d.sectors && setCategories(d))
            .catch(() => {});
        }, 3000);
      });
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentPage(1);
  }, [selectedTab, selectedDistrict, searchKeyword, selectedSectors, selectedFunction, selectedSource]);

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

      // CV অনুযায়ী কাজের ক্ষেত্র নিজে থেকেই বাছা হবে
      if (result.profile.job_function && result.profile.job_function !== "general") {
        setSelectedFunction(result.profile.job_function);
      }

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
    const nowApplied = !appliedJobs[id];

    // UI সাথে সাথে বদলাবে, তারপর সার্ভারে যাবে
    setAppliedJobs((prev) => {
      const updated = { ...prev, [id]: nowApplied };
      localStorage.setItem(STORAGE_KEY_APPLIED, JSON.stringify(updated));
      return updated;
    });

    // লগইন থাকলে ডাটাবেসেও — তখন যেকোনো ডিভাইসে দেখা যাবে
    if (isSignedIn && nowApplied) {
      saveApplication(id, "APPLIED").catch((e) =>
        console.error("ট্র্যাকারে যোগ করা যায়নি:", e)
      );
    }
  };

  const toggleSector = (id: string) => {
    setSelectedSectors((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const clearAllFilters = () => {
    setSelectedSectors([]);
    setSelectedFunction("ALL");
    setSelectedSource("ALL");
    setSelectedDistrict("ALL");
    setSearchKeyword("");
    setSelectedTab("ALL");
  };

  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      // ১. স্ট্যাটাস ট্যাব
      if (selectedTab === "APPLIED" && !appliedJobs[job.id]) return false;
      if (selectedTab === "HIGH_MATCH" && (job.match_score || 0) < 50) return false;

      // ২. সেক্টর — একটাও মিললেই চলবে
      const jobSectors = job.sectors || ["private"];
      if (selectedSectors.length > 0 && !selectedSectors.some((s) => jobSectors.includes(s)))
        return false;

      // ৩. কাজের ক্ষেত্র
      if (selectedFunction !== "ALL" && job.job_function !== selectedFunction)
        return false;

      // ৪. উৎস
      if (
        selectedSource !== "ALL" &&
        !(job.source || "").toUpperCase().includes(selectedSource.toUpperCase())
      )
        return false;

      // ৫. কি-ওয়ার্ড
      const kw = (searchKeyword || "").toLowerCase().trim();
      if (kw) {
        const hay = `${job.title} ${job.company} ${(job.tags || []).join(" ")}`.toLowerCase();
        if (!hay.includes(kw)) return false;
      }

      // ৬. জেলা — সরকারি ও রিমোট জব সব জেলাতেই দেখাবে
      if (selectedDistrict !== "ALL") {
        const target = selectedDistrict.toLowerCase().trim();
        const place = `${job.district || ""} ${job.location || ""}`.toLowerCase();
        const isCountryWide =
          job.is_remote || jobSectors.includes("govt") || place.includes("bangladesh");
        if (!isCountryWide && !place.includes(target)) return false;
      }

      return true;
    });
  }, [
    jobs,
    selectedTab,
    appliedJobs,
    searchKeyword,
    selectedDistrict,
    selectedSectors,
    selectedFunction,
    selectedSource,
  ]);

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
            <UrgentDeadlines
              jobs={jobs}
              appliedJobs={appliedJobs}
              onOpenApplyStudio={(job) => setSelectedJobForStudio(job)}
            />

            <FilterBar
              selectedTab={selectedTab}
              onSelectTab={setSelectedTab}
              totalCount={jobs.length}
              sectors={categories.sectors}
              selectedSectors={selectedSectors}
              onToggleSector={toggleSector}
              functions={categories.functions}
              selectedFunction={selectedFunction}
              onSelectFunction={setSelectedFunction}
              sources={categories.sources}
              selectedSource={selectedSource}
              onSelectSource={setSelectedSource}
              districts={districts}
              selectedDistrict={selectedDistrict}
              onSelectDistrict={setSelectedDistrict}
              searchKeyword={searchKeyword}
              onSearchKeywordChange={setSearchKeyword}
              profileFunction={profile?.job_function}
              onClearAll={clearAllFilters}
            />

            <SocialSearchLinks
              keyword={searchKeyword || profile.preferred_job_titles?.[0] || "React Developer"}
              location={selectedDistrict !== "ALL" ? selectedDistrict : profile.district || "Bangladesh"}
            />

            <OfficialPortals />

            <JobGrid
              jobs={paginatedJobs}
              profile={profile}
              appliedJobs={{ ...appliedJobs, ...Object.fromEntries(
                Object.entries(statusByJobId).map(([k, v]) => [k, v !== "SAVED"])
              ) }}
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