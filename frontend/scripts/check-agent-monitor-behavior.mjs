import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')
const workspaceStore = await readFile(path.join(frontendRoot, 'src', 'stores', 'workspace.js'), 'utf8')
const mainLayout = await readFile(path.join(frontendRoot, 'src', 'views', 'MainLayout.vue'), 'utf8')

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

assert(workspaceStore.includes('ALL_AGENT_NAMES'), 'Workspace store should define a stable full agent topology.')
assert(/const names\s*=\s*ALL_AGENT_NAMES/.test(workspaceStore), 'Agent monitor should always render the full topology, not only the latest sequence.')
assert(workspaceStore.includes('active: agentSequence.value.includes(name)'), 'Agent status should expose whether an agent participated in the latest run.')
assert(workspaceStore.includes("status: log?.status || 'idle'"), 'Agents without execution logs should remain visible as idle.')
assert(mainLayout.includes('activeAgentCount'), 'MainLayout should count active/done participants in the top agent stats.')
assert(mainLayout.includes('agentStatuses.value.filter(a => a.active && a.status !=='), 'Agent running stat should not show zero while completed participants are visible.')

console.log('Agent monitor keeps the full topology visible.')
