import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
    getDestekTalepleri,
    createDestekTalebi,
    updateDestekTalebi
} from '../services/api';
import toast from 'react-hot-toast';
import { hataMetni } from '../utils/hata';
import { motion, AnimatePresence, useDragControls } from 'framer-motion';
import {
    HelpCircle, Plus, Search, Filter, RefreshCw, Clock,
    CheckCircle2, X, MessageCircle, AlertTriangle
} from 'lucide-react';

// ========================
// YARDIMCI FONKSİYONLAR
// ========================

const formatDate = (dateString, includeTime = false) => {
    if (!dateString) return 'Tarih Yok';
    try {
        const options = { day: 'numeric', month: 'short', year: 'numeric' };
        if (includeTime) {
            options.hour = '2-digit';
            options.minute = '2-digit';
        }
        return new Date(dateString).toLocaleString('tr-TR', options);
    } catch {
        return 'Geçersiz Tarih';
    }
};

// ========================
// BADGES (Kurumsal & Minimal)
// ========================

const DurumBadge = ({ durum }) => {
    const configs = {
        'Açık': { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', icon: <Clock className="w-3.5 h-3.5" /> },
        'İşlemde': { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', icon: <RefreshCw className="w-3.5 h-3.5 animate-spin" /> },
        'Çözüldü': { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', icon: <CheckCircle2 className="w-3.5 h-3.5" /> }
    };
    const conf = configs[durum] || { bg: 'bg-slate-50', text: 'text-slate-600', border: 'border-slate-200', icon: null };

    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${conf.bg} ${conf.text} ${conf.border}`}>
            {conf.icon}
            {durum}
        </span>
    );
};

const OncelikBadge = ({ oncelik }) => {
    const configs = {
        'Düşük': 'bg-slate-100 text-slate-600',
        'Normal': 'bg-slate-800 text-white',
        'Yüksek': 'bg-rose-50 text-rose-700 border border-rose-200'
    };
    const style = configs[oncelik] || 'bg-slate-100 text-slate-600';

    return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wide ${style}`}>
            {oncelik === 'Yüksek' && <AlertTriangle className="w-3 h-3 mr-1" />}
            {oncelik}
        </span>
    );
};

// ========================
// SKELETON LOADER
// ========================

const SkeletonCard = () => (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 flex flex-col relative overflow-hidden h-[180px]">
        <div className="flex justify-between items-start mb-4">
            <div className="w-16 h-5 bg-slate-100 rounded animate-pulse" />
            <div className="w-20 h-6 bg-slate-100 rounded-md animate-pulse" />
        </div>
        <div className="space-y-2 mb-4">
            <div className="w-3/4 h-5 bg-slate-100 rounded animate-pulse" />
            <div className="w-1/2 h-5 bg-slate-100 rounded animate-pulse" />
        </div>
        <div className="mt-auto pt-4 border-t border-slate-50 flex justify-between items-center">
            <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-slate-100 animate-pulse" />
                <div className="w-24 h-4 bg-slate-100 rounded animate-pulse" />
            </div>
            <div className="w-16 h-3 bg-slate-100 rounded animate-pulse" />
        </div>
    </div>
);

// ========================
// FRAMER MOTION MODAL
// ========================

function ModalWrapper({ isOpen, onClose, children, maxWidth = "max-w-xl" }) {
    const dragControls = useDragControls();

    useEffect(() => {
        const handleEsc = (e) => e.key === 'Escape' && onClose();
        if (isOpen) window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [isOpen, onClose]);

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-slate-900/40 z-[100] backdrop-blur-sm"
                        aria-hidden="true"
                    />
                    
                    {/* Modal Container */}
                    <div className="fixed inset-0 z-[101] flex items-end sm:items-center justify-center sm:p-4 pointer-events-none">
                        <motion.div
                            drag="y"
                            dragControls={dragControls}
                            dragListener={false} // Sadece handle üzerinden sürüklenebilir
                            dragConstraints={{ top: 0, bottom: 0 }}
                            dragElastic={0.2}
                            onDragEnd={(e, info) => {
                                if (info.offset.y > 100 || info.velocity.y > 500) onClose();
                            }}
                            initial={{ y: "100%", opacity: 0.5 }}
                            animate={{ y: 0, opacity: 1 }}
                            exit={{ y: "100%", opacity: 0, transition: { duration: 0.2 } }}
                            transition={{ type: "spring", damping: 25, stiffness: 300 }}
                            className={`w-full ${maxWidth} bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl flex flex-col max-h-[92vh] pointer-events-auto`}
                            role="dialog"
                            aria-modal="true"
                            onClick={e => e.stopPropagation()}
                        >
                            {/* Drag Handle (Mobil) */}
                            <div 
                                className="sm:hidden w-full flex justify-center pt-3 pb-2 cursor-grab active:cursor-grabbing touch-none"
                                onPointerDown={(e) => dragControls.start(e)}
                            >
                                <div className="w-12 h-1.5 rounded-full bg-slate-200" />
                            </div>
                            
                            {children}
                        </motion.div>
                    </div>
                </>
            )}
        </AnimatePresence>
    );
}

