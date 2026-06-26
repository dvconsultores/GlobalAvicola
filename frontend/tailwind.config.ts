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
        // Brand palette — Deep Midnight Navy
        brand: {
          950: '#030C18',
          900: '#071829',
          800: '#0B2340',
          700: '#0F3361',
          600: '#154F94',
          500: '#1A6DCC',
          400: '#3B82F6',
          300: '#60A5FA',
          200: '#BFDBFE',
          100: '#DBEAFE',
          50:  '#EFF6FF',
        },
        // Dark mode surfaces
        'dark-bg':      '#0A0F1A',
        'dark-surface': '#111827',
        'dark-card':    '#1C2533',
        'dark-border':  '#1E293B',
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
      boxShadow: {
        'card':    '0 1px 4px 0 rgb(15 23 42 / 0.06), 0 1px 2px -1px rgb(15 23 42 / 0.04)',
        'card-md': '0 4px 12px -2px rgb(15 23 42 / 0.10), 0 2px 4px -2px rgb(15 23 42 / 0.07)',
        'card-lg': '0 10px 24px -4px rgb(15 23 42 / 0.12), 0 4px 8px -4px rgb(15 23 42 / 0.07)',
        'inset-t': 'inset 0 1px 0 0 rgb(255 255 255 / 0.06)',
        'nav':     '0 -1px 0 0 rgb(15 23 42 / 0.06), 0 -4px 16px -2px rgb(15 23 42 / 0.05)',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(160deg, #071829 0%, #0F3361 100%)',
        'accent-gradient': 'linear-gradient(135deg, #1A6DCC 0%, #3B82F6 100%)',
        'card-shine': 'linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0) 60%)',
      },
    },
  },
  plugins: [],
} satisfies Config
