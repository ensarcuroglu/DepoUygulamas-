const clampConfidence = (value) => {
    const number = Number(value);
    if (!Number.isFinite(number)) return null;
    return Math.max(0, Math.min(number, 1));
};

const guvenSeviyesi = (confidence) => {
    const score = clampConfidence(confidence);

    if (score === null) {
        return {
            label: 'Belirsiz',
            className: 'bg-slate-500/10 text-slate-600 ring-slate-500/20 dark:text-slate-400',
        };
    }

    if (score >= 0.85) {
        return {
            label: 'Yüksek',
            className: 'bg-emerald-500/10 text-emerald-600 ring-emerald-500/20 dark:text-emerald-400',
        };
    }

    if (score >= 0.5) {
        return {
            label: 'Orta',
            className: 'bg-amber-500/10 text-amber-600 ring-amber-500/20 dark:text-amber-400',
        };
    }

    return {
        label: 'Düşük',
        className: 'bg-rose-500/10 text-rose-600 ring-rose-500/20 dark:text-rose-400',
    };
};

export default function AlanGuvenRozeti({ confidence, className = '' }) {
    const score = clampConfidence(confidence);
    const level = guvenSeviyesi(score);
    const percent = score === null ? null : Math.round(score * 100);

    return (
        <span
            title={score === null ? 'Güven skoru yok' : `Güven skoru: %${percent}`}
            className={`inline-flex h-6 items-center rounded-full px-2 text-[11px] font-semibold ring-1 ring-inset ${level.className} ${className}`}
        >
            {level.label}{percent !== null ? ` %${percent}` : ''}
        </span>
    );
}
