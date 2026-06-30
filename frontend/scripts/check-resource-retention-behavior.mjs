import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')

const resourcePanel = await readFile(path.join(frontendRoot, 'src', 'components', 'ResourcePanel.vue'), 'utf8')
const workspaceStore = await readFile(path.join(frontendRoot, 'src', 'stores', 'workspace.js'), 'utf8')

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

assert(resourcePanel.includes('generationTopic'), 'ResourcePanel should derive generation topic from the latest chat/question context.')
assert(resourcePanel.includes('workspaceStore.lastMessage'), 'ResourcePanel should use the latest conversation question as the resource topic.')
assert(!resourcePanel.includes("'Cache 映射方式',"), 'ResourcePanel must not hard-code Cache 映射方式 as the generation topic.')
assert(resourcePanel.includes("['doc', 'quiz', 'code']"), 'ResourcePanel should generate a useful core resource bundle, including code when relevant.')
assert(resourcePanel.includes('workspaceStore.appendResources'), 'ResourcePanel should append generated resources instead of replacing history.')

assert(workspaceStore.includes('appendResources'), 'Workspace store should expose appendResources for preserving generated history.')
assert(workspaceStore.includes('mergeResourceHistory'), 'Workspace store should merge resource history instead of overwriting it.')
assert(workspaceStore.includes('makeResourceKey'), 'Workspace store should use stable resource keys for resource history.')
assert(!workspaceStore.includes('resources.value = Array.isArray(data.resources) ? data.resources.map(normalizeResource) : []'), 'Chat resources should not overwrite existing resource history.')
assert(!workspaceStore.includes('resources.value = items.map(normalizeResource)'), 'Resource factory resources should not overwrite existing resource history.')

console.log('Resource retention behavior checks passed.')
