import {
  Smartphone,
  Laptop,
  Tv,
  Headphones,
  Watch,
  Gamepad2,
  Monitor,
  Keyboard,
  WashingMachine,
  Refrigerator,
  Fan,
  Camera,
  Package,
  type LucideIcon,
} from "lucide-react";
import { CategorySlug } from "@/lib/types";

export const categoryIcons: Record<CategorySlug, LucideIcon> = {
  smartphones: Smartphone,
  laptops: Laptop,
  tvs: Tv,
  audio: Headphones,
  wearables: Watch,
  gaming: Gamepad2,
  monitors: Monitor,
  accessories: Keyboard,
  appliances: WashingMachine,
  refrigerators: Refrigerator,
  "home-appliances": Fan,
  cameras: Camera,
};

export function iconForCategory(category: string): LucideIcon {
  return categoryIcons[category as CategorySlug] ?? Package;
}
