import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const panelVariants = cva(
  "rounded-[calc(var(--radius)+1px)] border text-card-foreground",
  {
    variants: {
      tone: {
        default: "border-[hsl(var(--border)/0.78)] bg-[var(--panel)] shadow-panel",
        subtle: "border-[hsl(var(--border)/0.68)] bg-[var(--panel-subtle)] shadow-panel",
        elevated: "border-[hsl(var(--border)/0.82)] bg-card shadow-panel-md",
        muted: "border-[hsl(var(--border)/0.66)] bg-[var(--panel-muted)] shadow-none",
      },
      padding: {
        default: "p-5",
        compact: "p-4",
        roomy: "p-6",
        none: "p-0",
      },
    },
    defaultVariants: {
      tone: "default",
      padding: "default",
    },
  },
);

export interface PanelProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof panelVariants> {}

const Panel = React.forwardRef<HTMLDivElement, PanelProps>(({ className, tone, padding, ...props }, ref) => (
  <div ref={ref} className={cn(panelVariants({ tone, padding }), className)} {...props} />
));
Panel.displayName = "Panel";

export { Panel, panelVariants };
