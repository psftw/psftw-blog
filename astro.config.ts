// @ts-check
import { defineConfig, passthroughImageService } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';
import mdx from '@astrojs/mdx';

// https://astro.build/config
export default defineConfig({
  site: 'https://psftw.com',

  image: {
    service: passthroughImageService()
  },

  vite: {
    plugins: [tailwindcss()],
  },

  devToolbar: {
    enabled: false,
  },

  integrations: [mdx()],

  markdown: {
    shikiConfig: {
      themes: {
        light: 'slack-dark',
      }
    }
  }
});
