import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')

const mainLayout = await readFile(path.join(frontendRoot, 'src', 'views', 'MainLayout.vue'), 'utf8')
const theme = await readFile(path.join(frontendRoot, 'src', 'assets', 'theme.css'), 'utf8')
const chatApi = await readFile(path.join(frontendRoot, 'src', 'api', 'chat.js'), 'utf8')
const resourceApi = await readFile(path.join(frontendRoot, 'src', 'api', 'resource.js'), 'utf8')
const chatPanel = await readFile(path.join(frontendRoot, 'src', 'components', 'ChatPanel.vue'), 'utf8')

const failures = []

if (/v-if="activeModule\s*===/.test(mainLayout) || /v-else-if="activeModule\s*===/.test(mainLayout)) {
  failures.push('MainLayout should keep module components mounted with v-show instead of v-if/v-else-if.')
}

const bodyRule = theme.match(/body\s*\{[\s\S]*?\}/)?.[0] || ''
if (/overflow\s*:\s*hidden\s*;/.test(bodyRule) || !/overflow-y\s*:\s*auto\s*;/.test(bodyRule)) {
  failures.push('Global body style should allow vertical page scrolling.')
}

if (!/timeout\s*:\s*120000/.test(chatApi)) {
  failures.push('Chat API should use an extended timeout for long agent workflows.')
}

if (!/timeout\s*:\s*120000/.test(resourceApi)) {
  failures.push('Resource generation API should use an extended timeout for long agent workflows.')
}

if (/streamContent\.value\s*=\s*mockReply\(userMsg\)/.test(chatPanel)) {
  failures.push('ChatPanel should not pretend mock resources were generated when the backend request fails.')
}

if (failures.length) {
  console.error('Workspace behavior check failed:')
  console.error(failures.map(item => `- ${item}`).join('\n'))
  process.exit(1)
}

console.log('Workspace behavior keeps state, scrolls, and handles long agent requests explicitly.')
