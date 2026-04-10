export const DEFAULT_TEMA = 'kurumsal';
export const DEFAULT_MOD = 'acik';

export const TEMALAR = [
    {
        id: 'kurumsal',
        ad: 'Kurumsal',
        aciklama: 'Mavi / Lacivert',
        renkler: { primary: '#2563eb', secondary: '#1e3a5f', accent: '#f59e0b' },
    },
    {
        id: 'ocean',
        ad: 'Ocean',
        aciklama: 'Teal / Cyan',
        renkler: { primary: '#0891b2', secondary: '#164e63', accent: '#14b8a6' },
    },
    {
        id: 'indigo',
        ad: 'Indigo',
        aciklama: 'Indigo / Violet',
        renkler: { primary: '#4f46e5', secondary: '#312e81', accent: '#a855f7' },
    },
    {
        id: 'emerald',
        ad: 'Emerald',
        aciklama: 'Yesil / Dogal',
        renkler: { primary: '#059669', secondary: '#064e3b', accent: '#22c55e' },
    },
];

export const MODLAR = [
    { id: 'acik', ad: 'Acik', icon: 'sun' },
    { id: 'koyu', ad: 'Koyu', icon: 'moon' },
    { id: 'sistem', ad: 'Sistemle Eslestir', icon: 'monitor' },
];
