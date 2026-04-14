import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import {
    ShieldAlert, Search, Filter, Clock, Activity,
    Trash2, PlusCircle, Edit3, Eye, X,
    UserCircle, Server, RefreshCw, Download, Code2, SlidersHorizontal, ChevronRight
} from 'lucide-react';
import { getSistemLoglari } from '../services/api';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import * as XLSX from 'xlsx';
import { useVirtualizer } from '@tanstack/react-virtual';
import { motion, AnimatePresence } from 'framer-motion';

const HAS_TZ_INFO_REGEX = /([zZ]|[+-]\d{2}:\d{2})$/;
const ISO_DATE_REGEX = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/;

const parseLogDate = (value) => {
    if (!value) return null;
    if (typeof value === 'string' && !HAS_TZ_INFO_REGEX.test(value)) {
        return new Date(`${value}Z`);
    }
    return new Date(value);
};

// ─── Alan Etiketi Haritası ────────────────────────────────────────────────────
const ALAN_ETIKETLERI = {
    id: 'ID', ad: 'Ad', ad_soyad: 'Ad Soyad', email: 'E-posta',
    telefon: 'Telefon', adres: 'Adres', aciklama: 'Açıklama',
    miktar: 'Miktar', fiyat: 'Fiyat', stok_miktari: 'Stok Miktarı',
    barkod: 'Barkod', aktif: 'Aktif', durum: 'Durum', tarih: 'Tarih',
    olusturma_tarihi: 'Oluşturma Tarihi', guncelleme_tarihi: 'Güncelleme Tarihi',
    kategori_id: 'Kategori ID', marka_id: 'Marka ID', depo_id: 'Depo ID',
    raf_id: 'Raf ID', urun_id: 'Ürün ID', lot_id: 'Lot ID',
    palet_id: 'Palet ID', tedarikci_id: 'Tedarikçi ID', kullanici_id: 'Kullanıcı ID',
    rol: 'Rol', isim: 'İsim', soyisim: 'Soyisim', urun_adi: 'Ürün Adı',
    urun_kodu: 'Ürün Kodu', lot_kodu: 'Lot Kodu', palet_kodu: 'Palet Kodu',
    koli_adedi: 'Koli Adedi', birim: 'Birim', notlar: 'Notlar', not: 'Not',
    vergi_no: 'Vergi No', sehir: 'Şehir', ulke: 'Ülke', kapasite: 'Kapasite',
    konum: 'Konum', tip: 'Tip', islem_tipi: 'İşlem Tipi', modul: 'Modül',
    detay: 'Detay', son_giris: 'Son Giriş', kargo_takip_no: 'Kargo Takip No',
    sevkiyat_tarihi: 'Sevkiyat Tarihi', teslim_tarihi: 'Teslim Tarihi',
    zon_id: 'Zon ID', siparis_no: 'Sipariş No', irsaliye_no: 'İrsaliye No',
    kategori_adi: 'Kategori Adı', marka_adi: 'Marka Adı', depo_adi: 'Depo Adı',
    min_stok: 'Min. Stok', max_stok: 'Maks. Stok', birim_fiyat: 'Birim Fiyat',
    kdv_orani: 'KDV Oranı', agirlik: 'Ağırlık', hacim: 'Hacim',
    sifre_hash: 'Şifre (Hash)',
};

// ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────
const duzlestir = (obj, prefix = '', derinlik = 0) => {
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) {
        return prefix ? { [prefix]: obj } : {};
    }
    return Object.entries(obj).reduce((acc, [key, val]) => {
        const yeniAnahtar = prefix ? `${prefix}.${key}` : key;
        if (val && typeof val === 'object' && !Array.isArray(val) && derinlik < 2) {
            Object.assign(acc, duzlestir(val, yeniAnahtar, derinlik + 1));
        } else {
            acc[yeniAnahtar] = val;
        }
        return acc;
    }, {});
};

const degerBicimlendir = (val) => {
    if (val === null || val === undefined) return '—';
    if (typeof val === 'boolean') return val ? 'Evet' : 'Hayır';
    if (Array.isArray(val)) return `[${val.length} öğe]`;
    if (typeof val === 'object') return JSON.stringify(val);
    if (typeof val === 'string' && ISO_DATE_REGEX.test(val)) {
        const d = parseLogDate(val);
        if (d && !isNaN(d)) return d.toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });
    }
    return String(val);
};

