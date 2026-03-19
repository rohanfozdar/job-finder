/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0E1117",
        card: "#1E2130",
        primary: "#4F8BF9",
        text: "#FAFAFA",
        success: "#2ecc71",
        info: "#3498db",
        warning: "#e67e22"
      }
    }
  },
  plugins: []
};

