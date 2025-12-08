import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
                mono: ['var(--font-mono)', 'monospace'],
            },
            colors: {
                primary: {
                    DEFAULT: 'rgb(251, 146, 60)',
                    dark: 'rgb(234, 88, 12)',
                    light: 'rgb(253, 186, 116)',
                },
                accent: {
                    DEFAULT: 'rgb(168, 85, 247)',
                    dark: 'rgb(126, 34, 206)',
                    light: 'rgb(192, 132, 252)',
                },
                surface: {
                    DEFAULT: 'rgb(51, 65, 85)',
                    elevated: 'rgb(71, 85, 105)',
                    hover: 'rgb(100, 116, 139)',
                },
            },
            boxShadow: {
                'glow': '0 0 20px rgb(251 146 60 / 0.3)',
                'glow-accent': '0 0 20px rgb(168 85 247 / 0.3)',
            },
            animation: {
                'slide-in': 'slide-in 0.3s ease-out',
                'fade-in': 'fade-in 0.2s ease-out',
                'scale-in': 'scale-in 0.2s ease-out',
                'slide-up': 'slide-up 0.3s ease-out',
                'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
            },
            keyframes: {
                'slide-in': {
                    from: { transform: 'translateX(100%)', opacity: '0' },
                    to: { transform: 'translateX(0)', opacity: '1' },
                },
                'fade-in': {
                    from: { opacity: '0' },
                    to: { opacity: '1' },
                },
                'scale-in': {
                    from: { transform: 'scale(0.95)', opacity: '0' },
                    to: { transform: 'scale(1)', opacity: '1' },
                },
                'slide-up': {
                    from: { transform: 'translateY(10px)', opacity: '0' },
                    to: { transform: 'translateY(0)', opacity: '1' },
                },
                'pulse-glow': {
                    '0%, 100%': { boxShadow: '0 0 0 0 rgb(251 146 60 / 0)' },
                    '50%': { boxShadow: '0 0 20px 4px rgb(251 146 60 / 0.3)' },
                },
            },
        },
    },
    plugins: [],
};
export default config;
