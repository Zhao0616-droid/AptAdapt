export function parseJsonContent(content) {
  if (typeof content !== 'string') return content
  try {
    return JSON.parse(content)
  } catch {
    return content
  }
}

export function decodeEscapedText(value = '') {
  return String(value || '')
    .replace(/\\r\\n/g, '\n')
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '\t')
    .replace(/\\"/g, '"')
}

export function extractMarkdownCodeBlock(text = '') {
  const decoded = decodeEscapedText(text)
  const match = decoded.match(/```([\w#+-]*)\s*\n([\s\S]*?)```/)
  if (!match) return null
  return {
    language: normalizeCodeLanguage(match[1]),
    source: match[2].trim(),
    before: decoded.slice(0, match.index).trim(),
    after: decoded.slice(match.index + match[0].length).trim()
  }
}

export function splitCodeExplanation(text = '') {
  const decoded = decodeEscapedText(text).trim()
  const lines = decoded.split('\n')
  const firstCodeLine = lines.findIndex(line =>
    /^\s*(\.data|\.text|#include|module\s+\w+|def\s+\w+|addi?\s|li\s|la\s|lw\s|sw\s|syscall|main:|[A-Za-z_]\w*:)/.test(line)
  )
  if (firstCodeLine <= 0) {
    return { source: decoded, explanation: '' }
  }
  return {
    source: lines.slice(firstCodeLine).join('\n').trim(),
    explanation: lines.slice(0, firstCodeLine).join('\n').trim()
  }
}

export function normalizeCodeLanguage(language = '') {
  const lang = String(language || '').trim().toLowerCase()
  if (['asm', 'assembly', 'mips', 'riscv', 'risc-v'].includes(lang)) return 'x86asm'
  if (['verilog', 'systemverilog'].includes(lang)) return 'verilog'
  if (['py', 'python'].includes(lang)) return 'python'
  if (['c', 'cpp', 'c++'].includes(lang)) return 'c'
  return lang || 'x86asm'
}

export function normalizeCodeContent(content, title = '') {
  const parsed = parseJsonContent(content)
  if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
    const rawSource = parsed.source || parsed.code || parsed.content || ''
    const block = extractMarkdownCodeBlock(rawSource)
    if (block) {
      return {
        language: normalizeCodeLanguage(parsed.language || block.language),
        source: block.source,
        explanation: decodeEscapedText(parsed.explanation || [block.before, block.after].filter(Boolean).join('\n\n')).trim()
      }
    }
    const split = splitCodeExplanation(rawSource)
    return {
      language: normalizeCodeLanguage(parsed.language || title),
      source: split.source,
      explanation: decodeEscapedText(parsed.explanation || split.explanation).trim()
    }
  }

  const raw = decodeEscapedText(parsed)
  const block = extractMarkdownCodeBlock(raw)
  if (block) {
    return {
      language: block.language,
      source: block.source,
      explanation: [block.before, block.after].filter(Boolean).join('\n\n')
    }
  }
  const split = splitCodeExplanation(raw)
  return {
    language: normalizeCodeLanguage(title),
    source: split.source,
    explanation: split.explanation
  }
}

export function normalizeQuizContent(content, title) {
  const parsed = typeof content === 'string' ? parseJsonContent(content) : content
  if (parsed?.questions && Array.isArray(parsed.questions)) {
    return {
      title: parsed.title || title || '巩固练习',
      knowledge_point: parsed.knowledge_point || 'Cache 映射方式',
      questions: parsed.questions
    }
  }
  if (Array.isArray(parsed)) {
    return {
      title: title || '巩固练习',
      knowledge_point: parsed[0]?.knowledge_point || 'Cache 映射方式',
      questions: parsed
    }
  }
  return {
    title: title || parsed?.title || '巩固练习',
    knowledge_point: parsed?.knowledge_point || 'Cache 映射方式',
    questions: parsed?.question ? [parsed] : []
  }
}

export function normalizeResourceContent(item) {
  const content = item.type === 'quiz' || item.type === 'code'
    ? parseJsonContent(item.content)
    : item.content
  if (item.type === 'quiz') return normalizeQuizContent(content, item.title)
  if (item.type === 'code') return normalizeCodeContent(content, item.title)
  return content
}
