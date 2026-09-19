import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: ["class", '[data-theme="courseraDark"]'],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        heading: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        // Coursera Palette Tokens
        primary: {
          DEFAULT: "var(--color-primary)",
          hover: "var(--color-primary-hover)",
          soft: "var(--color-primary-soft)",
          surface: "var(--color-primary-soft)",
        },
        btn: {
          "primary-bg": "var(--color-btn-primary-bg)",
          "primary-text": "var(--color-btn-primary-text)",
          "secondary-border": "var(--color-btn-secondary-border)",
          "secondary-text": "var(--color-btn-secondary-text)",
          "disabled-bg": "var(--color-btn-disabled-bg)",
          "disabled-text": "var(--color-btn-disabled-text)",
        },
        accent: {
          DEFAULT: "var(--color-accent)",
          soft: "var(--color-accent-soft)",
        },
        highlight: {
          DEFAULT: "var(--color-highlight)",
        },
        canvas: {
          bg: "var(--color-bg)",
          surface: "var(--color-surface)",
          elevated: "var(--color-surface-elevated)",
        },
        border: {
          DEFAULT: "var(--color-border)",
          strong: "var(--color-border-strong)",
        },
        ink: {
          primary: "var(--color-text-primary)",
          secondary: "var(--color-text-secondary)",
          muted: "var(--color-text-muted)",
        },
        semantic: {
          success: "var(--color-success)",
          warning: "var(--color-warning)",
          error: "var(--color-error)",
          info: "var(--color-info)",
        },
        // Subject Router Accents
        subject: {
          math: {
            DEFAULT: "#0056D2",
            surface: "#E9F1FC",
          },
          bio: {
            DEFAULT: "#0F7B3F",
            surface: "#E6F4EA",
          },
          history: {
            DEFAULT: "#B75F00",
            surface: "#FFF1E6",
          },
          cs: {
            DEFAULT: "#0056D2",
            surface: "#E9F1FC",
          },
        },
        // Backwards compatibility mappings
        brand: {
          50: "#E9F1FC",
          100: "#CFE2FA",
          200: "#9FC5F5",
          300: "#6FA8F0",
          400: "#3F8BEB",
          500: "#0056D2",
          600: "#00419E",
          700: "#002D6B",
          800: "#001838",
          900: "#000000",
          950: "#000000",
        },
      },
    },
  },
  plugins: [
    require("daisyui")
  ],
  daisyui: {
    themes: [
      {
        courseraLight: {
          "primary": "#0056D2",
          "secondary": "#000000",
          "accent": "#F97316",
          "neutral": "#1F1F1F",
          "base-100": "#FFFFFF",
          "base-200": "#FFFFFF",
          "base-300": "#F8FAFC",
          "info": "#0056D2",
          "success": "#0F7B3F",
          "warning": "#B75F00",
          "error": "#C21E1E",
        },
      },
      "light",
    ],
    defaultTheme: "courseraLight",
    base: true,
    styled: true,
    utils: true,
    prefix: "",
    logs: false,
  },
};
export default config;
