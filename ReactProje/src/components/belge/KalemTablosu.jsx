import { useMemo } from 'react';
import { Plus, Search, Trash2 } from 'lucide-react';
import AlanGuvenRozeti from './AlanGuvenRozeti';

const emptyKalem = () => ({
    urun_id: '',
    urun_kodu: '',
    ad: '',
    miktar: '',
    birim: 'ADET',
    palet_no: '',
    lot_no: '',
    uretim_tarihi: '',
    son_kullanma_tarihi: '',
    confidence: {},
});

const normalize = (value) =>
    String(value ?? '').trim().toLocaleLowerCase('tr-TR');

const productCode = (urun) =>
    urun?.barkod || urun?.ean || urun?.urun_kodu || urun?.kod || '';

const productName = (urun) =>
    urun?.isim || urun?.ad || urun?.urun_adi || '';

const productLabel = (urun) => {
    const name = productName(urun);
    const code = productCode(urun);
    return code ? `${name} | ${code}` : name;
};

const findProduct = (value, urunler) => {
    const needle = normalize(value);
    if (!needle) return null;

    return urunler.find((urun) => {
        const candidates = [
            productLabel(urun),
            productName(urun),
            productCode(urun),
            urun?.barkod,
            urun?.ean,
            urun?.kod,
            urun?.urun_kodu,
        ].map(normalize);
        return candidates.includes(needle);
    }) ?? null;
};

const FieldLabel = ({ children, confidence }) => (
    <div className="mb-1.5 flex min-h-6 items-center justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            {children}
        </span>
        {confidence !== undefined && <AlanGuvenRozeti confidence={confidence} />}
    </div>
);

const inputClass = 'h-11 w-full rounded-xl border border-slate-200/60 bg-slate-50/50 px-4 text-sm text-slate-800 outline-none transition-all duration-300 focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-500/10 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-800/60 dark:bg-slate-950/50 dark:text-slate-100 dark:focus:border-sky-500 dark:focus:bg-slate-900';

