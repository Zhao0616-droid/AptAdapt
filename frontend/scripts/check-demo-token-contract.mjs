import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(scriptDir, '..', '..')

const jwtHandler = await readFile(path.join(repoRoot, 'app', 'utils', 'jwt_handler.py'), 'utf8')
const router = await readFile(path.join(repoRoot, 'frontend', 'src', 'router', 'index.js'), 'utf8')
const userStore = await readFile(path.join(repoRoot, 'frontend', 'src', 'stores', 'user.js'), 'utf8')

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

assert(router.includes("localStorage.setItem('token', 'demo-token')"), 'Router should still open the workspace in demo mode.')
assert(userStore.includes("token.value = 'demo-token'"), 'Demo mode should still use the shared demo token.')
assert(jwtHandler.includes('DEMO_TOKEN'), 'Backend auth should define the shared demo token.')
assert(jwtHandler.includes('DEMO_USER_ID'), 'Backend auth should map demo mode to a stable user id.')
assert(jwtHandler.includes('credentials.credentials == DEMO_TOKEN'), 'Backend auth should accept demo-token before JWT verification.')

console.log('Demo token contract checks passed.')
