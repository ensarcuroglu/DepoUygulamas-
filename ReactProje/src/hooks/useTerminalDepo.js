/**
 * Terminal için seçili depo_id'yi localStorage'da saklar.
 * İlk kullanımda depo seçimi zorunlu kılınır.
 */
import { useState } from 'react';

const KEY = 'terminal_depo_id';

export function useTerminalDepo() {
    const [depoId, setDepoIdState] = useState(() => {
        const saved = localStorage.getItem(KEY);
        return saved ? parseInt(saved, 10) : null;
    });

    const setDepoId = (id) => {
        if (id) {
            localStorage.setItem(KEY, String(id));
        } else {
            localStorage.removeItem(KEY);
        }
        setDepoIdState(id ? parseInt(id, 10) : null);
    };

    return { depoId, setDepoId };
}
