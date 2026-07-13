// 可切換主題盤（皆淺色）。切換時只覆寫 index.css 的配色變數，玻璃結構不變。
// 見 reference/frontend/frontend-style-aurora-glass.md §11。
export type Theme = { id: string; name: string; from: string; to: string };

export const THEMES: Theme[] = [
  { id: "aurora-glass",   name: "極光琉璃", from: "#14B8A6", to: "#6366F1" },
  { id: "sunset-coral",   name: "珊瑚晚霞", from: "#FB7185", to: "#F59E0B" },
  { id: "rose-quartz",    name: "玫瑰石英", from: "#F472B6", to: "#A855F7" },
  { id: "mint-meadow",    name: "薄荷草原", from: "#34D399", to: "#06B6D4" },
  { id: "lavender-mist",  name: "薰衣草霧", from: "#818CF8", to: "#C084FC" },
  { id: "ocean-deep",     name: "深海潮",   from: "#3B82F6", to: "#22D3EE" },
  { id: "golden-hour",    name: "蜜金時光", from: "#FBBF24", to: "#FB7185" },
  { id: "graphite-frost", name: "石墨霜",   from: "#64748B", to: "#94A3B8" },
];

const STORAGE_KEY = "multimodel-theme";

export function applyTheme(id: string) {
  document.documentElement.setAttribute("data-theme", id);
  try {
    localStorage.setItem(STORAGE_KEY, id);
  } catch {
    /* ignore */
  }
}

export function initTheme(): string {
  let id = "aurora-glass";
  try {
    id = localStorage.getItem(STORAGE_KEY) || id;
  } catch {
    /* ignore */
  }
  applyTheme(id);
  return id;
}
