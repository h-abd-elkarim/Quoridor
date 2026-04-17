import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Props {
  content: React.ReactNode;
  children: React.ReactNode;
  side?: "top" | "bottom";
}

export default function Tooltip({ content, children, side = "top" }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      {children}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: side === "top" ? 4 : -4, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: side === "top" ? 4 : -4, scale: 0.97 }}
            transition={{ duration: 0.14, ease: "easeOut" }}
            className={`absolute z-50 left-1/2 -translate-x-1/2 ${
              side === "top" ? "bottom-full mb-2" : "top-full mt-2"
            } pointer-events-none`}
          >
            <div className="glass-strong rounded-lg px-3 py-2 w-64 shadow-[0_8px_32px_-8px_rgba(0,0,0,0.8)]">
              <div className="text-[10px] leading-relaxed text-zinc-300 font-mono">
                {content}
              </div>
              <div className="absolute left-1/2 -translate-x-1/2 w-2 h-2 bg-[rgba(10,10,18,0.85)] border border-white/10 rotate-45"
                style={side === "top" ? { bottom: -4, borderTop: "none", borderLeft: "none" } : { top: -4, borderBottom: "none", borderRight: "none" }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}