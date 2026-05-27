/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#09090b", // zinc-950
        foreground: "#fafafa", // zinc-50
        card: {
          DEFAULT: "#0f0f12", // Vercel/Linear dark card
          foreground: "#fafafa",
        },
        popover: {
          DEFAULT: "#0f0f12",
          foreground: "#fafafa",
        },
        primary: {
          DEFAULT: "#6366f1", // Indigo-500
          foreground: "#fafafa",
        },
        secondary: {
          DEFAULT: "#27272a", // zinc-800
          foreground: "#fafafa",
        },
        muted: {
          DEFAULT: "#18181b", // zinc-900
          foreground: "#a1a1aa", // zinc-400
        },
        accent: {
          DEFAULT: "#27272a",
          foreground: "#fafafa",
        },
        destructive: {
          DEFAULT: "#ef4444",
          foreground: "#fafafa",
        },
        border: "#1f1f23", // very fine subtle border
        input: "#18181b",
        ring: "#6366f1",
        
        // Custom Health Status colors
        health: {
          healthy: "#10b981", // emerald-500
          stagnant: "#f59e0b", // amber-500
          atrisk: "#ef4444", // red-500
          archived: "#6b7280", // gray-500
        }
      },
      borderRadius: {
        lg: "0.75rem",
        md: "0.5rem",
        sm: "0.25rem",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "pulse-glow": "pulse-glow 2s infinite ease-in-out",
        "gradient-x": "gradient-x 15s ease infinite",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "0.6", boxShadow: "0 0 15px -3px rgba(99, 102, 241, 0.2)" },
          "50%": { opacity: "1", boxShadow: "0 0 25px 2px rgba(99, 102, 241, 0.4)" },
        },
        "gradient-x": {
          "0%, 100%": { "background-position": "0% 50%" },
          "50%": { "background-position": "100% 50%" },
        }
      },
      backgroundImage: {
        "grid-pattern": "linear-gradient(to right, rgba(255, 255, 255, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.05) 1px, transparent 1px)",
      }
    },
  },
  plugins: [],
}
