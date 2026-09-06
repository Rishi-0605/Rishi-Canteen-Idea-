import { Product, CategorySlug } from "@/lib/types";
import { makeRetailers } from "@/lib/data/partners";
import { makeReviews } from "@/lib/data/reviews";
import { sizeForCategory } from "@/lib/utils";

interface RawProduct {
  id: string;
  name: string;
  brand: string;
  category: CategorySlug;
  price: number;
  mrp: number;
  color: string;
  tags: string[];
  specs: { label: string; value: string }[];
  box: string[];
  description: string;
  featured?: boolean;
  dealTag?: Product["dealTag"];
  installationAvailable?: boolean;
  emiFrom?: number;
}

const raw: RawProduct[] = [
  // Smartphones
  {
    id: "iphone-17", name: "iPhone 17", brand: "Apple", category: "smartphones",
    price: 79999, mrp: 84999, color: "Midnight", tags: ["5G", "A19 chip", "Titanium frame"],
    specs: [{ label: "Display", value: "6.1\" Super Retina XDR" }, { label: "Chip", value: "A19 Bionic" }, { label: "Storage", value: "256GB" }, { label: "Camera", value: "48MP Dual" }],
    box: ["Handset", "USB-C Cable", "Documentation"],
    description: "The latest generation iPhone with a faster chip, refined camera system, and all-day battery life.",
    featured: true, dealTag: "phones", emiFrom: 3999,
  },
  {
    id: "iphone-17-pro", name: "iPhone 17 Pro", brand: "Apple", category: "smartphones",
    price: 129999, mrp: 134900, color: "Natural Titanium", tags: ["5G", "Pro camera", "ProMotion"],
    specs: [{ label: "Display", value: "6.3\" ProMotion XDR" }, { label: "Chip", value: "A19 Pro" }, { label: "Storage", value: "512GB" }, { label: "Camera", value: "48MP Triple" }],
    box: ["Handset", "USB-C Cable", "Documentation"],
    description: "Pro-level performance with a triple camera system and a durable titanium design.",
    dealTag: "phones", emiFrom: 6499,
  },
  {
    id: "iphone-17-pro-max", name: "iPhone 17 Pro Max", brand: "Apple", category: "smartphones",
    price: 154999, mrp: 159900, color: "Deep Blue", tags: ["5G", "Largest display", "Pro camera"],
    specs: [{ label: "Display", value: "6.9\" ProMotion XDR" }, { label: "Chip", value: "A19 Pro" }, { label: "Storage", value: "1TB" }, { label: "Camera", value: "48MP Triple" }],
    box: ["Handset", "USB-C Cable", "Documentation"],
    description: "The biggest, most capable iPhone with pro cameras and the longest battery life yet.",
    emiFrom: 7799,
  },
  {
    id: "galaxy-s26-ultra", name: "Galaxy S26 Ultra", brand: "Samsung", category: "smartphones",
    price: 124999, mrp: 132999, color: "Titanium Black", tags: ["5G", "S Pen", "200MP camera"],
    specs: [{ label: "Display", value: "6.8\" Dynamic AMOLED" }, { label: "Chip", value: "Snapdragon Gen 6" }, { label: "Storage", value: "256GB" }, { label: "Camera", value: "200MP Quad" }],
    box: ["Handset", "S Pen", "USB-C Cable"],
    description: "Flagship Samsung experience with a built-in S Pen and an ultra-versatile camera system.",
    featured: true, dealTag: "phones", emiFrom: 6199,
  },
  {
    id: "galaxy-s26", name: "Galaxy S26", brand: "Samsung", category: "smartphones",
    price: 69999, mrp: 74999, color: "Ice Silver", tags: ["5G", "Compact flagship"],
    specs: [{ label: "Display", value: "6.2\" Dynamic AMOLED" }, { label: "Chip", value: "Snapdragon Gen 6" }, { label: "Storage", value: "128GB" }, { label: "Camera", value: "50MP Triple" }],
    box: ["Handset", "USB-C Cable"],
    description: "Compact flagship with flagship performance and a refined triple camera setup.",
    dealTag: "phones", emiFrom: 3499,
  },
  {
    id: "pixel-10", name: "Pixel 10", brand: "Google", category: "smartphones",
    price: 64999, mrp: 69999, color: "Storm Grey", tags: ["Stock Android", "AI camera"],
    specs: [{ label: "Display", value: "6.3\" OLED 120Hz" }, { label: "Chip", value: "Tensor G6" }, { label: "Storage", value: "256GB" }, { label: "Camera", value: "50MP Dual" }],
    box: ["Handset", "USB-C Cable"],
    description: "Clean software experience with computational photography that punches above its price.",
    emiFrom: 3199,
  },
  {
    id: "oneplus-14", name: "OnePlus 14", brand: "OnePlus", category: "smartphones",
    price: 54999, mrp: 59999, color: "Emerald Green", tags: ["Fast charging", "120Hz"],
    specs: [{ label: "Display", value: "6.7\" AMOLED 120Hz" }, { label: "Chip", value: "Snapdragon Gen 6" }, { label: "Storage", value: "256GB" }, { label: "Charging", value: "100W SuperVOOC" }],
    box: ["Handset", "100W Charger", "Cable"],
    description: "Blazing fast charging paired with a fluid 120Hz display for power users.",
    dealTag: "flash", emiFrom: 2699,
  },
  {
    id: "nothing-phone-4", name: "Nothing Phone (4)", brand: "Nothing", category: "smartphones",
    price: 39999, mrp: 44999, color: "White", tags: ["Glyph Interface", "Unique design"],
    specs: [{ label: "Display", value: "6.5\" AMOLED 120Hz" }, { label: "Chip", value: "Snapdragon 8s Gen 5" }, { label: "Storage", value: "128GB" }],
    box: ["Handset", "USB-C Cable"],
    description: "Distinctive transparent design with the signature Glyph lighting interface.",
    dealTag: "flash", emiFrom: 1999,
  },

  // Laptops
  {
    id: "macbook-air-m5", name: "MacBook Air M5", brand: "Apple", category: "laptops",
    price: 114900, mrp: 119900, color: "Midnight", tags: ["M5 chip", "18hr battery"],
    specs: [{ label: "Display", value: "13.6\" Liquid Retina" }, { label: "Chip", value: "Apple M5" }, { label: "RAM", value: "16GB" }, { label: "Storage", value: "512GB SSD" }],
    box: ["Laptop", "USB-C Charger", "Documentation"],
    description: "Impossibly thin and fast, with all-day battery life for work anywhere.",
    featured: true, dealTag: "laptops", emiFrom: 5699,
  },
  {
    id: "macbook-pro-14", name: "MacBook Pro 14\"", brand: "Apple", category: "laptops",
    price: 189900, mrp: 199900, color: "Space Black", tags: ["M5 Pro", "Liquid Retina XDR"],
    specs: [{ label: "Display", value: "14.2\" Liquid Retina XDR" }, { label: "Chip", value: "Apple M5 Pro" }, { label: "RAM", value: "32GB" }, { label: "Storage", value: "1TB SSD" }],
    box: ["Laptop", "140W Charger"],
    description: "Pro-level performance for demanding creative and engineering workflows.",
    emiFrom: 9399,
  },
  {
    id: "xps-14", name: "Dell XPS 14", brand: "Dell", category: "laptops",
    price: 149999, mrp: 159999, color: "Platinum", tags: ["OLED display", "Premium build"],
    specs: [{ label: "Display", value: "14.5\" 3K OLED" }, { label: "CPU", value: "Intel Core Ultra 9" }, { label: "RAM", value: "32GB" }, { label: "Storage", value: "1TB SSD" }],
    box: ["Laptop", "Charger"],
    description: "A stunning OLED canvas wrapped in a premium CNC-machined chassis.",
    dealTag: "laptops", emiFrom: 7399,
  },
  {
    id: "thinkpad-x1", name: "ThinkPad X1 Carbon", brand: "Lenovo", category: "laptops",
    price: 134999, mrp: 144999, color: "Black", tags: ["Business", "Ultra-light"],
    specs: [{ label: "Display", value: "14\" 2.8K OLED" }, { label: "CPU", value: "Intel Core Ultra 7" }, { label: "RAM", value: "16GB" }, { label: "Storage", value: "512GB SSD" }],
    box: ["Laptop", "Charger"],
    description: "The business standard for durability, security, and portability.",
    emiFrom: 6599,
  },
  {
    id: "rog-zephyrus-g16", name: "ROG Zephyrus G16", brand: "ASUS", category: "laptops",
    price: 174999, mrp: 189999, color: "Eclipse Grey", tags: ["RTX 5070", "Gaming"],
    specs: [{ label: "Display", value: "16\" 240Hz OLED" }, { label: "GPU", value: "RTX 5070" }, { label: "RAM", value: "32GB" }, { label: "Storage", value: "1TB SSD" }],
    box: ["Laptop", "240W Charger"],
    description: "Slim gaming powerhouse that doesn't compromise on style or performance.",
    dealTag: "gaming", emiFrom: 8599,
  },
  {
    id: "pavilion-15", name: "HP Pavilion 15", brand: "HP", category: "laptops",
    price: 54999, mrp: 62999, color: "Silver", tags: ["Everyday laptop", "Lightweight"],
    specs: [{ label: "Display", value: "15.6\" FHD" }, { label: "CPU", value: "Intel Core i5" }, { label: "RAM", value: "16GB" }, { label: "Storage", value: "512GB SSD" }],
    box: ["Laptop", "Charger"],
    description: "A dependable everyday companion for study, browsing and productivity.",
    dealTag: "flash", emiFrom: 2699,
  },

  // TVs
  {
    id: "bravia-xr-65", name: "Bravia XR 65\" 4K", brand: "Sony", category: "tvs",
    price: 149999, mrp: 179999, color: "Black", tags: ["4K HDR", "Cognitive Processor XR"],
    specs: [{ label: "Size", value: "65 inch" }, { label: "Resolution", value: "4K HDR" }, { label: "Panel", value: "OLED" }, { label: "Sound", value: "Acoustic Surface Audio" }],
    box: ["TV Unit", "Remote", "Stand", "Power Cable"],
    description: "Cinema-grade picture processing that brings every scene to life.",
    featured: true, installationAvailable: true, emiFrom: 7199,
  },
  {
    id: "qled-q80-55", name: "QLED Q80 55\"", brand: "Samsung", category: "tvs",
    price: 89999, mrp: 109999, color: "Black", tags: ["Quantum Dot", "Smart TV"],
    specs: [{ label: "Size", value: "55 inch" }, { label: "Resolution", value: "4K QLED" }, { label: "Refresh", value: "120Hz" }, { label: "OS", value: "Tizen Smart Hub" }],
    box: ["TV Unit", "Remote", "Stand"],
    description: "Vivid Quantum Dot color with deep contrast for a premium home cinema feel.",
    dealTag: "flash", installationAvailable: true, emiFrom: 4299,
  },
  {
    id: "oled-c5-55", name: "OLED C5 55\"", brand: "LG", category: "tvs",
    price: 129999, mrp: 149999, color: "Black", tags: ["Self-lit OLED", "webOS"],
    specs: [{ label: "Size", value: "55 inch" }, { label: "Resolution", value: "4K OLED" }, { label: "Refresh", value: "144Hz" }, { label: "Gaming", value: "4x HDMI 2.1" }],
    box: ["TV Unit", "Magic Remote", "Stand"],
    description: "Perfect blacks and infinite contrast make every frame pop.",
    installationAvailable: true, emiFrom: 6199,
  },
  {
    id: "smart-tv-43", name: "Smart TV 43\" Full HD", brand: "Mi", category: "tvs",
    price: 26999, mrp: 34999, color: "Black", tags: ["Android TV", "Budget friendly"],
    specs: [{ label: "Size", value: "43 inch" }, { label: "Resolution", value: "Full HD" }, { label: "OS", value: "Google TV" }],
    box: ["TV Unit", "Remote", "Stand"],
    description: "Reliable everyday entertainment with built-in streaming apps.",
    dealTag: "flash", installationAvailable: true, emiFrom: 1299,
  },

  // Audio
  {
    id: "airpods-pro-3", name: "AirPods Pro 3", brand: "Apple", category: "audio",
    price: 22999, mrp: 24900, color: "White", tags: ["ANC", "Spatial Audio"],
    specs: [{ label: "Battery", value: "Up to 30hrs with case" }, { label: "ANC", value: "Adaptive" }, { label: "Chip", value: "H3" }],
    box: ["Earbuds", "Charging Case", "USB-C Cable"],
    description: "Immersive sound with industry-leading noise cancellation.",
    featured: true,  emiFrom: 1099,
  },
  {
    id: "wh1000xm6", name: "WH-1000XM6", brand: "Sony", category: "audio",
    price: 29999, mrp: 34990, color: "Black", tags: ["Best-in-class ANC", "30hr battery"],
    specs: [{ label: "Battery", value: "30 hours" }, { label: "ANC", value: "Industry-leading" }, { label: "Type", value: "Over-ear" }],
    box: ["Headphones", "Carry Case", "USB-C Cable"],
    description: "The gold standard for wireless noise cancellation and comfort.",
    emiFrom: 1499,
  },
  {
    id: "buds3-pro", name: "Galaxy Buds3 Pro", brand: "Samsung", category: "audio",
    price: 17999, mrp: 21999, color: "Silver", tags: ["ANC", "Hi-Fi audio"],
    specs: [{ label: "Battery", value: "26hrs with case" }, { label: "ANC", value: "Intelligent" }],
    box: ["Earbuds", "Charging Case", "USB-C Cable"],
    description: "Studio-quality sound in a compact, comfortable design.",
  },
  {
    id: "soundlink-flex", name: "SoundLink Flex", brand: "Bose", category: "audio",
    price: 11999, mrp: 14900, color: "Blue", tags: ["Portable speaker", "Waterproof"],
    specs: [{ label: "Battery", value: "12 hours" }, { label: "Rating", value: "IP67" }],
    box: ["Speaker", "USB-C Cable"],
    description: "Big, room-filling sound that travels wherever you go.",
    dealTag: "weekend",
  },
  {
    id: "earbuds-basic", name: "Wireless Earbuds Lite", brand: "boAt", category: "audio",
    price: 999, mrp: 1999, color: "Black", tags: ["Budget", "12hr playback"],
    specs: [{ label: "Battery", value: "12 hours" }, { label: "Type", value: "In-ear" }],
    box: ["Earbuds", "Charging Case", "Cable"],
    description: "Affordable everyday earbuds with punchy bass.",
    dealTag: "under999",
  },
  {
    id: "wired-earphones", name: "Wired Earphones with Mic", brand: "boAt", category: "audio",
    price: 349, mrp: 699, color: "Black", tags: ["Budget", "In-line mic"],
    specs: [{ label: "Jack", value: "3.5mm" }, { label: "Mic", value: "In-line" }],
    box: ["Earphones"],
    description: "Reliable everyday wired earphones with clear calling.",
    dealTag: "under999",
  },

  // Wearables
  {
    id: "watch-ultra-3", name: "Watch Ultra 3", brand: "Apple", category: "wearables",
    price: 89900, mrp: 94900, color: "Titanium", tags: ["GPS + Cellular", "Rugged"],
    specs: [{ label: "Display", value: "Always-on Retina" }, { label: "Battery", value: "Up to 72hrs" }, { label: "Build", value: "Titanium case" }],
    box: ["Watch", "Band", "Charger"],
    description: "Built for adventure with extreme durability and precision GPS.",
    emiFrom: 4499,
  },
  {
    id: "galaxy-watch-8", name: "Galaxy Watch8", brand: "Samsung", category: "wearables",
    price: 32999, mrp: 36999, color: "Graphite", tags: ["Health tracking", "AMOLED"],
    specs: [{ label: "Display", value: "1.5\" AMOLED" }, { label: "Battery", value: "Up to 40hrs" }],
    box: ["Watch", "Charger"],
    description: "Comprehensive health insights on your wrist, day and night.",
    dealTag: "flash",
  },
  {
    id: "band-9", name: "Smart Band 9", brand: "Mi", category: "wearables",
    price: 3499, mrp: 4499, color: "Black", tags: ["Fitness band", "14 day battery"],
    specs: [{ label: "Battery", value: "14 days" }, { label: "Display", value: "AMOLED" }],
    box: ["Band", "Charging Cable"],
    description: "Long-lasting fitness tracking without the bulk.",
  },

  // Gaming
  {
    id: "ps6", name: "PlayStation 6", brand: "Sony", category: "gaming", price: 59999, mrp: 64999,
    color: "White", tags: ["Next-gen console", "4K gaming"],
    specs: [{ label: "Storage", value: "1TB SSD" }, { label: "Resolution", value: "Up to 8K" }, { label: "Controller", value: "DualSense included" }],
    box: ["Console", "DualSense Controller", "HDMI Cable"],
    description: "Next-generation gaming with lightning-fast load times.",
    featured: true, dealTag: "gaming", emiFrom: 2899,
  },
  {
    id: "xbox-series-x2", name: "Xbox Series X2", brand: "Microsoft", category: "gaming", price: 54999, mrp: 59999,
    color: "Black", tags: ["4K gaming", "Game Pass ready"],
    specs: [{ label: "Storage", value: "1TB SSD" }, { label: "Resolution", value: "4K @ 120fps" }],
    box: ["Console", "Controller", "HDMI Cable"],
    description: "Raw power for the ultimate console gaming experience.",
    dealTag: "gaming", emiFrom: 2599,
  },
  {
    id: "dualsense-edge", name: "DualSense Edge Controller", brand: "Sony", category: "gaming", price: 16999, mrp: 19999,
    color: "White", tags: ["Pro controller", "Customizable"],
    specs: [{ label: "Connectivity", value: "Bluetooth / Wired" }, { label: "Battery", value: "12 hours" }],
    box: ["Controller", "USB-C Cable", "Case"],
    description: "Precision-tuned controls for competitive players.",
    dealTag: "gaming",
  },
  {
    id: "steam-deck-oled", name: "Steam Deck OLED", brand: "Valve", category: "gaming", price: 54999, mrp: 59999,
    color: "Black", tags: ["Handheld PC", "OLED display"],
    specs: [{ label: "Display", value: "7.4\" OLED" }, { label: "Storage", value: "1TB" }],
    box: ["Handheld", "Charger", "Case"],
    description: "Your entire PC game library, now in your hands.",
    dealTag: "gaming",
  },

  // Monitors
  {
    id: "odyssey-g9", name: "Odyssey G9 49\"", brand: "Samsung", category: "monitors", price: 89999, mrp: 99999,
    color: "White", tags: ["Curved", "240Hz"], specs: [{ label: "Size", value: "49 inch" }, { label: "Refresh", value: "240Hz" }, { label: "Resolution", value: "5120x1440" }],
    box: ["Monitor", "Stand", "Power Cable"],
    description: "Dual QHD immersive curved display for gaming and productivity.",
    dealTag: "gaming",
  },
  {
    id: "ultrasharp-27", name: "UltraSharp 27\" 4K", brand: "Dell", category: "monitors", price: 39999, mrp: 44999,
    color: "Silver", tags: ["Color accurate", "USB-C hub"], specs: [{ label: "Size", value: "27 inch" }, { label: "Resolution", value: "4K UHD" }, { label: "Ports", value: "USB-C 90W" }],
    box: ["Monitor", "Stand", "Cables"],
    description: "Factory color-calibrated display built for creative professionals.",
  },
  {
    id: "monitor-24-fhd", name: "24\" FHD Monitor", brand: "LG", category: "monitors", price: 8999, mrp: 11999,
    color: "Black", tags: ["Budget", "IPS panel"], specs: [{ label: "Size", value: "24 inch" }, { label: "Resolution", value: "Full HD" }, { label: "Panel", value: "IPS" }],
    box: ["Monitor", "Stand", "Cable"],
    description: "Crisp, colour-accurate display for everyday computing.",
    dealTag: "weekend",
  },

  // Accessories
  {
    id: "mx-master-4", name: "MX Master 4", brand: "Logitech", category: "accessories", price: 8999, mrp: 10999,
    color: "Graphite", tags: ["Ergonomic mouse", "Multi-device"], specs: [{ label: "Battery", value: "70 days" }, { label: "Connectivity", value: "Bluetooth / USB-C dongle" }],
    box: ["Mouse", "USB-C Cable", "Dongle"],
    description: "Precision and comfort engineered for all-day productivity.",
    dealTag: "weekend",
  },
  {
    id: "mech-keyboard-k9", name: "Mechanical Keyboard K9", brand: "Keychron", category: "accessories", price: 7999, mrp: 9999,
    color: "Grey", tags: ["Hot-swappable", "Wireless"], specs: [{ label: "Switches", value: "Hot-swappable" }, { label: "Connectivity", value: "Bluetooth / Wired" }],
    box: ["Keyboard", "USB-C Cable", "Keycap Puller"],
    description: "Satisfying tactile typing with full customization.",
  },
  {
    id: "usbc-charging-cable", name: "USB-C Fast Charging Cable", brand: "Anker", category: "accessories", price: 599, mrp: 999,
    color: "White", tags: ["100W", "1.5m braided"], specs: [{ label: "Output", value: "100W" }, { label: "Length", value: "1.5m" }],
    box: ["Cable"],
    description: "Durable braided cable for fast, reliable charging.",
    dealTag: "under999",
  },
  {
    id: "power-bank-20000", name: "20000mAh Power Bank", brand: "Anker", category: "accessories", price: 2499, mrp: 3499,
    color: "Black", tags: ["Fast charge", "Dual USB-C"], specs: [{ label: "Capacity", value: "20000mAh" }, { label: "Output", value: "65W" }],
    box: ["Power Bank", "USB-C Cable"],
    description: "Charge your laptop and phone together, all day long.",
  },
  {
    id: "webcam-4k", name: "4K Webcam Pro", brand: "Logitech", category: "accessories", price: 12999, mrp: 15999,
    color: "Black", tags: ["4K video", "Auto-focus"], specs: [{ label: "Resolution", value: "4K @ 30fps" }, { label: "Field of View", value: "90°" }],
    box: ["Webcam", "USB-C Cable", "Mount"],
    description: "Studio-quality video for meetings and streaming.",
  },

  // Appliances / large
  {
    id: "front-load-wm-8kg", name: "Front Load Washing Machine 8kg", brand: "LG", category: "appliances", price: 34999, mrp: 42999,
    color: "Silver", tags: ["Inverter motor", "8kg capacity"], specs: [{ label: "Capacity", value: "8 kg" }, { label: "Type", value: "Front Load" }, { label: "Motor", value: "Inverter" }],
    box: ["Washing Machine", "Inlet Hose", "Manual"],
    description: "Gentle, efficient washing with smart inverter technology.",
    installationAvailable: true, dealTag: "appliances", emiFrom: 1699,
  },
  {
    id: "microwave-conv-28l", name: "Convection Microwave 28L", brand: "Samsung", category: "appliances", price: 14999, mrp: 18999,
    color: "Black", tags: ["Convection", "28L capacity"], specs: [{ label: "Capacity", value: "28 L" }, { label: "Type", value: "Convection" }],
    box: ["Microwave", "Tray", "Manual"],
    description: "Bake, grill and reheat with a single versatile appliance.",
    installationAvailable: true, dealTag: "appliances",
  },
  {
    id: "dishwasher-14pl", name: "Dishwasher 14 Place Settings", brand: "Bosch", category: "appliances", price: 42999, mrp: 49999,
    color: "Steel", tags: ["14 place settings", "Quiet operation"], specs: [{ label: "Capacity", value: "14 place settings" }, { label: "Noise", value: "44 dB" }],
    box: ["Dishwasher", "Manual"],
    description: "Sparkling clean dishes with minimal water and noise.",
    installationAvailable: true, dealTag: "appliances", emiFrom: 2099,
  },

  // Refrigerators
  {
    id: "double-door-fridge-260l", name: "Double Door Refrigerator 260L", brand: "Samsung", category: "refrigerators", price: 29999, mrp: 36999,
    color: "Silver", tags: ["Frost free", "260L"], specs: [{ label: "Capacity", value: "260 L" }, { label: "Type", value: "Double Door" }, { label: "Cooling", value: "Frost Free" }],
    box: ["Refrigerator", "Manual", "Warranty Card"],
    description: "Spacious and efficient cooling for the whole family.",
    installationAvailable: true, featured: true, dealTag: "appliances", emiFrom: 1499,
  },
  {
    id: "single-door-fridge-190l", name: "Single Door Refrigerator 190L", brand: "LG", category: "refrigerators", price: 17999, mrp: 21999,
    color: "Blue", tags: ["Direct cool", "190L"], specs: [{ label: "Capacity", value: "190 L" }, { label: "Type", value: "Single Door" }],
    box: ["Refrigerator", "Manual"],
    description: "Compact and reliable cooling for smaller households.",
    installationAvailable: true, dealTag: "appliances",
  },
  {
    id: "side-by-side-fridge-580l", name: "Side-by-Side Refrigerator 580L", brand: "LG", category: "refrigerators", price: 89999, mrp: 104999,
    color: "Black Steel", tags: ["Smart cooling", "580L"], specs: [{ label: "Capacity", value: "580 L" }, { label: "Type", value: "Side by Side" }, { label: "Display", value: "Smart panel" }],
    box: ["Refrigerator", "Manual", "Warranty Card"],
    description: "Premium capacity and smart cooling for large families.",
    installationAvailable: true, emiFrom: 4299,
  },
  {
    id: "split-ac-1.5t", name: "Split AC 1.5 Ton 5 Star", brand: "Daikin", category: "appliances", price: 39999, mrp: 46999,
    color: "White", tags: ["5 Star", "Inverter"], specs: [{ label: "Capacity", value: "1.5 Ton" }, { label: "Rating", value: "5 Star" }, { label: "Type", value: "Inverter Split AC" }],
    box: ["Indoor Unit", "Outdoor Unit", "Remote"],
    description: "Powerful, energy-efficient cooling built for Indian summers.",
    installationAvailable: true, dealTag: "appliances", emiFrom: 1899,
  },

  // Home appliances
  {
    id: "robot-vacuum", name: "Robot Vacuum & Mop", brand: "Ecovacs", category: "home-appliances", price: 24999, mrp: 32999,
    color: "Black", tags: ["Auto mop", "App controlled"], specs: [{ label: "Battery", value: "3hrs runtime" }, { label: "Navigation", value: "LiDAR mapping" }],
    box: ["Robot Vacuum", "Charging Dock", "Manual"],
    description: "Effortless cleaning that maps your home and cleans on schedule.",
    dealTag: "appliances", emiFrom: 1199,
  },
  {
    id: "air-fryer-5l", name: "Digital Air Fryer 5L", brand: "Philips", category: "home-appliances", price: 8999, mrp: 11999,
    color: "Black", tags: ["Oil-free frying", "5L capacity"], specs: [{ label: "Capacity", value: "5 L" }, { label: "Wattage", value: "1500W" }],
    box: ["Air Fryer", "Basket", "Manual"],
    description: "Crispy favourites with up to 90% less oil.",
    dealTag: "weekend",
  },
  {
    id: "mixer-grinder-750w", name: "Mixer Grinder 750W", brand: "Bajaj", category: "home-appliances", price: 3499, mrp: 4499,
    color: "Black", tags: ["3 jars", "750W motor"], specs: [{ label: "Wattage", value: "750W" }, { label: "Jars", value: "3" }],
    box: ["Mixer Body", "3 Jars", "Manual"],
    description: "Powerful everyday mixing, grinding and blending.",
  },
  {
    id: "vacuum-cleaner-corded", name: "Corded Vacuum Cleaner", brand: "Eureka Forbes", category: "home-appliances", price: 6999, mrp: 8999,
    color: "Red", tags: ["Bagless", "Powerful suction"], specs: [{ label: "Power", value: "1600W" }, { label: "Type", value: "Bagless" }],
    box: ["Vacuum Cleaner", "Attachments", "Manual"],
    description: "Deep-clean carpets, floors and upholstery with ease.",
  },

  // Cameras
  {
    id: "mirrorless-a7v", name: "Mirrorless A7V", brand: "Sony", category: "cameras", price: 189999, mrp: 209999,
    color: "Black", tags: ["Full-frame", "8K video"], specs: [{ label: "Sensor", value: "Full-frame 33MP" }, { label: "Video", value: "8K30" }],
    box: ["Camera Body", "Battery", "Charger"],
    description: "Professional-grade stills and video in a compact full-frame body.",
    featured: true, emiFrom: 9199,
  },
  {
    id: "action-cam-13", name: "Action Camera 13", brand: "GoPro", category: "cameras", price: 39999, mrp: 44999,
    color: "Black", tags: ["5.3K video", "Waterproof"], specs: [{ label: "Video", value: "5.3K60" }, { label: "Waterproof", value: "10m without housing" }],
    box: ["Camera", "Mount", "Battery"],
    description: "Capture your adventures in stunning stabilized detail.",
    dealTag: "flash",
  },
  {
    id: "instant-cam", name: "Instant Camera Mini", brand: "Fujifilm", category: "cameras", price: 6999, mrp: 8999,
    color: "Pastel Blue", tags: ["Instant prints", "Compact"], specs: [{ label: "Film", value: "Instax Mini" }, { label: "Flash", value: "Automatic" }],
    box: ["Camera", "Strap", "Battery"],
    description: "Print your memories instantly with a pocketable, playful design.",
    dealTag: "weekend",
  },
];

