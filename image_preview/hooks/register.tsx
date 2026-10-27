import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, RenderSurface } from 'claude-code'

import type { Preview } from '../types'

const PANE = 'image-preview'
const TITLE = '画像プレビュー'
// 変換後の PNG の長辺の上限（px）。端末に描くには十分で、読み込みも軽い。
const MAX_EDGE = 1600
// プロンプト上の帯に出すときの、画像 1 枚の高さ（行）。
const BAND_ROWS = 8
const IMAGE_TOKEN = /\[Image #(\d+)\]/g
const IMAGE_FILE = /\.(png|jpe?g|gif|webp|heic|tiff?|bmp)$/i

// ペインに出す画像（送信前は入力中の画像、送信後は送った画像）。
const previews = atom({ plugin: 'image-preview', key: 'previews' } as const, [], {
  shape: 'previews-1',
})
// 入力欄に添付中の画像。
const draft = atom({ plugin: 'image-preview', key: 'draft' } as const, [], { shape: 'draft-1' })

type ImageBlock = { type: 'image'; source?: { type?: string; media_type?: string; data?: string } }

const isImageBlock = (b: { type: string }): b is ImageBlock =>
  b.type === 'image' && (b as ImageBlock).source?.type === 'base64'

// 同じ画像を二度処理しないための目印。
const signatureOf = (blocks: ImageBlock[]) =>
  blocks.map(b => `${b.source?.data?.length ?? 0}:${b.source?.data?.slice(-32) ?? ''}`).join('|')

const imageNumbers = (text: string) => new Set([...text.matchAll(IMAGE_TOKEN)].map(m => Number(m[1])))

const cacheDir = ($: EngineInterface, kind: 'sent' | 'draft') => `${$.plugin.root}/.cache/${kind}`

// 画像ファイルを長辺 MAX_EDGE の PNG にして保存し、大きさを読む（macOS の sips を使う）。
const pngFrom = async ($: EngineInterface, source: string, png: string, mediaType: string) => {
  const script = [
    'set -e',
    'sips -s format png -Z "$3" "$1" --out "$2" >/dev/null',
    'test -s "$2"',
    'sips -g pixelWidth -g pixelHeight "$2"',
  ].join('\n')
  const { exitCode, stdout, stderr } = await $.process.run([
    '/bin/sh',
    '-c',
    script,
    'sh',
    source,
    png,
    String(MAX_EDGE),
  ])
  if (exitCode !== 0) {
    throw new Error(stderr.trim() || `sips exited ${exitCode}`)
  }
  const width = Number(/pixelWidth:\s*(\d+)/.exec(stdout)?.[1] ?? 1)
  const height = Number(/pixelHeight:\s*(\d+)/.exec(stdout)?.[1] ?? 1)
  const preview: Preview = { path: png, width, height, mediaType }

  return preview
}

// base64 の画像（送信したメッセージの画像ブロック）を PNG にする。
const toPng = async ($: EngineInterface, data: string, mediaType: string, name: string) => {
  const dir = cacheDir($, 'sent')
  const b64 = `${dir}/${name}.b64`
  const raw = `${dir}/${name}.raw`
  await $.fs.write(b64, data)
  await $.process.run(['/usr/bin/base64', '-D', '-i', b64, '-o', raw])
  try {
    return await pngFrom($, raw, `${dir}/${name}.png`, mediaType)
  } finally {
    await $.process.run(['/bin/rm', '-f', b64, raw])
  }
}

// 貼り付けた直後のクリップボードの画像を PNG で書き出す。
const fromClipboard = async ($: EngineInterface, name: string) => {
  const dir = cacheDir($, 'draft')
  const raw = `${dir}/${name}.clip.png`
  await $.process.run(['/bin/mkdir', '-p', dir])
  const { exitCode, stderr } = await $.process.run([
    '/usr/bin/osascript',
    '-e',
    'on run argv',
    '-e',
    'set f to open for access (POSIX file (item 1 of argv)) with write permission',
    '-e',
    'try',
    '-e',
    'write (the clipboard as «class PNGf») to f',
    '-e',
    'end try',
    '-e',
    'close access f',
    '-e',
    'end run',
    raw,
  ])
  if (exitCode !== 0) {
    throw new Error(stderr.trim() || 'クリップボードに画像がありません')
  }
  try {
    return await pngFrom($, raw, `${dir}/${name}.png`, 'image/png')
  } finally {
    await $.process.run(['/bin/rm', '-f', raw])
  }
}

// ドラッグや貼り付けで入ったファイルのパス（引用符や `\ ` を外す）。
const imagePathIn = async ($: EngineInterface, text: string) => {
  const path = text
    .trim()
    .replace(/^['"]|['"]$/g, '')
    .replace(/\\(.)/g, '$1')
  if (path.startsWith('/') && IMAGE_FILE.test(path) && (await $.fs.exists(path))) {
    return path
  }

  return undefined
}

// macOS のペーストボードにあるファイルのパスと、その版数を読む。
// drag: 最後にドラッグしたもの。D&D で添付すると、エンジンはパスを `[Image #N]` に置き換えて
//       渡してくれないので、ここから読む。
// general: クリップボード。Finder でコピーしたファイルなら元のパスが入っている。
const pasteboardScript = (board: 'drag' | 'general') =>
  [
    'ObjC.import("AppKit")',
    board === 'drag'
      ? 'const pb = $.NSPasteboard.pasteboardWithName($.NSPasteboardNameDrag)'
      : 'const pb = $.NSPasteboard.generalPasteboard',
    'const urls = pb.readObjectsForClassesOptions($([$.NSURL]), $({}))',
    'const paths = []',
    'if (urls) { for (let i = 0; i < urls.count; i++) { const u = urls.objectAtIndex(i); if (u.isFileURL) paths.push(u.path.js) } }',
    'JSON.stringify({ changeCount: Number(pb.changeCount), paths })',
  ].join('\n')

const readPasteboard = async (
  $: EngineInterface,
  board: 'drag' | 'general',
): Promise<{ changeCount: number; paths: string[] }> => {
  const { exitCode, stdout } = await $.process.run([
    '/usr/bin/osascript',
    '-l',
    'JavaScript',
    '-e',
    pasteboardScript(board),
  ])
  if (exitCode !== 0) {
    return { changeCount: -1, paths: [] }
  }
  const parsed = JSON.parse(stdout) as { changeCount?: unknown; paths?: unknown }

  return {
    changeCount: typeof parsed.changeCount === 'number' ? parsed.changeCount : -1,
    paths: Array.isArray(parsed.paths)
      ? parsed.paths.filter((p): p is string => typeof p === 'string' && IMAGE_FILE.test(p))
      : [],
  }
}

// 使い終えたドラッグの版数。これと違う版数のドラッグだけを、新しい D&D として使う。
let usedDrag = -1
let lastSignature = ''
// 直前まで入力欄にあった画像（送信後の画像に元のパスを引き継ぐため）。
let lastDraft: Preview[] = []
// 入力欄にある `[Image #N]` の N（前回見たとき）。
let seenNumbers = new Set<number>()
const logLines: string[] = []

// 動かないときに追えるよう、何が起きたかを debug.log に残す。
const log = async ($: EngineInterface, line: string) => {
  logLines.push(`${new Date().toISOString()} ${line}`)
  await $.fs.write(`${$.plugin.root}/debug.log`, logLines.slice(-100).join('\n') + '\n')
}

// 画像のファイルを Finder で選んだ状態で開く。
const reveal = async ($: EngineInterface, path: string) => {
  await $.process.run(['/usr/bin/open', '-R', path])
}

const copyPath = async ($: EngineInterface, path: string, surface: RenderSurface) => {
  const { isCopied } = await $.ui.copy({ text: path, surface })
  $.ui.toast(isCopied ? `コピーしました: ${path}` : 'パスをコピーできませんでした')
}

// 送信した画像をペインに出す。
const present = async ($: EngineInterface, list: Preview[], title: string) => {
  await update($, previews, () => list)
  const { isPlaced } = await $.ui.open({ id: PANE, title })

  return isPlaced
}

const showSent = async ($: EngineInterface, blocks: ImageBlock[], from: string) => {
  const signature = signatureOf(blocks)
  if (blocks.length === 0 || signature === lastSignature) {
    return
  }
  lastSignature = signature
  try {
    await log($, `${from}: ${blocks.length} image(s)`)
    await $.process.run(['/bin/rm', '-rf', cacheDir($, 'sent')])
    await $.process.run(['/bin/mkdir', '-p', cacheDir($, 'sent')])
    const stamp = Date.now()
    const made = await Promise.all(
      blocks.map((b, i) =>
        toPng($, b.source?.data ?? '', b.source?.media_type ?? 'image/png', `${stamp}-${i}`),
      ),
    )
    const sources = lastDraft.length === made.length ? lastDraft.map(p => p.source) : []
    const withSources = made.map((p, i) => ({ ...p, source: sources[i] }))
    const isPlaced = await present($, withSources, `${TITLE}（${made.length}枚）`)
    await log($, `converted ${made.map(p => `${p.width}x${p.height}`).join(', ')}; isPlaced=${isPlaced}`)
  } catch (error) {
    await log($, `failed: ${String(error)}`)
    $.ui.toast(`画像プレビューに失敗しました: ${String(error)}`)
  }
}

// 入力欄の `[Image #N]` が増えたら、その画像を手に入れて送信前のプレビューに出す。
// 減ったら（消した・送信した）プレビューからも外す。
const syncDraft = async ($: EngineInterface, text: string, inputText: string) => {
  const now = imageNumbers(text)
  const added = [...now].filter(n => !seenNumbers.has(n))
  seenNumbers = now
  const kept = (await read($, draft)).filter(p => p.n !== undefined && now.has(p.n))
  if (added.length === 0) {
    await update($, draft, () => kept)

    return
  }
  try {
    const typed = await imagePathIn($, inputText)
    const drag = await readPasteboard($, 'drag')
    const dragged = drag.changeCount !== usedDrag ? drag.paths : []
    usedDrag = drag.changeCount
    const copied = typed || dragged.length > 0 ? [] : (await readPasteboard($, 'general')).paths
    const made: Preview[] = []
    for (const [i, n] of added.entries()) {
      const name = `${Date.now()}-${n}`
      const source = typed ?? dragged[i] ?? copied[i]
      const preview = source
        ? await pngFrom($, source, `${cacheDir($, 'draft')}/${name}.png`, 'image/png')
        : await fromClipboard($, name)
      made.push({ ...preview, n, source })
      await log($, `draft: +${n} from ${source ?? 'clipboard'}`)
    }
    const list = [...kept, ...made]
    await update($, draft, () => list)
    lastDraft = list
  } catch (error) {
    await log($, `draft failed: ${String(error)}`)
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'image-preview',
      description: '添付画像のプレビューペインを開く（clear で消去）',
    })
    usedDrag = (await readPasteboard($, 'drag')).changeCount
    // 添付した瞬間には edit も change も来ないことがあるので、入力欄を短い間隔で見る。
    $.clock.every(400, () => {
      void $.prompt.read().then(box => syncDraft($, box.text, ''))
    })

    return next(e)
  })

  on('command.run', { command: 'image-preview' }, async ($, e) => {
    if (e.args.trim() === 'clear') {
      await $.process.run(['/bin/rm', '-rf', `${$.plugin.root}/.cache`])
      await update($, previews, () => [])
      await update($, draft, () => [])
      await $.ui.close({ id: PANE })

      return { text: '画像プレビューを消去しました。' }
    }
    await $.ui.open({ id: PANE, title: TITLE, focus: true, closeOnEscape: true })

    return { text: '画像プレビューを開きました。' }
  })

  // 入力欄への貼り付け・ドラッグ（edit）と、それ以外の書き換え（change）の両方を見る。
  on('prompt.edit', async ($, e, next) => {
    const box = await next(e)
    void syncDraft($, box.text, e.inputText)

    return box
  })

  on('prompt.change', async ($, e, next) => {
    const changed = await next(e)
    void syncDraft($, e.text, '')

    return changed
  })

  // 会話に行が足されるとき（通常の送信も、作業中に送ったメッセージも）に画像を拾う。
  on('session.append', async ($, e, next) => {
    const appended = await next(e)
    if (e.agentId === undefined && e.message.type === 'user') {
      const content = e.message.content
      if (!content.some(b => b.type === 'tool_result')) {
        void showSent($, content.filter(isImageBlock), `session.append(${e.door})`)
      }
    }

    return appended
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const list = await read($, draft)
    // 送信前の画像は、入力欄のすぐ上の帯に出す。
    if (e.props.hasSurvey || list.length === 0 || e.surface !== 'terminal') {
      return next(e)
    }
    const { Box, Button, Text, Image } = $.ui.resolve(e)
    const rows = Math.max(3, Math.min(BAND_ROWS, e.props.maxRows - 3))

    return (
      <Box flexDirection="column">
        <Text dimColor>添付中の画像（送信前）</Text>
        <Box>
          {list.map((p, i) => {
            const columns = Math.max(16, Math.min(80, Math.round((rows * 2 * p.width) / p.height)))
            const file = p.source ?? p.path
            return (
              <Box flexDirection="column" marginRight={2} width={columns}>
                <Image source={{ file: p.path, format: 'png' }} columns={columns} rows={rows} alt={`[Image #${p.n ?? '?'}]`} />
                <Text dimColor wrap="truncate-start">
                  [Image #{p.n ?? '?'}] {file}
                </Text>
                <Box>
                  <Button key={`band-reveal-${i}`} plain dimColor label="Finder" onPress={() => reveal($, file)} />
                  <Text> </Text>
                  <Button key={`band-copy-${i}`} plain dimColor label="パスをコピー" onPress={press => copyPath($, file, press.surface)} />
                </Box>
              </Box>
            )
          })}
        </Box>
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    // Image は端末の描画面にだけある。
    const Image = e.surface === 'terminal' ? $.ui.resolve(e).Image : undefined
    const list = await read($, previews)
    if (list.length === 0) {
      return <Text dimColor>まだ画像はありません。画像を添付するとここに表示されます。</Text>
    }
    const columns = Math.max(10, Math.min(255, (e.viewport?.columns ?? 60) - 2))
    const room = Math.max(4, (e.viewport?.rows ?? 30) - list.length * 3)
    const each = Math.max(3, Math.floor(room / list.length))

    return (
      <Box flexDirection="column">
        {list.map((p, i) => {
          // 端末のセルは縦長（おおよそ 横1:縦2）なので、行数は半分にする。
          const fitRows = Math.round((columns * p.height) / p.width / 2)
          const rows = Math.max(1, Math.min(255, each, fitRows))
          const cols = Math.max(1, Math.min(columns, Math.round((rows * 2 * p.width) / p.height)))
          return (
            <Box flexDirection="column">
              <Text dimColor wrap="truncate-start">
                {p.n !== undefined ? `[Image #${p.n}]` : `#${i + 1}`} {p.width}×{p.height}  {p.source ?? p.path}
              </Text>
              <Box>
                <Button key={`reveal-${i}`} plain dimColor label="Finder で表示" onPress={() => reveal($, p.source ?? p.path)} />
                <Text> </Text>
                <Button
                  key={`copy-${i}`}
                  plain
                  dimColor
                  label="パスをコピー"
                  onPress={press => copyPath($, p.source ?? p.path, press.surface)}
                />
              </Box>
              {Image ? (
                <Image
                  source={{ file: p.path, format: 'png' }}
                  columns={cols}
                  rows={rows}
                  alt={`添付画像 ${i + 1}`}
                />
              ) : (
                <Text dimColor>この画面では画像を表示できません: {p.path}</Text>
              )}
            </Box>
          )
        })}
      </Box>
    )
  })
}
