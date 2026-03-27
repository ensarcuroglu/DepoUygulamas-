import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
    getDestekTalepleri,
    createDestekTalebi,
    updateDestekTalebi
} from '../services/api';
import toast from 'react-hot-toast';
import { hataMetni } from '../utils/hata';
import {
    HelpCircle,
    Plus,
    Search,
    Filter,
    RefreshCw,
    Clock,
    CheckCircle2,
    X,
    MessageCircle,
    Eye,
    AlertTriangle,
    UserCircle,
    Tag,
    ChevronDown
} from 'lucide-react';

// ========================
// YARDIMCI BİLEŞENLER (BADGES)
// ========================

const getDurumBadge = (durum) => {
    const styles = {
        'Açık': 'bg-blue-50/80 text-blue-600 border-blue-200/50',
        'İşlemde': 'bg-amber-50/80 text-amber-600 border-amber-200/50',
        'Çözüldü': 'bg-emerald-50/80 text-emerald-600 border-emerald-200/50'
    };
    const currentStyle = styles[durum] || 'bg-slate-50 text-slate-500 border-slate-200';

    let icon = <Clock className="w-3.5 h-3.5" />;
    if (durum === 'İşlemde') icon = <RefreshCw className="w-3.5 h-3.5 animate-[spin_3s_linear_infinite]" />;
    if (durum === 'Çözüldü') icon = <CheckCircle2 className="w-3.5 h-3.5" />;

    return (
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${currentStyle} shadow-sm backdrop-blur-md transition-all`}>
            {icon}
            {durum}
        </span>
    );
};

const getOncelikBadge = (oncelik) => {
    const styles = {
        'Düşük': 'bg-slate-100/80 text-slate-500 border border-slate-200/60',
        'Normal': 'bg-indigo-50/80 text-indigo-600 border border-indigo-200/50',
        'Yüksek': 'bg-rose-50/80 flex text-rose-600 border border-rose-200/50 shadow-sm'
    };
    const currentStyle = styles[oncelik] || 'bg-slate-100 text-slate-500 border border-slate-200';

    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-[11px] font-bold uppercase tracking-wider backdrop-blur-sm ${currentStyle}`}>
            {oncelik === 'Yüksek' && <AlertTriangle className="w-3 h-3 mr-1" />}
            {oncelik}
        </span>
    );
};

// ========================
// ANA BİLEŞEN
// ========================

