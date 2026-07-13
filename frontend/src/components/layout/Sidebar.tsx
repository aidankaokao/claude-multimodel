import { useEffect, useRef, useState } from "react";
import { NavLink } from "react-router-dom";
import { MessageSquare, Settings2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

// 玻璃白側邊欄：可折疊 + 可拖曳寬度（存 localStorage）。見 §7.1。
const NAV = [
  { to: "/", label: "問答對話", icon: MessageSquare, end: true },
  { to: "/settings/providers", label: "LLM Provider", icon: Settings2, end: false },
];

const WIDTH_KEY = "multimodel-sidebar-w";
const MIN_W = 180;
const MAX_W = 480;

export function Sidebar({ collapsed }: { collapsed: boolean }) {
  const [width, setWidth] = useState<number>(() => {
    const saved = Number(localStorage.getItem(WIDTH_KEY));
    return saved >= MIN_W && saved <= MAX_W ? saved : 240;
  });
  const dragging = useRef(false);

  useEffect(() => {
    function onMove(e: MouseEvent) {
      if (!dragging.current) return;
      const w = Math.min(MAX_W, Math.max(MIN_W, e.clientX));
      setWidth(w);
    }
    function onUp() {
      if (!dragging.current) return;
      dragging.current = false;
      document.body.style.userSelect = "";
      localStorage.setItem(WIDTH_KEY, String(width));
    }
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [width]);

  return (
    <aside
      className="glass relative flex h-full flex-col border-r border-white/40"
      style={{ width: collapsed ? 64 : width }}
    >
      {/* 品牌區 */}
      <div className="flex h-14 items-center gap-2 px-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-gradient text-white">
          <Sparkles className="h-5 w-5" strokeWidth={1.75} />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <div className="truncate text-sm font-bold">
              <span className="text-gradient">multimodel</span>
            </div>
            <div className="truncate text-xs text-muted-foreground">多模態問答</div>
          </div>
        )}
      </div>

      {/* 導覽 */}
      <nav className="flex-1 space-y-1 px-2 py-2">
        {!collapsed && (
          <div className="px-2 pb-1 pt-2 text-xs font-medium text-muted-foreground">功能</div>
        )}
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            title={collapsed ? label : undefined}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors",
                collapsed && "justify-center px-0",
                isActive
                  ? "bg-white text-primary shadow-sm"
                  : "text-muted-foreground hover:bg-white/50"
              )
            }
          >
            <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* 拖曳感應區（折疊時隱藏）*/}
      {!collapsed && (
        <div
          onMouseDown={() => {
            dragging.current = true;
            document.body.style.userSelect = "none";
          }}
          className="absolute right-0 top-0 h-full w-[5px] cursor-col-resize hover:bg-[hsl(var(--primary)/0.4)]"
        />
      )}
    </aside>
  );
}
