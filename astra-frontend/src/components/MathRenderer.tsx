import React, { useMemo } from 'react';
import katex from 'katex';

interface MathRendererProps {
  content: string;
  className?: string;
}

/**
 * MathRenderer component for rendering mixed text and LaTeX mathematical expressions.
 * Supports:
 *  - Inline math: $...$
 *  - Display/Block math: $$...$$
 *  - Plain text fallback if KaTeX parsing encounters syntax anomalies
 */
export const MathRenderer: React.FC<MathRendererProps> = ({ content, className = '' }) => {
  const renderedContent = useMemo(() => {
    if (!content) return '';

    // Regex to detect $$block$$ and $inline$ delimiters
    // Matches $$...$$ or $...$
    const parts: string[] = [];
    const regex = /(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$)/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(content)) !== null) {
      // Push preceding plain text
      if (match.index > lastIndex) {
        parts.push(escapeHtml(content.substring(lastIndex, match.index)));
      }

      const token = match[0];
      const isBlock = token.startsWith('$$');
      const mathCode = isBlock ? token.slice(2, -2).trim() : token.slice(1, -1).trim();

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

      lastIndex = regex.lastIndex;
    }

    // Push trailing plain text
    if (lastIndex < content.length) {
      parts.push(escapeHtml(content.substring(lastIndex)));
    }

    return parts.join('');
  }, [content]);

  return (
    <span
      className={`math-renderer ${className}`}
      dangerouslySetInnerHTML={{ __html: renderedContent }}
    />
  );
};

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/\n/g, '<br/>');
}
