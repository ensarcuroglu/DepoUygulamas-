export const queryKeys = {
    all: ['app'],
    auth: {
        all: ['auth'],
        currentUser: () => ['auth', 'currentUser'],
    },
    dashboard: {
        all: ['dashboard'],
        stats: () => ['dashboard', 'stats'],
        recentMovements: (params = {}) => ['dashboard', 'recentMovements', params],
    },
    urunler: {
        all: ['urunler'],
        lists: () => ['urunler', 'list'],
        list: (params = {}) => ['urunler', 'list', params],
        detail: (id) => ['urunler', 'detail', id],
        byBarkod: (barkod) => ['urunler', 'barkod', barkod],
        critical: () => ['urunler', 'critical'],
        stockDetail: (urunId) => ['urunler', 'stockDetail', urunId],
    },
    kategoriler: {
        all: ['kategoriler'],
        list: () => ['kategoriler', 'list'],
    },
    markalar: {
        all: ['markalar'],
        list: () => ['markalar', 'list'],
    },
};
