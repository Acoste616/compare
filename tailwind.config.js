/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./**/*.{js,ts,jsx,tsx}",
    "!./node_modules/**"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        tesla: {
          red: '#E31937',
          dark: '#18181b', // Zinc 900
          gray: '#27272a', // Zinc 800
          light: '#f4f4f5', // Zinc 100
        }
      }
    }
  },
  plugins: [],
}