export default function DestekMasasiPage() {
    const { user } = useAuth();
    const isAdmin = user?.rol === 'admin';

    // --- State Yönetimi ---
    const [talepler, setTalepler] = useState([]);
    const [loading, setLoading] = useState(true);
    const [aramaGirdisi, setAramaGirdisi] = useState('');
    const [filtreDurum, setFiltreDurum] = useState('');

    // Modal States
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [isDetailOpen, setIsDetailOpen] = useState(false);
    const [selectedTalep, setSelectedTalep] = useState(null);

    // Form States (Yeni Talep)
    const [yeniKonu, setYeniKonu] = useState('');
    const [yeniKategori, setYeniKategori] = useState('Hata Bildirimi');
    const [yeniOncelik, setYeniOncelik] = useState('Normal');
    const [yeniAciklama, setYeniAciklama] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Form States (Cevaplama / Güncelleme)
    const [cevapMetni, setCevapMetni] = useState('');
    const [updateDurum, setUpdateDurum] = useState('');

    // --- Veri Çekme ---
    const fetchTalepler = async () => {
        setLoading(true);
        try {
            const params = {};
            if (filtreDurum) params.durum = filtreDurum;

            const res = await getDestekTalepleri(params);
            setTalepler(res.data);
        } catch (error) {
            console.error("Talepler yüklenemedi:", error);
            toast.error(hataMetni(error, 'Talepler yüklenirken bir sorun oluştu.'));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTalepler();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filtreDurum]);

    // --- Yeni Talep Gönderimi ---
    const handleCreateSubmit = async (e) => {
        e.preventDefault();
        if (!yeniKonu.trim() || !yeniAciklama.trim()) {
            toast.error("Lütfen konu ve açıklama alanlarını doldurun.");
            return;
        }

        setIsSubmitting(true);
        try {
            await createDestekTalebi({
                konu: yeniKonu,
                kategori: yeniKategori,
                oncelik: yeniOncelik,
                aciklama: yeniAciklama
            });
            toast.success("Destek talebiniz başarıyla oluşturuldu.");
            setIsCreateOpen(false);

            // Formu sıfırla
            setYeniKonu('');
            setYeniKategori('Hata Bildirimi');
            setYeniOncelik('Normal');
            setYeniAciklama('');

            fetchTalepler();
        } catch (err) {
            toast.error(hataMetni(err, 'Talep oluşturulamadı'));
        } finally {
            setIsSubmitting(false);
        }
    };

    // --- Talep Güncelleme (Sadece Admin) ---
    const handleUpdateTalep = async () => {
        if (!selectedTalep || !isAdmin) return;

        setIsSubmitting(true);
        try {
            await updateDestekTalebi(selectedTalep.id, {
                durum: updateDurum,
                admin_cevabi: cevapMetni
            });

            toast.success("Talep durumu güncellendi.");
            setIsDetailOpen(false);
            fetchTalepler();
        } catch (err) {
            toast.error(hataMetni(err, 'Güncelleme başarısız'));
        } finally {
            setIsSubmitting(false);
        }
    };

    // --- Detay Modalı Açma ---
    const openDetailModal = (talep) => {
        setSelectedTalep(talep);
        setCevapMetni(talep.admin_cevabi || '');
        setUpdateDurum(talep.durum);
        setIsDetailOpen(true);
    };

    // --- Filtreleme Performans Optimizasyonu ---
    const filteredTalepler = useMemo(() => {
        return talepler.filter(t =>
            t.konu.toLowerCase().includes(aramaGirdisi.toLowerCase()) ||
            t.kullanici?.ad_soyad?.toLowerCase().includes(aramaGirdisi.toLowerCase())
        );
    }, [talepler, aramaGirdisi]);

    // Modal açıldığında arkaplan kaydırmasını engelle
    useEffect(() => {
        if (isCreateOpen || isDetailOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [isCreateOpen, isDetailOpen]);

    return (
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-8 animate-in fade-in duration-500 relative z-10 min-h-screen pb-32">
            
            {/* BAŞLIK VE EYLEMLER - Modern Glassmorphism Card */}
            <div className="relative overflow-hidden bg-white/70 backdrop-blur-xl border border-slate-200/60 shadow-sm p-6 sm:p-8 rounded-[32px] flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                
                {/* Dekoratif Arkaplan Gradient */}
                <div className="absolute -right-32 -top-32 w-96 h-96 bg-indigo-500/10 rounded-full blur-[80px] pointer-events-none" />
                <div className="absolute -left-32 -bottom-32 w-96 h-96 bg-emerald-500/10 rounded-full blur-[80px] pointer-events-none" />

                <div className="flex items-center gap-4 sm:gap-6 relative z-10">
                    <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center shadow-lg shadow-slate-900/20 shrink-0 transform transition-transform hover:scale-105 duration-300">
                        <HelpCircle className="w-7 h-7 sm:w-8 sm:h-8 text-indigo-400 stroke-[2.5]" />
                    </div>
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight leading-none mb-1.5">Destek Masası</h1>
                        <p className="text-sm font-medium text-slate-500/90">Sistem yardım ve talep yönetimi</p>
                    </div>
                </div>

                <div className="relative z-10 flex flex-row gap-3 w-full sm:w-auto mt-2 sm:mt-0">
                    <button
                        onClick={fetchTalepler}
                        disabled={loading}
                        className="flex items-center justify-center gap-2.5 px-4 h-12 bg-white hover:bg-slate-50 text-slate-700 rounded-xl transition-all border border-slate-200 font-bold text-sm active:scale-95 shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:opacity-50 disabled:active:scale-100 flex-1 sm:flex-none"
                        aria-label="Talepleri Yenile"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        <span className="hidden sm:inline">Yenile</span>
                    </button>

                    <button
                        onClick={() => setIsCreateOpen(true)}
                        className="flex items-center justify-center gap-2.5 px-5 h-12 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl transition-all shadow-md shadow-indigo-600/20 font-bold text-sm active:scale-95 group focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-600 flex-[2] sm:flex-none"
                    >
                        <Plus className="w-5 h-5 transition-transform duration-300 group-hover:rotate-90" />
                        Yeni Talep
                    </button>
                </div>
            </div>

            {/* FİLTRELER - Kompakt ve Odaklı Grid */}
            <div className="bg-white/50 backdrop-blur-md p-3 rounded-2xl border border-slate-200/60 shadow-sm flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1 group">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-500 transition-colors duration-200" />
                    <input
                        type="text"
                        placeholder="Konu veya İsimle Ara..."
                        className="w-full pl-11 pr-4 h-12 bg-white/60 sm:bg-transparent border border-slate-200/60 sm:border-transparent rounded-xl focus:outline-none focus:bg-white focus:ring-2 focus:ring-indigo-500/20 text-sm font-semibold text-slate-800 placeholder:text-slate-400 transition-all shadow-sm sm:shadow-none"
                        value={aramaGirdisi}
                        onChange={(e) => setAramaGirdisi(e.target.value)}
                    />
                </div>

                <div className="hidden sm:block w-px h-8 bg-slate-200 self-center" />

                <div className="relative w-full sm:w-56 group">
                    <Filter className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                    <select
                        className="w-full pl-11 pr-10 h-12 bg-white/60 sm:bg-transparent border border-slate-200/60 sm:border-transparent rounded-xl focus:outline-none focus:bg-white focus:ring-2 focus:ring-indigo-500/20 text-sm font-bold text-slate-700 cursor-pointer appearance-none transition-all shadow-sm sm:shadow-none"
                        value={filtreDurum}
                        onChange={(e) => setFiltreDurum(e.target.value)}
                    >
                        <option value="">Tüm Durumlar</option>
                        <option value="Açık">Açık</option>
                        <option value="İşlemde">İşlemde</option>
                        <option value="Çözüldü">Çözüldü</option>
                    </select>
                    <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
            </div>

            {/* LİSTE GÖRÜNÜMÜ - Modern Kartlar */}
            <div className="min-h-[400px]">
                {loading ? (
                    <div className="flex flex-col items-center justify-center p-20 text-slate-400 space-y-5">
                        <div className="relative">
                            <div className="w-12 h-12 rounded-full border-4 border-slate-100 animate-pulse" />
                            <div className="absolute top-0 left-0 w-12 h-12 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin" />
                        </div>
                        <p className="text-sm font-bold uppercase tracking-widest text-slate-400">Veriler Yükleniyor</p>
                    </div>
                ) : filteredTalepler.length === 0 ? (
                    <div className="bg-white/50 backdrop-blur-md rounded-[32px] p-16 sm:p-24 flex flex-col items-center text-center border border-slate-200/60 shadow-sm animate-in zoom-in-95 duration-500">
                        <div className="w-24 h-24 bg-indigo-50 rounded-[2rem] flex items-center justify-center mb-6 rotate-3">
                            <MessageCircle className="w-10 h-10 text-indigo-400 -rotate-3" />
                        </div>
                        <h3 className="text-xl sm:text-2xl font-black text-slate-800 mb-2">Buralar oldukça sakin.</h3>
                        <p className="text-sm sm:text-base font-medium text-slate-500 max-w-sm">
                            Kriterlerinize uygun destek talebi bulunamadı veya henüz hiç talep oluşturulmamış.
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                        {filteredTalepler.map((talep) => (
                            <div
                                key={talep.id}
                                onClick={() => openDetailModal(talep)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(e) => e.key === 'Enter' && openDetailModal(talep)}
                                className="group bg-white p-5 sm:p-6 rounded-[24px] border border-slate-200/80 hover:border-indigo-300 hover:shadow-xl hover:shadow-indigo-500/5 transition-all duration-300 cursor-pointer flex flex-col relative overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                            >
                                {/* Durum Renk Göstergesi */}
                                <div className={`absolute top-0 left-0 bottom-0 w-1.5 transition-colors duration-300 ${
                                    talep.durum === 'Açık' ? 'bg-blue-500' :
                                    talep.durum === 'Çözüldü' ? 'bg-emerald-500' : 'bg-amber-500'
                                }`} />

                                <div className="flex justify-between items-start mb-4 pl-2">
                                    {getOncelikBadge(talep.oncelik)}
                                    {getDurumBadge(talep.durum)}
                                </div>

                                <h3 className="font-bold text-slate-900 text-base sm:text-lg leading-tight mb-2 pl-2 group-hover:text-indigo-600 transition-colors line-clamp-1">
                                    {talep.konu}
                                </h3>

                                <p className="text-sm text-slate-500/90 mb-5 pl-2 font-medium line-clamp-2">
                                    {talep.aciklama}
                                </p>

                                <div className="mt-auto pt-4 border-t border-slate-100 flex flex-row items-center justify-between pl-2 gap-3">
                                    <div className="flex items-center gap-2.5 min-w-0">
                                        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center font-bold text-xs flex-shrink-0 uppercase border border-slate-200">
                                            {talep.kullanici?.ad_soyad?.charAt(0) || '?'}
                                        </div>
                                        <span className="text-xs sm:text-sm font-bold text-slate-600 truncate">
                                            {talep.kullanici?.ad_soyad || 'Bilinmiyor'}
                                        </span>
                                    </div>

                                    <div className="flex items-center gap-1.5 text-slate-400 flex-shrink-0">
                                        <Clock className="w-3.5 h-3.5" />
                                        <span className="text-[11px] sm:text-xs font-semibold">
                                            {new Date(talep.olusturma_tarihi).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* ==============================
                YENİ TALEP OLUŞTURMA MODALI
            ============================== */}
            {isCreateOpen && (
                <div 
                    className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center bg-slate-900/40 backdrop-blur-sm transition-opacity duration-300 sm:p-4"
                    onClick={() => setIsCreateOpen(false)}
                >
                    <div 
                        className="bg-white w-full sm:max-w-xl rounded-t-[28px] sm:rounded-[28px] shadow-2xl flex flex-col max-h-[90vh] sm:max-h-[85vh] animate-in slide-in-from-bottom-full sm:slide-in-from-bottom-0 sm:zoom-in-95 duration-300" 
                        onClick={(e) => e.stopPropagation()}
                        role="dialog"
                        aria-modal="true"
                    >
                        {/* Sabit Header (Sticky) */}
                        <div className="shrink-0 bg-white rounded-t-[28px] px-5 py-4 border-b border-slate-100 flex items-center justify-between z-10">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-indigo-50 rounded-full flex items-center justify-center text-indigo-600">
                                    <Plus className="w-5 h-5" />
                                </div>
                                <h2 className="text-lg font-black text-slate-800">
                                    Yeni Destek Talebi
                                </h2>
                            </div>
                            <button 
                                onClick={() => setIsCreateOpen(false)} 
                                className="w-10 h-10 flex items-center justify-center rounded-full bg-slate-50 text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                                aria-label="Kapat"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Kaydırılabilir Form Alanı (Scrollable Body) */}
                        <form onSubmit={handleCreateSubmit} className="flex flex-col flex-1 overflow-hidden">
                            <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5 bg-slate-50/50 custom-scrollbar">
                                <div className="space-y-2">
                                    <label htmlFor="yeniKonu" className="text-[13px] font-bold text-slate-700 block">Konu Başlığı</label>
                                    <input
                                        id="yeniKonu"
                                        type="text"
                                        autoFocus
                                        required
                                        placeholder="Kısaca sorunu/ihtiyacı yazın..."
                                        className="w-full h-12 px-4 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 placeholder:text-slate-400 transition-all font-semibold text-[15px] shadow-sm"
                                        value={yeniKonu}
                                        onChange={e => setYeniKonu(e.target.value)}
                                    />
                                </div>

                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                                    <div className="space-y-2 relative group">
                                        <label htmlFor="yeniKategori" className="text-[13px] font-bold text-slate-700 block">Kategori</label>
                                        <div className="relative">
                                            <select
                                                id="yeniKategori"
                                                className="w-full h-12 px-4 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 font-semibold text-[15px] shadow-sm appearance-none cursor-pointer"
                                                value={yeniKategori}
                                                onChange={e => setYeniKategori(e.target.value)}
                                            >
                                                <option>Hata Bildirimi</option>
                                                <option>Donanım Talebi</option>
                                                <option>Yazılım İsteği</option>
                                                <option>Bilgi Alma</option>
                                                <option>Diğer</option>
                                            </select>
                                            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none group-focus-within:text-indigo-500" />
                                        </div>
                                    </div>

                                    <div className="space-y-2 relative group">
                                        <label htmlFor="yeniOncelik" className="text-[13px] font-bold text-slate-700 block">Öncelik Derecesi</label>
                                        <div className="relative">
                                            <select
                                                id="yeniOncelik"
                                                className="w-full h-12 px-4 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 font-semibold text-[15px] shadow-sm appearance-none cursor-pointer"
                                                value={yeniOncelik}
                                                onChange={e => setYeniOncelik(e.target.value)}
                                            >
                                                <option>Düşük</option>
                                                <option>Normal</option>
                                                <option>Yüksek</option>
                                            </select>
                                            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none group-focus-within:text-indigo-500" />
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-2 flex-1">
                                    <label htmlFor="yeniAciklama" className="text-[13px] font-bold text-slate-700 block">Detaylı Açıklama</label>
                                    <textarea
                                        id="yeniAciklama"
                                        required
                                        rows={4}
                                        placeholder="Yaşadığınız sorunu veya talebinizi detaylı olarak açıklayın..."
                                        className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 placeholder:text-slate-400 transition-all font-medium resize-none text-[15px] shadow-sm min-h-[120px]"
                                        value={yeniAciklama}
                                        onChange={e => setYeniAciklama(e.target.value)}
                                    />
                                </div>
                            </div>

                            {/* Sabit Footer (Sticky) - Mobilde home bar'a çarpmaması için safe-area padding kullanıldı */}
                            <div className="shrink-0 bg-white border-t border-slate-100 px-5 py-4 pb-[calc(1rem+env(safe-area-inset-bottom))] flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => setIsCreateOpen(false)}
                                    className="flex-1 sm:flex-none sm:w-32 h-12 rounded-xl font-bold text-[15px] text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                                >
                                    İptal
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="flex-[2] sm:flex-none sm:px-8 h-12 rounded-xl font-bold text-[15px] text-white bg-indigo-600 hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2 shadow-md shadow-indigo-500/20 disabled:opacity-70 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-600"
                                >
                                    {isSubmitting ? <RefreshCw className="w-5 h-5 animate-spin" /> : <CheckCircle2 className="w-5 h-5" />}
                                    Talebi Gönder
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* ==============================
                TALEP DETAY / CEVAP MODALI
            ============================== */}
            {isDetailOpen && selectedTalep && (
                <div 
                    className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center bg-slate-900/40 backdrop-blur-sm transition-opacity duration-300 sm:p-4"
                    onClick={() => setIsDetailOpen(false)}
                >
                    <div 
                        className="bg-white w-full sm:max-w-2xl rounded-t-[28px] sm:rounded-[28px] shadow-2xl flex flex-col max-h-[95vh] sm:max-h-[90vh] animate-in slide-in-from-bottom-full sm:slide-in-from-bottom-0 sm:zoom-in-95 duration-300" 
                        onClick={(e) => e.stopPropagation()}
                        role="dialog"
                        aria-modal="true"
                    >
                        {/* Sabit Header */}
                        <div className="shrink-0 bg-white rounded-t-[28px] px-5 py-4 border-b border-slate-100 flex items-center justify-between z-10">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center text-slate-600">
                                    <Tag className="w-5 h-5" />
                                </div>
                                <div>
                                    <h2 className="text-[16px] sm:text-lg font-black text-slate-800 leading-none mb-1 line-clamp-1 pr-4">
                                        {selectedTalep.konu}
                                    </h2>
                                    <p className="text-[12px] font-semibold text-slate-500">Talep #{selectedTalep.id}</p>
                                </div>
                            </div>
                            <button 
                                onClick={() => setIsDetailOpen(false)} 
                                className="shrink-0 w-10 h-10 flex items-center justify-center rounded-full bg-slate-50 text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Kaydırılabilir İçerik (Timeline/Mesaj Görünümü) */}
                        <div className="flex-1 overflow-y-auto bg-slate-50 p-4 sm:p-6 space-y-6 custom-scrollbar">
                            
                            {/* Talep ve Etiketler */}
                            <div className="flex gap-2 mb-2">
                                {getOncelikBadge(selectedTalep.oncelik)}
                                {getDurumBadge(selectedTalep.durum)}
                            </div>

                            {/* Kullanıcı Mesajı */}
                            <div className="flex gap-3 sm:gap-4">
                                <div className="shrink-0 mt-1">
                                    <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm uppercase shadow-sm">
                                        {selectedTalep.kullanici?.ad_soyad?.charAt(0) || '?'}
                                    </div>
                                </div>
                                <div className="flex-1 space-y-1">
                                    <div className="flex items-baseline justify-between">
                                        <span className="font-bold text-[14px] text-slate-800">{selectedTalep.kullanici?.ad_soyad || 'Bilinmiyor'}</span>
                                        <span className="text-[11px] font-semibold text-slate-400">
                                            {new Date(selectedTalep.olusturma_tarihi).toLocaleString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute:'2-digit' })}
                                        </span>
                                    </div>
                                    <div className="bg-white p-4 rounded-2xl rounded-tl-sm border border-slate-200/60 shadow-sm text-[14px] text-slate-700 leading-relaxed font-medium whitespace-pre-wrap">
                                        {selectedTalep.aciklama}
                                    </div>
                                </div>
                            </div>

                            {/* Sistem / Admin Cevabı */}
                            <div className="flex gap-3 sm:gap-4 pt-2">
                                <div className="shrink-0 mt-1">
                                    <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-sm shadow-sm">
                                        <HelpCircle className="w-5 h-5" />
                                    </div>
                                </div>
                                <div className="flex-1 space-y-1">
                                    <div className="flex items-baseline">
                                        <span className="font-bold text-[14px] text-slate-800">Sistem Yönetimi</span>
                                    </div>
                                    
                                    {!isAdmin && !selectedTalep.admin_cevabi ? (
                                        <div className="bg-transparent border-2 border-dashed border-slate-200 p-4 rounded-2xl rounded-tl-sm text-[14px] text-slate-500 font-medium flex items-center gap-2">
                                            <Clock className="w-4 h-4" /> Talep inceleniyor, henüz yanıtlanmadı.
                                        </div>
                                    ) : (
                                        isAdmin ? (
                                            /* Admin İse: Düzenleme Alanı */
                                            <div className="bg-white p-4 rounded-2xl rounded-tl-sm border border-slate-200 shadow-sm space-y-3">
                                                <textarea
                                                    rows={4}
                                                    placeholder="Kullanıcıya iletilecek yanıtı buraya yazın..."
                                                    className="w-full h-full min-h-[100px] p-0 bg-transparent border-none focus:ring-0 text-slate-800 placeholder:text-slate-400 resize-none text-[14px] font-medium"
                                                    value={cevapMetni}
                                                    onChange={e => setCevapMetni(e.target.value)}
                                                />
                                            </div>
                                        ) : (
                                            /* Kullanıcı İse: Sadece Görüntüleme */
                                            selectedTalep.admin_cevabi && (
                                                <div className="bg-emerald-50 p-4 rounded-2xl rounded-tl-sm border border-emerald-100 text-[14px] text-slate-800 leading-relaxed font-medium whitespace-pre-wrap">
                                                    {selectedTalep.admin_cevabi}
                                                </div>
                                            )
                                        )
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Admin Kontrol Paneli (Sadece Adminde Görünür ve Alta Sabittir) */}
                        {isAdmin && (
                            <div className="shrink-0 bg-white border-t border-slate-100 p-4 sm:px-6 sm:py-4 pb-[calc(1rem+env(safe-area-inset-bottom))]">
                                <div className="flex flex-col sm:flex-row gap-3">
                                    <div className="flex-1 relative">
                                        <select
                                            className="w-full h-12 pl-4 pr-10 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-[14px] font-bold cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500/20 appearance-none"
                                            value={updateDurum}
                                            onChange={e => setUpdateDurum(e.target.value)}
                                        >
                                            <option>Açık</option>
                                            <option>İşlemde</option>
                                            <option>Çözüldü</option>
                                        </select>
                                        <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                                    </div>
                                    
                                    <button
                                        onClick={handleUpdateTalep}
                                        disabled={isSubmitting}
                                        className="flex-[2] h-12 rounded-xl font-bold text-[15px] text-white bg-indigo-600 hover:bg-indigo-700 transition-all flex items-center justify-center gap-2 shadow-md shadow-indigo-500/20 disabled:opacity-70 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-600"
                                    >
                                        {isSubmitting ? <RefreshCw className="w-5 h-5 animate-spin" /> : <MessageCircle className="w-5 h-5" />}
                                        Yanıtı ve Durumu Kaydet
                                    </button>
                                </div>
                            </div>
                        )}
                        
                        {/* Admin değilse ve alt çentik boşluğu vermek gerekirse (opsiyonel footer padding) */}
                        {!isAdmin && (
                             <div className="shrink-0 pb-[env(safe-area-inset-bottom)] bg-slate-50"></div>
                        )}
                    </div>
                </div>
            )}
            
            {/* CSS for custom scrollbar (global veya index.css dosyanızda ekleyebilirsiniz, burada class olarak bırakıldı) */}
            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background-color: #cbd5e1;
                    border-radius: 20px;
                }
            `}</style>
        </div>
    );
}