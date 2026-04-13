import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
    ShieldAlert, Search, Filter, Clock, Activity,
    Trash2, PlusCircle, Edit3, Eye, X,
    UserCircle, Server, RefreshCw, Download, Code2
} from 'lucide-react';
import { getSistemLoglari } from '../services/api';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import * as XLSX from 'xlsx';

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

/** İç içe nesneyi maksimum 2 seviye derinliğe kadar düzleştirir. */
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

/** Ham değeri kullanıcı dostu metne çevirir. */
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

/** Noktalı anahtar için okunabilir etiket döndürür. */
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

// ─── JsonTablo Bileşeni ───────────────────────────────────────────────────────
const JsonTablo = ({ data, baslik, renk = 'slate' }) => {
    if (!data) return null;
    const duzData = duzlestir(data);
    const entries = Object.entries(duzData);
    if (entries.length === 0) return <p className="text-sm text-slate-400 italic py-2">Veri bulunamadı.</p>;

    const renkler = {
        slate:   { dot: 'bg-slate-500',   label: 'text-slate-500'   },
        rose:    { dot: 'bg-rose-500',     label: 'text-rose-600'    },
        emerald: { dot: 'bg-emerald-500',  label: 'text-emerald-600' },
    };
    const r = renkler[renk] ?? renkler.slate;

    return (
        <div>
            {baslik && (
                <div className="flex items-center gap-2 mb-2 px-1">
                    <div className={`w-2 h-2 rounded-full ${r.dot}`} />
                    <span className={`text-[11px] font-black uppercase tracking-wider ${r.label}`}>{baslik}</span>
                </div>
            )}
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-[12px]">
                    <tbody>
                        {entries.map(([key, val], i) => (
                            <tr key={key} className={`${i % 2 === 0 ? 'bg-white' : 'bg-slate-50'} border-t border-slate-100 first:border-0`}>
                                <td className="px-3 py-2 font-semibold text-slate-500 w-2/5 border-r border-slate-100 whitespace-nowrap">
                                    {etiketAl(key)}
                                </td>
                                <td className="px-3 py-2 font-medium text-slate-800 break-all">
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

// ─── DiffTablo Bileşeni ───────────────────────────────────────────────────────
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
                if (!eskiMevcut)                                                              durum = 'eklendi';
                else if (!yeniMevcut)                                                         durum = 'silindi';
                else if (JSON.stringify(duzEski[key]) !== JSON.stringify(duzYeni[key]))       durum = 'degisti';
                else                                                                          durum = 'ayni';
                return { key, eskiDeger: duzEski[key], yeniDeger: duzYeni[key], durum };
            })
            .sort((a, b) => DURUM_SIRASI[a.durum] - DURUM_SIRASI[b.durum]);
    }, [duzEski, duzYeni]);

    const ozet = useMemo(() => ({
        degisti: satirlar.filter(s => s.durum === 'degisti').length,
        eklendi: satirlar.filter(s => s.durum === 'eklendi').length,
        silindi: satirlar.filter(s => s.durum === 'silindi').length,
    }), [satirlar]);

    return (
        <div>
            {/* Özet Rozetleri */}
            <div className="flex items-center gap-2 mb-3 flex-wrap">
                {ozet.degisti > 0 && (
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-bold bg-amber-100 text-amber-700 px-2.5 py-1 rounded-full">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block" />
                        {ozet.degisti} değişiklik
                    </span>
                )}
                {ozet.eklendi > 0 && (
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-bold bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                        {ozet.eklendi} yeni alan
                    </span>
                )}
                {ozet.silindi > 0 && (
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-bold bg-rose-100 text-rose-700 px-2.5 py-1 rounded-full">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block" />
                        {ozet.silindi} silinen alan
                    </span>
                )}
                {ozet.degisti === 0 && ozet.eklendi === 0 && ozet.silindi === 0 && (
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-bold bg-slate-100 text-slate-500 px-2.5 py-1 rounded-full">
                        Değişiklik tespit edilmedi
                    </span>
                )}
            </div>

            {/* Karşılaştırma Tablosu */}
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                {/* Başlık Satırı */}
                <div className="grid grid-cols-[2fr_3fr_3fr] bg-slate-50 border-b border-slate-200 text-[10px] font-black uppercase tracking-widest">
                    <div className="px-3 py-2 text-slate-500">Alan</div>
                    <div className="px-3 py-2 text-rose-500 border-l border-slate-200 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block" />
                        Eski Değer
                    </div>
                    <div className="px-3 py-2 text-emerald-600 border-l border-slate-200 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                        Yeni Değer
                    </div>
                </div>

                <table className="w-full text-[12px]">
                    <tbody>
                        {satirlar.map(({ key, eskiDeger, yeniDeger, durum }, i) => {
                            const satirBg = {
                                degisti: 'bg-amber-50/70',
                                eklendi: 'bg-emerald-50/70',
                                silindi: 'bg-rose-50/70',
                                ayni: i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50',
                            }[durum];

                            return (
                                <tr key={key} className={`${satirBg} border-t border-slate-100/80`}>
                                    <td className="px-3 py-2.5 font-semibold text-slate-600 border-r border-slate-100 whitespace-nowrap">
                                        <div className="flex items-center gap-1.5">
                                            {durum === 'degisti' && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />}
                                            {durum === 'eklendi' && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />}
                                            {durum === 'silindi' && <span className="w-1.5 h-1.5 rounded-full bg-rose-400 flex-shrink-0" />}
                                            {etiketAl(key)}
                                        </div>
                                    </td>
                                    <td className="px-3 py-2.5 border-r border-slate-100 break-all">
                                        {durum === 'eklendi' ? (
                                            <span className="text-slate-300 select-none">—</span>
                                        ) : (
                                            <span className={
                                                durum === 'degisti' ? 'line-through text-rose-400' :
                                                durum === 'silindi' ? 'text-rose-700 font-medium' :
                                                'text-slate-700'
                                            }>
                                                {degerBicimlendir(eskiDeger)}
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-3 py-2.5 break-all">
                                        {durum === 'silindi' ? (
                                            <span className="text-slate-300 select-none">—</span>
                                        ) : (
                                            <span className={
                                                durum === 'degisti' || durum === 'eklendi'
                                                    ? 'font-bold text-emerald-700'
                                                    : 'text-slate-700'
                                            }>
                                                {degerBicimlendir(yeniDeger)}
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

// ─── İkon ve Renk Haritası ────────────────────────────────────────────────────
const ActionStyles = {
    CREATE:  { icon: PlusCircle,  color: 'emerald', label: 'Ekleme'       },
    UPDATE:  { icon: Edit3,       color: 'blue',    label: 'Güncelleme'   },
    DELETE:  { icon: Trash2,      color: 'rose',    label: 'Silme'        },
    LOGIN:   { icon: UserCircle,  color: 'indigo',  label: 'Giriş'        },
    DEFAULT: { icon: Activity,    color: 'slate',   label: 'Diğer İşlem'  },
};

// ─── Ana Sayfa Bileşeni ───────────────────────────────────────────────────────
export default function SistemLoglariPage() {
    const [loglar, setLoglar] = useState([]);
    const { loading, run } = useAsync(true);

    const [aramaTaramasi, setAramaTaramasi] = useState('');
    const [seciliModul, setSeciliModul] = useState('');
    const [seciliTip, setSeciliTip] = useState('');
    const [baslangicTarihi, setBaslangicTarihi] = useState('');
    const [bitisTarihi, setBitisTarihi] = useState('');

    const [seciliLog, setSeciliLog] = useState(null);
    const [hamJsonGoster, setHamJsonGoster] = useState(false);

    // Modal her değiştiğinde ham JSON görünümünü kapat
    useEffect(() => { setHamJsonGoster(false); }, [seciliLog]);

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

    const moduller = useMemo(() => {
        return [...new Set(loglar.map(l => l.modul))].filter(Boolean).sort();
    }, [loglar]);

    const islemTipleri = useMemo(() => {
        return [...new Set(loglar.map(l => l.islem_tipi))].filter(Boolean).sort();
    }, [loglar]);

    const filteredLoglar = useMemo(() => {
        return loglar.filter(log => {
            const aramaMetni = aramaTaramasi.toLowerCase();
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
    }, [loglar, aramaTaramasi, seciliModul, seciliTip, baslangicTarihi, bitisTarihi]);

    const exportToExcel = () => {
        if (filteredLoglar.length === 0) { toast.error("İndirilecek veri yok."); return; }

        const excelData = filteredLoglar.map(log => ({
            "Tarih":        parseLogDate(log.tarih)?.toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' }) || '-',
            "İşlem Tipi":  ActionStyles[log.islem_tipi]?.label || log.islem_tipi,
            "Modül":        log.modul,
            "Kullanıcı":   log.kullanici_ad_soyad || 'Sistem',
            "İşlem Detayı": log.detay,
            "Eski Veri":   log.eski_veri ? JSON.stringify(log.eski_veri) : '-',
            "Yeni Veri":   log.yeni_veri ? JSON.stringify(log.yeni_veri) : '-',
        }));

        const ws = XLSX.utils.json_to_sheet(excelData);
        ws['!cols'] = [
            { wch: 20 }, { wch: 15 }, { wch: 20 },
            { wch: 20 }, { wch: 50 }, { wch: 30 }, { wch: 30 },
        ];
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Sistem Logları");
        XLSX.writeFile(wb, `Sistem_Loglari_${new Date().toLocaleDateString('tr-TR')}.xlsx`);
        toast.success("Excel başarıyla indirildi.");
    };

    return (
        <div className="max-w-[1400px] mx-auto p-4 sm:p-6 pb-24 space-y-6">

            {/* ── HEADER ── */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 md:gap-6 bg-white p-5 sm:p-8 rounded-[24px] md:rounded-[32px] border border-slate-100 shadow-sm relative overflow-hidden">
                <div className="absolute -right-20 -top-20 w-64 h-64 bg-slate-50 rounded-full blur-3xl opacity-50 pointer-events-none" />

                <div className="flex items-center gap-4 md:gap-5 relative z-10">
                    <div className="w-12 h-12 md:w-16 md:h-16 rounded-xl md:rounded-2xl bg-slate-900 flex items-center justify-center flex-shrink-0 shadow-lg shadow-slate-900/20">
                        <ShieldAlert className="w-6 h-6 md:w-8 md:h-8 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl sm:text-[28px] font-black text-slate-800 tracking-tight leading-none mb-1">Sistem Logları</h1>
                        <p className="text-xs sm:text-[14px] font-medium text-slate-500">Tüm sistem ve kullanıcı hareketlerini inceliyorsunuz.</p>
                    </div>
                </div>

                <div className="relative z-10 flex items-center gap-2 md:gap-3 w-full md:w-auto mt-2 md:mt-0">
                    <button
                        onClick={exportToExcel}
                        className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 md:px-5 md:py-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold hover:bg-emerald-100 hover:text-emerald-800 active:scale-95 transition-all shadow-sm text-sm"
                    >
                        <Download className="w-4 h-4" />
                        <span className="md:inline">İndir</span>
                    </button>
                    <button
                        onClick={fetchData}
                        className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 md:px-5 md:py-3 rounded-xl bg-white border border-slate-200 text-slate-700 font-bold hover:bg-slate-50 hover:text-slate-900 active:scale-95 transition-all shadow-sm text-sm"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        <span className="md:inline">Yenile</span>
                    </button>
                </div>
            </div>

            {/* ── FİLTRELER ── */}
            <div className="bg-white p-2 md:p-3 border border-slate-100/80 rounded-2xl shadow-sm flex flex-col md:flex-row gap-2 md:gap-3">
                <div className="relative w-full md:flex-1 group">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                    <input
                        type="text"
                        placeholder="İşlem veya kullanıcı ara..."
                        value={aramaTaramasi}
                        onChange={(e) => setAramaTaramasi(e.target.value)}
                        className="w-full h-10 md:h-12 pl-9 pr-3 bg-slate-50 md:bg-transparent rounded-xl md:rounded-lg text-[13px] md:text-[14px] font-semibold text-slate-800 focus:outline-none focus:bg-white border border-slate-200 md:border-transparent placeholder:text-slate-400 transition-colors"
                    />
                </div>

                <div className="hidden md:block w-px h-8 bg-slate-200 self-center" />

                <div className="grid grid-cols-2 md:flex gap-2">
                    <div className="relative">
                        <Server className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <select
                            value={seciliModul}
                            onChange={(e) => setSeciliModul(e.target.value)}
                            className="w-full md:w-40 h-10 md:h-12 pl-8 pr-6 bg-slate-50 md:bg-transparent border border-slate-200 md:border-transparent rounded-xl text-[12px] md:text-[13px] font-bold text-slate-700 focus:outline-none focus:bg-white transition-colors appearance-none cursor-pointer"
                        >
                            <option value="">Tüm Modüller</option>
                            {moduller.map(m => <option key={m} value={m}>{m}</option>)}
                        </select>
                    </div>

                    <div className="relative">
                        <Filter className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <select
                            value={seciliTip}
                            onChange={(e) => setSeciliTip(e.target.value)}
                            className="w-full md:w-40 h-10 md:h-12 pl-8 pr-6 bg-slate-50 md:bg-transparent border border-slate-200 md:border-transparent rounded-xl text-[12px] md:text-[13px] font-bold text-slate-700 focus:outline-none focus:bg-white transition-colors appearance-none cursor-pointer"
                        >
                            <option value="">Tüm İşlemler</option>
                            {islemTipleri.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                    </div>
                </div>

                <div className="hidden md:block w-px h-8 bg-slate-200 self-center" />

                <div className="grid grid-cols-2 md:flex items-center gap-2">
                    <input
                        type="date"
                        value={baslangicTarihi}
                        onChange={(e) => setBaslangicTarihi(e.target.value)}
                        className="w-full md:w-auto h-10 md:h-12 px-2.5 bg-slate-50 md:bg-transparent border border-slate-200 md:border-transparent rounded-xl text-[12px] md:text-[13px] font-bold text-slate-700 focus:outline-none focus:bg-white transition-colors"
                    />
                    <input
                        type="date"
                        value={bitisTarihi}
                        onChange={(e) => setBitisTarihi(e.target.value)}
                        className="w-full md:w-auto h-10 md:h-12 px-2.5 bg-slate-50 md:bg-transparent border border-slate-200 md:border-transparent rounded-xl text-[12px] md:text-[13px] font-bold text-slate-700 focus:outline-none focus:bg-white transition-colors"
                    />
                </div>
            </div>

            {/* ── LİSTE ── */}
            {loading ? (
                <div className="flex flex-col items-center justify-center p-20 gap-4">
                    <RefreshCw className="w-10 h-10 text-slate-300 animate-spin" />
                    <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Kayıtlar Taranıyor...</p>
                </div>
            ) : filteredLoglar.length === 0 ? (
                <div className="bg-white rounded-3xl p-16 flex flex-col items-center text-center border border-slate-100 shadow-sm">
                    <div className="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center mb-6">
                        <Search className="w-12 h-12 text-slate-300" />
                    </div>
                    <h3 className="text-xl font-black text-slate-800 mb-2">Kayıt Bulunamadı</h3>
                    <p className="text-sm font-medium text-slate-500">Arama kriterlerinize uygun sistem logu bulunmuyor.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-3">
                    {filteredLoglar.map((log) => {
                        const styleInfo = ActionStyles[log.islem_tipi] ?? ActionStyles.DEFAULT;
                        const Icon = styleInfo.icon;
                        const c = styleInfo.color;
                        const hasDiff = log.eski_veri || log.yeni_veri;

                        return (
                            <div
                                key={log.id}
                                onClick={() => hasDiff && setSeciliLog(log)}
                                className={`flex flex-col md:flex-row md:items-center justify-between gap-3 md:gap-4 p-3.5 sm:p-5 bg-white rounded-xl md:rounded-2xl border border-slate-200 transition-all duration-300
                                ${hasDiff ? 'cursor-pointer hover:border-slate-300 hover:shadow-md' : ''}`}
                            >
                                <div className="flex items-start md:items-center gap-3 md:gap-4 min-w-0">
                                    <div className={`w-10 h-10 md:w-12 md:h-12 rounded-lg md:rounded-xl bg-${c}-50 flex items-center justify-center flex-shrink-0 ring-1 ring-${c}-100`}>
                                        <Icon className={`w-5 h-5 md:w-6 md:h-6 text-${c}-600`} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                                            <span className={`text-[10px] md:text-[11px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded-md bg-${c}-100/50 text-${c}-700`}>
                                                {styleInfo.label}
                                            </span>
                                            <span className="text-[11px] md:text-[12px] font-bold text-slate-400 bg-slate-100 px-1.5 md:px-2 py-0.5 rounded-md truncate max-w-[120px] md:max-w-none">
                                                Modül: {log.modul}
                                            </span>
                                        </div>
                                        <p className="text-[13px] md:text-[15px] font-bold text-slate-800 leading-snug break-words line-clamp-2 md:line-clamp-none">
                                            {log.detay || 'İşlem detayı yok.'}
                                        </p>
                                    </div>
                                </div>

                                <div className="flex flex-row items-center justify-between md:justify-center md:flex-col gap-2 md:gap-1 flex-shrink-0 pt-2.5 md:pt-0 mt-1 md:mt-0 border-t md:border-0 border-slate-100">
                                    <div className="flex items-center gap-3 md:gap-1.5">
                                        <div className="flex items-center gap-1 md:gap-1.5 text-slate-500">
                                            <UserCircle className="w-3.5 h-3.5 md:w-4 md:h-4" />
                                            <span className="text-[11px] md:text-[13px] font-black truncate max-w-[90px] md:max-w-[120px]">{log.kullanici_ad_soyad || 'Sistem'}</span>
                                        </div>
                                        <div className="flex items-center gap-1 md:gap-1.5 text-slate-400 md:hidden">
                                            <Clock className="w-3.5 h-3.5" />
                                            <span className="text-[11px] font-semibold">
                                                {parseLogDate(log.tarih)?.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', timeZone: 'Europe/Istanbul' }) || '-'}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="hidden md:flex items-center gap-1.5 text-slate-400">
                                        <Clock className="w-3.5 h-3.5" />
                                        <span className="text-[12px] font-semibold">
                                            {parseLogDate(log.tarih)?.toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Istanbul' }) || '-'}
                                        </span>
                                    </div>

                                    {hasDiff && (
                                        <span className="md:hidden text-[10px] font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded border border-blue-100">
                                            İncele
                                        </span>
                                    )}
                                </div>

                                {hasDiff && (
                                    <div className="hidden md:flex items-center justify-center w-10 h-10 rounded-full bg-slate-50 text-slate-400 hover:bg-blue-50 hover:text-blue-600 transition-colors shrink-0">
                                        <Eye className="w-5 h-5" />
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* ── DETAY MODALI ── */}
            {seciliLog && (
                <div
                    className="fixed inset-0 z-[100] flex items-center justify-center p-3 md:p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in"
                    onClick={() => setSeciliLog(null)}
                >
                    <div
                        className="bg-white rounded-[24px] md:rounded-[32px] w-full max-w-3xl max-h-[90vh] overflow-hidden shadow-2xl flex flex-col animate-in zoom-in-95 duration-200"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Modal Başlığı */}
                        <div className="flex items-center justify-between p-4 md:p-6 pb-3 md:pb-4 border-b border-slate-100 shadow-sm z-10">
                            <div className="flex items-center gap-3 md:gap-4">
                                <div className={`w-10 h-10 md:w-12 md:h-12 rounded-lg md:rounded-xl bg-${ActionStyles[seciliLog.islem_tipi]?.color ?? 'slate'}-50 flex items-center justify-center`}>
                                    {React.createElement(ActionStyles[seciliLog.islem_tipi]?.icon ?? Activity, {
                                        className: `w-5 h-5 md:w-6 md:h-6 text-${ActionStyles[seciliLog.islem_tipi]?.color ?? 'slate'}-600`
                                    })}
                                </div>
                                <div>
                                    <h3 className="text-[16px] md:text-[18px] font-black text-slate-900 leading-none mb-1">Kayıt Detayı</h3>
                                    <p className="text-[12px] md:text-[13px] font-semibold text-slate-500">ID: #{seciliLog.id} • {seciliLog.modul}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setSeciliLog(null)}
                                className="w-8 h-8 md:w-10 md:h-10 flex items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-rose-100 hover:text-rose-600 transition-colors"
                            >
                                <X className="w-4 h-4 md:w-5 md:h-5" />
                            </button>
                        </div>

                        {/* Modal Gövdesi */}
                        <div className="p-4 md:p-6 overflow-y-auto custom-scrollbar flex-1 bg-slate-50 space-y-5">

                            {/* İşlem Özeti */}
                            <div className="bg-white p-3.5 md:p-4 rounded-xl md:rounded-2xl border border-slate-200 shadow-sm">
                                <p className="text-[13px] md:text-[14px] font-bold text-slate-800 mb-2.5">{seciliLog.detay}</p>
                                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-[11px] md:text-[12px] font-semibold text-slate-500">
                                    <span className="flex items-center gap-1.5 bg-slate-50 w-fit px-2 py-1 rounded">
                                        <UserCircle className="w-4 h-4 text-slate-400" />
                                        {seciliLog.kullanici_ad_soyad}
                                    </span>
                                    <span className="flex items-center gap-1.5 bg-slate-50 w-fit px-2 py-1 rounded">
                                        <Clock className="w-4 h-4 text-slate-400" />
                                        {parseLogDate(seciliLog.tarih)?.toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' }) || '-'}
                                    </span>
                                </div>
                            </div>

                            {/* Veri Görünümü */}
                            {(seciliLog.eski_veri || seciliLog.yeni_veri) && (
                                <div>
                                    {/* Başlık + Toggle */}
                                    <div className="flex items-center justify-between mb-3">
                                        <h4 className="text-[12px] font-black text-slate-500 uppercase tracking-wider">
                                            {seciliLog.eski_veri && seciliLog.yeni_veri
                                                ? 'Değişiklik Karşılaştırması'
                                                : 'Kayıt Verisi'}
                                        </h4>
                                        <button
                                            onClick={() => setHamJsonGoster(v => !v)}
                                            className="flex items-center gap-1.5 text-[11px] font-bold text-slate-400 hover:text-slate-600 bg-slate-100 hover:bg-slate-200 px-2.5 py-1.5 rounded-lg transition-colors"
                                        >
                                            <Code2 className="w-3.5 h-3.5" />
                                            {hamJsonGoster ? 'Tablo Görünümü' : 'Ham JSON'}
                                        </button>
                                    </div>

                                    {hamJsonGoster ? (
                                        /* Ham JSON */
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            {seciliLog.eski_veri && (
                                                <div className="flex flex-col">
                                                    <div className="flex items-center gap-2 mb-2 px-1">
                                                        <div className="w-2 h-2 rounded-full bg-rose-500" />
                                                        <span className="text-[11px] font-black text-slate-600 uppercase tracking-wider">Eski Veri</span>
                                                    </div>
                                                    <div className="bg-[#1e1e1e] rounded-xl p-3 md:p-4 overflow-x-auto border border-rose-900/30 flex-1">
                                                        <pre className="text-[12px] text-rose-300 font-mono leading-relaxed">
                                                            {JSON.stringify(seciliLog.eski_veri, null, 2)}
                                                        </pre>
                                                    </div>
                                                </div>
                                            )}
                                            {seciliLog.yeni_veri && (
                                                <div className="flex flex-col">
                                                    <div className="flex items-center gap-2 mb-2 px-1">
                                                        <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                                        <span className="text-[11px] font-black text-slate-600 uppercase tracking-wider">Yeni Veri</span>
                                                    </div>
                                                    <div className="bg-[#1e1e1e] rounded-xl p-3 md:p-4 overflow-x-auto border border-emerald-900/30 flex-1">
                                                        <pre className="text-[12px] text-emerald-300 font-mono leading-relaxed">
                                                            {JSON.stringify(seciliLog.yeni_veri, null, 2)}
                                                        </pre>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        /* Tablo Görünümü */
                                        seciliLog.eski_veri && seciliLog.yeni_veri ? (
                                            <DiffTablo
                                                eskiVeri={seciliLog.eski_veri}
                                                yeniVeri={seciliLog.yeni_veri}
                                            />
                                        ) : (
                                            <JsonTablo
                                                data={seciliLog.eski_veri ?? seciliLog.yeni_veri}
                                                baslik={seciliLog.eski_veri ? 'Eski Veri' : 'Yeni Veri'}
                                                renk={seciliLog.eski_veri ? 'rose' : 'emerald'}
                                            />
                                        )
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
