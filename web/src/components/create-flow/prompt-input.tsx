import { type ChangeEvent } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  className?: string;
}

export function PromptInput({ value, onChange, disabled, className }: PromptInputProps) {
  const charCount = value.length;
  const minChars = 10;
  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between">
        <Label htmlFor="prompt">Video prompt</Label>
        <span className={cn("text-xs tabular-nums", charCount < minChars ? "text-destructive" : "text-muted-foreground")}>
          {charCount} / {minChars} min
        </span>
      </div>
      <Textarea
        id="prompt"
        placeholder="Describe video you want to create..."
        value={value}
        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => onChange(e.target.value)}
        disabled={disabled}
        rows={5}
        className="resize-y min-h-[120px]"
      />
    </div>
  );
}
