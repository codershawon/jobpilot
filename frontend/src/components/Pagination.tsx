"use client";

import React from "react";
import { BsChevronLeft, BsChevronRight } from "react-icons/bs";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
}: PaginationProps) {
  if (totalPages <= 1) return null;

  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  // পেজ নাম্বার খুব বেশি হলে স্মার্টলি লিমিট দেখানো (সর্বোচ্চ ৫টি দৃশ্যমান পেজ)
  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    let start = Math.max(1, currentPage - 2);
    let end = Math.min(totalPages, start + maxVisible - 1);

    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  };

  return (
    <div className="pt-6 pb-2 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-cyan-950/40 w-full">
      {/* কাউন্টার ইনফো */}
      <p className="text-xs text-slate-400 order-2 sm:order-1">
        Showing <span className="text-cyan-400 font-semibold">{startItem}</span> to{" "}
        <span className="text-cyan-400 font-semibold">{endItem}</span> of{" "}
        <span className="text-slate-200 font-semibold">{totalItems}</span> vacancies
      </p>

      {/* বাটন কন্ট্রোলস */}
      <div className="flex items-center gap-1.5 sm:gap-2 order-1 sm:order-2">
        {/* Previous Button */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="p-2 sm:p-2.5 rounded-xl border border-slate-800 bg-slate-900/80 text-slate-300 hover:text-cyan-400 hover:border-cyan-900/80 transition-all disabled:opacity-30 disabled:pointer-events-none active:scale-95"
          aria-label="Previous Page"
        >
          <BsChevronLeft className="w-3.5 h-3.5" />
        </button>

        {/* Page Numbers */}
        <div className="flex items-center gap-1 sm:gap-1.5">
          {getPageNumbers().map((page) => (
            <button
              key={page}
              onClick={() => onPageChange(page)}
              className={`w-8 h-8 sm:w-9 sm:h-9 text-xs font-semibold rounded-xl transition-all ${
                currentPage === page
                  ? "bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20 scale-105"
                  : "bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700"
              }`}
            >
              {page}
            </button>
          ))}
        </div>

        {/* Next Button */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="p-2 sm:p-2.5 rounded-xl border border-slate-800 bg-slate-900/80 text-slate-300 hover:text-cyan-400 hover:border-cyan-900/80 transition-all disabled:opacity-30 disabled:pointer-events-none active:scale-95"
          aria-label="Next Page"
        >
          <BsChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}