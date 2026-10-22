import React, { createContext, useContext, useState, ReactNode } from "react";

interface CardContextValue {
  isOpen: boolean;
  toggle: () => void;
}

const CardContext = createContext<CardContextValue | undefined>(undefined);

export const SovereignCard: React.FC<{ children: ReactNode; className?: string }> = ({ children, className = "" }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <CardContext.Provider value={{ isOpen, toggle: () => setIsOpen(p => !p) }}>
      <article className={`rounded-lg border border-border bg-card p-6 text-card-foreground shadow-sm ${className}`}>
        {children}
      </article>
    </CardContext.Provider>
  );
};

export const CardHeader: React.FC<{ title: string; subtitle?: string }> = ({ title, subtitle }) => (
  <header className="mb-4">
    <h3 className="text-xl font-bold tracking-tight">{title}</h3>
    {subtitle && <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>}
  </header>
);

export const CardToggle: React.FC = () => {
  const ctx = useContext(CardContext);
  if (!ctx) throw new Error("CardToggle must be within SovereignCard");
  return (
    <button
      type="button"
      onClick={ctx.toggle}
      aria-expanded={ctx.isOpen}
      className="inline-flex min-h-[44px] items-center rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-2"
    >
      {ctx.isOpen ? "Show Less" : "Show Details"}
    </button>
  );
};
