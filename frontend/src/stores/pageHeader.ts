// 集中式 Header 標題 store。各頁設定「標題 + 副標」，Header 讀取顯示。
// 見 reference/frontend/frontend-backend-integration.md §7。
import { create } from "zustand";

type State = {
  title: string;
  subtitle?: string;
  set: (t: string, s?: string) => void;
};

export const usePageHeader = create<State>((set) => ({
  title: "",
  set: (title, subtitle) => set({ title, subtitle }),
}));
