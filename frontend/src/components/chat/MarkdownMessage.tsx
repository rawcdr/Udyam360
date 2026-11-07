import React from 'react';

interface MarkdownMessageProps {
  content: string;
  isAssistant?: boolean;
}

export const MarkdownMessage: React.FC<MarkdownMessageProps> = ({ content, isAssistant = true }) => {
  // Helper to parse inline styles (**bold**, *italic*, `code`)
  const renderInline = (text: string): React.ReactNode[] => {
    // Split by markdown bold (**...**) and inline code (`...`)
    const parts: React.ReactNode[] = [];
    const regex = /(\*\*.*?\*\*|`.*?`|\*.*?\*)/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }

      const token = match[0];
      if (token.startsWith('**') && token.endsWith('**')) {
        const inner = token.slice(2, -2);
        parts.push(
          <strong key={match.index} className={isAssistant ? "font-bold text-slate-900" : "font-bold text-white"}>
            {inner}
          </strong>
        );
      } else if (token.startsWith('`') && token.endsWith('`')) {
        const inner = token.slice(1, -1);
        parts.push(
          <code
            key={match.index}
            className={`px-1 py-0.5 rounded text-xs font-mono ${
              isAssistant ? 'bg-slate-200/80 text-slate-800' : 'bg-red-700 text-white'
            }`}
          >
            {inner}
          </code>
        );
      } else if (token.startsWith('*') && token.endsWith('*')) {
        const inner = token.slice(1, -1);
        parts.push(
          <em key={match.index} className="italic">
            {inner}
          </em>
        );
      }

      lastIndex = regex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts.length > 0 ? parts : [text];
  };

  // Group lines into blocks (headings, lists, tables, paragraphs)
  const lines = content.split('\n');
  const blocks: React.ReactNode[] = [];
  let currentList: { type: 'ul' | 'ol'; items: string[] } | null = null;
  let currentTable: string[] | null = null;

  const flushList = () => {
    if (currentList) {
      if (currentList.type === 'ul') {
        blocks.push(
          <ul key={`ul-${blocks.length}`} className="my-2 space-y-1 pl-4 list-disc marker:text-red-500">
            {currentList.items.map((item, idx) => (
              <li key={idx} className="leading-snug">
                {renderInline(item)}
              </li>
            ))}
          </ul>
        );
      } else {
        blocks.push(
          <ol key={`ol-${blocks.length}`} className="my-2 space-y-1 pl-4 list-decimal marker:text-red-500 marker:font-semibold">
            {currentList.items.map((item, idx) => (
              <li key={idx} className="leading-snug">
                {renderInline(item)}
              </li>
            ))}
          </ol>
        );
      }
      currentList = null;
    }
  };

  const flushTable = () => {
    if (currentTable && currentTable.length >= 2) {
      const headerRow = currentTable[0]
        .split('|')
        .map((c) => c.trim())
        .filter((c) => c.length > 0);
      const dataRows = currentTable
        .slice(1)
        .filter((r) => !r.includes('---'))
        .map((r) =>
          r
            .split('|')
            .map((c) => c.trim())
            .filter((c) => c.length > 0)
        );

      blocks.push(
        <div key={`table-${blocks.length}`} className="my-3 overflow-x-auto rounded-lg border border-slate-200 shadow-2xs">
          <table className="w-full text-xs text-left text-slate-700 bg-white">
            <thead className="bg-slate-50 text-slate-800 font-bold border-b border-slate-200">
              <tr>
                {headerRow.map((h, i) => (
                  <th key={i} className="px-3 py-2">
                    {renderInline(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {dataRows.map((row, rIdx) => (
                <tr key={rIdx} className={rIdx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                  {row.map((cell, cIdx) => (
                    <td key={cIdx} className="px-3 py-1.5 whitespace-nowrap">
                      {renderInline(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      currentTable = null;
    }
  };

  lines.forEach((rawLine, idx) => {
    const line = rawLine.trim();

    // Check if line is part of a markdown table
    if (line.startsWith('|') && line.endsWith('|')) {
      flushList();
      if (!currentTable) currentTable = [];
      currentTable.push(line);
      return;
    } else {
      flushTable();
    }

    // Horizontal Rule
    if (/^---+$|^===+$/.test(line)) {
      flushList();
      blocks.push(<hr key={`hr-${idx}`} className="my-3 border-slate-200" />);
      return;
    }

    // Headings
    if (line.startsWith('#### ')) {
      flushList();
      blocks.push(
        <h5 key={`h4-${idx}`} className="font-bold text-slate-900 text-xs uppercase tracking-wider mt-3 mb-1">
          {renderInline(line.replace('#### ', ''))}
        </h5>
      );
      return;
    }

    if (line.startsWith('### ')) {
      flushList();
      blocks.push(
        <h4 key={`h3-${idx}`} className="font-extrabold text-slate-900 text-sm mt-3 mb-1.5 flex items-center space-x-1.5">
          <span className="w-1.5 h-3.5 bg-red-600 rounded-full inline-block" />
          <span>{renderInline(line.replace('### ', ''))}</span>
        </h4>
      );
      return;
    }

    if (line.startsWith('## ')) {
      flushList();
      blocks.push(
        <h3 key={`h2-${idx}`} className="font-extrabold text-slate-900 text-base mt-4 mb-2">
          {renderInline(line.replace('## ', ''))}
        </h3>
      );
      return;
    }

    // Bullet List Item (* or -)
    const bulletMatch = line.match(/^[\*\-]\s+(.+)/);
    if (bulletMatch) {
      if (!currentList || currentList.type !== 'ul') {
        flushList();
        currentList = { type: 'ul', items: [] };
      }
      currentList.items.push(bulletMatch[1]);
      return;
    }

    // Numbered List Item (1. , 2. )
    const numberedMatch = line.match(/^\d+\.\s+(.+)/);
    if (numberedMatch) {
      if (!currentList || currentList.type !== 'ol') {
        flushList();
        currentList = { type: 'ol', items: [] };
      }
      currentList.items.push(numberedMatch[1]);
      return;
    }

    // Regular line or empty line
    flushList();
    if (line.length > 0) {
      blocks.push(
        <p key={`p-${idx}`} className="my-1.5 leading-relaxed">
          {renderInline(line)}
        </p>
      );
    }
  });

  // Flush remaining list/table
  flushList();
  flushTable();

  return <div className="space-y-1 text-sm">{blocks}</div>;
};

