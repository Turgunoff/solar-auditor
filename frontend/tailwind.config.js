/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0B1220',
          900: '#0F172A',
          800: '#1E293B',
          700: '#334155',
        },
        accent: {
          cyan: '#06B6D4',
          emerald: '#10B981',
        },
      },
      fontFamily: {
        sans: ['"Segoe UI"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        panel: '0 12px 32px rgba(15, 35, 25, 0.10)',
      },
    },
  },
  plugins: [],
}
