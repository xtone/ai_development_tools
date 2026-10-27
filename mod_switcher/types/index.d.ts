export type ModEntry = {
  name: string
  // dev: Claude が書く mod のフォルダにある開発中の mod / installed: インストール済みのプラグイン
  kind: 'dev' | 'installed'
  // installed なら `<name>@<marketplace>`、dev なら名前
  id: string
  root: string
  scope?: string
  isEnabled: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'mod-switcher': {
      mods: Shaped<ModEntry[]>
      busy: string[]
      isOpen: boolean
      cursor: number
    }
  }
}