// ========================
// YENİ TALEP MODALI
// ========================

function CreateModal({ isOpen, onClose, fetchTalepler }) {
    const [yeniKonu, setYeniKonu] = useState('');
    const [yeniKategori, setYeniKategori] = useState('Hata Bildirimi');
    const [yeniOncelik, setYeniOncelik] = useState('Normal');
    const [yeniAciklama, setYeniAciklama] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Modal kapandığında formu temizle
    useEffect(() => {
        if (!isOpen) {
            setYeniKonu('');
            setYeniKategori('Hata Bildirimi');
            setYeniOncelik('Normal');
            setYeniAciklama('');
        }
    }, [isOpen]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!yeniKonu.trim() || !yeniAciklama.trim()) {
            return toast.error("Lütfen konu ve açıklama alanlarını doldurun.");
        }

        setIsSubmitting(true);
        try {
            await createDestekTalebi({ 
                konu: yeniKonu.trim(), 
                kategori: yeniKategori, 
                oncelik: yeniOncelik, 
                aciklama: yeniAciklama.trim() 
            });
            toast.success("Talebiniz başarıyla oluşturuldu.");
            fetchTalepler();
            onClose();
        } catch (err) { 
            toast.error(hataMetni(err, 'Talep oluşturulamadı.')); 
        } finally { 
            setIsSubmitting(false); 
        }
    };

    return (
        <ModalWrapper isOpen={isOpen} onClose={onClose}>
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between shrink-0">
                <h2 className="text-lg font-bold text-slate-900">Yeni Destek Talebi</h2>
                <button 
                    onClick={onClose} 
                    className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-full transition-colors outline-none focus:ring-2 focus:ring-slate-200"
                    aria-label="Kapat"
                >
                    <X className="w-5 h-5" />
                </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
                <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5 overscroll-contain">
                    <div>
                        <label className="text-sm font-semibold text-slate-700 block mb-1.5" htmlFor="konu">Konu Başlığı</label>
                        <input
                            id="konu" type="text" autoFocus required
                            className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-slate-900 transition-shadow outline-none"
                            placeholder="Kısaca sorunu özetleyin..."
                            value={yeniKonu} onChange={e => setYeniKonu(e.target.value)}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm font-semibold text-slate-700 block mb-1.5" htmlFor="kategori">Kategori</label>
                            <select
                                id="kategori"
                                className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 text-slate-900 outline-none appearance-none"
                                value={yeniKategori} onChange={e => setYeniKategori(e.target.value)}
                            >
                                <option>Hata Bildirimi</option>
                                <option>Donanım Talebi</option>
                                <option>Yazılım İsteği</option>
                                <option>Bilgi Alma</option>
                                <option>Diğer</option>
                            </select>
                        </div>
                        <div>
                            <label className="text-sm font-semibold text-slate-700 block mb-1.5" htmlFor="oncelik">Öncelik</label>
                            <select
                                id="oncelik"
                                className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 text-slate-900 outline-none appearance-none"
                                value={yeniOncelik} onChange={e => setYeniOncelik(e.target.value)}
                            >
                                <option>Düşük</option>
                                <option>Normal</option>
                                <option>Yüksek</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="text-sm font-semibold text-slate-700 block mb-1.5" htmlFor="aciklama">Detaylı Açıklama</label>
                        <textarea
                            id="aciklama" required rows={5}
                            className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 text-slate-900 resize-none outline-none transition-shadow"
                            placeholder="Yaşadığınız durumu detaylıca anlatın..."
                            value={yeniAciklama} onChange={e => setYeniAciklama(e.target.value)}
                        />
                    </div>
                </div>

                <div className="shrink-0 px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-3 pb-[calc(1rem+env(safe-area-inset-bottom))]">
                    <button 
                        type="button" 
                        onClick={onClose} 
                        className="px-5 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-200 rounded-lg transition-colors hidden sm:block outline-none focus:ring-2 focus:ring-slate-300"
                    >
                        İptal
                    </button>
                    <button
                        type="submit" disabled={isSubmitting}
                        className="flex-1 sm:flex-none px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-70 outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
                    >
                        {isSubmitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                        Talebi Oluştur
                    </button>
                </div>
            </form>
        </ModalWrapper>
    );
}

