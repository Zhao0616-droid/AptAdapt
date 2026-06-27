import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(scriptDir, '..', 'src')
const extensions = new Set(['.vue', '.js'])
const garbledPatterns = [
  '瀵', '寮', '涔', '鐢', '鏅', '绋', '璧', '鎴', '甯', '璋', '涓', '鍚',
  '澶', '姝', '钖', '杈', '鐭', '绛', '绔', '寰', '宸', '鎺', '浣', '閫',
  '鏂', '櫤', '娴', '骞', '€', '�'
]

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true })
  const files = []
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) files.push(...await walk(fullPath))
    else if (extensions.has(path.extname(entry.name))) files.push(fullPath)
  }
  return files
}

const offenders = []
for (const file of await walk(root)) {
  const text = await readFile(file, 'utf8')
  const lines = text.split(/\r?\n/)
  lines.forEach((line, index) => {
    if (garbledPatterns.some(pattern => line.includes(pattern))) {
      offenders.push(`${path.relative(process.cwd(), file)}:${index + 1}: ${line.trim()}`)
    }
  })
}

if (offenders.length) {
  console.error(`Found possible garbled text in ${offenders.length} line(s):`)
  console.error(offenders.slice(0, 80).join('\n'))
  if (offenders.length > 80) console.error(`...and ${offenders.length - 80} more`)
  process.exit(1)
}

console.log('No garbled text patterns found.')