function build(rp: RawProduct, index: number): Product {
  const size = sizeForCategory(rp.category);
  const retailers = makeRetailers(2 + (index % 3), index + 1);
  const reviews = makeReviews(index + 1, 3 + (index % 4));
  const avgRating = reviews.length
    ? Number((reviews.reduce((s, r) => s + r.rating, 0) / reviews.length).toFixed(1))
    : 4.3;
  return {
    id: rp.id,
    name: rp.name,
    brand: rp.brand,
    category: rp.category,
    price: rp.price,
    mrp: rp.mrp,
    rating: avgRating,
    reviewCount: 40 + index * 17,
    images: [rp.color],
    color: rp.color,
    tags: rp.tags,
    size,
    installationAvailable: rp.installationAvailable ?? (size === "large" || size === "bulky"),
    warranty: size === "bulky" || size === "large" ? "1 Year Manufacturer Warranty + Extended options" : "1 Year Manufacturer Warranty",
    returnPolicy: "7-day easy replacement",
    emiFrom: rp.emiFrom,
    specs: rp.specs,
    whatsInTheBox: rp.box,
    description: rp.description,
    featured: rp.featured,
    dealTag: rp.dealTag,
    reviews,
    retailers,
  };
}

export const products: Product[] = raw.map(build);

export function getProduct(id: string): Product | undefined {
  return products.find((p) => p.id === id);
}

export function getProductsByCategory(category: string): Product[] {
  return products.filter((p) => p.category === category);
}

export function getFeaturedProducts(): Product[] {
  return products.filter((p) => p.featured);
}

export function getDealsByTag(tag: NonNullable<Product["dealTag"]>): Product[] {
  return products.filter((p) => p.dealTag === tag);
}

export function searchProducts(query: string): Product[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return products.filter((p) =>
    p.name.toLowerCase().includes(q) ||
    p.brand.toLowerCase().includes(q) ||
    p.category.toLowerCase().includes(q) ||
    p.tags.some((t) => t.toLowerCase().includes(q))
  );
}
