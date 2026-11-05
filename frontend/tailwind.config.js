/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        airtel: {
          red: '#E40000',
          darkred: '#B80000',
          black: '#1F1F1F',
          gray: '#F4F5F7',
          border: '#E2E8F0',
        },
        udyam: {
          navy: '#0F172A',
          blue: '#1E40AF',
          teal: '#0D9488',
          emerald: '#059669',
          amber: '#D97706',
          card: '#FFFFFF',
          muted: '#64748B',
        }
      },
      boxShadow: {
        'card': '0 2px 8px -2px rgba(15, 23, 42, 0.08), 0 4px 16px -4px rgba(15, 23, 42, 0.04)',
        'card-hover': '0 10px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.06)',
      }
    },
  },
  plugins: [],
}

