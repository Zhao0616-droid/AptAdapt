import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const apiDir = path.resolve(scriptDir, '..', 'src', 'api')
const forbiddenPatterns = [
  { label: 'legacy user_id query/body field', pattern: /\buser_id\b/ },
  { label: 'legacy userId API parameter', pattern: /\buserId\b/ }
]

const entries = await readdir(apiDir, { withFileTypes: true })
const offenders = []

for (const entry of entries) {
  if (!entry.isFile() || !entry.name.endsWith('.js')) continue
  const file = path.join(apiDir, entry.name)
  const text = await readFile(file, 'utf8')
  const lines = text.split(/\r?\n/)
  lines.forEach((line, index) => {
    for (const { label, pattern } of forbiddenPatterns) {
      if (pattern.test(line)) {
        offenders.push(`${path.relative(process.cwd(), file)}:${index + 1}: ${label}: ${line.trim()}`)
      }
    }
  })
}

if (offenders.length) {
  console.error('Frontend API should rely on JWT instead of passing user ids:')
  console.error(offenders.join('\n'))
  process.exit(1)
}

console.log('Frontend API contract uses JWT user context.')
