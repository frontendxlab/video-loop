import { Film } from "lucide-react";

export function Topbar() {
  return (
    <header className="flex h-12 items-center gap-4 border-b bg-background px-4">
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <Film className="h-4 w-4" />
        <span className="hidden sm:inline">VideoForge</span>
      </div>
      <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> idle
        </span>
      </div>
    </header>
  );
}
