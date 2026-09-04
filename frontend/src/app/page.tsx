"use client";

import React, { useState, useEffect, useMemo } from "react";
import { BsFileEarmarkTextFill } from "react-icons/bs";
import { PipelineResponse, JobItem, CVProfile } from "@/types/job";
import { API_BASE_URL } from "@/config/api";
import Header from "@/components/Header";
import ProfileSummary from "@/components/ProfileSummary";
import JobGrid from "@/components/JobGrid";
import LoadingState from "@/components/LoadingState";
import CoverLetterModal from "@/components/CoverLetterModal";
import FilterBar from "@/components/FilterBar";
import SocialSearchLinks from "@/components/SocialSearchLinks";
import ApplyStudioModal from "@/components/ApplyStudioModal";
import Pagination from "@/components/Pagination";

const STORAGE_KEY_PROFILE = "jobpilot_saved_profile";
const STORAGE_KEY_JOBS = "jobpilot_saved_jobs";
const STORAGE_KEY_APPLIED = "jobpilot_applied_jobs";
const STORAGE_KEY_SYNC_TIME = "jobpilot_last_synced";

const ITEMS_PER_PAGE = 6; // প্রতি পেজে ৬টি করে জব

export default function DashboardPage() {
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

  useEffect(() => {
    try {
      const savedProfile = localStorage.getItem(STORAGE_KEY_PROFILE);
      const savedJobs = localStorage.getItem(STORAGE_KEY_JOBS);
      const savedApplied = localStorage.getItem(STORAGE_KEY_APPLIED);
      const savedTime = localStorage.getItem(STORAGE_KEY_SYNC_TIME);

      if (savedProfile) setProfile(JSON.parse(savedProfile));
      if (savedJobs) setJobs(JSON.parse(savedJobs));
      if (savedApplied) setAppliedJobs(JSON.parse(savedApplied));
      if (savedTime) setLastSynced(savedTime);
    } catch (e) {
      console.error("Local storage load error:", e);
    }
  }, []);

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

  // ট্যাব, সার্চ বা জেলা পরিবর্তন হলে পেজ নাম্বার ১-এ রিসেট
  useEffect(() => {
    setCurrentPage(1);
  }, [selectedTab, selectedDistrict, searchKeyword]);

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
      if (!res.ok) throw new Error("Pipeline execution failed");
      const result: PipelineResponse = await res.json();

      const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      setProfile(result.profile);
      setJobs(result.matched_jobs);
      setLastSynced(timeStr);
      setCurrentPage(1);

      localStorage.setItem(STORAGE_KEY_PROFILE, JSON.stringify(result.profile));
      localStorage.setItem(STORAGE_KEY_JOBS, JSON.stringify(result.matched_jobs));
      localStorage.setItem(STORAGE_KEY_SYNC_TIME, timeStr);
    } catch (err) {
      alert("Error parsing resume and aggregating jobs. Ensure backend is running.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshJobs = async () => {
    if (!profile) return;

    setRefreshing(true);
    try {
      const searchKeywords = profile.preferred_job_titles?.length
        ? profile.preferred_job_titles
        : profile.skills.slice(0, 4);

      const res = await fetch(`${API_BASE_URL}/api/jobs/search`, {
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

      const matchRes = await fetch(`${API_BASE_URL}/api/jobs/match`, {
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

  // পেজিনেশন স্লাইস ও পেইজ ট্রানজিশন
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
    <div className="min-h-screen bg-[#090D16] text-slate-100 p-4 sm:p-6 md:p-12 font-sans selection:bg-cyan-500 selection:text-slate-950 overflow-x-hidden w-full">
      <div className="max-w-6xl mx-auto space-y-6 md:space-y-8 w-full">
        <Header
          loading={loading}
          refreshing={refreshing}
          hasProfile={!!profile}
          lastSynced={lastSynced}
          onFileUpload={handleFileUpload}
          onRefreshJobs={handleRefreshJobs}
        />

        <main className="space-y-6 md:space-y-8">
          {loading && <LoadingState />}

          {!loading && !profile && (
            <div className="rounded-3xl border border-dashed border-cyan-950/80 bg-slate-900/20 p-12 md:p-20 text-center flex flex-col items-center justify-center">
              <div className="p-4 rounded-2xl bg-slate-950 border border-cyan-950 text-cyan-400 mb-4 shadow-sm">
                <BsFileEarmarkTextFill className="w-8 h-8 md:w-10 md:h-10" />
              </div>
              <h3 className="text-lg md:text-xl font-bold text-slate-200">No Resume Uploaded</h3>
              <p className="text-slate-400 text-xs md:text-sm max-w-sm mt-2 leading-relaxed">
                Upload your PDF or DOCX resume once. It will stay saved so you can check fresh vacancies anytime with a single click.
              </p>
            </div>
          )}

          {!loading && profile && (
            <>
              <ProfileSummary profile={profile} totalFound={jobs.length} />

              <div className="space-y-4">
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

                {/* জব কার্ড গ্রিড */}
                <JobGrid
                  jobs={paginatedJobs}
                  profile={profile}
                  appliedJobs={appliedJobs}
                  onToggleApply={toggleApplied}
                  onOpenCoverLetter={(job) => setSelectedJobForModal(job)}
                  onOpenApplyStudio={(job) => setSelectedJobForStudio(job)}
                />

                {/* রিইউজেবল পেজিনেশন কম্পোনেন্ট */}
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  totalItems={filteredJobs.length}
                  itemsPerPage={ITEMS_PER_PAGE}
                  onPageChange={handlePageChange}
                />
              </div>
            </>
          )}
        </main>
      </div>

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