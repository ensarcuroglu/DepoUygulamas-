import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Warehouse, Plus, X, MapPin, Building, Calendar, LayoutGrid, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { getDepolar, createDepo, createRaf } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';

// Mobil dostu, modern Depo ve Raf yönetim sayfası
export default function DepolarPage() {
    const [depolar, setDepolar] = useState([]);
    const { loading, run } = useAsync(true);
    
    // Depo Modal State'leri
    const [depoModalOpen, setDepoModalOpen] = useState(false);
    const [depoForm, setDepoForm] = useState({ isim: '', adres: '', aciklama: '' });

    // Raf Modal State'leri
    const [rafModalOpen, setRafModalOpen] = useState(false);
    const [rafForm, setRafForm] = useState({ depo_id: '', kod: '', bolge: '', kapasite: 100 });

    const fetchData = useCallback(async () => {
        try {
            const res = await run(() => getDepolar());
            setDepolar(res.data);
        } catch {
            toast.error('Depolar yüklenemedi');
        }
    }, [run]);

    useEffect(() => {
        let aktif = true;
        run(() => getDepolar())
            .then((res) => {
                if (aktif) {
                    setDepolar(res.data);
                }
            })
            .catch(() => {
                if (aktif) {
                    toast.error('Depolar yüklenemedi');
                }
            });

        return () => {
            aktif = false;
        };
    }, [run]);

    const handleDepoSave = async (e) => {
        e.preventDefault();
        try {
            await createDepo(depoForm);
            toast.success('Depo başarıyla oluşturuldu');
            setDepoModalOpen(false);
            setDepoForm({ isim: '', adres: '', aciklama: '' });
            await fetchData();
        } catch (err) {
            toast.error(hataMetni(err, 'Depo oluşturulamadı'));
        }
    };

    const handleRafSave = async (e) => {
        e.preventDefault();
        try {
            await createRaf(rafForm);
            toast.success('Raf başarıyla oluşturuldu');
            setRafModalOpen(false);
            setRafForm({ depo_id: '', kod: '', bolge: '', kapasite: 100 });
        } catch (err) {
            toast.error(hataMetni(err, 'Raf oluşturulamadı'));
        }
    };

    // Modern Form Input Sınıfı (Masaüstü ve Mobil için optimize touch target)
    const inputClass = `w-full min-h-[48px] px-4 text-[15px] font-medium rounded-xl border-2 border-transparent bg-slate-100/80
    text-slate-900 placeholder-slate-400 focus:outline-none focus:border-violet-500 focus:bg-white 
    transition-all duration-300 hover:bg-slate-200/50`;

    // Animasyon Varyantları
    const containerVariants = {
        hidden: { opacity: 0 },
        show: { opacity: 1, transition: { staggerChildren: 0.1 } }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
    };

    const modalBackdropVariants = {
        hidden: { opacity: 0 },
        visible: { opacity: 1 }
    };

    const modalVariants = {
        hidden: { opacity: 0, y: "100%", scale: 0.95 },
        visible: { 
            opacity: 1, 
            y: 0, 
            scale: 1,
            transition: { type: "spring", bounce: 0, duration: 0.4 }
        },
        exit: { opacity: 0, y: "100%", transition: { duration: 0.2 } }
    };

    return (
        <div className="min-h-screen bg-slate-50/50 pb-20">
            <div className="max-w-[1400px] mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
                
                {/* Modern Toolbar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl shadow-sm border border-slate-200/60">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-600 flex items-center justify-center shadow-violet-200 shadow-lg">
                            <Warehouse className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Depo & Raf Yönetimi</h2>
                            <p className="text-[14px] font-medium text-slate-500 mt-0.5">Operasyonel depo lokasyonlarınızı yönetin</p>
                        </div>
                    </div>
                    <button 
                        onClick={() => setDepoModalOpen(true)}
                        className="w-full sm:w-auto h-12 px-6 bg-slate-900 text-white text-[14px] font-semibold rounded-xl hover:bg-slate-800 active:scale-95 transition-all flex items-center justify-center gap-2"
                    >
                        <Plus className="w-5 h-5" /> 
                        <span>Yeni Depo Ekle</span>
                    </button>
                </div>

                {/* İçerik Alanı */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                        {[...Array(6)].map((_, i) => (
                            <div key={i} className="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm animate-pulse">
                                <div className="flex items-center gap-4 mb-6">
                                    <div className="w-12 h-12 bg-slate-200 rounded-xl" />
                                    <div className="space-y-2 flex-1">
                                        <div className="h-5 bg-slate-200 rounded-lg w-2/3" />
                                        <div className="h-4 bg-slate-100 rounded-lg w-1/3" />
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <div className="h-4 bg-slate-100 rounded-lg w-full" />
                                    <div className="h-4 bg-slate-100 rounded-lg w-4/5" />
                                </div>
                            </div>
                        ))}
                    </div>
                ) : depolar.length === 0 ? (
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="w-full max-w-md mx-auto bg-white border border-dashed border-slate-300 rounded-3xl p-10 text-center flex flex-col items-center justify-center shadow-sm mt-10"
                    >
                        <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-5 border border-slate-100">
                            <Warehouse className="w-10 h-10 text-slate-400" />
                        </div>
                        <h3 className="text-lg font-bold text-slate-800 mb-2">Henüz Depo Bulunmuyor</h3>
                        <p className="text-[15px] text-slate-500 mb-6 leading-relaxed">
                            Sisteme kayıtlı hiçbir depo bulunamadı. Hemen yeni bir depo ekleyerek yönetime başlayın.
                        </p>
                        <button 
                            onClick={() => setDepoModalOpen(true)}
                            className="h-12 px-6 bg-violet-50 text-violet-700 text-[14px] font-bold rounded-xl hover:bg-violet-100 transition-colors flex items-center gap-2"
                        >
                            <Plus className="w-5 h-5" /> Depo Oluştur
                        </button>
                    </motion.div>
                ) : (
                    <motion.div 
                        variants={containerVariants}
                        initial="hidden"
                        animate="show"
                        className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
                    >
                        {depolar.map(depo => (
                            <motion.div 
                                variants={itemVariants}
                                key={depo.id} 
                                className="group relative bg-white rounded-3xl border border-slate-200/70 shadow-sm hover:shadow-xl hover:shadow-violet-500/5 hover:border-violet-200 transition-all duration-300 overflow-hidden flex flex-col"
                            >
                                {/* Aktif/Pasif İndikatörü */}
                                <div className={`absolute top-0 left-0 w-full h-1.5 ${depo.aktif ? 'bg-gradient-to-r from-emerald-400 to-teal-400' : 'bg-slate-300'}`} />

                                <div className="p-6 flex-1">
                                    <div className="flex items-start justify-between mb-5">
                                        <div className="flex items-center gap-4">
                                            <div className="w-12 h-12 rounded-2xl bg-violet-50 text-violet-600 flex items-center justify-center group-hover:bg-violet-600 group-hover:text-white transition-colors duration-300">
                                                <Building className="w-6 h-6" />
                                            </div>
                                            <div>
                                                <h3 className="text-[17px] font-bold text-slate-900 leading-tight">{depo.isim}</h3>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <span className="text-[12px] font-semibold text-slate-400">ID: #{depo.id}</span>
                                                    <span className="w-1 h-1 rounded-full bg-slate-300" />
                                                    <span className={`text-[12px] font-semibold flex items-center gap-1.5 ${depo.aktif ? 'text-emerald-600' : 'text-slate-500'}`}>
                                                        <span className={`w-1.5 h-1.5 rounded-full ${depo.aktif ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                                                        {depo.aktif ? 'Aktif' : 'Pasif'}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        {depo.adres ? (
                                            <div className="flex items-start gap-3">
                                                <MapPin className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                                                <p className="text-[14px] text-slate-600 leading-relaxed line-clamp-2">{depo.adres}</p>
                                            </div>
                                        ) : (
                                            <div className="flex items-center gap-3 opacity-50">
                                                <MapPin className="w-5 h-5 text-slate-300" />
                                                <span className="text-[14px] text-slate-400 italic">Adres belirtilmemiş</span>
                                            </div>
                                        )}

                                        {depo.aciklama && (
                                            <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-100 mt-4">
                                                <p className="text-[13px] text-slate-600 line-clamp-2">{depo.aciklama}</p>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Alt Kısım & Aksiyon */}
                                <div className="p-4 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between gap-4">
                                    <div className="flex items-center gap-2 text-[12px] font-medium text-slate-500">
                                        <Calendar className="w-4 h-4" />
                                        {new Date(depo.olusturma_tarihi).toLocaleDateString('tr-TR')}
                                    </div>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); setRafForm({ ...rafForm, depo_id: depo.id }); setRafModalOpen(true); }}
                                        className="h-10 px-4 bg-white border border-slate-200 text-slate-700 text-[13px] font-bold rounded-lg hover:border-violet-500 hover:text-violet-700 active:scale-95 transition-all flex items-center gap-2 shadow-sm"
                                    >
                                        <LayoutGrid className="w-4 h-4 text-violet-500" /> 
                                        Raf Ekle
                                    </button>
                                </div>
                            </motion.div>
                        ))}
                    </motion.div>
                )}
            </div>

            {/* Yeni Depo Modalı */}
            <AnimatePresence>
                {depoModalOpen && (
                    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4">
                        <motion.div 
                            variants={modalBackdropVariants}
                            initial="hidden" animate="visible" exit="hidden"
                            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
                            onClick={() => setDepoModalOpen(false)} 
                        />
                        <motion.div 
                            variants={modalVariants}
                            initial="hidden" animate="visible" exit="exit"
                            className="relative w-full sm:max-w-md bg-white rounded-t-[28px] sm:rounded-3xl shadow-2xl flex flex-col max-h-[90vh]"
                        >
                            <div className="flex-shrink-0 flex items-center justify-between px-6 sm:px-8 py-5 border-b border-slate-100">
                                <div>
                                    <h3 className="text-xl font-bold text-slate-900">Yeni Depo</h3>
                                    <p className="text-[13px] text-slate-500 mt-1">Sisteme yeni bir tesis ekleyin.</p>
                                </div>
                                <button 
                                    onClick={() => setDepoModalOpen(false)} 
                                    className="w-10 h-10 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                            
                            <form onSubmit={handleDepoSave} className="flex-1 overflow-y-auto px-6 sm:px-8 py-6 space-y-5">
                                <div>
                                    <label className="text-[13px] font-bold text-slate-700 mb-2 flex items-center gap-1">
                                        Depo Adı <span className="text-red-500">*</span>
                                    </label>
                                    <input 
                                        className={inputClass} 
                                        value={depoForm.isim} 
                                        onChange={e => setDepoForm({ ...depoForm, isim: e.target.value })} 
                                        placeholder="Örn: Ana Dağıtım Merkezi" 
                                        autoFocus
                                        required 
                                    />
                                </div>
                                <div>
                                    <label className="text-[13px] font-bold text-slate-700 mb-2 block">Açık Adres</label>
                                    <input 
                                        className={inputClass} 
                                        value={depoForm.adres} 
                                        onChange={e => setDepoForm({ ...depoForm, adres: e.target.value })} 
                                        placeholder="OSB 1. Cadde No:12, İstanbul" 
                                    />
                                </div>
                                <div>
                                    <label className="text-[13px] font-bold text-slate-700 mb-2 block">Detaylı Açıklama</label>
                                    <textarea 
                                        className={`${inputClass} min-h-[100px] resize-none py-3`} 
                                        value={depoForm.aciklama} 
                                        onChange={e => setDepoForm({ ...depoForm, aciklama: e.target.value })} 
                                        placeholder="Depo ile ilgili operasyonel notlar..."
                                    />
                                </div>
                                
                                {/* Padding for mobile scroll bottom */}
                                <div className="h-4 sm:hidden"></div>
                            </form>

                            <div className="flex-shrink-0 flex gap-3 px-6 sm:px-8 py-5 border-t border-slate-100 bg-slate-50 sm:rounded-b-3xl">
                                <button 
                                    type="button" 
                                    onClick={() => setDepoModalOpen(false)} 
                                    className="flex-1 h-12 rounded-xl bg-white border border-slate-200 font-bold text-slate-600 hover:bg-slate-50 transition-colors"
                                >
                                    İptal
                                </button>
                                <button 
                                    onClick={handleDepoSave}
                                    type="submit" 
                                    disabled={!depoForm.isim}
                                    className="flex-1 h-12 rounded-xl bg-slate-900 font-bold text-white hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                >
                                    Kaydet
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            {/* Raf Ekleme Modalı */}
            <AnimatePresence>
                {rafModalOpen && (
                    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4">
                        <motion.div 
                            variants={modalBackdropVariants}
                            initial="hidden" animate="visible" exit="hidden"
                            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
                            onClick={() => setRafModalOpen(false)} 
                        />
                        <motion.div 
                            variants={modalVariants}
                            initial="hidden" animate="visible" exit="exit"
                            className="relative w-full sm:max-w-md bg-white rounded-t-[28px] sm:rounded-3xl shadow-2xl flex flex-col max-h-[90vh]"
                        >
                            <div className="flex-shrink-0 flex items-center justify-between px-6 sm:px-8 py-5 border-b border-slate-100">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-violet-100 text-violet-600 flex items-center justify-center">
                                        <LayoutGrid className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-slate-900">Raf Ekle</h3>
                                        <p className="text-[13px] text-slate-500">Seçili depoya yeni lokasyon tanımlayın.</p>
                                    </div>
                                </div>
                                <button 
                                    onClick={() => setRafModalOpen(false)} 
                                    className="w-10 h-10 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                            
                            <form onSubmit={handleRafSave} className="flex-1 overflow-y-auto px-6 sm:px-8 py-6 space-y-5">
                                <div>
                                    <label className="text-[13px] font-bold text-slate-700 mb-2 flex items-center gap-1">
                                        Raf Kodu <span className="text-red-500">*</span>
                                    </label>
                                    <input 
                                        className={`${inputClass} font-mono uppercase tracking-wider`} 
                                        value={rafForm.kod} 
                                        onChange={e => setRafForm({ ...rafForm, kod: e.target.value.toUpperCase() })} 
                                        placeholder="A-01, ZEMİN-1" 
                                        autoFocus
                                        required 
                                    />
                                    <p className="text-[12px] text-slate-400 mt-2 flex items-center gap-1">
                                        <AlertCircle className="w-3.5 h-3.5" /> Benzersiz ve kısa bir kod belirleyin.
                                    </p>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="col-span-2 sm:col-span-1">
                                        <label className="text-[13px] font-bold text-slate-700 mb-2 block">Bölge / Koridor</label>
                                        <input 
                                            className={inputClass} 
                                            value={rafForm.bolge} 
                                            onChange={e => setRafForm({ ...rafForm, bolge: e.target.value })} 
                                            placeholder="A Blok" 
                                        />
                                    </div>
                                    <div className="col-span-2 sm:col-span-1">
                                        <label className="text-[13px] font-bold text-slate-700 mb-2 block">Kapasite (Adet)</label>
                                        <input 
                                            type="number" 
                                            className={inputClass} 
                                            value={rafForm.kapasite} 
                                            onChange={e => setRafForm({ ...rafForm, kapasite: parseInt(e.target.value) || 0 })} 
                                            min="1" 
                                            required 
                                        />
                                    </div>
                                </div>
                                
                                <div className="h-4 sm:hidden"></div>
                            </form>

                            <div className="flex-shrink-0 flex gap-3 px-6 sm:px-8 py-5 border-t border-slate-100 bg-slate-50 sm:rounded-b-3xl">
                                <button 
                                    type="button" 
                                    onClick={() => setRafModalOpen(false)} 
                                    className="flex-1 h-12 rounded-xl bg-white border border-slate-200 font-bold text-slate-600 hover:bg-slate-50 transition-colors"
                                >
                                    İptal
                                </button>
                                <button 
                                    onClick={handleRafSave}
                                    type="submit" 
                                    disabled={!rafForm.kod}
                                    className="flex-1 h-12 rounded-xl bg-violet-600 font-bold text-white hover:bg-violet-700 shadow-lg shadow-violet-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                >
                                    Rafı Ekle
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
}