/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#172026',
        fern: '#2f6f5e',
        signal: '#d96c3f',
        mist: '#eef3f1',
        line: '#d9e2de'
      }
    }
  },
  plugins: [],
};
