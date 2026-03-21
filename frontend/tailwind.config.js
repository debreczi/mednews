/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#F7F5F0',
        'bg-card': '#FFFFFF',
        'bg-header': '#1A2332',
        'bg-footer': '#151D28',
        'accent-teal': '#0D9488',
        'accent-teal-light': '#14B8A6',
        'accent-teal-dark': '#0F766E',
        'text-primary': '#1E293B',
        'text-secondary': '#475569',
        'text-muted': '#94A3B8',
      },
      borderRadius: {
        card: '14px',
        'card-sm': '8px',
      },
      fontFamily: {
        serif: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Source Sans 3', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
