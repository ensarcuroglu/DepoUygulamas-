import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
    ShieldAlert, Search, Filter, Clock, Activity,
    Trash2, PlusCircle, Edit3, Eye, X, ArrowRight,
    UserCircle, Server, RefreshCw, Download
} from 'lucide-react';
import { getSistemLoglari } from '../services/api';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import * as XLSX from 'xlsx';

const HAS_TZ_INFO_REGEX = /([zZ]|[+-]\d{2}:\d{2})$/;

const parseLogDate = (value) => {
    if (!value) return null;
    if (typeof value === 'string' && !HAS_TZ_INFO_REGEX.test(value)) {
        return new Date(`${value}Z`);
    }
    return new Date(value);
};

// İkon ve Renk Haritası
const ActionStyles = {
    CREATE: { icon: PlusCircle, color: 'emerald', label: 'Ekleme' },
    UPDATE: { icon: Edit3, color: 'blue', label: 'Güncelleme' },
    DELETE: { icon: Trash2, color: 'rose', label: 'Silme' },
    LOGIN: { icon: UserCircle, color: 'indigo', label: 'Giriş' },
    DEFAULT: { icon: Activity, color: 'slate', label: 'Diğer İşlem' }
};

export default function SistemLoglariPage() {
    const [loglar, setLoglar] = useState([]);
    const { loading, run } = useAsync(true);

    // Filtre state'leri
    const [aramaTaramasi, setAramaTaramasi] = useState('');
    const [seciliModul, setSeciliModul] = useState('');
    const [seciliTip, setSeciliTip] = useState('');
    const [baslangicTarihi, setBaslangicTarihi] = useState('');
    const [bitisTarihi, setBitisTarihi] = useState('');

    // Detay Modalı State
    const [seciliLog, setSeciliLog] = useState(null);

    const fetchData = useCallback(async () => {
        try {
            const res = await run(() => getSistemLoglari(200));
            setLoglar(res.data);
        } catch {
            toast.error('Loglar yüklenirken hata oluştu');
        }
    }, [run]);

    useEffect(() => {
        const timeoutId = setTimeout(() => {
            void fetchData();
        }, 0);

        return () => clearTimeout(timeoutId);
    }, [fetchData]);

    // Modüllerin ve Tiplerin dinamik listesi (dropdown için)
    const moduller = useMemo(() => {
        const unique = [...new Set(loglar.map(l => l.modul))].filter(Boolean);
        return unique.sort();
    }, [loglar]);

    const islemTipleri = useMemo(() => {
        const unique = [...new Set(loglar.map(l => l.islem_tipi))].filter(Boolean);
        return unique.sort();
    }, [loglar]);

    // Filtreleme mantığı
    const filteredLoglar = useMemo(() => {
        return loglar.filter(log => {
            const aramaMetni = aramaTaramasi.toLowerCase();
            const matchesSearch =
                (log.detay && log.detay.toLowerCase().includes(aramaMetni)) ||
                (log.kullanici_ad_soyad && log.kullanici_ad_soyad.toLowerCase().includes(aramaMetni)) ||
                (log.modul && log.modul.toLowerCase().includes(aramaMetni));

            const matchesModul = seciliModul ? log.modul === seciliModul : true;
            const matchesTip = seciliTip ? log.islem_tipi === seciliTip : true;

            let matchesTarih = true;
            if (baslangicTarihi || bitisTarihi) {
                const parsedLogDate = parseLogDate(log.tarih);
                if (!parsedLogDate || Number.isNaN(parsedLogDate.getTime())) return false;
                const logAman = parsedLogDate.getTime();
                const starTime = baslangicTarihi ? new Date(baslangicTarihi).getTime() : 0;
                // Bitiş gününün son saniyesini almak için +1 gün
                const endTime = bitisTarihi ? new Date(bitisTarihi).getTime() + 86400000 : Infinity;
                matchesTarih = logAman >= starTime && logAman < endTime;
            }

            return matchesSearch && matchesModul && matchesTip && matchesTarih;
        });
    }, [loglar, aramaTaramasi, seciliModul, seciliTip, baslangicTarihi, bitisTarihi]);

    // Excel Export
    const exportToExcel = () => {
        if (filteredLoglar.length === 0) {
            toast.error("İndirilecek veri yok.");
            return;
        }

        const excelData = filteredLoglar.map(log => ({
            "Tarih": parseLogDate(log.tarih)?.toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' }) || '-',
            "İşlem Tipi": ActionStyles[log.islem_tipi]?.label || log.islem_tipi,
            "Modül": log.modul,
            "Kullanıcı": log.kullanici_ad_soyad || 'Sistem',
            "İşlem Detayı": log.detay,
            "Eski Veri": log.eski_veri ? JSON.stringify(log.eski_veri) : '-',
            "Yeni Veri": log.yeni_veri ? JSON.stringify(log.yeni_veri) : '-'
        }));

        const ws = XLSX.utils.json_to_sheet(excelData);
        // Sütun genişlikleri ayarı (isteğe bağlı)
        const wscols = [
            { wch: 20 }, // Tarih
            { wch: 15 }, // İşlem Tipi
            { wch: 20 }, // Modül
            { wch: 20 }, // Kullanıcı
            { wch: 50 }, // Detay
            { wch: 30 }, // Eski Veri
            { wch: 30 }  // Yeni Veri
        ];
        ws['!cols'] = wscols;

        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Sistem Logları");

        XLSX.writeFile(wb, `Sistem_Loglari_${new Date().toLocaleDateString('tr-TR')}.xlsx`);
        toast.success("Excel başarıyla indirildi.");
    };

    // JSON formatter
    const formatJSON = (data) => {
        if (!data) return "Veri bulunmuyor.";
        try {
            return JSON.stringify(data, null, 2);
        } catch {
            return String(data);
        }
    };

    return (
        <div className="max-w-[1400px] mx-auto p-4 sm:p-6 pb-24 space-y-6">

            {/* --- HEADER KISMI --- */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 md:gap-6 bg-white p-5 sm:p-8 rounded-[24px] md:rounded-[32px] border border-slate-100 shadow-sm relative overflow-hidden">
                {/* Dekoratif Arkaplan */}
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

            {/* --- FİLTRELER --- */}
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

                {/* Tarih Filtreleri */}
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

            {/* --- LİSTE GÖRÜNÜMÜ --- */}
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
                        const styleInfo = ActionStyles[log.islem_tipi] || ActionStyles.DEFAULT;
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
                                {/* Sol Bölüm: İcon ve Detay */}
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

                                {/* Sağ Bölüm: Tarih ve Info */}
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

                                    {/* Mobilde görünür incele butonu minik */}
                                    {hasDiff && (
                                        <span className="md:hidden text-[10px] font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded border border-blue-100">
                                            İncele
                                        </span>
                                    )}
                                </div>

                                {/* Desktop için incele butonu */}
                                {hasDiff && (
                                    <div className="hidden md:flex items-center justify-center w-10 h-10 rounded-full bg-slate-50 text-slate-400 group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors shrink-0">
                                        <Eye className="w-5 h-5" />
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* --- DETAY MODALI --- */}
            {seciliLog && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 md:p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
                    <div
                        className="bg-white rounded-[24px] md:rounded-[32px] w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-2xl flex flex-col animate-in zoom-in-95 duration-200"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Modal Header */}
                        <div className="flex items-center justify-between p-4 md:p-6 pb-3 md:pb-4 border-b border-slate-100 shadow-sm z-10">
                            <div className="flex items-center gap-3 md:gap-4">
                                <div className={`w-10 h-10 md:w-12 md:h-12 rounded-lg md:rounded-xl bg-${ActionStyles[seciliLog.islem_tipi]?.color || 'slate'}-50 flex items-center justify-center`}>
                                    {React.createElement(ActionStyles[seciliLog.islem_tipi]?.icon || Activity, {
                                        className: `w-5 h-5 md:w-6 md:h-6 text-${ActionStyles[seciliLog.islem_tipi]?.color || 'slate'}-600`
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

                        {/* Modal Body */}
                        <div className="p-4 md:p-6 overflow-y-auto custom-scrollbar flex-1 bg-slate-50">

                            {/* Özet */}
                            <div className="bg-white p-3.5 md:p-4 rounded-xl md:rounded-2xl border border-slate-200 shadow-sm mb-4 md:mb-6">
                                <p className="text-[13px] md:text-[14px] font-bold text-slate-800 mb-2.5 md:mb-2">{seciliLog.detay}</p>
                                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-[11px] md:text-[12px] font-semibold text-slate-500">
                                    <span className="flex items-center gap-1.5 bg-slate-50 w-fit px-2 py-1 rounded"><UserCircle className="w-4 h-4 text-slate-400" /> {seciliLog.kullanici_ad_soyad}</span>
                                    <span className="flex items-center gap-1.5 bg-slate-50 w-fit px-2 py-1 rounded"><Clock className="w-4 h-4 text-slate-400" /> {parseLogDate(seciliLog.tarih)?.toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' }) || '-'}</span>
                                </div>
                            </div>

                            {/* Diff Görünümü */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Eski Veri */}
                                {seciliLog.eski_veri && (
                                    <div className="flex flex-col">
                                        <div className="flex items-center gap-2 mb-2 px-1">
                                            <div className="w-2 h-2 rounded-full bg-rose-500" />
                                            <span className="text-[11px] md:text-[12px] font-black text-slate-600 uppercase tracking-wider">Eski Veri</span>
                                        </div>
                                        <div className="bg-[#1e1e1e] rounded-xl md:rounded-2xl p-3 md:p-4 overflow-x-auto border border-rose-900/30 flex-1">
                                            <pre className="text-[12px] md:text-[13px] text-rose-300 font-mono leading-relaxed">
                                                {formatJSON(seciliLog.eski_veri)}
                                            </pre>
                                        </div>
                                    </div>
                                )}

                                {/* Yeni Veri */}
                                {seciliLog.yeni_veri && (
                                    <div className="flex flex-col">
                                        <div className="flex items-center gap-2 mb-2 px-1">
                                            <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                            <span className="text-[11px] md:text-[12px] font-black text-slate-600 uppercase tracking-wider">Yeni Veri</span>
                                        </div>
                                        <div className="bg-[#1e1e1e] rounded-xl md:rounded-2xl p-3 md:p-4 overflow-x-auto border border-emerald-900/30 flex-1">
                                            <pre className="text-[12px] md:text-[13px] text-emerald-300 font-mono leading-relaxed">
                                                {formatJSON(seciliLog.yeni_veri)}
                                            </pre>
                                        </div>
                                    </div>
                                )}
                            </div>

                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
