/**
 * dsh-skill-bilibili-video-to-gif —— 把「B站视频转 GIF」技能打包成 DSH 插件。
 *
 * 插件做一件事：从本包 `bilibili-video-to-gif/SKILL.md` 读取技能定义，
 * 用 `ctx.skills.register()` 注册成运行时技能。技能的 scripts/ 目录通过
 * `resourceBase` 暴露，供 Agent 按技能正文里的相对路径调用。
 */

import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

/** Cordis 插件名。 */
export const name = 'dsh-skill-bilibili-video-to-gif'

/** 依赖技能服务。 */
export const inject = ['skills']

/**
 * 解析 SKILL.md 的 YAML frontmatter（只处理本技能用到的标量、折叠块与列表）。
 * @param {string} text 原始 Markdown。
 * @returns {{ data: Record<string, string>, body: string }}
 */
function parseFrontmatter(text) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(text)
  if (!match) return { data: {}, body: text }
  const data = {}
  const lines = match[1].split(/\r?\n/)
  let key = null
  let buffer = []
  const flush = () => {
    if (key !== null && buffer.length > 0) data[key] = buffer.join(' ').replace(/\s+/g, ' ').trim()
    key = null
    buffer = []
  }
  for (const line of lines) {
    const kv = /^([A-Za-z0-9_-]+):\s*(.*)$/.exec(line)
    if (kv) {
      flush()
      key = kv[1]
      const value = kv[2].trim()
      if (value !== '' && value !== '>-' && value !== '>' && value !== '|' && value !== '|-') buffer.push(value)
    } else if (key !== null) {
      const value = line.trim()
      if (value !== '') buffer.push(value)
    }
  }
  flush()
  return { data, body: text.slice(match[0].length) }
}

/**
 * 注册技能。
 * @param {import('@deepseek-ai/cordis').Context} ctx 插件上下文。
 */
export function apply(ctx) {
  const here = dirname(fileURLToPath(import.meta.url))
  const skillDir = join(here, 'bilibili-video-to-gif')
  const skillFile = join(skillDir, 'SKILL.md')

  const { data, body } = parseFrontmatter(readFileSync(skillFile, 'utf8'))

  ctx.effect(
    () =>
      ctx.skills.register({
        name: data.name ?? 'bilibili-video-to-gif',
        description: data.description ?? '把 B站或本地视频截成 GIF 动图，含抽帧定位法与调色板压缩。',
        content: body.trimStart(),
        source: 'custom',
        provider: 'dsh-skill-bilibili-video-to-gif',
        path: skillFile,
        resourceBase: { kind: 'directory', path: skillDir },
      }),
    'bilibili-video-to-gif skill',
  )
}
