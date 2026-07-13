import { useState } from "react";
import { Outlet } from "react-router-dom";
import { GlassBackground } from "@/components/GlassBackground";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

// 版面：GlassBackground + h-screen overflow-hidden，只有 main 捲動。見 §7。
export function AppLayout({
  theme,
  onThemeChange,
}: {
  theme: string;
  onThemeChange: (id: string) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      <GlassBackground />
      <div className="flex h-screen overflow-hidden">
        <Sidebar collapsed={collapsed} />
        <div className="flex min-w-0 flex-1 flex-col">
          <Header
            collapsed={collapsed}
            onToggle={() => setCollapsed((c) => !c)}
            theme={theme}
            onThemeChange={onThemeChange}
          />
          {/* 寬度交給各頁自己控制（聊天頁較寬、設定頁較窄）*/}
          <main className="nice-scroll flex-1 overflow-auto p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </>
  );
}