const etiketAl = (anahtar) => {
    if (ALAN_ETIKETLERI[anahtar]) return ALAN_ETIKETLERI[anahtar];
    const parcalar = anahtar.split('.');
    if (parcalar.length > 1) {
        const ust = ALAN_ETIKETLERI[parcalar[0]] || parcalar[0];
        const alt = ALAN_ETIKETLERI[parcalar[parcalar.length - 1]] || parcalar[parcalar.length - 1];
        return `${ust} › ${alt}`;
    }
    return anahtar.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

// ─── Custom Hook: useDebounce ─────────────────────────────────────────────────
function useDebounce(value, delay) {
    const [debouncedValue, setDebouncedValue] = useState(value);
    useEffect(() => {
        const handler = setTimeout(() => { setDebouncedValue(value); }, delay);
        return () => { clearTimeout(handler); };
    }, [value, delay]);
    return debouncedValue;
}

// ─── Minimal JsonTablo ────────────────────────────────────────────────────────
const JsonTablo = ({ data, baslik, renk = 'slate' }) => {
    if (!data) return null;
    const duzData = duzlestir(data);
    const entries = Object.entries(duzData);
    if (entries.length === 0) return <p className="text-sm text-slate-400 italic py-2">Veri bulunamadı.</p>;

    const r = renk === 'rose' ? 'text-rose-600 bg-rose-50' : 'text-emerald-600 bg-emerald-50';

    return (
        <div className="space-y-3">
            {baslik && (
                <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md ${r}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-current opacity-75" />
                    <span className="text-[11px] font-bold uppercase tracking-widest">{baslik}</span>
                </div>
            )}
            <div className="bg-white border border-slate-100 rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-[13px]">
                    <tbody>
                        {entries.map(([key, val], i) => (
                            <tr key={key} className={`${i !== 0 ? 'border-t border-slate-50' : ''} hover:bg-slate-50/50 transition-colors`}>
                                <td className="px-4 py-3 font-medium text-slate-500 w-1/3 whitespace-nowrap bg-slate-50/30">
                                    {etiketAl(key)}
                                </td>
                                <td className="px-4 py-3 font-medium text-slate-900 break-all">
                                    {degerBicimlendir(val)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

// ─── Minimal DiffTablo ────────────────────────────────────────────────────────
const DURUM_SIRASI = { degisti: 0, eklendi: 1, silindi: 2, ayni: 3 };

const DiffTablo = ({ eskiVeri, yeniVeri }) => {
    const duzEski = useMemo(() => duzlestir(eskiVeri ?? {}), [eskiVeri]);
    const duzYeni = useMemo(() => duzlestir(yeniVeri ?? {}), [yeniVeri]);

    const satirlar = useMemo(() => {
        const tumAnahtarlar = [...new Set([...Object.keys(duzEski), ...Object.keys(duzYeni)])];
        return tumAnahtarlar
            .map(key => {
                const eskiMevcut = key in duzEski;
                const yeniMevcut = key in duzYeni;
                let durum;
                if (!eskiMevcut) durum = 'eklendi';
                else if (!yeniMevcut) durum = 'silindi';
                else if (JSON.stringify(duzEski[key]) !== JSON.stringify(duzYeni[key])) durum = 'degisti';
                else durum = 'ayni';
                return { key, eskiDeger: duzEski[key], yeniDeger: duzYeni[key], durum };
            })
            .sort((a, b) => DURUM_SIRASI[a.durum] - DURUM_SIRASI[b.durum]);
    }, [duzEski, duzYeni]);

    return (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <div className="grid grid-cols-[30%_35%_35%] bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                <div className="px-4 py-3">Alan Adı</div>
                <div className="px-4 py-3 border-l border-slate-200">Eski Değer</div>
                <div className="px-4 py-3 border-l border-slate-200">Yeni Değer</div>
            </div>
            <div className="divide-y divide-slate-100">
                {satirlar.map(({ key, eskiDeger, yeniDeger, durum }) => (
                    <div key={key} className={`grid grid-cols-[30%_35%_35%] text-[13px] hover:bg-slate-50/50 transition-colors
                        ${durum === 'degisti' ? 'bg-amber-50/30' : durum === 'eklendi' ? 'bg-emerald-50/30' : durum === 'silindi' ? 'bg-rose-50/30' : ''}
                    `}>
                        <div className="px-4 py-3 font-medium text-slate-600 flex items-center gap-2">
                            {durum === 'degisti' && <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />}
                            {durum === 'eklendi' && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
                            {durum === 'silindi' && <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />}
                            <span className="truncate">{etiketAl(key)}</span>
                        </div>
                        <div className={`px-4 py-3 border-l border-slate-100 break-all ${durum === 'silindi' ? 'text-rose-600 line-through opacity-70' : durum === 'degisti' ? 'text-rose-600 line-through' : 'text-slate-700'}`}>
                            {durum === 'eklendi' ? <span className="text-slate-300">—</span> : degerBicimlendir(eskiDeger)}
                        </div>
                        <div className={`px-4 py-3 border-l border-slate-100 break-all ${durum === 'eklendi' || durum === 'degisti' ? 'text-emerald-600 font-medium' : 'text-slate-700'}`}>
                            {durum === 'silindi' ? <span className="text-slate-300">—</span> : degerBicimlendir(yeniDeger)}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

// ─── İkon ve Renk Haritası ────────────────────────────────────────────────────
const ActionStyles = {
    CREATE:  { icon: PlusCircle,  color: 'emerald', bg: 'bg-emerald-50',  text: 'text-emerald-600', label: 'Ekleme' },
    UPDATE:  { icon: Edit3,       color: 'blue',    bg: 'bg-blue-50',     text: 'text-blue-600',    label: 'Güncelleme' },
    DELETE:  { icon: Trash2,      color: 'rose',    bg: 'bg-rose-50',     text: 'text-rose-600',    label: 'Silme' },
    LOGIN:   { icon: UserCircle,  color: 'indigo',  bg: 'bg-indigo-50',   text: 'text-indigo-600',  label: 'Giriş' },
    DEFAULT: { icon: Activity,    color: 'slate',   bg: 'bg-slate-100',   text: 'text-slate-600',   label: 'Sistem İşlemi' },
};

// ─── Ana Sayfa Bileşeni ───────────────────────────────────────────────────────
export default function SistemLoglariPage() {
    const [loglar, setLoglar] = useState([]);
    const { loading, run } = useAsync(true);

    const [aramaTaramasi, setAramaTaramasi] = useState('');
    const debouncedArama = useDebounce(aramaTaramasi, 300); // 300ms Debounce Eklendi

    const [seciliModul, setSeciliModul] = useState('');
    const [seciliTip, setSeciliTip] = useState('');
    const [baslangicTarihi, setBaslangicTarihi] = useState('');
    const [bitisTarihi, setBitisTarihi] = useState('');

    const [seciliLog, setSeciliLog] = useState(null);
    const [hamJsonGoster, setHamJsonGoster] = useState(false);
    
    const [mobilFiltreAcik, setMobilFiltreAcik] = useState(false);
    const parentRef = useRef(null);

    const fetchData = useCallback(async () => {
        try {
            const res = await run(() => getSistemLoglari(200));
            setLoglar(res.data);
        } catch {
            toast.error('Loglar yüklenirken hata oluştu');
        }
    }, [run]);

    useEffect(() => {
        const id = setTimeout(() => { void fetchData(); }, 0);
        return () => clearTimeout(id);
    }, [fetchData]);

    const moduller = useMemo(() => [...new Set(loglar.map(l => l.modul))].filter(Boolean).sort(), [loglar]);
    const islemTipleri = useMemo(() => [...new Set(loglar.map(l => l.islem_tipi))].filter(Boolean).sort(), [loglar]);

    const filteredLoglar = useMemo(() => {
        return loglar.filter(log => {
            const aramaMetni = debouncedArama.toLowerCase(); // Debounce edilmiş değer kullanılıyor
            const matchesSearch =
                (log.detay && log.detay.toLowerCase().includes(aramaMetni)) ||
                (log.kullanici_ad_soyad && log.kullanici_ad_soyad.toLowerCase().includes(aramaMetni)) ||
                (log.modul && log.modul.toLowerCase().includes(aramaMetni));
            const matchesModul = seciliModul ? log.modul === seciliModul : true;
            const matchesTip   = seciliTip   ? log.islem_tipi === seciliTip : true;

            let matchesTarih = true;
            if (baslangicTarihi || bitisTarihi) {
                const parsedLogDate = parseLogDate(log.tarih);
                if (!parsedLogDate || Number.isNaN(parsedLogDate.getTime())) return false;
                const logAman   = parsedLogDate.getTime();
                const starTime  = baslangicTarihi ? new Date(baslangicTarihi).getTime() : 0;
                const endTime   = bitisTarihi ? new Date(bitisTarihi).getTime() + 86400000 : Infinity;
                matchesTarih    = logAman >= starTime && logAman < endTime;
            }
            return matchesSearch && matchesModul && matchesTip && matchesTarih;
        });
    }, [loglar, debouncedArama, seciliModul, seciliTip, baslangicTarihi, bitisTarihi]);

    const rowVirtualizer = useVirtualizer({
        count: filteredLoglar.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 90, 
        overscan: 5, 
    });

    const exportToExcel = () => {
        if (filteredLoglar.length === 0) { toast.error("İndirilecek veri yok."); return; }
        const excelData = filteredLoglar.map(log => ({
            "Tarih":        parseLogDate(log.tarih)?.toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' }) || '-',
            "İşlem Tipi":   ActionStyles[log.islem_tipi]?.label || log.islem_tipi,
            "Modül":        log.modul,
            "Kullanıcı":    log.kullanici_ad_soyad || 'Sistem',
            "İşlem Detayı": log.detay,
            "Eski Veri":    log.eski_veri ? JSON.stringify(log.eski_veri) : '-',
            "Yeni Veri":    log.yeni_veri ? JSON.stringify(log.yeni_veri) : '-',
        }));
        const ws = XLSX.utils.json_to_sheet(excelData);
        ws['!cols'] = [{ wch: 20 }, { wch: 15 }, { wch: 20 }, { wch: 20 }, { wch: 50 }, { wch: 30 }, { wch: 30 }];
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Sistem Logları");
        XLSX.writeFile(wb, `Sistem_Loglari_${new Date().toLocaleDateString('tr-TR')}.xlsx`);
        toast.success("Excel başarıyla indirildi.");
    };

    const clearFilters = () => {
        setAramaTaramasi(''); setSeciliModul(''); setSeciliTip(''); setBaslangicTarihi(''); setBitisTarihi('');
    };
    const hasActiveFilters = seciliModul || seciliTip || baslangicTarihi || bitisTarihi;

    return (
        <div className="h-screen flex flex-col bg-[#FAFAFA] font-sans">
            
            {/* ── HEADER ── */}
            <div className="bg-white border-b border-slate-200 flex-shrink-0 z-10 px-4 sm:px-6 md:px-8 py-4 sm:py-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 md:w-12 md:h-12 rounded-xl bg-slate-900 flex items-center justify-center shadow-md shadow-slate-900/10">
                        <ShieldAlert className="w-5 h-5 md:w-6 md:h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">Sistem Logları</h1>
                        <p className="text-xs md:text-sm text-slate-500 font-medium">Platformdaki tüm izleri ve hareketleri inceleyin.</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <button onClick={fetchData} className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-white border border-slate-200 text-slate-700 font-semibold hover:bg-slate-50 hover:border-slate-300 transition-all text-sm">
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        <span className="hidden sm:inline">Yenile</span>
                    </button>
                    <button onClick={exportToExcel} className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-slate-900 text-white font-semibold hover:bg-slate-800 transition-all shadow-sm text-sm">
                        <Download className="w-4 h-4" />
                        <span>Dışa Aktar</span>
                    </button>
                </div>
            </div>

            {/* ── DESKTOP FİLTRE BARI ── */}
            <div className="hidden md:flex items-center gap-3 px-8 py-3 bg-white border-b border-slate-100 flex-shrink-0">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        placeholder="İşlem veya kullanıcı ara..."
                        value={aramaTaramasi}
                        onChange={(e) => setAramaTaramasi(e.target.value)}
                        className="w-full h-10 pl-9 pr-4 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:bg-white transition-all"
                    />
                </div>
                <div className="w-px h-6 bg-slate-200" />
                <select value={seciliModul} onChange={(e) => setSeciliModul(e.target.value)} className="h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-900/10 cursor-pointer min-w-[140px]">
                    <option value="">Tüm Modüller</option>
                    {moduller.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
                <select value={seciliTip} onChange={(e) => setSeciliTip(e.target.value)} className="h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-900/10 cursor-pointer min-w-[140px]">
                    <option value="">Tüm İşlemler</option>
                    {islemTipleri.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
                <div className="flex items-center gap-2">
                    <input type="date" value={baslangicTarihi} onChange={(e) => setBaslangicTarihi(e.target.value)} className="h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm font-medium text-slate-700 focus:outline-none" />
                    <span className="text-slate-400">-</span>
                    <input type="date" value={bitisTarihi} onChange={(e) => setBitisTarihi(e.target.value)} className="h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm font-medium text-slate-700 focus:outline-none" />
                </div>
                {hasActiveFilters && (
                    <button onClick={clearFilters} className="ml-auto text-xs font-semibold text-slate-500 hover:text-slate-800 underline underline-offset-2">Temizle</button>
                )}
            </div>

            {/* ── MOBILE SEARCH & FILTER TOGGLE ── */}
            <div className="md:hidden flex items-center gap-2 px-4 py-3 bg-white border-b border-slate-100 flex-shrink-0">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Ara..."
                        value={aramaTaramasi}
                        onChange={(e) => setAramaTaramasi(e.target.value)}
                        className="w-full h-10 pl-9 pr-4 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-none"
                    />
                </div>
                <button 
                    onClick={() => setMobilFiltreAcik(true)}
                    className={`h-10 px-3 flex items-center justify-center rounded-lg border transition-colors ${hasActiveFilters ? 'bg-slate-900 text-white border-slate-900' : 'bg-slate-50 text-slate-600 border-slate-200'}`}
                >
                    <SlidersHorizontal className="w-4 h-4" />
                </button>
            </div>

            {/* ── İÇERİK ALANI (Virtual List - min-h-0 Eklendi) ── */}
            <div className="flex-1 overflow-hidden relative min-h-0">
                {loading ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
                        <RefreshCw className="w-8 h-8 text-slate-300 animate-spin" />
                        <span className="text-sm font-medium text-slate-500">Loglar yükleniyor...</span>
                    </div>
                ) : filteredLoglar.length === 0 ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
                        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                            <Search className="w-6 h-6 text-slate-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-800 mb-1">Kayıt Bulunamadı</h3>
                        <p className="text-sm text-slate-500 max-w-sm">Filtrelerinize uygun herhangi bir sistem hareketi bulunmuyor.</p>
                        {hasActiveFilters && (
                            <button onClick={clearFilters} className="mt-4 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50">Filtreleri Temizle</button>
                        )}
                    </div>
                ) : (
                    <div ref={parentRef} className="h-full w-full overflow-y-auto overflow-x-hidden px-4 sm:px-6 md:px-8 py-4">
                        <div
                            style={{
                                height: `${rowVirtualizer.getTotalSize()}px`,
                                width: '100%',
                                position: 'relative',
                            }}
                        >
                            {rowVirtualizer.getVirtualItems().map((virtualItem) => {
                                const log = filteredLoglar[virtualItem.index];
                                const styleInfo = ActionStyles[log.islem_tipi] ?? ActionStyles.DEFAULT;
                                const Icon = styleInfo.icon;
                                const hasDiff = (log.eski_veri && Object.keys(log.eski_veri).length > 0) || (log.yeni_veri && Object.keys(log.yeni_veri).length > 0);

                                return (
                                    <div
                                        key={virtualItem.key}
                                        ref={rowVirtualizer.measureElement}
                                        data-index={virtualItem.index}
                                        style={{
                                            position: 'absolute',
                                            top: 0,
                                            left: 0,
                                            width: '100%',
                                            transform: `translateY(${virtualItem.start}px)`,
                                        }}
                                        className="py-1.5"
                                    >
                                        <div 
                                            onClick={() => hasDiff && setSeciliLog(log)}
                                            className={`group flex items-start gap-4 p-4 bg-white rounded-xl border border-slate-200 transition-all duration-200
                                                ${hasDiff ? 'cursor-pointer hover:border-slate-300 hover:shadow-sm' : ''}
                                            `}
                                        >
                                            <div className={`w-10 h-10 rounded-lg ${styleInfo.bg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                                                <Icon className={`w-5 h-5 ${styleInfo.text}`} />
                                            </div>
                                            
                                            <div className="flex-1 min-w-0">
                                                <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs font-semibold text-slate-900">{log.modul}</span>
                                                        <span className="w-1 h-1 rounded-full bg-slate-300" />
                                                        <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${styleInfo.bg} ${styleInfo.text}`}>
                                                            {styleInfo.label}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-1.5 text-slate-400">
                                                        <Clock className="w-3.5 h-3.5" />
                                                        <span className="text-[11px] font-medium whitespace-nowrap">
                                                            {parseLogDate(log.tarih)?.toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Istanbul' }) || '-'}
                                                        </span>
                                                    </div>
                                                </div>
                                                
                                                <p className="text-sm font-medium text-slate-700 leading-snug line-clamp-2 pr-4">{log.detay}</p>
                                                
                                                <div className="mt-2.5 flex items-center gap-2">
                                                    <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 rounded text-xs font-medium text-slate-600 border border-slate-100">
                                                        <UserCircle className="w-3.5 h-3.5 text-slate-400" />
                                                        <span className="truncate max-w-[120px] sm:max-w-xs">{log.kullanici_ad_soyad || 'Sistem'}</span>
                                                    </div>
                                                </div>
                                            </div>

                                            {hasDiff && (
                                                <div className="hidden sm:flex self-center w-8 h-8 items-center justify-center rounded-full bg-white border border-slate-200 text-slate-400 group-hover:bg-slate-50 group-hover:text-slate-900 group-hover:border-slate-300 transition-all flex-shrink-0">
                                                    <ChevronRight className="w-4 h-4" />
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>

            {/* ── MOBILE FILTER BOTTOM SHEET (Key propları eklendi) ── */}
            <AnimatePresence>
                {mobilFiltreAcik && (
                    <>
                        <motion.div
                            key="filter-backdrop"
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[100] md:hidden"
                            onClick={() => setMobilFiltreAcik(false)}
                        />
                        <motion.div
                            key="filter-sheet"
                            initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }} transition={{ type: "spring", bounce: 0, duration: 0.4 }}
                            className="fixed bottom-0 left-0 right-0 bg-white rounded-t-3xl z-[101] p-5 pb-8 flex flex-col gap-4 md:hidden border-t border-slate-200 shadow-2xl"
                        >
                            <div className="w-12 h-1.5 bg-slate-200 rounded-full mx-auto mb-2" />
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="text-lg font-bold text-slate-900">Filtreler</h3>
                                <button onClick={() => setMobilFiltreAcik(false)} className="w-8 h-8 flex items-center justify-center bg-slate-100 rounded-full text-slate-600"><X className="w-4 h-4" /></button>
                            </div>
                            
                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-semibold text-slate-500 uppercase mb-1.5 block">Modül</label>
                                    <select value={seciliModul} onChange={(e) => setSeciliModul(e.target.value)} className="w-full h-12 px-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800">
                                        <option value="">Tüm Modüller</option>
                                        {moduller.map(m => <option key={m} value={m}>{m}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-slate-500 uppercase mb-1.5 block">İşlem Tipi</label>
                                    <select value={seciliTip} onChange={(e) => setSeciliTip(e.target.value)} className="w-full h-12 px-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800">
                                        <option value="">Tüm İşlemler</option>
                                        {islemTipleri.map(t => <option key={t} value={t}>{t}</option>)}
                                    </select>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="text-xs font-semibold text-slate-500 uppercase mb-1.5 block">Başlangıç</label>
                                        <input type="date" value={baslangicTarihi} onChange={(e) => setBaslangicTarihi(e.target.value)} className="w-full h-12 px-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800" />
                                    </div>
                                    <div>
                                        <label className="text-xs font-semibold text-slate-500 uppercase mb-1.5 block">Bitiş</label>
                                        <input type="date" value={bitisTarihi} onChange={(e) => setBitisTarihi(e.target.value)} className="w-full h-12 px-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800" />
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-3 mt-4 pt-4 border-t border-slate-100">
                                <button onClick={() => { clearFilters(); setMobilFiltreAcik(false); }} className="flex-1 h-12 rounded-xl border border-slate-200 font-semibold text-slate-600 bg-white">Temizle</button>
                                <button onClick={() => setMobilFiltreAcik(false)} className="flex-1 h-12 rounded-xl bg-slate-900 font-semibold text-white">Uygula</button>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* ── LOG DETAY SIDE DRAWER / BOTTOM SHEET (Key propları eklendi) ── */}
            <AnimatePresence>
                {seciliLog && (
                    <>
                        <motion.div
                            key="drawer-backdrop"
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-slate-900/20 backdrop-blur-[2px] z-[200]"
                            onClick={() => setSeciliLog(null)}
                        />
                        <motion.div
                            key="drawer-panel"
                            initial={{ x: '100%', y: 0 }} 
                            animate={{ x: 0, y: 0 }} 
                            exit={{ x: '100%', y: 0 }}
                            transition={{ type: "spring", bounce: 0, duration: 0.4 }}
                            className="fixed top-0 right-0 h-full w-full max-w-[600px] bg-white shadow-2xl z-[201] flex flex-col border-l border-slate-200"
                        >
                            {/* Drawer Header */}
                            <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-white">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-lg ${ActionStyles[seciliLog.islem_tipi]?.bg ?? 'bg-slate-100'} flex items-center justify-center`}>
                                        {React.createElement(ActionStyles[seciliLog.islem_tipi]?.icon ?? Activity, {
                                            className: `w-5 h-5 ${ActionStyles[seciliLog.islem_tipi]?.text ?? 'text-slate-600'}`
                                        })}
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-slate-900 leading-tight">Log Detayı</h3>
                                        <p className="text-xs font-medium text-slate-500">Kayıt No: #{seciliLog.id}</p>
                                    </div>
                                </div>
                                <button onClick={() => setSeciliLog(null)} className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-50 text-slate-500 hover:bg-slate-100 transition-colors">
                                    <X className="w-4 h-4" />
                                </button>
                            </div>

                            {/* Drawer Body */}
                            <div className="flex-1 overflow-y-auto p-5 sm:p-6 bg-[#FAFAFA] space-y-6">
                                {/* Üst Özet Kartı */}
                                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                                    <p className="text-sm font-semibold text-slate-800 mb-4 leading-relaxed">{seciliLog.detay}</p>
                                    <div className="flex flex-wrap items-center gap-3">
                                        <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 rounded-md border border-slate-100">
                                            <UserCircle className="w-4 h-4 text-slate-400" />
                                            <span className="text-xs font-semibold text-slate-600">{seciliLog.kullanici_ad_soyad || 'Sistem'}</span>
                                        </div>
                                        <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 rounded-md border border-slate-100">
                                            <Clock className="w-4 h-4 text-slate-400" />
                                            <span className="text-xs font-semibold text-slate-600">
                                                {parseLogDate(seciliLog.tarih)?.toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' }) || '-'}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Veri Alanı */}
                                {(seciliLog.eski_veri || seciliLog.yeni_veri) && (
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <h4 className="text-sm font-bold text-slate-900">
                                                {seciliLog.eski_veri && seciliLog.yeni_veri ? 'Değişiklik Karşılaştırması' : 'İşlem Verisi'}
                                            </h4>
                                            <button
                                                onClick={() => setHamJsonGoster(v => !v)}
                                                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-white border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors shadow-sm"
                                            >
                                                <Code2 className="w-3.5 h-3.5" />
                                                {hamJsonGoster ? 'Tablo Gösterimi' : 'Ham JSON'}
                                            </button>
                                        </div>

                                        {hamJsonGoster ? (
                                            <div className="space-y-3">
                                                {seciliLog.eski_veri && (
                                                    <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto shadow-inner">
                                                        <span className="text-xs font-bold text-rose-400 mb-2 block uppercase tracking-wider">Eski Veri</span>
                                                        <pre className="text-[12px] font-mono text-slate-300 leading-relaxed">
                                                            {JSON.stringify(seciliLog.eski_veri, null, 2)}
                                                        </pre>
                                                    </div>
                                                )}
                                                {seciliLog.yeni_veri && (
                                                    <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto shadow-inner">
                                                        <span className="text-xs font-bold text-emerald-400 mb-2 block uppercase tracking-wider">Yeni Veri</span>
                                                        <pre className="text-[12px] font-mono text-slate-300 leading-relaxed">
                                                            {JSON.stringify(seciliLog.yeni_veri, null, 2)}
                                                        </pre>
                                                    </div>
                                                )}
                                            </div>
                                        ) : (
                                            seciliLog.eski_veri && seciliLog.yeni_veri ? (
                                                <DiffTablo eskiVeri={seciliLog.eski_veri} yeniVeri={seciliLog.yeni_veri} />
                                            ) : (
                                                <JsonTablo
                                                    data={seciliLog.eski_veri ?? seciliLog.yeni_veri}
                                                    baslik={seciliLog.eski_veri ? 'Silinen/Eski Veri' : 'Eklenen/Yeni Veri'}
                                                    renk={seciliLog.eski_veri ? 'rose' : 'emerald'}
                                                />
                                            )
                                        )}
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}