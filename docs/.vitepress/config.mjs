import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "PrivaSub",
  description: "Offline, Privacy-First Desktop Captions Overlay.",
  base: '/PrivaSub/',
  head: [['link', { rel: 'icon', href: '/PrivaSub/favicon.png' }]],
  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Guide', link: '/guide/introduction' },
      { text: 'Roadmap', link: 'https://trello.com/b/dP5oqzYl/privasub' },
      { text: 'Changelog', link: 'https://github.com/paudang/PrivaSub/blob/main/changelog.md' },
      { text: 'v1.0.0', link: 'https://github.com/paudang/PrivaSub/releases' }
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
          { text: 'Contributing', link: '/guide/contributing' },
          { text: 'Troubleshooting', link: '/guide/troubleshooting' }
        ]
      },
      {
        text: 'Features',
        items: [
          { text: 'User Interface', link: '/features/ui' },
          { text: 'Configuration', link: '/features/configuration' },
        ]
      },
      {
        text: 'Architecture',
        items: [
          { text: 'System Architecture', link: '/architecture/system-architecture' },
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
