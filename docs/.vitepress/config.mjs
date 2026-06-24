import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "PrivaSub",
  description: "Offline, Privacy-First Desktop Captions Overlay.",
  base: '/PrivaSub/',
  head: [
    ['link', { rel: 'icon', href: '/PrivaSub/favicon.png' }],
    ['meta', { property: 'og:image', content: 'https://paudang.github.io/PrivaSub/favicon.png' }],
    ['meta', { property: 'og:title', content: 'PrivaSub | Offline Desktop Captions' }],
    ['meta', { property: 'og:description', content: 'Offline, Privacy-First Desktop Captions Overlay. Translate English to Vietnamese in real-time.' }],
    ['meta', { property: 'og:site_name', content: 'PrivaSub' }],
    ['meta', { property: 'og:url', content: 'https://paudang.github.io/PrivaSub/' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { name: 'twitter:card', content: 'summary' }],
    ['meta', { name: 'twitter:title', content: 'PrivaSub | Offline Desktop Captions' }],
    ['meta', { name: 'twitter:description', content: 'Offline, Privacy-First Desktop Captions Overlay.' }],
    ['meta', { name: 'twitter:image', content: 'https://paudang.github.io/PrivaSub/favicon.png' }]
  ],
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
          { text: 'System Requirements', link: '/guide/system-requirements' },
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
