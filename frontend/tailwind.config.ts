import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class', // Usar clase 'dark' en el elemento html
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark mode specific colors
        'dark-bg': '#0f172a',
        'dark-surface': '#1e293b',
        'dark-card': '#334155',
      },
      opacity: {
        'dark': 0.8,
      },
    },
  },
  plugins: [],
} satisfies Config
