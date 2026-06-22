import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "PrivaSub",
  description: "Offline, Privacy-First Desktop Captions Overlay.",
  base: '/PrivaSub/',
  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Guide', link: '/guide/introduction' },
      { text: 'Roadmap', link: 'https://trello.com/b/dP5oqzYl/privasub' },
      { text: 'Changelog', link: 'https://github.com/paudang/PrivaSub/blob/main/changelog.md' }
    ],

    editLink: {
      pattern: 'https://github.com/paudang/PrivaSub/edit/main/docs/:path',
      text: 'Edit this page on GitHub'
    },

    sidebar: [
      {
        text: 'Getting Started',
        items: [
          { text: 'Introduction', link: '/guide/introduction' },
          { text: 'Quick Start', link: '/guide/getting-started' },
        ]
      },
      {
        text: 'Core Features',
        items: [
          { text: 'Configuration & Settings', link: '/guide/configuration' },
          { text: 'Under the Hood (VAD & Loopback)', link: '/guide/how-it-works' },
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/paudang/PrivaSub' }
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2026-present PrivaSub Contributors'
    }
  }
})
