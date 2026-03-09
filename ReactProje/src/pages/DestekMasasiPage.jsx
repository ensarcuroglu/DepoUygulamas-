import React, { useState, useEffect } from 'react';
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
    AlertCircle,
    CheckCircle2,
    X,
    MessageCircle,
    Eye,
    AlertTriangle,
    UserCircle
} from 'lucide-react';

// ========================
// YARDIMCI BİLEŞENLER (BADGES)
// ========================

const getDurumBadge = (durum) => {
    const styles = {
        'Açık': 'bg-blue-50 text-blue-600 border-blue-200',
        'İşlemde': 'bg-amber-50 text-amber-600 border-amber-200',
        'Çözüldü': 'bg-emerald-50 text-emerald-600 border-emerald-200'
    };
    const currentStyle = styles[durum] || 'bg-slate-50 text-slate-500 border-slate-200';

    let icon = <Clock className="w-3.5 h-3.5" />;
    if (durum === 'İşlemde') icon = <RefreshCw className="w-3.5 h-3.5 animate-spin-slow" />;
    if (durum === 'Çözüldü') icon = <CheckCircle2 className="w-3.5 h-3.5" />;

    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${currentStyle} shadow-sm backdrop-blur-sm`}>
            {icon}
            {durum}
        </span>
    );
};

const getOncelikBadge = (oncelik) => {
    const styles = {
        'Düşük': 'bg-slate-100 text-slate-500 border border-slate-200',
        'Normal': 'bg-indigo-50 text-indigo-600 border border-indigo-100',
        'Yüksek': 'bg-rose-50 flex text-rose-600 border border-rose-200 shadow-sm'
    };
    const currentStyle = styles[oncelik] || 'bg-slate-100 text-slate-500 border border-slate-200';

    return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold uppercase tracking-wider ${currentStyle}`}>
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
            toast.error("Talepler yüklenirken bir sorun oluştu.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTalepler();
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

    // --- Filtreleme ---
    const filteredTalepler = talepler.filter(t =>
        t.konu.toLowerCase().includes(aramaGirdisi.toLowerCase()) ||
        t.kullanici?.ad_soyad?.toLowerCase().includes(aramaGirdisi.toLowerCase())
    );

    return (
        <div className="max-w-[1400px] mx-auto p-4 sm:p-6 pb-24 space-y-6 animate-fade-in relative z-10">

            {/* BAŞLIK VE EYLEMLER - Açık Tema Mobile First Tasarım */}
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 sm:gap-4 bg-white p-5 sm:p-8 rounded-[24px] md:rounded-[32px] border border-slate-100 shadow-sm relative overflow-hidden">
                {/* Dekoratif Arkaplan */}
                <div className="absolute -right-20 -top-20 w-64 h-64 bg-slate-50 rounded-full blur-3xl opacity-50 pointer-events-none" />

                <div className="flex items-center gap-3 md:gap-5 relative z-10">
                    <div className="w-12 h-12 md:w-16 md:h-16 rounded-xl md:rounded-2xl bg-slate-900 flex items-center justify-center flex-shrink-0 shadow-lg shadow-slate-900/20">
                        <HelpCircle className="w-6 h-6 md:w-8 md:h-8 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl sm:text-[28px] font-black text-slate-800 tracking-tight leading-none mb-1">Destek Masası</h1>
                        <p className="text-[12px] sm:text-[14px] font-medium text-slate-500">Sistem yardım ve talep yönetimi</p>
                    </div>
                </div>

                <div className="relative z-10 flex gap-2 w-full sm:w-auto mt-2 sm:mt-0">
                    <button
                        onClick={fetchTalepler}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 h-[42px] sm:h-[48px] bg-white hover:bg-slate-50 text-slate-700 rounded-xl transition-all border border-slate-200 font-bold text-[13px] sm:text-sm active:scale-95 shadow-sm"
                        title="Yenile"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        <span className="hidden sm:inline">Yenile</span>
                    </button>

                    <button
                        onClick={() => setIsCreateOpen(true)}
                        className="flex-[2] sm:flex-none flex items-center justify-center gap-2 px-4 h-[42px] sm:h-[48px] bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl transition-all shadow-sm font-bold text-[13px] sm:text-sm active:scale-95 group"
                    >
                        <Plus className="w-4 h-4 sm:w-5 sm:h-5 group-hover:rotate-90 transition-transform" />
                        Yeni Talep
                    </button>
                </div>
            </div>

            {/* FİLTRELER - Açık Tema Kompakt Grid */}
            <div className="bg-white p-2.5 sm:p-3 rounded-2xl border border-slate-100 shadow-sm flex flex-col sm:flex-row gap-2.5 sm:gap-3">
                <div className="relative flex-1 group">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                    <input
                        type="text"
                        placeholder="Konu veya İsimle Ara..."
                        className="w-full pl-9 pr-3 h-10 sm:h-12 bg-slate-50 sm:bg-transparent border border-slate-200 sm:border-transparent rounded-xl focus:outline-none focus:bg-white text-[13px] sm:text-[14px] font-semibold text-slate-800 placeholder:text-slate-400 transition-colors"
                        value={aramaGirdisi}
                        onChange={(e) => setAramaGirdisi(e.target.value)}
                    />
                </div>

                <div className="hidden sm:block w-px h-8 bg-slate-200 self-center" />

                <div className="relative w-full sm:w-48">
                    <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <select
                        className="w-full pl-9 pr-8 h-10 sm:h-12 bg-slate-50 sm:bg-transparent border border-slate-200 sm:border-transparent rounded-xl focus:outline-none focus:bg-white text-[13px] sm:text-[14px] font-bold text-slate-700 cursor-pointer appearance-none transition-colors"
                        value={filtreDurum}
                        onChange={(e) => setFiltreDurum(e.target.value)}
                    >
                        <option value="">Tüm Durumlar</option>
                        <option value="Açık">Açık</option>
                        <option value="İşlemde">İşlemde</option>
                        <option value="Çözüldü">Çözüldü</option>
                    </select>
                </div>
            </div>

            {/* LİSTE GÖRÜNÜMÜ - Açık Tema Kartlar */}
            <div className="min-h-[400px]">
                {loading ? (
                    <div className="flex flex-col items-center justify-center p-12 text-slate-400 space-y-4">
                        <RefreshCw className="w-8 h-8 animate-spin text-slate-300" />
                        <p className="text-sm font-bold uppercase tracking-widest animate-pulse">Talepler yükleniyor...</p>
                    </div>
                ) : filteredTalepler.length === 0 ? (
                    <div className="bg-white rounded-3xl p-16 flex flex-col items-center text-center border border-slate-100 shadow-sm">
                        <div className="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center mb-6">
                            <MessageCircle className="w-12 h-12 text-slate-300" />
                        </div>
                        <h3 className="text-xl font-black text-slate-800 mb-2">Buralar sakin...</h3>
                        <p className="text-sm font-medium text-slate-500">Kriterlerinize uygun hiç talep bulunamadı.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 sm:gap-4">
                        {filteredTalepler.map((talep) => (
                            <div
                                key={talep.id}
                                onClick={() => openDetailModal(talep)}
                                className="group bg-white p-4 sm:p-5 rounded-xl md:rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all duration-300 cursor-pointer flex flex-col relative overflow-hidden"
                            >
                                {/* Sol taraftaki ince dekoratif çizgi - Açık tema versiyon */}
                                <div className={`absolute top-0 left-0 bottom-0 w-1 transition-colors ${talep.durum === 'Açık' ? 'bg-blue-500' :
                                    talep.durum === 'Çözüldü' ? 'bg-emerald-500' : 'bg-amber-500'
                                    }`} />

                                <div className="flex justify-between items-start mb-3 pl-2">
                                    <div className="scale-90 sm:scale-100 origin-top-left">{getOncelikBadge(talep.oncelik)}</div>
                                    <div className="scale-90 sm:scale-100 origin-top-right">{getDurumBadge(talep.durum)}</div>
                                </div>

                                <h3 className="font-bold text-slate-800 text-[14px] sm:text-[16px] leading-snug mb-1.5 pl-2 group-hover:text-indigo-600 transition-colors line-clamp-1">
                                    {talep.konu}
                                </h3>

                                <p className="text-[12px] sm:text-[13px] text-slate-500 mb-4 pl-2 font-medium line-clamp-2">
                                    {talep.aciklama}
                                </p>

                                <div className="mt-auto pt-3 sm:pt-4 border-t border-slate-100 flex flex-row items-center justify-between pl-2 gap-2">
                                    <div className="flex items-center gap-2 min-w-0">
                                        <div className="w-6 h-6 sm:w-7 sm:h-7 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center font-bold text-[10px] sm:text-xs flex-shrink-0">
                                            {talep.kullanici?.ad_soyad?.charAt(0) || '?'}
                                        </div>
                                        <span className="text-[11px] sm:text-xs font-bold text-slate-600 truncate max-w-[80px] sm:max-w-full">
                                            {talep.kullanici?.ad_soyad || 'Bilinmiyor'}
                                        </span>
                                    </div>

                                    <div className="flex items-center gap-1.5 text-slate-400 flex-shrink-0">
                                        <Clock className="w-3.5 h-3.5" />
                                        <span className="text-[10px] sm:text-xs font-semibold">
                                            {new Date(talep.olusturma_tarihi).toLocaleDateString('tr-TR')}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* ==============================
          YENİ TALEP OLUŞTURMA MODALI - Açık Tema
      ============================== */}
            {isCreateOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 md:p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
                    <div className="bg-white border border-slate-100 w-full max-w-lg rounded-[24px] md:rounded-[32px] shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-in zoom-in-95 duration-200" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-between p-4 md:p-6 pb-3 md:pb-4 border-b border-slate-100 shadow-sm z-10">
                            <h2 className="text-base sm:text-lg font-black text-slate-800 flex items-center gap-2">
                                <Plus className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-500" />
                                Yeni Destek Talebi
                            </h2>
                            <button onClick={() => setIsCreateOpen(false)} className="w-8 h-8 md:w-10 md:h-10 flex items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-700 transition-colors">
                                <X className="w-4 h-4 sm:w-5 sm:h-5" />
                            </button>
                        </div>

                        <form onSubmit={handleCreateSubmit} className="p-4 md:p-6 overflow-y-auto custom-scrollbar flex-1 space-y-4 sm:space-y-5 bg-slate-50/50">

                            <div className="space-y-1.5 sm:space-y-2">
                                <label className="text-[11px] sm:text-xs font-bold text-slate-600 uppercase tracking-wider pl-1">Konu Başlığı</label>
                                <input
                                    type="text"
                                    autoFocus
                                    required
                                    placeholder="Kısaca sorunu/ihtiyacı yazın..."
                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 placeholder:text-slate-400 transition-all font-semibold text-[13px] sm:text-[14px] shadow-sm"
                                    value={yeniKonu}
                                    onChange={e => setYeniKonu(e.target.value)}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-3 sm:gap-4">
                                <div className="space-y-1.5 sm:space-y-2">
                                    <label className="text-[11px] sm:text-xs font-bold text-slate-600 uppercase tracking-wider pl-1">Kategori</label>
                                    <select
                                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 font-semibold text-[13px] sm:text-[14px] shadow-sm appearance-none cursor-pointer"
                                        value={yeniKategori}
                                        onChange={e => setYeniKategori(e.target.value)}
                                    >
                                        <option>Hata Bildirimi</option>
                                        <option>Donanım Talebi</option>
                                        <option>Yazılım İsteği</option>
                                        <option>Bilgi Alma</option>
                                        <option>Diğer</option>
                                    </select>
                                </div>

                                <div className="space-y-1.5 sm:space-y-2">
                                    <label className="text-[11px] sm:text-xs font-bold text-slate-600 uppercase tracking-wider pl-1">Öncelik Derecesi</label>
                                    <select
                                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 font-semibold text-[13px] sm:text-[14px] shadow-sm appearance-none cursor-pointer"
                                        value={yeniOncelik}
                                        onChange={e => setYeniOncelik(e.target.value)}
                                    >
                                        <option>Düşük</option>
                                        <option>Normal</option>
                                        <option>Yüksek</option>
                                    </select>
                                </div>
                            </div>

                            <div className="space-y-1.5 sm:space-y-2">
                                <label className="text-[11px] sm:text-xs font-bold text-slate-600 uppercase tracking-wider pl-1">Detaylı Açıklama</label>
                                <textarea
                                    required
                                    rows={4}
                                    placeholder="Yaşadığınız sorunu veya talebinizi detaylı olarak açıklayın..."
                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 placeholder:text-slate-400 transition-all font-medium resize-none text-[13px] sm:text-[14px] shadow-sm"
                                    value={yeniAciklama}
                                    onChange={e => setYeniAciklama(e.target.value)}
                                />
                            </div>

                            <div className="pt-4 sm:pt-6 flex justify-end gap-2.5 sm:gap-3">
                                <button
                                    type="button"
                                    onClick={() => setIsCreateOpen(false)}
                                    className="px-4 sm:px-5 py-2.5 sm:py-3 rounded-xl font-bold text-[13px] sm:text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
                                >
                                    İptal
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="px-5 sm:px-6 py-2.5 sm:py-3 rounded-xl font-bold text-[13px] sm:text-sm text-white bg-indigo-600 hover:bg-indigo-700 transition-colors flex items-center gap-2 shadow-md shadow-indigo-500/20 disabled:opacity-70 disabled:cursor-not-allowed"
                                >
                                    {isSubmitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                                    Talebi Gönder
                                </button>
                            </div>

                        </form>
                    </div>
                </div>
            )}

            {/* ==============================
          TALEP DETAY / CEVAP MODALI - Açık Tema
      ============================== */}
            {isDetailOpen && selectedTalep && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 md:p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
                    <div className="bg-white border border-slate-100 w-full max-w-2xl rounded-[24px] md:rounded-[32px] shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-in zoom-in-95 duration-200" onClick={(e) => e.stopPropagation()}>

                        {/* Header */}
                        <div className="flex items-center justify-between p-4 md:p-6 pb-3 md:pb-4 border-b border-slate-100 shadow-sm z-10">
                            <div className="flex gap-3 md:gap-4 items-center">
                                <div className="p-2 md:p-3 bg-indigo-50 rounded-lg md:rounded-xl"><Eye className="w-5 h-5 md:w-6 md:h-6 text-indigo-500" /></div>
                                <div>
                                    <h2 className="text-[14px] md:text-[18px] font-black text-slate-900 leading-none mb-1">Talep Detayı</h2>
                                    <p className="text-[12px] md:text-[13px] font-semibold text-slate-500">ID: #{selectedTalep.id}</p>
                                </div>
                            </div>
                            <button onClick={() => setIsDetailOpen(false)} className="w-8 h-8 md:w-10 md:h-10 flex items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-rose-100 hover:text-rose-600 transition-colors">
                                <X className="w-4 h-4 md:w-5 md:h-5" />
                            </button>
                        </div>

                        <div className="p-4 md:p-6 overflow-y-auto custom-scrollbar flex-1 bg-slate-50">

                            {/* Talep Özeti */}
                            <div className="bg-white p-4 md:p-6 rounded-xl md:rounded-2xl border border-slate-200 shadow-sm mb-4 md:mb-6 space-y-4">
                                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 sm:gap-4">
                                    <h3 className="text-lg md:text-xl font-black text-slate-800 leading-tight">
                                        {selectedTalep.konu}
                                    </h3>
                                    <div className="flex gap-2 flex-shrink-0 self-start">
                                        <div className="origin-left sm:origin-center">{getOncelikBadge(selectedTalep.oncelik)}</div>
                                        <div className="origin-left sm:origin-center">{getDurumBadge(selectedTalep.durum)}</div>
                                    </div>
                                </div>

                                <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-[12px] md:text-[13px] font-semibold text-slate-500">
                                    <span className="flex items-center gap-1.5 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100">
                                        <UserCircle className="w-4 h-4 text-slate-400" /> {selectedTalep.kullanici?.ad_soyad || 'Bilinmiyor'}
                                    </span>
                                    <span className="flex items-center gap-1.5 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100">
                                        🏷️ {selectedTalep.kategori}
                                    </span>
                                    <span className="flex items-center gap-1.5 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100">
                                        <Clock className="w-4 h-4 text-slate-400" /> {new Date(selectedTalep.olusturma_tarihi).toLocaleString('tr-TR')}
                                    </span>
                                </div>

                                <div className="pt-2 border-t border-slate-100/80">
                                    <p className="text-[13px] md:text-[15px] text-slate-700 whitespace-pre-wrap leading-relaxed font-medium">{selectedTalep.aciklama}</p>
                                </div>
                            </div>

                            {/* Chat / Cevap Alanı */}
                            <div className="space-y-3 sm:space-y-4">
                                <div className="flex items-center gap-2 mb-2 px-1">
                                    <div className="w-2 h-2 rounded-full bg-indigo-500" />
                                    <span className="text-[11px] md:text-[12px] font-black text-slate-600 uppercase tracking-wider">Sistem Yönetimi & Yanıt</span>
                                </div>

                                {!isAdmin && !selectedTalep.admin_cevabi && (
                                    <div className="bg-white p-6 rounded-2xl border border-slate-200 border-dashed text-center flex flex-col items-center">
                                        <Clock className="w-8 h-8 text-slate-300 mb-2" />
                                        <p className="text-slate-500 text-[13px] sm:text-sm font-semibold">Destek ekibi henüz bir yanıt vermedi. Lütfen bekleyiniz.</p>
                                    </div>
                                )}

                                {/* Kullanıcı Sadece Görüntüler, Admin Düzenleyebilir */}
                                {isAdmin ? (
                                    <div className="bg-white p-4 md:p-5 rounded-xl md:rounded-2xl border border-slate-200 shadow-sm space-y-4">
                                        <textarea
                                            rows={3}
                                            placeholder="Kullanıcıya iletilecek yanıtı buraya yazın..."
                                            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 placeholder:text-slate-400 transition-all resize-none text-[13px] sm:text-sm font-medium"
                                            value={cevapMetni}
                                            onChange={e => setCevapMetni(e.target.value)}
                                        />

                                        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-4 pt-2 border-t border-slate-100">
                                            <div className="flex items-center gap-3 w-full sm:w-auto">
                                                <label className="text-[12px] sm:text-[13px] font-bold text-slate-500 whitespace-nowrap">Durumu Güncelle:</label>
                                                <select
                                                    className="w-full sm:w-40 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 text-[13px] sm:text-sm cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-semibold appearance-none"
                                                    value={updateDurum}
                                                    onChange={e => setUpdateDurum(e.target.value)}
                                                >
                                                    <option>Açık</option>
                                                    <option>İşlemde</option>
                                                    <option>Çözüldü</option>
                                                </select>
                                            </div>

                                            <button
                                                onClick={handleUpdateTalep}
                                                disabled={isSubmitting}
                                                className="w-full sm:w-auto px-5 sm:px-6 py-2.5 rounded-xl font-bold text-[13px] sm:text-sm text-white bg-indigo-600 hover:bg-indigo-700 transition-all flex items-center justify-center gap-2 shadow-md shadow-indigo-500/20 disabled:opacity-70 disabled:scale-100"
                                            >
                                                {isSubmitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <MessageCircle className="w-4 h-4" />}
                                                Yanıt ve Durumu Kaydet
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    selectedTalep.admin_cevabi && (
                                        <div className="bg-indigo-50 p-4 md:p-6 rounded-xl md:rounded-2xl border border-indigo-100 shadow-sm relative overflow-hidden">
                                            <div className="absolute top-0 right-8 w-1 h-full bg-indigo-200/50 opacity-0 sm:opacity-100" />
                                            <div className="flex gap-3 md:gap-4 relative z-10">
                                                <div className="w-10 h-10 md:w-12 md:h-12 rounded-xl bg-white shadow-sm flex flex-shrink-0 items-center justify-center border border-indigo-100">
                                                    <span className="text-indigo-600 font-black text-[14px] md:text-[16px]">YD</span>
                                                </div>
                                                <div>
                                                    <p className="text-[12px] md:text-[13px] font-black text-indigo-700 mb-1">Yönetim Takımı</p>
                                                    <p className="text-[13px] md:text-[15px] font-medium text-slate-700 whitespace-pre-wrap leading-relaxed">{selectedTalep.admin_cevabi}</p>
                                                </div>
                                            </div>
                                        </div>
                                    )
                                )}
                            </div>

                        </div>
                    </div>
                </div>
            )}

        </div>
    );
}

