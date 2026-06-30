import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(scriptDir, '..', '..')
const frontendRoot = path.join(repoRoot, 'frontend')

const mainLayout = await readFile(path.join(frontendRoot, 'src', 'views', 'MainLayout.vue'), 'utf8')
const userStore = await readFile(path.join(frontendRoot, 'src', 'stores', 'user.js'), 'utf8')
const profileCard = await readFile(path.join(frontendRoot, 'src', 'components', 'ProfileCard.vue'), 'utf8')
const profileManager = await readFile(path.join(repoRoot, 'app', 'services', 'profile_manager.py'), 'utf8')

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

assert(mainLayout.includes('DEFAULT_WORKSPACE_PANE_HEIGHT'), 'Workspace panes should share one default height constant.')
assert(mainLayout.includes('chatPaneHeight = ref(DEFAULT_WORKSPACE_PANE_HEIGHT)'), 'Chat pane should start from the shared default height.')
assert(mainLayout.includes('pathPaneHeight = ref(DEFAULT_WORKSPACE_PANE_HEIGHT)'), 'Path pane should start from the shared default height.')
assert(mainLayout.includes('activeAgentCount'), 'Agent stats should count active/done agents, not only literal running status.')
assert(
  mainLayout.includes("agentStatuses.value.filter(a => a.status !== 'idle' && a.status !== 'error').length"),
  'Active agent count should match visible running/done agent statuses.'
)
assert(mainLayout.includes('grid-template-rows: auto minmax(0, 1fr)'), 'Left course/profile column should stretch the profile card to match the workbench height.')

assert(userStore.includes('dedupeSimilarItems'), 'Frontend profile normalization should remove similar duplicate tags.')
assert(userStore.includes('normalizeTagKey'), 'Frontend profile dedupe should normalize tag text before comparison.')
assert(profileCard.includes('visibleWeakPoints'), 'ProfileCard should render deduped weak point tags.')
assert(profileCard.includes('visibleLearningPreferences'), 'ProfileCard should render deduped preference tags.')

assert(profileManager.includes('_dedupe_similar_items'), 'Backend profile merge should dedupe similar list values.')
assert(profileManager.includes('_merge_similar_lists'), 'Backend profile merge should merge lists with similarity filtering.')
assert(!profileManager.includes('list(set(merged[key] + value))'), 'Backend profile merge should not use exact-match set dedupe only.')

console.log('Profile layout and agent stats checks passed.')
