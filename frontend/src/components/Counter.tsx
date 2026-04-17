import React, { useEffect, useRef, useState } from "react";

interface Props {
  value: number;
  duration?: number; // ms
  className?: string;
  format?: (n: number) => string;
}

/**
 * Compteur animé type "odomètre" : interpole la valeur précédente
 * vers la nouvelle. Utilisé pour les nœuds explorés, la profondeur, etc.
 */
export default function Counter({ value, duration = 650, className = "", format }: Props) {
  const [display, setDisplay] = useState(value);
  const fromRef = useRef(value);
  const rafRef = useRef<number | null>(null);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    fromRef.current = display;
    startRef.current = null;

    const tick = (ts: number) => {
      if (startRef.current === null) startRef.current = ts;
      const elapsed = ts - startRef.current;
      const t = Math.min(1, elapsed / duration);
      // easeOutCubic pour un feel "premium"
      const eased = 1 - Math.pow(1 - t, 3);
      const next = fromRef.current + (value - fromRef.current) * eased;
      setDisplay(next);
      if (t < 1) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        setDisplay(value);
      }
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, duration]);

  const rounded = Math.round(display);
  const text = format ? format(rounded) : rounded.toLocaleString("fr-FR");

  return <span className={`tabular ${className}`}>{text}</span>;
}