// ========================
// DETAY & YANIT MODALI
// ========================

function DetailModal({ isOpen, onClose, talep, isAdmin, fetchTalepler }) {
    const [cevapMetni, setCevapMetni] = useState('');
    const [updateDurum, setUpdateDurum] = useState('Açık');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Talep değiştiğinde state'leri senkronize et
    useEffect(() => {
        if (talep && isOpen) {
            setCevapMetni(talep.admin_cevabi || '');
            setUpdateDurum(talep.durum || 'Açık');
        }
    }, [talep, isOpen]);

    const handleUpdate = async () => {
        if (!talep || !isAdmin) return;
        setIsSubmitting(true);
        try {
            await updateDestekTalebi(talep.id, { 
                durum: updateDurum, 
                admin_cevabi: cevapMetni.trim() 
            });
            toast.success("Talep başarıyla güncellendi.");
            fetchTalepler();
            onClose();
        } catch (err) { 
            toast.error(hataMetni(err, 'Talep güncellenemedi.')); 
        } finally { 
            setIsSubmitting(false); 
        }
    };

    if (!talep) return null;

    return (
        <ModalWrapper isOpen={isOpen} onClose={onClose} maxWidth="max-w-2xl">
            <div className="shrink-0 px-6 py-4 border-b border-slate-100 flex items-start justify-between gap-4">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 leading-tight">{talep.konu}</h2>
                    <p className="text-xs font-medium text-slate-500 mt-1 flex items-center gap-2">
                        <span>#{talep.id}</span> • 
                        <span>{formatDate(talep.olusturma_tarihi, true)}</span>
                    </p>
                </div>
                <button 
                    onClick={onClose} 
                    className="p-2 text-slate-400 hover:text-slate-600 bg-slate-50 hover:bg-slate-100 rounded-full transition-colors shrink-0 outline-none focus:ring-2 focus:ring-slate-200"
                    aria-label="Kapat"
                >
                    <X className="w-5 h-5" />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6 overscroll-contain">
                <div className="flex gap-2">
                    <OncelikBadge oncelik={talep.oncelik} />
                    <DurumBadge durum={talep.durum} />
                </div>

                <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center font-bold text-sm shrink-0 uppercase">
                        {talep.kullanici?.ad_soyad?.charAt(0) || '?'}
                    </div>
                    <div className="flex-1 min-w-0">
                        <span className="font-semibold text-sm text-slate-900 block mb-1 truncate">{talep.kullanici?.ad_soyad || 'Bilinmeyen Kullanıcı'}</span>
                        <div className="bg-slate-50 p-4 rounded-xl text-sm text-slate-700 whitespace-pre-wrap border border-slate-100 break-words">
                            {talep.aciklama}
                        </div>
                    </div>
                </div>

                <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                        <HelpCircle className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <span className="font-semibold text-sm text-slate-900 block mb-1">Sistem Yönetimi</span>
                        
                        {!isAdmin && !talep.admin_cevabi && (
                            <div className="border border-dashed border-slate-300 p-4 rounded-xl text-sm text-slate-500 flex items-center gap-2">
                                <Clock className="w-4 h-4 shrink-0" /> 
                                <span>Talep inceleniyor, henüz yanıtlanmadı.</span>
                            </div>
                        )}
                        
                        {isAdmin ? (
                            <textarea
                                rows={4} 
                                placeholder="Kullanıcıya iletilecek yanıtı buraya yazın..."
                                className="w-full p-4 bg-white border border-slate-300 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-slate-900 outline-none resize-none transition-shadow"
                                value={cevapMetni} onChange={e => setCevapMetni(e.target.value)}
                            />
                        ) : talep.admin_cevabi ? (
                            <div className="bg-indigo-50/50 p-4 rounded-xl text-sm text-slate-800 whitespace-pre-wrap border border-indigo-100 break-words">
                                {talep.admin_cevabi}
                            </div>
                        ) : null}
                    </div>
                </div>
            </div>

            {isAdmin && (
                <div className="shrink-0 px-6 py-4 border-t border-slate-100 bg-white flex flex-col sm:flex-row gap-3 pb-[calc(1rem+env(safe-area-inset-bottom))]">
                    <select
                        className="sm:w-48 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm font-semibold text-slate-900 outline-none focus:ring-2 focus:ring-slate-900"
                        value={updateDurum} onChange={e => setUpdateDurum(e.target.value)}
                    >
                        <option>Açık</option>
                        <option>İşlemde</option>
                        <option>Çözüldü</option>
                    </select>
                    <button
                        onClick={handleUpdate} disabled={isSubmitting}
                        className="flex-1 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-70 outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
                    >
                        {isSubmitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <MessageCircle className="w-4 h-4" />}
                        Kaydet ve Yanıtla
                    </button>
                </div>
            )}
        </ModalWrapper>
    );
}

