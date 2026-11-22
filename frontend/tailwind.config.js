/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base: '#080D18',
        side: '#101827',
        card: '#151F30',
        line: '#24324A',
        primary: { DEFAULT: '#3B82F6', soft: '#60A5FA' },
        accent: '#22D3EE',
        ink: { DEFAULT: '#E6ECF5', mute: '#9AA9C2' },
        // Flood information trust levels, always shown with a text label as well as colour.
        trust: { official: '#60A5FA', verified: '#34D399', unverified: '#FBBF24', historical: '#A78BFA', unknown: '#94A3B8' },
        danger: '#F87171',
      },
      fontFamily: {
        display: ['Sora', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
