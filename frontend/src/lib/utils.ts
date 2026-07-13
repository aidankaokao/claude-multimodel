import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// 每個元件都用它合 className。見 frontend-style-aurora-glass.md §1。
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
