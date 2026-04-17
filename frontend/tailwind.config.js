/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      colors: {
        // Abysse
        abyss: {
          950: "#05060a",
          900: "#0a0a12",
          800: "#0f0f1a",
          700: "#15151f",
        },
        // Accents néon
        neon: {
          violet: "#c084fc",
          fuchsia: "#d946ef",
          emerald: "#34d399",
          amber: "#fbbf24",
          cyan: "#67e8f9",
        },
      },
      boxShadow: {
        "glow-violet": "0 0 24px -4px rgba(192, 132, 252, 0.5)",
        "glow-fuchsia": "0 0 24px -4px rgba(217, 70, 239, 0.5)",
        "glow-emerald": "0 0 20px -4px rgba(52, 211, 153, 0.5)",
        "glow-amber": "0 0 20px -4px rgba(251, 191, 36, 0.55)",
        "glow-red": "0 0 16px -2px rgba(239, 68, 68, 0.65)",
        "inset-border": "inset 0 0 0 1px rgba(255,255,255,0.08)",
      },
      letterSpacing: {
        "mega": "0.28em",
      },
    },
  },
  plugins: [],
};