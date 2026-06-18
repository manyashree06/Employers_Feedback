/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./src/**/*.{js,jsx,ts,tsx}"],
    theme: {
        extend: {
            fontFamily: {
                sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "Noto Sans", "sans-serif", "Apple Color Emoji", "Segoe UI Emoji"],
            },
            colors: {
                'primary': '#3B82F6',
                'primary-dark': '#1E3A8A',
                'secondary': '#10B981',
                'accent': '#F59E0B',
                'neutral': '#1F2937',
                'neutral-light': '#4B5563',
                'background': '#111827',
                'text-primary': '#E5E7EB',
                'text-secondary': '#9CA3AF',
            },
            animation: {
                'subtle-pulse': 'subtle-pulse 4s ease-in-out infinite',
            },
            keyframes: {
                'subtle-pulse': {
                    '0%, 100%': { opacity: 1 },
                    '50%': { opacity: .95 },
                },
            },
            boxShadow: {
                soft: '0 10px 15px -3px rgba(2, 6, 23, 0.08), 0 4px 6px -4px rgba(2, 6, 23, 0.06)'
            }
        },
    },
    plugins: [],
};
