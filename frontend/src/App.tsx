import { useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { ChatPage } from "@/pages/ChatPage";
import { SettingsProvidersPage } from "@/pages/SettingsProvidersPage";
import { initTheme } from "@/lib/themes";

export default function App() {
  const [theme, setTheme] = useState<string>(() => initTheme());

  return (
    // basename 讓子路徑部署（/<APP_ROUTE>/）與 dev 根路徑共用同一份程式（BASE_URL 由 Vite 帶入）
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <Routes>
        <Route element={<AppLayout theme={theme} onThemeChange={setTheme} />}>
          <Route index element={<ChatPage />} />
          <Route path="settings/providers" element={<SettingsProvidersPage />} />
        </Route>
      </Routes>
      {/* toast 用 glass-strong 提高對比，右下角 */}
      <Toaster position="bottom-right" richColors toastOptions={{ className: "glass-strong" }} />
    </BrowserRouter>
  );
}
