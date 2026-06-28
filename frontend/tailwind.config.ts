import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Brand palette — Atenea Blue-Teal (copied from atenea-front)
        brand: {
          950: '#162e3a',
          900: '#264c5f',
          800: '#305e75',
          700: '#3d748f',
          600: '#4e8fad',
          500: '#5a9bba',
          400: '#6fabc5',
          300: '#7fbad8',
          200: '#b3d5e8',
          100: '#daeaf3',
          50:  '#f0f7fa',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        'xl':  '10px',
        '2xl': '14px',
        '3xl': '18px',
        '4xl': '24px',
      },
    },
  },
  plugins: [],
} satisfies Config
