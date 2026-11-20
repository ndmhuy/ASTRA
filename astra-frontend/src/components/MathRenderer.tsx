import React, { useMemo } from 'react';
import katex from 'katex';

interface MathRendererProps {
  content: string;
  className?: string;
}

const TABULAR_BLOCK_RE = /(\\begin\{tabular\}\{(?:[^{}]|\{[^{}]*\})*\}[\s\S]*?\\end\{tabular\})/g;
const MATH_TOKEN_RE = /(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$[^$\n]+?\$)/g;

/**
 * MathRenderer component for rendering mixed Vietnamese prose, LaTeX math,
 * simple formatting macros, and tabular blocks cleanly without raw TeX leaks.
 */
export const MathRenderer: React.FC<MathRendererProps> = ({ content, className = '' }) => {
  const renderedContent = useMemo(() => {
    if (!content) return '';

    const normalized = content
      .replace(/\\begin\{(?:center|adjustbox)\}(?:\{(?:[^{}]|\{[^{}]*\})*\})?/g, '')
      .replace(/\\end\{(?:center|adjustbox)\}/g, '');

    const segments = normalized.split(TABULAR_BLOCK_RE);
    return segments
      .map(segment => {
        if (!segment) return '';
        if (segment.startsWith('\\begin{tabular}')) {
          return renderTabularBlock(segment);
        }
        return renderInlineAndMath(segment);
      })
      .join('');
  }, [content]);

  return (
    <span
      className={`math-renderer ${className}`}
      dangerouslySetInnerHTML={{ __html: renderedContent }}
    />
  );
};

function renderTabularBlock(block: string): string {
  const match = block.match(/^\\begin\{tabular\}\{(?:[^{}]|\{[^{}]*\})*\}([\s\S]*?)\\end\{tabular\}$/);
  if (!match) return renderInlineAndMath(block);

  const cleaned = match[1]
    .replace(/\\(?:hline|toprule|midrule|bottomrule)\b/g, '')
    .replace(/\\cline\{[^}]*\}/g, '');

  const rows = cleaned
    .split(/\\\\(?:\[[^\]]*\])?/)
    .map(row => row.trim())
    .filter(Boolean);

  if (rows.length === 0) return '';

  const htmlRows = rows
    .map((row, rowIndex) => {
      const cells = row.split(/(?<!\\)&/).map(cell => renderInlineAndMath(cell.trim()));
      const tag = rowIndex === 0 ? 'th' : 'td';
      return `<tr>${cells.map(cell => `<${tag}>${cell}</${tag}>`).join('')}</tr>`;
    })
    .join('');

  return `<div class="math-table-wrap"><table class="math-latex-table"><tbody>${htmlRows}</tbody></table></div>`;
}

function renderInlineAndMath(text: string): string {
  const parts: string[] = [];
  MATH_TOKEN_RE.lastIndex = 0;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = MATH_TOKEN_RE.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(formatPlainLatex(escapeHtml(text.slice(lastIndex, match.index))));
    }

    const token = match[0];
    const isBlock = token.startsWith('$$') || token.startsWith('\\[');
    const sliceLen = token.startsWith('$$') || token.startsWith('\\[') || token.startsWith('\\(') ? 2 : 1;
    const mathCode = token.slice(sliceLen, -sliceLen).trim();

    try {
      const renderedMath = katex.renderToString(mathCode, {
        displayMode: isBlock,
        throwOnError: false,
        output: 'htmlAndMathml',
      });
      parts.push(renderedMath);
    } catch (err) {
      console.warn('KaTeX rendering error:', err);
      parts.push(escapeHtml(token));
    }

    lastIndex = MATH_TOKEN_RE.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(formatPlainLatex(escapeHtml(text.slice(lastIndex))));
  }

  return parts.join('');
}

function formatPlainLatex(escaped: string): string {
  let out = escaped;
  for (let i = 0; i < 2; i++) {
    out = out
      .replace(/\\textbf\{([^{}]*)\}/g, '<strong>$1</strong>')
      .replace(/\\(?:textit|emph)\{([^{}]*)\}/g, '<em>$1</em>')
      .replace(/\\underline\{([^{}]*)\}/g, '<u>$1</u>');
  }
  return out
    .replace(/\\\\(?:\[[^\]]*\])?/g, '<br/>')
    .replace(/\\[,;:]|~/g, ' ')
    .replace(/\\%/g, '%')
    .replace(/\\&amp;/g, '&amp;')
    .replace(/\\_/g, '_');
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/\n/g, '<br/>');
}
