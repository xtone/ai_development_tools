import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { ModEntry } from '../types'

const SELF = 'mod-switcher'
const ROW = 'mod-'

const mods = atom({ plugin: 'mod-switcher', key: 'mods' } as const, [], { shape: 'mods-2' })
// 切り替え中の mod の id。
const busy = atom({ plugin: 'mod-switcher', key: 'busy' } as const, [] as string[])
// プロンプトの上の帯に一覧を出しているか。
const isOpen = atom({ plugin: 'mod-switcher', key: 'isOpen' } as const, false)
// 帯の中で選んでいる行。
const cursor = atom({ plugin: 'mod-switcher', key: 'cursor' } as const, 0)

const logLines: string[] = []
// 動かないときに追えるよう、何が起きたかを debug.log に残す。
const log = async ($: EngineInterface, line: string) => {
  logLines.push(`${new Date().toISOString()} ${line}`)
  await $.fs.write(`${$.plugin.root}/debug.log`, logLines.slice(-100).join('\n') + '\n')
}

// 選んでいる行を step だけ動かし、フォーカスリングもそこへ移す。
const moveCursor = async ($: EngineInterface, bandId: string, step: number) => {
  const list = await read($, mods)
  if (list.length === 0) {
    return
  }
  const at = Math.max(0, Math.min(list.length - 1, (await read($, cursor)) + step))
  await update($, cursor, () => at)
  const target = list[at]
  if (target && bandId) {
    const result = await $.ui.focus({ requestId: bandId, key: `${ROW}${target.id}` })
    if (result.deny) {
      await log($, `focus denied: ${result.deny}`)
    }
  }
}

