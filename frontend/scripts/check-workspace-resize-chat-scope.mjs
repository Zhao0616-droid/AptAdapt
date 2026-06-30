import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')

const mainLayout = await readFile(path.join(frontendRoot, 'src', 'views', 'MainLayout.vue'), 'utf8')
const chatPanel = await readFile(path.join(frontendRoot, 'src', 'components', 'ChatPanel.vue'), 'utf8')
const pathTree = await readFile(path.join(frontendRoot, 'src', 'components', 'PathTree.vue'), 'utf8')
const evaluationPanel = await readFile(path.join(frontendRoot, 'src', 'components', 'EvaluationPanel.vue'), 'utf8')

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

assert(mainLayout.includes("display: flex"), 'Workspace stack should use flex rows so pane heights visibly change.')
assert(mainLayout.includes("height: var(--chat-pane-height)"), 'Chat pane should bind directly to the draggable height variable.')
assert(mainLayout.includes("height: var(--path-pane-height)"), 'Path pane should bind directly to the draggable height variable.')
assert(mainLayout.includes('setPointerCapture'), 'Resize handle should capture pointer events during dragging.')
assert(mainLayout.includes('workspace-resizing'), 'Resize should add a body state to prevent text selection while dragging.')
assert(mainLayout.includes('handleChatOnlyRefresh'), 'MainLayout should expose a chat-only refresh action.')
assert(!mainLayout.includes('workspaceStore.resetForCourse(courseId)'), 'Course/chat refresh should not reset workspace resources or agent state.')
assert(mainLayout.includes('aptadapt:chat-reset'), 'Chat refresh should use a dedicated chat reset event.')

assert(chatPanel.includes('aptadapt:chat-reset'), 'ChatPanel should listen for chat-only reset events.')
assert(chatPanel.includes('createFreshConversation'), 'ChatPanel should create a fresh conversation on reset.')
assert(
  /onMounted\(\(\)\s*=>\s*\{[\s\S]*createFreshConversation\(courseStore\.currentId\)/.test(chatPanel),
  'Page refresh should start a fresh conversational learning profile instead of restoring cached chat history.'
)
assert(
  !/onMounted\(\(\)\s*=>\s*\{[\s\S]*loadMessagesForCourse\(courseStore\.currentId\)/.test(chatPanel),
  'ChatPanel must not restore cached chat messages when the page is refreshed.'
)

assert(!pathTree.includes('aptadapt:chat-reset'), 'PathTree should not react to chat reset events.')
assert(!evaluationPanel.includes('aptadapt:chat-reset'), 'EvaluationPanel should not react to chat reset events.')

console.log('Workspace resize and chat-only refresh checks passed.')
