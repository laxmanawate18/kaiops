/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        'inter': ['Inter', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        kaiops: {
          dark: '#0B1120', // Deep Space Blue
          black: '#000000', // Void Black
          primary: '#00F0FF', // Neon Cyan
          secondary: '#7000FF', // Electric Purple
          success: '#00FF94', // Signal Green
          warning: '#FFB000', // Alert Orange
          error: '#FF0055', // Critical Red
          glass: 'rgba(11, 17, 32, 0.7)',
          'glass-border': 'rgba(255, 255, 255, 0.1)',
        }
      },
      animation: {
        'bounce': 'bounce 1.4s infinite ease-in-out both',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 240, 255, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 240, 255, 0.6), 0 0 10px rgba(0, 240, 255, 0.4)' },
        }
      }
    },
  },
  plugins: [],
}
