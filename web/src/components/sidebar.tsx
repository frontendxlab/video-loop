import { Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";
import { Clapperboard, PlusCircle, BookOpen, BarChart3, Settings, Film } from "lucide-react";

const navItems = [
  { label: "Jobs", to: "/jobs", icon: Clapperboard },
  { label: "Create", to: "/create", icon: PlusCircle },
  { label: "Recipes", to: "/recipes", icon: BookOpen },
  { label: "Reports", to: "/reports", icon: BarChart3 },
  { label: "Settings", to: "/settings", icon: Settings },
] as const;

export function Sidebar() {
  const location = useLocation();
  return (
    <TooltipProvider>
      <aside className="flex h-full w-16 flex-col items-center gap-2 border-r bg-sidebar-background py-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Film className="h-5 w-5" />
        </div>
        <Separator className="my-1 w-8" />
        <nav className="flex flex-col items-center gap-1">
          {navItems.map((item) => {
            const active = location.pathname.startsWith(item.to);
            return (
              <Tooltip key={item.to}>
                <TooltipTrigger asChild>
                  <Button asChild variant={active ? "secondary" : "ghost"} size="icon" className={cn("h-10 w-10 rounded-lg", active && "bg-sidebar-accent text-sidebar-accent-foreground")}>
                    <Link to={item.to}><item.icon className="h-5 w-5" /></Link>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">{item.label}</TooltipContent>
              </Tooltip>
            );
          })}
        </nav>
      </aside>
    </TooltipProvider>
  );
}
