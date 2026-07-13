import { PanelLeftClose, PanelLeftOpen, Palette } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { usePageHeader } from "@/stores/pageHeader";
import { THEMES, applyTheme } from "@/lib/themes";

// h-14 玻璃白 Header：左折疊鈕 + 頁面標題/副標 + 右主題切換。見 §7.2。
export function Header({
  collapsed,
  onToggle,
  theme,
  onThemeChange,
}: {
  collapsed: boolean;
  onToggle: () => void;
  theme: string;
  onThemeChange: (id: string) => void;
}) {
  const { title, subtitle } = usePageHeader();

  return (
    <header className="glass z-10 flex h-14 items-center gap-3 border-b border-white/40 px-4">
      <Button variant="ghost" size="icon" onClick={onToggle} aria-label="切換側邊欄">
        {collapsed ? (
          <PanelLeftOpen className="h-5 w-5" strokeWidth={1.75} />
        ) : (
          <PanelLeftClose className="h-5 w-5" strokeWidth={1.75} />
        )}
      </Button>

      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{title}</div>
        {subtitle && <div className="truncate text-xs text-muted-foreground">{subtitle}</div>}
      </div>

      <div className="flex items-center gap-2">
        <Palette className="h-4 w-4 text-muted-foreground" strokeWidth={1.75} />
        <Select
          value={theme}
          onChange={(e) => {
            applyTheme(e.target.value);
            onThemeChange(e.target.value);
          }}
          className="h-9 w-36"
        >
          {THEMES.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </Select>
      </div>
    </header>
  );
}
