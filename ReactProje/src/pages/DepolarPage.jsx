import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Warehouse, Plus, X, MapPin, Building } from 'lucide-react';
import toast from 'react-hot-toast';
import { getDepolar, createDepo, createRaf } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';

// Bu sayfa hem Depo hem Raf yönetimini kapsar

export default function DepolarPage() {
    const [depolar, setDepolar] = useState([]);
    const { loading, run } = useAsync(true);
    const [depoModalOpen, setDepoModalOpen] = useState(false);
    const [depoForm, setDepoForm] = useState({ isim: '', adres: '', aciklama: '' });

    // Raf Form State'leri
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

    const inputClass = `w-full h-11 px-4 text-[14px] font-medium rounded-xl border border-slate-200 bg-slate-50/50
    text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-blue-500/10
    focus:border-blue-500 focus:bg-white transition-all duration-300`;

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto p-4 sm:p-6">
            {/* Toolbar */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-violet-100 border border-violet-200 flex items-center justify-center">
                        <Warehouse className="w-5 h-5 text-violet-600" />
                    </div>
                    <div>
                        <h2 className="text-[17px] font-extrabold text-slate-800">Depo & Raf Yönetimi</h2>
                        <p className="text-[12px] font-medium text-slate-500">Depoları ve raf lokasyonlarını yönetin</p>
                    </div>
                </div>
                <button onClick={() => setDepoModalOpen(true)}
                    className="h-11 px-5 bg-violet-600 text-white text-[14px] font-bold rounded-xl hover:bg-violet-700 shadow-lg hover:-translate-y-0.5 transition-all flex items-center gap-2">
                    <Plus className="w-5 h-5 stroke-[2.5px]" /> <span className="hidden sm:inline">Yeni Depo</span>
                </button>
            </div>

            {/* Depo Kartları */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    [...Array(3)].map((_, i) => (
                        <div key={i} className="bg-white rounded-2xl border border-slate-200 p-6 animate-pulse">
                            <div className="h-5 bg-slate-200 rounded w-32 mb-3" />
                            <div className="h-4 bg-slate-100 rounded w-48 mb-2" />
                            <div className="h-4 bg-slate-100 rounded w-24" />
                        </div>
                    ))
                ) : depolar.length === 0 ? (
                    <div className="col-span-full flex flex-col items-center justify-center py-20 text-center">
                        <Warehouse className="w-14 h-14 text-slate-200 mb-4" />
                        <p className="text-[15px] font-bold text-slate-600">Henüz depo kaydı yok</p>
                        <p className="text-[13px] text-slate-400 mt-1">Yeni depo ekleyerek başlayın</p>
                    </div>
                ) : (
                    depolar.map(depo => (
                        <div key={depo.id} className="bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow overflow-hidden group">
                            <div className="p-6">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-violet-50 border border-violet-100 flex items-center justify-center">
                                            <Building className="w-5 h-5 text-violet-600" />
                                        </div>
                                        <div>
                                            <h3 className="text-[16px] font-extrabold text-slate-800">{depo.isim}</h3>
                                            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">ID: #{depo.id}</span>
                                        </div>
                                    </div>
                                </div>

                                {depo.adres && (
                                    <div className="flex items-start gap-2 mb-3">
                                        <MapPin className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                                        <p className="text-[13px] text-slate-600">{depo.adres}</p>
                                    </div>
                                )}

                                {depo.aciklama && (
                                    <p className="text-[13px] text-slate-500 bg-slate-50 rounded-xl px-4 py-3 border border-slate-100">{depo.aciklama}</p>
                                )}
                            </div>

                            <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                                <span className={`text-[11px] font-extrabold px-2.5 py-1 rounded-full border ${depo.aktif ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'}`}>
                                    {depo.aktif ? 'AKTİF' : 'PASİF'}
                                </span>
                                <span className="text-[11px] text-slate-400">
                                    {new Date(depo.olusturma_tarihi).toLocaleDateString('tr-TR')}
                                </span>
                            </div>

                            {/* Raf Ekle Butonu */}
                            <div className="px-6 py-3 bg-white border-t border-slate-100 flex items-center justify-end">
                                <button
                                    onClick={(e) => { e.stopPropagation(); setRafForm({ ...rafForm, depo_id: depo.id }); setRafModalOpen(true); }}
                                    className="flex items-center gap-1.5 text-[12px] font-bold text-violet-600 hover:text-violet-700 bg-violet-50 px-3 py-1.5 rounded-lg transition-colors"
                                >
                                    <Plus className="w-3.5 h-3.5 stroke-[3px]" /> Raf Ekle
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Depo Ekleme Modalı */}
            {depoModalOpen && createPortal(
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={() => setDepoModalOpen(false)}>
                    <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-md" />
                    <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md animate-fade-in ring-1 ring-slate-900/10" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 bg-slate-50/50 rounded-t-2xl">
                            <h3 className="text-[18px] font-extrabold text-slate-900">Yeni Depo</h3>
                            <button onClick={() => setDepoModalOpen(false)} className="w-9 h-9 rounded-full bg-white border border-slate-200 shadow-sm hover:bg-slate-100 flex items-center justify-center">
                                <X className="w-5 h-5 text-slate-500" />
                            </button>
                        </div>
                        <form onSubmit={handleDepoSave} className="p-6 space-y-5">
                            <div>
                                <label className="text-[12px] font-bold text-slate-700 mb-2 block uppercase">Depo Adı *</label>
                                <input className={inputClass} value={depoForm.isim} onChange={e => setDepoForm({ ...depoForm, isim: e.target.value })} placeholder="Ana Depo" required />
                            </div>
                            <div>
                                <label className="text-[12px] font-bold text-slate-700 mb-2 block uppercase">Adres</label>
                                <input className={inputClass} value={depoForm.adres} onChange={e => setDepoForm({ ...depoForm, adres: e.target.value })} placeholder="OSB 1. Cadde No:12" />
                            </div>
                            <div>
                                <label className="text-[12px] font-bold text-slate-700 mb-2 block uppercase">Açıklama</label>
                                <textarea className={`${inputClass} h-20 resize-none py-3`} value={depoForm.aciklama} onChange={e => setDepoForm({ ...depoForm, aciklama: e.target.value })} />
                            </div>
                            <div className="flex gap-3 pt-3">
                                <button type="button" onClick={() => setDepoModalOpen(false)} className="flex-1 h-11 rounded-xl border border-slate-200 font-bold text-slate-600 hover:bg-slate-50">İptal</button>
                                <button type="submit" className="flex-1 h-11 rounded-xl bg-violet-600 font-bold text-white hover:bg-violet-700 shadow-lg transition-all">Kaydet</button>
                            </div>
                        </form>
                    </div>
                </div>,
                document.body
            )}

            {/* Raf Ekleme Modalı */}
            {rafModalOpen && createPortal(
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={() => setRafModalOpen(false)}>
                    <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-md" />
                    <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md animate-fade-in ring-1 ring-slate-900/10" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 bg-slate-50/50 rounded-t-2xl">
                            <h3 className="text-[18px] font-extrabold text-slate-900">Raf Ekle</h3>
                            <button onClick={() => setRafModalOpen(false)} className="w-9 h-9 rounded-full bg-white border border-slate-200 shadow-sm hover:bg-slate-100 flex items-center justify-center">
                                <X className="w-5 h-5 text-slate-500" />
                            </button>
                        </div>
                        <form onSubmit={handleRafSave} className="p-6 space-y-5">
                            <div>
                                <label className="text-[12px] font-bold text-slate-700 mb-2 block uppercase">Raf Kodu *</label>
                                <input className={inputClass} value={rafForm.kod} onChange={e => setRafForm({ ...rafForm, kod: e.target.value.toUpperCase() })} placeholder="A-01, ZEMİN-1 vb." required />
                            </div>
                            <div>
                                <label className="text-[12px] font-bold text-slate-700 mb-2 block uppercase">Bölge</label>
                                <input className={inputClass} value={rafForm.bolge} onChange={e => setRafForm({ ...rafForm, bolge: e.target.value })} placeholder="A Blok Zemin Kat" />
                            </div>
                            <div>
                                <label className="text-[12px] font-bold text-slate-700 mb-2 block uppercase">Kapasite (Palet)</label>
                                <input type="number" className={inputClass} value={rafForm.kapasite} onChange={e => setRafForm({ ...rafForm, kapasite: parseInt(e.target.value) || 0 })} min="1" required />
                            </div>
                            <div className="flex gap-3 pt-3">
                                <button type="button" onClick={() => setRafModalOpen(false)} className="flex-1 h-11 rounded-xl border border-slate-200 font-bold text-slate-600 hover:bg-slate-50">İptal</button>
                                <button type="submit" className="flex-1 h-11 rounded-xl bg-violet-600 font-bold text-white hover:bg-violet-700 shadow-lg transition-all">Kaydet</button>
                            </div>
                        </form>
                    </div>
                </div>,
                document.body
            )}
        </div>
    );
}
