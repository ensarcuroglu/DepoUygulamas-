function renderInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={index}
          className="rounded bg-zinc-100 px-1 py-0.5 font-['JetBrains_Mono'] text-[0.88em] text-zinc-800 dark:bg-white/10 dark:text-zinc-200"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return <span key={index}>{part}</span>;
  });
}

export default function MarkdownContent({ content }) {
  const blocks = String(content ?? '').split(/\n{2,}/);

  return (
    <div className="space-y-2">
      {blocks.map((block, blockIndex) => {
        const lines = block.split('\n').filter((line) => line.trim().length > 0);
        const isList = lines.every((line) => line.trimStart().startsWith('- '));

        if (isList) {
          return (
            <ul key={blockIndex} className="list-disc space-y-1 pl-5">
              {lines.map((line, lineIndex) => (
                <li key={lineIndex}>{renderInline(line.trimStart().slice(2))}</li>
              ))}
            </ul>
          );
        }

        return (
          <p key={blockIndex} className="whitespace-pre-wrap">
            {renderInline(lines.join('\n'))}
          </p>
        );
      })}
    </div>
  );
}
