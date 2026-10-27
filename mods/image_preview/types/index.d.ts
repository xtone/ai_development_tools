export type Preview = {
  path: string
  width: number
  height: number
  mediaType: string
  // 送信前の画像なら、入力欄の `[Image #N]` の N
  n?: number
  // 元のファイルのパス（D&D や Finder からのコピーで分かったとき）
  source?: string
}

declare module 'claude-code' {
  interface PluginState {
    'image-preview': {
      previews: Shaped<Preview[]>
      draft: Shaped<Preview[]>
    }
  }
}
