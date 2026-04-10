import { createContext, useContext, useEffect, useState, useCallback } from 'react';

// eslint-disable-next-line react-refresh/only-export-components
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
        aciklama: 'Yeşil / Doğal',
        renkler: { primary: '#059669', secondary: '#064e3b', accent: '#22c55e' },
    },
];

// eslint-disable-next-line react-refresh/only-export-components
export const MODLAR = [
    { id: 'acik',   ad: 'Açık',              icon: 'sun' },
    { id: 'koyu',   ad: 'Koyu',              icon: 'moon' },
    { id: 'sistem', ad: 'Sistemle Eşleştir', icon: 'monitor' },
];

const LS_TEMA = 'depo_tema';
const LS_MOD  = 'depo_mod';
const VARSAYILAN_TEMA = 'kurumsal';
const VARSAYILAN_MOD = 'acik';

const ThemeContext = createContext(null);

function getSystemMod() {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
        return VARSAYILAN_MOD;
    }

    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'koyu' : 'acik';
}

function resolveMode(mod, systemMod) {
    return mod === 'sistem' ? systemMod : mod;
}

function readStorage(key, fallbackValue) {
    if (typeof window === 'undefined') {
        return fallbackValue;
    }

    try {
        return window.localStorage.getItem(key) || fallbackValue;
    } catch {
        return fallbackValue;
    }
}

function writeStorage(key, value) {
    if (typeof window === 'undefined') {
        return;
    }

    try {
        window.localStorage.setItem(key, value);
    } catch {
        // Storage failures should not block app startup or theme changes.
    }
}

function applyToDOM(tema, resolvedMod) {
    const html = document.documentElement;
    html.setAttribute('data-theme', tema);
    html.setAttribute('data-mode', resolvedMod);
}

export function ThemeProvider({ children }) {
    const [tema, setTemaState] = useState(
        () => readStorage(LS_TEMA, VARSAYILAN_TEMA)
    );
    const [mod, setModState] = useState(
        () => readStorage(LS_MOD, VARSAYILAN_MOD)
    );
    const [systemMod, setSystemMod] = useState(() => getSystemMod());
    const resolvedMod = resolveMode(mod, systemMod);

    // DOM'a yaz ve localStorage'ı güncelle
    useEffect(() => {
        applyToDOM(tema, resolvedMod);
        writeStorage(LS_TEMA, tema);
        writeStorage(LS_MOD, mod);
    }, [tema, mod, resolvedMod]);

    // Sistem modu aktifken OS değişimini dinle
    useEffect(() => {
        if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
            return undefined;
        }

        const mq = window.matchMedia('(prefers-color-scheme: dark)');
        const handler = (event) => {
            setSystemMod(event.matches ? 'koyu' : 'acik');
        };

        if (typeof mq.addEventListener === 'function') {
            mq.addEventListener('change', handler);
            return () => mq.removeEventListener('change', handler);
        }

        mq.addListener(handler);
        return () => mq.removeListener(handler);
    }, []);

    const setTema = useCallback((yeniTema) => {
        setTemaState(yeniTema);
    }, []);

    const setMod = useCallback((yeniMod) => {
        setModState(yeniMod);
    }, []);

    // Header butonu: acik ↔ koyu toggle (sistem modundayken override eder)
    const toggleMod = useCallback(() => {
        setModState(prev => {
            if (prev === 'acik') return 'koyu';
            if (prev === 'koyu') return 'acik';
            // sistem modundaysa: şu an ne resolve ediliyorsa tersine geç
            return resolvedMod === 'koyu' ? 'acik' : 'koyu';
        });
    }, [resolvedMod]);

    return (
        <ThemeContext.Provider value={{ tema, mod, resolvedMod, setTema, setMod, toggleMod }}>
            {children}
        </ThemeContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useTheme() {
    const ctx = useContext(ThemeContext);
    if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
    return ctx;
}