const dirname = (path: string) => path.replace(/\/[^/]+\/?$/, '')
const basename = (path: string) => path.replace(/\/+$/, '').replace(/^.*\//, '')

// 開発中の mod のフォルダ（Claude が書く mod の置き場）と、無効にした mod の退避先。
// 退避先は置き場の外に置き、エンジンに mod として読まれないようにする。
const devFolders = ($: EngineInterface) => {
  const parent = dirname($.plugin.root)

  return { parent, parked: `${dirname(parent)}/.disabled/${basename(parent)}` }
}

const nameOf = async ($: EngineInterface, root: string): Promise<string | undefined> => {
  try {
    const parsed: unknown = JSON.parse(await $.fs.read(`${root}/.claude-plugin/plugin.json`))
    if (parsed && typeof parsed === 'object' && 'name' in parsed && typeof parsed.name === 'string') {
      return parsed.name
    }
  } catch {
    // plugin.json の無いフォルダは mod ではない。
  }

  return undefined
}

// hooks.json に modules がある（関数フックの）プラグインだけを mod として扱う。
const isMod = async ($: EngineInterface, root: string) => {
  try {
    return (await $.fs.read(`${root}/hooks/hooks.json`)).includes('"modules"')
  } catch {
    return false
  }
}

const listDev = async ($: EngineInterface, dir: string, isEnabled: boolean): Promise<ModEntry[]> => {
  if (!(await $.fs.exists(dir))) {
    return []
  }
  const found: ModEntry[] = []
  for (const entry of await $.fs.list(dir)) {
    const root = `${dir}/${entry.name}`
    if (entry.kind !== 'dir' || !(await isMod($, root))) {
      continue
    }
    const name = await nameOf($, root)
    if (name && name !== SELF) {
      found.push({ name, kind: 'dev', id: name, root, isEnabled })
    }
  }

  return found
}

const listInstalled = async ($: EngineInterface): Promise<ModEntry[]> => {
  const { exitCode, stdout } = await $.process.run(['claude', 'plugin', 'list', '--json'])
  if (exitCode !== 0) {
    return []
  }
  const parsed: unknown = JSON.parse(stdout)
  if (!Array.isArray(parsed)) {
    return []
  }
  const found: ModEntry[] = []
  for (const item of parsed as { id?: unknown; installPath?: unknown; enabled?: unknown; scope?: unknown }[]) {
    if (typeof item.id !== 'string' || typeof item.installPath !== 'string') {
      continue
    }
    if (!(await isMod($, item.installPath))) {
      continue
    }
    found.push({
      name: item.id.replace(/@.*$/, ''),
      kind: 'installed',
      id: item.id,
      root: item.installPath,
      scope: typeof item.scope === 'string' ? item.scope : undefined,
      isEnabled: item.enabled === true,
    })
  }

  return found
}

const refresh = async ($: EngineInterface) => {
  const { parent, parked } = devFolders($)
  const [on, off, installed] = await Promise.all([
    listDev($, parent, true),
    listDev($, parked, false),
    listInstalled($).catch(() => []),
  ])
  const all = [...on, ...off, ...installed].sort((a, b) => a.name.localeCompare(b.name))
  await update($, mods, () => all)

  return all
}

const run = async ($: EngineInterface, argv: readonly string[]) => {
  const { exitCode, stderr } = await $.process.run(argv)
  if (exitCode !== 0) {
    throw new Error(stderr.trim() || `${argv.join(' ')} exited ${exitCode}`)
  }
}

// 開発中の mod はフォルダごと退避先へ動かす（戻す）。置き場の変化でエンジンが読み込み直す。
// インストール済みの mod は claude plugin disable/enable のあと /reload-plugins で読み込み直す。
const toggle = async ($: EngineInterface, mod: ModEntry): Promise<string> => {
  const label = `${mod.name} を${mod.isEnabled ? '無効' : '有効'}にしました`
  if (mod.kind === 'dev') {
    const { parent, parked } = devFolders($)
    const target = `${mod.isEnabled ? parked : parent}/${basename(mod.root)}`
    if (await $.fs.exists(target)) {
      throw new Error(`${target} が既にあります`)
    }
    await run($, ['/bin/mkdir', '-p', dirname(target)])
    await run($, ['/bin/mv', mod.root, target])

    return label
  }
  const scope = mod.scope ? ['--scope', mod.scope] : []
  await run($, ['claude', 'plugin', mod.isEnabled ? 'disable' : 'enable', mod.id, ...scope])
  void $.command.run({ command: 'reload-plugins', args: '' }).catch(() => undefined)

  return label
}

const switchMod = async ($: EngineInterface, mod: ModEntry) => {
  if ((await read($, busy)).includes(mod.id)) {
    return
  }
  await update($, busy, list => [...list, mod.id])
  try {
    $.ui.toast(await toggle($, mod))
  } catch (error) {
    $.ui.toast(`${mod.name} を切り替えられませんでした: ${String(error)}`)
  } finally {
    await refresh($)
    await update($, busy, list => list.filter(id => id !== mod.id))
  }
}

const describe = (list: ModEntry[]) =>
  list.length === 0
    ? '切り替えられる mod はありません。'
    : list.map(m => `${m.isEnabled ? '●' : '○'} ${m.name}  ${m.kind === 'dev' ? 'dev-mods' : m.id}`).join('\n')

export const register: Register = on => {
  // 帯の id（フォーカスリングを動かすため）。
  let bandId = ''

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'mods',
      description: 'mod を一覧して on/off を切り替える（on/off <名前>、list も可）',
      immediate: true,
    })
    void refresh($)

    return next(e)
  })

  on('command.run', { command: 'mods' }, async ($, e) => {
    const list = await refresh($)
    const [action, ...rest] = e.args.trim().split(/\s+/)
    const name = rest.join(' ')
    if ((action === 'on' || action === 'off') && name) {
      const mod = list.find(m => m.name === name || m.id === name)
      if (!mod) {
        return { text: `${name} という mod は見つかりません。` }
      }
      if (mod.isEnabled === (action === 'on')) {
        return { text: `${mod.name} は既に${mod.isEnabled ? '有効' : '無効'}です。` }
      }
      await switchMod($, mod)

      return {}
    }
    if (action === 'list') {
      return { text: describe(list) }
    }
    const isNowOpen = !(await read($, isOpen))
    await update($, isOpen, () => isNowOpen)
    await update($, cursor, () => 0)

    return {}
  })

  // 帯が開いていて入力欄が空の間は、入力欄で押したキーを帯の操作に使う
  // （ctrl+x tab で帯に移らなくても操作できるように）。入力欄には何も入れない。
  on('prompt.edit', async ($, e, next) => {
    const key = e.key
    if (!key || key.ctrl || key.meta || e.text !== '' || !(await read($, isOpen))) {
      return next(e)
    }
    const consumed = { text: e.text, cursor: e.cursor }
    switch (key.key) {
      case 'j':
      case 'down':
        await moveCursor($, bandId, 1)
        return consumed
      case 'k':
      case 'up':
        await moveCursor($, bandId, -1)
        return consumed
      case 'x':
      case ' ':
      case 'space': {
        const list = await read($, mods)
        const target = list[Math.min(await read($, cursor), list.length - 1)]
        if (target) {
          void switchMod($, target)
        }
        return consumed
      }
      case 'q':
      case 'escape':
        await update($, isOpen, () => false)
        return consumed
      default:
        return next(e)
    }
  }).catch(($, e, next) => next(e))

  // 送信したら帯を閉じる。
  on('prompt.submit', async ($, e, next) => {
    await update($, isOpen, () => false)

    return next(e)
  }).catch(($, e, next) => next(e))

  // ↑↓ やクリックでリングが動いたら、選んでいる行もそこに合わせる。
  on('ui.focus', async ($, e, next) => {
    if (e.component === 'AbovePrompt' && e.element?.startsWith(ROW)) {
      const id = e.element.slice(ROW.length)
      const at = (await read($, mods)).findIndex(m => m.id === id)
      if (at >= 0) {
        await update($, cursor, () => at)
      }
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || !(await read($, isOpen))) {
      return next(e)
    }
    bandId = e.requestId
    const { Box, Button, Text } = $.ui.resolve(e)
    const list = await read($, mods)
    const working = await read($, busy)
    const at = Math.min(await read($, cursor), Math.max(0, list.length - 1))

    return (
      <Box flexDirection="column">
        <Text dimColor>mod の切り替え</Text>
        {list.length === 0 && <Text dimColor>切り替えられる mod はありません</Text>}
        {list.map((m, i) => (
          <Box>
            <Text color="cyan">{i === at ? '› ' : '  '}</Text>
            <Button
              key={`${ROW}${m.id}`}
              hotkey={i < 9 ? String(i + 1) : undefined}
              autoFocus={i === 0 ? true : undefined}
              onPress={() => {
                void switchMod($, m)
              }}
            >
              <Text color={m.isEnabled ? 'green' : undefined} dimColor={!m.isEnabled}>
                {m.isEnabled ? '● on ' : '○ off'} {m.name}
              </Text>
            </Button>
            <Text dimColor>
              {'  '}
              {m.kind === 'dev' ? 'dev-mods' : m.id}
              {working.includes(m.id) ? '  （切り替え中…）' : ''}
            </Text>
          </Box>
        ))}
        <Box>
          <Button key="down" plain dimColor hotkey="j" label="下" onPress={() => moveCursor($, bandId, 1)} />
          <Text dimColor> </Text>
          <Button key="up" plain dimColor hotkey="k" label="上" onPress={() => moveCursor($, bandId, -1)} />
          <Text dimColor> </Text>
          <Button
            key="toggle"
            plain
            dimColor
            hotkey="x"
            label="切り替え"
            onPress={() => {
              const target = list[at]
              if (target) {
                void switchMod($, target)
              }
            }}
          />
          <Text dimColor> </Text>
          <Button key="close" plain dimColor hotkey="q" label="閉じる" onPress={() => update($, isOpen, () => false)} />
          <Text dimColor>  j k / ↓↑ で移動・x / スペース / 数字キーで切り替え（その場で保存）・q / Esc で閉じる</Text>
        </Box>
      </Box>
    )
  })
}