// ========================
// ANA SAYFA BİLEŞENİ
// ========================

export default function DestekMasasiPage() {
    const { user } = useAuth();
    const isAdmin = user?.rol === 'admin';

    const [talepler, setTalepler] = useState([]);
    const [loading, setLoading] = useState(true);
    
    // Filtre State'leri
    const [aramaGirdisi, setAramaGirdisi] = useState('');
    const [filtreDurum, setFiltreDurum] = useState('');

    // Modal State'leri
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [isDetailOpen, setIsDetailOpen] = useState(false);
    const [selectedTalep, setSelectedTalep] = useState(null);

    const fetchTalepler = async () => {
        setLoading(true);
        try {
            const params = filtreDurum ? { durum: filtreDurum } : {};
            const res = await getDestekTalepleri(params);
            setTalepler(res.data || []);
        } catch (error) {
            toast.error(hataMetni(error, 'Talepler yüklenirken bir sorun oluştu.'));
        } finally {
            setLoading(false);
        }
    };

    // Filtre durumu değiştiğinde API'den veriyi tekrar çek
    useEffect(() => { 
        fetchTalepler(); 
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filtreDurum]);

    // Modallar açıkken arkaplan scroll'unu kapat
    useEffect(() => {
        if (isCreateOpen || isDetailOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => { document.body.style.overflow = 'unset'; };
    }, [isCreateOpen, isDetailOpen]);

    const openDetailModal = (talep) => {
        setSelectedTalep(talep);
        setIsDetailOpen(true);
    };

    // Arama filtresi (Client-side)
    const filteredTalepler = useMemo(() => {
        if (!aramaGirdisi.trim()) return talepler;
        const query = aramaGirdisi.toLowerCase();
        return talepler.filter(t =>
            t.konu?.toLowerCase().includes(query) ||
            t.kullanici?.ad_soyad?.toLowerCase().includes(query)
        );
    }, [talepler, aramaGirdisi]);

    return (
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 pb-24 sm:pb-8 bg-slate-50 min-h-screen">
            
            {/* Header Bölümü */}
            <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Destek Masası</h1>
                    <p className="text-sm font-medium text-slate-500 mt-1">Sistem talepleri ve yardım merkezi</p>
                </div>
                
                {/* Desktop Aksiyon Butonları */}
                <div className="hidden sm:flex items-center gap-3">
                    <button 
                        onClick={fetchTalepler} 
                        disabled={loading}
                        className="p-2.5 text-slate-600 hover:bg-slate-200 rounded-lg transition-colors border border-slate-200 bg-white outline-none focus:ring-2 focus:ring-slate-300 disabled:opacity-50"
                        aria-label="Talepleri Yenile"
                    >
                        <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                    <button 
                        onClick={() => setIsCreateOpen(true)} 
                        className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold rounded-lg transition-colors flex items-center gap-2 outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
                    >
                        <Plus className="w-4 h-4" /> Yeni Talep
                    </button>
                </div>
            </header>

            {/* Arama ve Filtreleme */}
            <div className="flex flex-col sm:flex-row gap-3 bg-white p-2 rounded-xl border border-slate-200 shadow-sm">
                <div className="relative flex-1">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text" 
                        placeholder="Konu veya İsimle Ara..."
                        className="w-full pl-10 pr-4 py-2.5 bg-transparent text-sm text-slate-900 outline-none"
                        value={aramaGirdisi} 
                        onChange={(e) => setAramaGirdisi(e.target.value)}
                    />
                </div>
                <div className="hidden sm:block w-px bg-slate-100 my-2" />
                <div className="relative sm:w-64 border-t border-slate-100 sm:border-0 pt-2 sm:pt-0">
                    <select
                        className="w-full pl-4 pr-10 py-2.5 bg-transparent text-sm font-medium text-slate-700 outline-none appearance-none cursor-pointer"
                        value={filtreDurum} 
                        onChange={(e) => setFiltreDurum(e.target.value)}
                        aria-label="Duruma Göre Filtrele"
                    >
                        <option value="">Tüm Durumlar</option>
                        <option value="Açık">Açık</option>
                        <option value="İşlemde">İşlemde</option>
                        <option value="Çözüldü">Çözüldü</option>
                    </select>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400 bg-white pl-2">
                        <Filter className="w-4 h-4 inline-block mr-1" />
                    </div>
                </div>
            </div>

            {/* Kart Listesi Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {loading ? (
                    Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
                ) : filteredTalepler.length === 0 ? (
                    <div className="col-span-full py-20 text-center border border-dashed border-slate-300 rounded-2xl bg-white">
                        <MessageCircle className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                        <h3 className="text-base font-semibold text-slate-700">Talep Bulunamadı</h3>
                        <p className="text-sm text-slate-500 mt-1">Kriterlerinize uygun bir kayıt görünmüyor.</p>
                    </div>
                ) : (
                    filteredTalepler.map((talep) => (
                        <div
                            key={talep.id}
                            role="button"
                            tabIndex={0}
                            onClick={() => openDetailModal(talep)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                    e.preventDefault();
                                    openDetailModal(talep);
                                }
                            }}
                            className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all cursor-pointer flex flex-col group relative outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                        >
                            <div className="flex justify-between items-start mb-3">
                                <OncelikBadge oncelik={talep.oncelik} />
                                <DurumBadge durum={talep.durum} />
                            </div>
                            
                            <h3 className="font-bold text-slate-900 text-base leading-snug mb-2 group-hover:text-slate-700 line-clamp-1">
                                {talep.konu}
                            </h3>
                            <p className="text-sm text-slate-500 line-clamp-2 mb-4">
                                {talep.aciklama}
                            </p>
                            
                            <div className="mt-auto pt-4 border-t border-slate-50 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center font-bold text-[10px] uppercase">
                                        {talep.kullanici?.ad_soyad?.charAt(0) || '?'}
                                    </div>
                                    <span className="text-xs font-semibold text-slate-600 truncate max-w-[120px]">
                                        {talep.kullanici?.ad_soyad?.split(' ')[0] || 'Bilinmiyor'}
                                    </span>
                                </div>
                                <span className="text-xs font-medium text-slate-400 shrink-0">
                                    {formatDate(talep.olusturma_tarihi)}
                                </span>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Mobil FAB (Floating Action Button) */}
            <button
                onClick={() => setIsCreateOpen(true)}
                className="sm:hidden fixed bottom-6 right-6 w-14 h-14 bg-slate-900 text-white rounded-2xl shadow-xl flex items-center justify-center active:scale-95 transition-transform z-40 outline-none focus:ring-4 focus:ring-slate-300"
                aria-label="Yeni Talep Oluştur"
            >
                <Plus className="w-6 h-6" />
            </button>

            {/* Modallar */}
            <CreateModal
                isOpen={isCreateOpen} 
                onClose={() => setIsCreateOpen(false)}
                fetchTalepler={fetchTalepler}
            />

            <DetailModal
                isOpen={isDetailOpen} 
                onClose={() => setIsDetailOpen(false)}
                talep={selectedTalep} 
                isAdmin={isAdmin}
                fetchTalepler={fetchTalepler}
            />
        </div>
    );
}