/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#a78bfa',
          vivid: '#8b5cf6',
          light: '#c4b5fd',
          dim: 'rgba(139, 92, 246, 0.12)',
        },
        neon: {
          DEFAULT: '#e879f9',
          dim: 'rgba(232, 121, 249, 0.10)',
        },
        background: '#06060f',
        surface: '#0c0c1d',
      },
      fontFamily: {
        display: ['Space Grotesk', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
