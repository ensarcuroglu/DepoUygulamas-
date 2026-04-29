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
    depolar: {
        all: ['depolar'],
        lists: () => ['depolar', 'list'],
        list: (params = {}) => ['depolar', 'list', params],
    },
    raflar: {
        all: ['raflar'],
        lists: () => ['raflar', 'list'],
        list: (params = {}) => ['raflar', 'list', params],
    },
    kullanicilar: {
        all: ['kullanicilar'],
        list: () => ['kullanicilar', 'list'],
    },
    lotlar: {
        all: ['lotlar'],
        lists: () => ['lotlar', 'list'],
        list: (params = {}) => ['lotlar', 'list', params],
        sktYaklasan: (gun = 30) => ['lotlar', 'sktYaklasan', gun],
    },
    tedarikciler: {
        all: ['tedarikciler'],
        lists: () => ['tedarikciler', 'list'],
        list: (params = {}) => ['tedarikciler', 'list', params],
    },
    siparisler: {
        all: ['siparisler'],
        lists: () => ['siparisler', 'list'],
        list: (params = {}) => ['siparisler', 'list', params],
    },
    sevkiyatPlanlari: {
        all: ['sevkiyatPlanlari'],
        lists: () => ['sevkiyatPlanlari', 'list'],
        list: (params = {}) => ['sevkiyatPlanlari', 'list', params],
    },
    irsaliyeler: {
        all: ['irsaliyeler'],
        lists: () => ['irsaliyeler', 'list'],
        list: (params = {}) => ['irsaliyeler', 'list', params],
    },
    malKabulIrsaliyeleri: {
        all: ['malKabulIrsaliyeleri'],
        lists: () => ['malKabulIrsaliyeleri', 'list'],
        list: (params = {}) => ['malKabulIrsaliyeleri', 'list', params],
    },
    destek: {
        all: ['destek'],
        lists: () => ['destek', 'list'],
        list: (params = {}) => ['destek', 'list', params],
    },
    uretimPaletleri: {
        all: ['uretimPaletleri'],
        lists: () => ['uretimPaletleri', 'list'],
        list: (params = {}) => ['uretimPaletleri', 'list', params],
    },
    yerlestirme: {
        all: ['yerlestirme'],
        oneri: (paletId) => ['yerlestirme', 'oneri', paletId],
    },
};
