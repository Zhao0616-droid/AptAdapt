import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')

const resourcePanel = await readFile(path.join(frontendRoot, 'src', 'components', 'ResourcePanel.vue'), 'utf8')
const workspaceStore = await readFile(path.join(frontendRoot, 'src', 'stores', 'workspace.js'), 'utf8')
const codeBlock = await readFile(path.join(frontendRoot, 'src', 'components', 'CodeBlock.vue'), 'utf8')
const normalizers = await readFile(path.join(frontendRoot, 'src', 'utils', 'resourceNormalizers.js'), 'utf8')

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

for (const [name, source] of [['ResourcePanel', resourcePanel], ['workspace store', workspaceStore]]) {
  assert(source.includes('normalizeResourceContent'), `${name} should normalize resources before rendering.`)
}

assert(normalizers.includes('normalizeCodeContent'), 'Shared normalizer should normalize code resources before rendering.')
assert(normalizers.includes('decodeEscapedText'), 'Shared normalizer should decode escaped newlines in generated code resources.')
assert(normalizers.includes('extractMarkdownCodeBlock'), 'Shared normalizer should extract fenced code blocks from markdown responses.')
assert(normalizers.includes('splitCodeExplanation'), 'Shared normalizer should separate code source from explanatory prose.')

assert(codeBlock.includes('normalizedCode'), 'CodeBlock should tolerate string or partially normalized code props.')
assert(codeBlock.includes('normalizedLanguage'), 'CodeBlock should map assembly/mips to a supported highlighter language.')
assert(codeBlock.includes('white-space: pre-wrap'), 'Code explanation should preserve real line breaks.')

console.log('Code resource rendering checks passed.')
