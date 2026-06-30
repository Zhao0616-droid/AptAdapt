import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')

const mainLayout = await readFile(path.join(frontendRoot, 'src', 'views', 'MainLayout.vue'), 'utf8')
const userStore = await readFile(path.join(frontendRoot, 'src', 'stores', 'user.js'), 'utf8')
const workspaceStore = await readFile(path.join(frontendRoot, 'src', 'stores', 'workspace.js'), 'utf8')
const mindMapViewer = await readFile(path.join(frontendRoot, 'src', 'components', 'MindMapViewer.vue'), 'utf8')

function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

assert(!mainLayout.includes('courseName.slice(0, 4)'), 'MainLayout should not truncate course names.')
assert(mainLayout.includes('applyCourseContext'), 'MainLayout should apply course context when course changes.')
assert(userStore.includes('applyCoursePersona'), 'User store should expose course-specific personas.')
assert(workspaceStore.includes('resetForCourse'), 'Workspace store should reset course-scoped state.')
assert(!mindMapViewer.includes("import mermaid from 'mermaid'"), 'MindMapViewer should not import mermaid during app boot.')
assert(mindMapViewer.includes("await import('mermaid')"), 'MindMapViewer should lazy-load mermaid only when rendering a mindmap.')

console.log('Course switch behavior checks passed.')