export default function KalemTablosu({
    kalemler,
    onChange,
    urunler = [],
    readonly = false,
}) {
    const rows = Array.isArray(kalemler) ? kalemler : [];
    const urunOptions = useMemo(() => urunler.map((urun) => ({
        id: urun.id,
        label: productLabel(urun),
    })).filter((option) => option.label), [urunler]);

    const updateRow = (index, patch) => {
        if (readonly) return;
        const next = rows.map((row, rowIndex) =>
            rowIndex === index ? { ...row, ...patch } : row
        );
        onChange(next);
    };

    const handleProductInput = (index, value) => {
        const product = findProduct(value, urunler);
        if (!product) {
            updateRow(index, { ad: value, urun_id: '' });
            return;
        }

        updateRow(index, {
            urun_id: product.id || '',
            urun_kodu: productCode(product),
            ad: productName(product),
        });
    };

    const addRow = () => {
        if (!readonly) onChange([...rows, emptyKalem()]);
    };

    const removeRow = (index) => {
        if (readonly) return;
        onChange(rows.filter((_, rowIndex) => rowIndex !== index));
    };

    return (
        <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Kalemler</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{rows.length} satır</p>
                </div>
                <button
                    type="button"
                    onClick={addRow}
                    disabled={readonly}
                    className="inline-flex h-11 cursor-pointer items-center gap-2 rounded-xl bg-slate-900 px-4 text-sm font-semibold text-white transition-all duration-300 hover:bg-slate-800 hover:shadow-lg hover:shadow-slate-900/20 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 dark:bg-slate-100 dark:text-slate-950 dark:hover:bg-white dark:hover:shadow-white/20"
                >
                    <Plus className="h-4 w-4" />
                    Satır ekle
                </button>
            </div>

            {rows.length === 0 ? (
                <div className="rounded-xl border-2 border-dashed border-slate-300/80 bg-slate-50/50 px-4 py-10 text-center text-sm text-slate-500 transition-colors dark:border-slate-700/80 dark:bg-slate-900/30 dark:text-slate-400">
                    Taslakta kalem bulunamadı. Onay için en az bir kalem ekleyin.
                </div>
            ) : (
                <div className="space-y-3">
                    {rows.map((row, index) => {
                        const datalistId = `urun-list-${index}`;
                        return (
                            <div
                                key={row.local_id || index}
                                className="rounded-2xl border border-slate-200/60 bg-white/60 p-4 shadow-sm backdrop-blur-md transition-all hover:shadow-md dark:border-slate-800/60 dark:bg-slate-900/60"
                            >
                                <div className="mb-3 flex items-center justify-between gap-3">
                                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
                                        <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-100/80 text-xs text-slate-600 shadow-sm dark:bg-slate-800/80 dark:text-slate-300">
                                            {index + 1}
                                        </span>
                                        Satır
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => removeRow(index)}
                                        disabled={readonly || rows.length === 1}
                                        title="Satırı sil"
                                        className="inline-flex h-10 w-10 cursor-pointer items-center justify-center rounded-full text-slate-500 transition-colors hover:bg-rose-50 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-50 dark:text-slate-400 dark:hover:bg-rose-950/40 dark:hover:text-rose-400"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </button>
                                </div>

                                <div className="grid gap-3 lg:grid-cols-[minmax(220px,1.6fr)_120px_120px_120px_140px_140px]">
                                    <div className="lg:col-span-2">
                                        <FieldLabel confidence={row.confidence?.ad}>Ürün</FieldLabel>
                                        <div className="relative">
                                            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                                            <input
                                                list={datalistId}
                                                value={row.ad || ''}
                                                onChange={(event) => handleProductInput(index, event.target.value)}
                                                disabled={readonly}
                                                className={`${inputClass} pl-9`}
                                                placeholder="Ürün adı veya barkod"
                                            />
                                            <datalist id={datalistId}>
                                                {urunOptions.map((option) => (
                                                    <option key={`${option.id}-${option.label}`} value={option.label} />
                                                ))}
                                            </datalist>
                                        </div>
                                    </div>

                                    <div>
                                        <FieldLabel confidence={row.confidence?.urun_kodu}>Kod</FieldLabel>
                                        <input
                                            value={row.urun_kodu || ''}
                                            onChange={(event) => updateRow(index, { urun_kodu: event.target.value })}
                                            disabled={readonly}
                                            className={inputClass}
                                            placeholder="Barkod/EAN"
                                        />
                                    </div>

                                    <div>
                                        <FieldLabel confidence={row.confidence?.miktar}>Miktar</FieldLabel>
                                        <input
                                            type="number"
                                            min="0"
                                            step="1"
                                            value={row.miktar ?? ''}
                                            onChange={(event) => updateRow(index, { miktar: event.target.value })}
                                            disabled={readonly}
                                            className={inputClass}
                                        />
                                    </div>

                                    <div>
                                        <FieldLabel confidence={row.confidence?.birim}>Birim</FieldLabel>
                                        <input
                                            value={row.birim || ''}
                                            onChange={(event) => updateRow(index, { birim: event.target.value })}
                                            disabled={readonly}
                                            className={inputClass}
                                            placeholder="ADET"
                                        />
                                    </div>

                                    <div>
                                        <FieldLabel>Palet</FieldLabel>
                                        <input
                                            value={row.palet_no || ''}
                                            onChange={(event) => updateRow(index, { palet_no: event.target.value })}
                                            disabled={readonly}
                                            className={inputClass}
                                            placeholder="Otomatik"
                                        />
                                    </div>
                                </div>

                                <div className="mt-3 grid gap-3 md:grid-cols-3">
                                    <div>
                                        <FieldLabel confidence={row.confidence?.lot_no}>LOT</FieldLabel>
                                        <input
                                            value={row.lot_no || ''}
                                            onChange={(event) => updateRow(index, { lot_no: event.target.value })}
                                            disabled={readonly}
                                            className={inputClass}
                                        />
                                    </div>
                                    <div>
                                        <FieldLabel confidence={row.confidence?.uretim_tarihi}>Üretim tarihi</FieldLabel>
                                        <input
                                            type="date"
                                            value={row.uretim_tarihi || ''}
                                            onChange={(event) => updateRow(index, { uretim_tarihi: event.target.value })}
                                            disabled={readonly}
                                            className={inputClass}
                                        />
                                    </div>
                                    <div>
                                        <FieldLabel confidence={row.confidence?.son_kullanma_tarihi}>SKT</FieldLabel>
                                        <input
                                            type="date"
                                            value={row.son_kullanma_tarihi || ''}
                                            onChange={(event) => updateRow(index, { son_kullanma_tarihi: event.target.value })}
                                            disabled={readonly}
                                            className={inputClass}
                                        />
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
