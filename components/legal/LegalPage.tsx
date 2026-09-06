export default function LegalPage({ title, updated, children }: { title: string; updated: string; children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 md:px-6">
      <h1 className="text-2xl font-extrabold tracking-tight text-white md:text-3xl">{title}</h1>
      <p className="mt-2 text-xs text-white/40">Last updated: {updated}</p>
      <div className="prose-invert mt-8 space-y-5 text-sm leading-relaxed text-white/60">{children}</div>
    </div>
  );
}
