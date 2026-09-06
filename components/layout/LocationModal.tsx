"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { MapPin, X, LocateFixed, Search } from "lucide-react";
import { mockLocations, useLocationStore } from "@/lib/store/locationStore";
import { useToastStore } from "@/lib/store/toastStore";

export default function LocationModal() {
  const modalOpen = useLocationStore((s) => s.modalOpen);
  const closeModal = useLocationStore((s) => s.closeModal);
  const setLocation = useLocationStore((s) => s.setLocation);
  const push = useToastStore((s) => s.push);
  const [query, setQuery] = useState("");
  const [locating, setLocating] = useState(false);

  const filtered = mockLocations.filter((l) => l.label.toLowerCase().includes(query.toLowerCase()));

  function useCurrentLocation() {
    setLocating(true);
    setTimeout(() => {
      setLocating(false);
      const loc = mockLocations[0];
      setLocation(loc);
      push(`Location set to ${loc.label}`, "success");
    }, 1200);
  }

  function pick(loc: (typeof mockLocations)[number]) {
    if (!loc.serviceable) {
      push("TECHRUSH isn't available in this area yet.", "error");
      return;
    }
    setLocation(loc);
    push(`Delivering to ${loc.label}`, "success");
  }

  return (
    <AnimatePresence>
      {modalOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[80] flex items-end justify-center bg-black/70 backdrop-blur-sm md:items-center"
          onClick={closeModal}
        >
          <motion.div
            initial={{ y: 40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 40, opacity: 0 }}
            transition={{ type: "spring", damping: 26, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
            className="glass w-full max-w-md rounded-t-3xl border-white/10 p-6 md:rounded-3xl"
            role="dialog"
            aria-modal="true"
            aria-label="Choose delivery location"
          >
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h2 className="text-lg font-bold text-white">WHERE SHOULD WE DELIVER?</h2>
                <p className="mt-1 text-sm text-white/60">Enter your delivery location</p>
              </div>
              <button
                onClick={closeModal}
                className="focus-ring rounded-full p-1.5 text-white/60 hover:bg-white/10 hover:text-white"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="relative mb-3">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search address / area / pincode"
                className="focus-ring w-full rounded-xl border border-white/10 bg-navy-800/80 py-3 pl-10 pr-3 text-sm text-white placeholder:text-white/40"
              />
            </div>

            <button
              onClick={useCurrentLocation}
              disabled={locating}
              className="focus-ring mb-4 flex w-full items-center gap-2 rounded-xl border border-rush/40 bg-rush/10 px-4 py-3 text-sm font-semibold text-rush-light transition hover:bg-rush/20 disabled:opacity-60"
            >
              <LocateFixed className={locating ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
              {locating ? "Locating you…" : "Use my current location"}
            </button>

            <div className="max-h-64 space-y-1 overflow-y-auto">
              {filtered.map((loc) => (
                <button
                  key={loc.label}
                  onClick={() => pick(loc)}
                  className="focus-ring flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-white/85 transition hover:bg-white/5"
                >
                  <MapPin className={loc.serviceable ? "h-4 w-4 text-rush-cyan" : "h-4 w-4 text-white/30"} />
                  <span className="flex-1">{loc.label}</span>
                  {!loc.serviceable && <span className="text-xs text-white/40">Not serviceable</span>}
                </button>
              ))}
              {filtered.length === 0 && (
                <p className="px-3 py-6 text-center text-sm text-white/40">No matching locations found.</p>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
