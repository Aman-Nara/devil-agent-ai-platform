/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        devil: {
          dark: '#0a0a0a',
          red: '#FF4444',
          orange: '#FF8C00',
          gray: '#1a1a1a',
        }
      }
    },
  },
  plugins: [],
}
