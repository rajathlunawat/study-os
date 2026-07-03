import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'brand-dark': '#0d0d0d',
        'brand-accent': '#FDE68A', // soft peach/yellow from the image
        'brand-sidebar': '#121212',
      },
    },
  },
  plugins: [],
}
export default config
