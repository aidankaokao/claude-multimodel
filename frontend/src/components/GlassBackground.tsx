// 漂浮光暈背景，掛在最外層。fixed 滿版、-z-10、pointer-events-none。
// 見 frontend-style-aurora-glass.md §3.2。
export function GlassBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div
        className="absolute -top-24 -left-24 h-[42rem] w-[42rem] rounded-full blur-3xl animate-blob"
        style={{ background: "hsl(var(--glow-1) / 0.40)" }}
      />
      <div
        className="absolute -top-16 right-[-8rem] h-[38rem] w-[38rem] rounded-full blur-3xl animate-blob"
        style={{ background: "hsl(var(--glow-2) / 0.40)", animationDelay: "6s" }}
      />
      <div
        className="absolute bottom-[-10rem] left-1/3 h-[36rem] w-[36rem] rounded-full blur-3xl animate-blob"
        style={{ background: "hsl(var(--glow-3) / 0.40)", animationDelay: "12s" }}
      />
    </div>
  );
}
