import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";

// 助理回覆的 Markdown 渲染（GFM：表格 / 刪除線 / 任務清單）。
// 樣式走 index.css 的 .markdown-body（配合 Aurora Glass 風格）。
export function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <div className={cn("markdown-body", className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
