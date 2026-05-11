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
            className: 'bg-slate-100 text-slate-600 ring-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-700',
        };
    }

    if (score >= 0.85) {
        return {
            label: 'Yüksek',
            className: 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:ring-emerald-800',
        };
    }

    if (score >= 0.5) {
        return {
            label: 'Orta',
            className: 'bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:ring-amber-800',
        };
    }

    return {
        label: 'Düşük',
        className: 'bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:ring-rose-800',
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
