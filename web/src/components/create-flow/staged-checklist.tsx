import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface StageItem { id: string; label: string; status: "pending" | "active" | "completed" | "failed"; progress?: number; }
interface StagedChecklistProps { stages: StageItem[]; className?: string; }

const icons = { pending: Circle, active: Loader2, completed: CheckCircle2, failed: XCircle };
const iconColors = { pending: "text-muted-foreground", active: "text-primary", completed: "text-green-400", failed: "text-destructive" };

export function StagedChecklist({ stages, className }: StagedChecklistProps) {
  return (
    <div className={cn("space-y-1", className)}>
      <h4 className="mb-3 text-sm font-medium">Pipeline stages</h4>
      {stages.map((s, i) => {
        const Icon = icons[s.status];
        const isLast = i === stages.length - 1;
        return (
          <div key={s.id} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <Icon className={cn("mt-0.5 h-4 w-4 shrink-0", iconColors[s.status], s.status === "active" && "animate-spin")} />
              {!isLast && <div className="min-h-[16px] w-px flex-1 bg-border" />}
            </div>
            <div className="flex-1 pb-4">
              <div className="flex items-center justify-between">
                <span className={cn("text-sm", s.status === "completed" && "text-muted-foreground line-through")}>{s.label}</span>
                {s.progress !== undefined && <span className="tabular-nums text-xs text-muted-foreground">{s.progress}%</span>}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
