"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { LocationInfo } from "@/lib/types";

interface LocationState {
  location: LocationInfo | null;
  modalOpen: boolean;
  setLocation: (loc: LocationInfo) => void;
  openModal: () => void;
  closeModal: () => void;
}

export const mockLocations: LocationInfo[] = [
  { label: "Bandra West, Mumbai", city: "Mumbai", state: "Maharashtra", pincode: "400050", serviceable: true },
  { label: "Andheri East, Mumbai", city: "Mumbai", state: "Maharashtra", pincode: "400069", serviceable: true },
  { label: "Koramangala, Bengaluru", city: "Bengaluru", state: "Karnataka", pincode: "560034", serviceable: true },
  { label: "Indiranagar, Bengaluru", city: "Bengaluru", state: "Karnataka", pincode: "560038", serviceable: true },
  { label: "Connaught Place, New Delhi", city: "New Delhi", state: "Delhi", pincode: "110001", serviceable: true },
  { label: "Banjara Hills, Hyderabad", city: "Hyderabad", state: "Telangana", pincode: "500034", serviceable: true },
  { label: "Salt Lake, Kolkata", city: "Kolkata", state: "West Bengal", pincode: "700064", serviceable: false },
  { label: "Anna Nagar, Chennai", city: "Chennai", state: "Tamil Nadu", pincode: "600040", serviceable: true },
];

export const useLocationStore = create<LocationState>()(
  persist(
    (set) => ({
      location: null,
      modalOpen: false,
      setLocation: (loc) => set({ location: loc, modalOpen: false }),
      openModal: () => set({ modalOpen: true }),
      closeModal: () => set({ modalOpen: false }),
    }),
    { name: "techrush-location" }
  )
);
