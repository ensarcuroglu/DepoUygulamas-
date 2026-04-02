import { useState, useEffect, useRef } from 'react';
import {
    Plus, Search, Loader2, X, Truck, Package, CheckCircle, Clock,
    ChevronDown, ChevronUp, Trash2, FileCheck, Calendar, MapPin, User
} from 'lucide-react';
import {
    getMalKabulIrsaliyeleri, createMalKabulIrsaliye, updateMalKabulIrsaliye,
    deleteMalKabulIrsaliye, getTedarikciler, getDepolar, getUrunler, getRaflar
} from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const durumRenkleri = {
    'Taslak': 'bg-slate-100 text-slate-700 border-slate-200',
    'Onaylandi': 'bg-blue-50 text-blue-700 border-blue-200',
    'Tamamlandi': 'bg-emerald-50 text-emerald-700 border-emerald-200',
};

const durumEtiketleri = {
    'Taslak': 'Taslak',
    'Onaylandi': 'Onaylandı',
    'Tamamlandi': 'Tamamlandı',
};

export default function MalKabulIrsaliyeleriPage() {
    const { loading, run } = useAsync(true);
    const [irsaliyeler, setIrsaliyeler] = useState([]);
    const [tedarikciler, setTedarikciler] = useState([]);
    const [depolar, setDepolar] = useState([]);
    const [urunler, setUrunler] = useState([]);
    const [raflar, setRaflar] = useState([]);

    const [aramaMetni, setAramaMetni] = useState('');
    const [durumFiltre, setDurumFiltre] = useState('');
    const [yeniModal, setYeniModal] = useState(false);
    const [expandedId, setExpandedId] = useState(null);
    const aramaMetniRef = useRef(aramaMetni);

    const [formData, setFormData] = useState({
        tedarikci_id: '',
        depo_id: '',
        tarih: new Date().toISOString().split('T')[0],
        tir_plaka: '',
        sofor_adi: '',
        kalemler: [],
    });

    const bosKalem = { palet_no: '', urun_id: '', lot_no: '', miktar: '', raf_id: '', uretim_tarihi: '', son_kullanma_tarihi: '' };

    // ===== REFERANS VERİLERİ =====
    useEffect(() => {
        const referansYukle = async () => {
            try {
                const [tedRes, depRes, urnRes, rafRes] = await Promise.all([
                    getTedarikciler({ limit: 500 }),
                    getDepolar(),
                    getUrunler({ limit: 500 }),
                    getRaflar(),
                ]);
                setTedarikciler(tedRes?.data || []);
                setDepolar(depRes?.data || []);
                setUrunler(urnRes?.data || []);
                setRaflar(rafRes?.data || []);
            } catch {
                toast.error('Referans verileri yüklenemedi');
            }
        };
        referansYukle();
    }, []);

    // ===== İRSALİYE LİSTESİ =====
    const yukle = async () => {
        try {
            const irsRes = await run(() =>
                getMalKabulIrsaliyeleri({ limit: 100, durum: durumFiltre || undefined, arama: aramaMetni || undefined })
            );
            setIrsaliyeler(irsRes?.data || []);
        } catch {
            toast.error('İrsaliyeler yüklenemedi');
        }
    };

    useEffect(() => {
        aramaMetniRef.current = aramaMetni;
    }, [aramaMetni]);

    useEffect(() => {
        let aktif = true;

        run(() =>
            getMalKabulIrsaliyeleri({
                limit: 100,
                durum: durumFiltre || undefined,
                arama: aramaMetniRef.current || undefined,
            })
        )
            .then((irsRes) => {
                if (aktif) {
                    setIrsaliyeler(irsRes?.data || []);
                }
            })
            .catch(() => {
                if (aktif) {
                    toast.error('İrsaliyeler yüklenemedi');
                }
            });

        return () => {
            aktif = false;
        };
    }, [durumFiltre, run]);

    // ===== KALEM YÖNETİMİ =====
    const kalemEkle = () => {
        setFormData(prev => ({ ...prev, kalemler: [...prev.kalemler, { ...bosKalem }] }));
    };

    const kalemGuncelle = (index, field, value) => {
        setFormData(prev => {
            const yeni = [...prev.kalemler];
            yeni[index] = { ...yeni[index], [field]: value };
            return { ...prev, kalemler: yeni };
        });
    };

    const kalemSil = (index) => {
        setFormData(prev => ({
            ...prev,
            kalemler: prev.kalemler.filter((_, i) => i !== index),
        }));
    };

    // ===== İRSALİYE OLUŞTUR =====
    const handleOlustur = async () => {
        if (!formData.tedarikci_id || !formData.depo_id || !formData.tarih) {
            toast.error('Tedarikçi, depo ve tarih zorunludur');
            return;
        }

        try {
            const payload = {
                tedarikci_id: Number(formData.tedarikci_id),
                depo_id: Number(formData.depo_id),
                tarih: formData.tarih,
                tir_plaka: formData.tir_plaka || null,
                sofor_adi: formData.sofor_adi || null,
                kalemler: formData.kalemler
                    .filter(k => k.palet_no && k.urun_id && k.miktar)
                    .map(k => ({
                        palet_no: k.palet_no,
                        urun_id: Number(k.urun_id),
                        lot_no: k.lot_no || null,
                        miktar: Number(k.miktar),
                        raf_id: k.raf_id ? Number(k.raf_id) : null,
                        uretim_tarihi: k.uretim_tarihi || null,
                        son_kullanma_tarihi: k.son_kullanma_tarihi || null,
                    })),
            };

            await createMalKabulIrsaliye(payload);
            toast.success('Mal kabul irsaliyesi oluşturuldu');
            setYeniModal(false);
            setFormData({
                tedarikci_id: '', depo_id: '', tarih: new Date().toISOString().split('T')[0],
                tir_plaka: '', sofor_adi: '', kalemler: [],
            });
            yukle();
        } catch (err) {
            toast.error(hataMetni(err, 'İrsaliye oluşturulamadı'));
        }
    };

    // ===== DURUM DEĞİŞTİR =====
    const durumDegistir = async (id, yeniDurum) => {
        try {
            await updateMalKabulIrsaliye(id, { durum: yeniDurum });
            toast.success(`Durum güncellendi: ${durumEtiketleri[yeniDurum]}`);
            yukle();
        } catch (err) {
            toast.error(hataMetni(err, 'Durum güncellenemedi'));
        }
    };

    // ===== SİL =====
    const handleSil = async (id) => {
        if (!window.confirm('Bu irsaliyeyi silmek istediğinize emin misiniz?')) return;
        try {
            await deleteMalKabulIrsaliye(id);
            toast.success('İrsaliye silindi');
            yukle();
        } catch (err) {
            toast.error(hataMetni(err, 'İrsaliye silinemedi'));
        }
    };

    // ===== HELPER =====
    const urunAdi = (id) => urunler.find(u => u.id === id)?.isim || '-';
    const tedarikciAdi = (id) => tedarikciler.find(t => t.id === id)?.firma_adi || '-';
    const depoAdi = (id) => depolar.find(d => d.id === id)?.isim || '-';
    const rafKodu = (id) => raflar.find(r => r.id === id)?.kod || '-';

    // ===== RENDER =====
    return (
        <div className="space-y-6 md:space-y-8 max-w-7xl mx-auto pb-10">
            {/* BAŞLIK + KONTROLLER */}
            <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">Mal Kabul İrsaliyeleri</h1>
                    <p className="text-sm md:text-base text-slate-500 mt-1">Tedarikçilerden gelen irsaliyeleri ve depo girişlerini yönetin</p>
                </div>
                <button
                    onClick={() => setYeniModal(true)}
                    className="flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 active:bg-blue-800 transition-all shadow-sm shadow-blue-200 text-sm font-semibold w-full sm:w-auto"
                >
                    <Plus className="w-5 h-5" />
                    Yeni İrsaliye
                </button>
            </div>

            {/* FİLTRELER */}
            <div className="flex flex-col sm:flex-row gap-3 bg-white p-3 rounded-2xl shadow-sm border border-slate-200/60">
                <div className="relative flex-1">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        placeholder="İrsaliye no, plaka, şoför ara..."
                        value={aramaMetni}
                        onChange={e => setAramaMetni(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && yukle()}
                        className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border-transparent rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                    />
                </div>
                <div className="w-full sm:w-48">
                    <select
                        value={durumFiltre}
                        onChange={e => setDurumFiltre(e.target.value)}
                        className="w-full px-4 py-2.5 bg-slate-50 border-transparent rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none appearance-none cursor-pointer"
                    >
                        <option value="">Tüm Durumlar</option>
                        <option value="Taslak">Taslak</option>
                        <option value="Onaylandi">Onaylandı</option>
                        <option value="Tamamlandi">Tamamlandı</option>
                    </select>
                </div>
            </div>

            {/* LİSTE */}
            {loading ? (
                <div className="flex flex-col items-center justify-center py-20">
                    <Loader2 className="w-10 h-10 animate-spin text-blue-500 mb-4" />
                    <p className="text-slate-500 font-medium">İrsaliyeler yükleniyor...</p>
                </div>
            ) : irsaliyeler.length === 0 ? (
                <div className="text-center py-20 bg-slate-50 border-2 border-dashed border-slate-200 rounded-3xl">
                    <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
                        <Truck className="w-8 h-8 text-slate-400" />
                    </div>
                    <h3 className="text-slate-900 font-bold text-lg">Kayıt Bulunamadı</h3>
                    <p className="text-slate-500 mt-1 max-w-sm mx-auto">Arama kriterlerinize uygun mal kabul irsaliyesi bulunmuyor veya henüz hiç eklenmemiş.</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {irsaliyeler.map(irs => (
                        <div key={irs.id} className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow overflow-hidden group">
                            {/* HEADER */}
                            <div
                                className="flex flex-col sm:flex-row sm:items-center justify-between p-4 sm:p-5 cursor-pointer"
                                onClick={() => setExpandedId(expandedId === irs.id ? null : irs.id)}
                            >
                                <div className="flex items-start sm:items-center gap-4">
                                    <div className="hidden sm:flex w-12 h-12 rounded-2xl bg-blue-50/50 border border-blue-100 items-center justify-center shrink-0">
                                        <FileCheck className="w-6 h-6 text-blue-600" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-3 mb-1">
                                            <h3 className="font-bold text-slate-900 truncate">{irs.irsaliye_no}</h3>
                                            <span className={`px-2.5 py-0.5 rounded-md border text-[11px] font-bold tracking-wide uppercase ${durumRenkleri[irs.durum] || ''}`}>
                                                {durumEtiketleri[irs.durum] || irs.durum}
                                            </span>
                                        </div>
                                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 font-medium">
                                            <span className="flex items-center gap-1"><User className="w-3.5 h-3.5" /> {tedarikciAdi(irs.tedarikci_id)}</span>
                                            <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {depoAdi(irs.depo_id)}</span>
                                            <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {irs.tarih}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center justify-between sm:justify-end gap-4 mt-4 sm:mt-0 w-full sm:w-auto pt-4 sm:pt-0 border-t sm:border-0 border-slate-100">
                                    <div className="text-sm font-semibold text-slate-700 bg-slate-50 px-3 py-1.5 rounded-lg">
                                        {irs.kalemler?.length || 0} <span className="text-slate-500 font-normal">Palet</span>
                                    </div>
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${expandedId === irs.id ? 'bg-blue-50 text-blue-600' : 'bg-slate-50 text-slate-400 group-hover:bg-slate-100 group-hover:text-slate-600'}`}>
                                        {expandedId === irs.id ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                                    </div>
                                </div>
                            </div>

                            {/* DETAY (EXPANDED) */}
                            {expandedId === irs.id && (
                                <div className="border-t border-slate-100 bg-slate-50/50">
                                    <div className="p-4 sm:p-5">
                                        {/* Meta bilgi */}
                                        <div className="flex flex-wrap gap-4 mb-6">
                                            {irs.tir_plaka && (
                                                <div className="bg-white border border-slate-200 px-3 py-2 rounded-xl text-sm flex items-center gap-2">
                                                    <Truck className="w-4 h-4 text-slate-400" />
                                                    <span className="text-slate-500">Plaka:</span>
                                                    <span className="font-bold text-slate-700">{irs.tir_plaka}</span>
                                                </div>
                                            )}
                                            {irs.sofor_adi && (
                                                <div className="bg-white border border-slate-200 px-3 py-2 rounded-xl text-sm flex items-center gap-2">
                                                    <User className="w-4 h-4 text-slate-400" />
                                                    <span className="text-slate-500">Şoför:</span>
                                                    <span className="font-bold text-slate-700">{irs.sofor_adi}</span>
                                                </div>
                                            )}
                                        </div>

                                        {/* Kalemler - Responsive Render */}
                                        {irs.kalemler && irs.kalemler.length > 0 ? (
                                            <>
                                                {/* Desktop Tablo Görünümü */}
                                                <div className="hidden md:block overflow-hidden rounded-xl border border-slate-200 bg-white">
                                                    <table className="w-full text-sm text-left">
                                                        <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs uppercase tracking-wider">
                                                            <tr>
                                                                <th className="px-4 py-3">Palet No</th>
                                                                <th className="px-4 py-3">Ürün</th>
                                                                <th className="px-4 py-3">Lot No</th>
                                                                <th className="px-4 py-3 text-right">Miktar</th>
                                                                <th className="px-4 py-3">Raf</th>
                                                                <th className="px-4 py-3">SKT</th>
                                                                <th className="px-4 py-3">Durum</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody className="divide-y divide-slate-100">
                                                            {irs.kalemler.map(kalem => (
                                                                <tr key={kalem.id} className="hover:bg-slate-50/50 transition-colors">
                                                                    <td className="px-4 py-3 font-mono text-xs font-bold text-blue-700">{kalem.palet_no}</td>
                                                                    <td className="px-4 py-3 font-medium text-slate-700">{urunAdi(kalem.urun_id)}</td>
                                                                    <td className="px-4 py-3 text-slate-500">{kalem.lot_no || '-'}</td>
                                                                    <td className="px-4 py-3 text-right font-bold text-slate-700">{kalem.miktar}</td>
                                                                    <td className="px-4 py-3 text-slate-500">{kalem.raf_id ? rafKodu(kalem.raf_id) : '-'}</td>
                                                                    <td className="px-4 py-3 text-slate-500">{kalem.son_kullanma_tarihi || '-'}</td>
                                                                    <td className="px-4 py-3">
                                                                        {kalem.durum === 'GirisYapildi' ? (
                                                                            <span className="inline-flex items-center gap-1.5 text-emerald-700 bg-emerald-50 px-2 py-1 rounded-md text-xs font-bold">
                                                                                <CheckCircle className="w-3.5 h-3.5" /> Giriş Yapıldı
                                                                            </span>
                                                                        ) : (
                                                                            <span className="inline-flex items-center gap-1.5 text-amber-700 bg-amber-50 px-2 py-1 rounded-md text-xs font-bold">
                                                                                <Clock className="w-3.5 h-3.5" /> Bekliyor
                                                                            </span>
                                                                        )}
                                                                    </td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>

                                                {/* Mobile Kart Görünümü */}
                                                <div className="md:hidden space-y-3">
                                                    {irs.kalemler.map((kalem, idx) => (
                                                        <div key={kalem.id || idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
                                                            <div className="flex justify-between items-start">
                                                                <div>
                                                                    <span className="inline-block px-2 py-1 bg-blue-50 text-blue-700 font-mono text-xs font-bold rounded mb-1">
                                                                        {kalem.palet_no}
                                                                    </span>
                                                                    <h4 className="font-bold text-slate-800">{urunAdi(kalem.urun_id)}</h4>
                                                                </div>
                                                                {kalem.durum === 'GirisYapildi' ? (
                                                                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                                                                ) : (
                                                                    <Clock className="w-5 h-5 text-amber-500" />
                                                                )}
                                                            </div>
                                                            <div className="grid grid-cols-2 gap-2 text-sm">
                                                                <div className="bg-slate-50 p-2 rounded-lg">
                                                                    <div className="text-xs text-slate-400 mb-0.5">Miktar</div>
                                                                    <div className="font-bold text-slate-700">{kalem.miktar}</div>
                                                                </div>
                                                                <div className="bg-slate-50 p-2 rounded-lg">
                                                                    <div className="text-xs text-slate-400 mb-0.5">Lot No</div>
                                                                    <div className="font-medium text-slate-700">{kalem.lot_no || '-'}</div>
                                                                </div>
                                                                <div className="bg-slate-50 p-2 rounded-lg">
                                                                    <div className="text-xs text-slate-400 mb-0.5">Raf</div>
                                                                    <div className="font-medium text-slate-700">{kalem.raf_id ? rafKodu(kalem.raf_id) : '-'}</div>
                                                                </div>
                                                                <div className="bg-slate-50 p-2 rounded-lg">
                                                                    <div className="text-xs text-slate-400 mb-0.5">SKT</div>
                                                                    <div className="font-medium text-slate-700">{kalem.son_kullanma_tarihi || '-'}</div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </>
                                        ) : (
                                            <div className="text-center py-6 text-slate-400 text-sm">Bu irsaliyede henüz kalem bulunmuyor.</div>
                                        )}

                                        {/* Aksiyonlar */}
                                        <div className="flex flex-wrap items-center gap-3 mt-6">
                                            {irs.durum === 'Taslak' && (
                                                <>
                                                    <button
                                                        onClick={() => durumDegistir(irs.id, 'Onaylandi')}
                                                        className="flex-1 sm:flex-none flex justify-center items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors shadow-sm"
                                                    >
                                                        <CheckCircle className="w-4 h-4" /> Onayla
                                                    </button>
                                                    <button
                                                        onClick={() => handleSil(irs.id)}
                                                        className="flex-1 sm:flex-none flex justify-center items-center gap-2 px-4 py-2.5 bg-white border border-red-200 text-red-600 rounded-xl text-sm font-semibold hover:bg-red-50 transition-colors"
                                                    >
                                                        <Trash2 className="w-4 h-4" /> Sil
                                                    </button>
                                                </>
                                            )}
                                            {irs.durum === 'Onaylandi' && (
                                                <button
                                                    onClick={() => durumDegistir(irs.id, 'Tamamlandi')}
                                                    className="w-full sm:w-auto flex justify-center items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-colors shadow-sm"
                                                >
                                                    <CheckCircle className="w-4 h-4" /> Tamamla
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* YENİ İRSALİYE MODAL */}
            {yeniModal && (
                <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
                    <div className="bg-white w-full sm:max-w-4xl max-h-[90vh] sm:max-h-[85vh] rounded-t-3xl sm:rounded-2xl shadow-2xl flex flex-col transform transition-all animate-in slide-in-from-bottom-4 sm:slide-in-from-bottom-0 sm:zoom-in-95 duration-200">

                        {/* Modal Header */}
                        <div className="flex items-center justify-between p-5 sm:px-6 sm:py-5 border-b border-slate-100 shrink-0">
                            <div>
                                <h2 className="text-xl font-extrabold text-slate-900">Yeni İrsaliye Oluştur</h2>
                                <p className="text-xs text-slate-500 mt-0.5">Sisteme yeni bir mal kabul kaydı girin</p>
                            </div>
                            <button onClick={() => setYeniModal(false)} className="p-2 bg-slate-50 hover:bg-slate-100 text-slate-500 rounded-full transition-colors">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-8">

                            {/* Ana Bilgiler Formu */}
                            <section>
                                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                                    <FileCheck className="w-4 h-4 text-blue-500" /> İrsaliye Bilgileri
                                </h3>
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                    <div className="space-y-1.5">
                                        <label className="text-xs font-semibold text-slate-600">Tedarikçi <span className="text-red-500">*</span></label>
                                        <select
                                            value={formData.tedarikci_id}
                                            onChange={e => setFormData(prev => ({ ...prev, tedarikci_id: e.target.value }))}
                                            className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none appearance-none"
                                        >
                                            <option value="">Seçiniz...</option>
                                            {tedarikciler.map(t => (
                                                <option key={t.id} value={t.id}>{t.firma_adi}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="text-xs font-semibold text-slate-600">Depo <span className="text-red-500">*</span></label>
                                        <select
                                            value={formData.depo_id}
                                            onChange={e => setFormData(prev => ({ ...prev, depo_id: e.target.value }))}
                                            className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none appearance-none"
                                        >
                                            <option value="">Seçiniz...</option>
                                            {depolar.map(d => (
                                                <option key={d.id} value={d.id}>{d.isim}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="text-xs font-semibold text-slate-600">Kabul Tarihi <span className="text-red-500">*</span></label>
                                        <input
                                            type="date"
                                            value={formData.tarih}
                                            onChange={e => setFormData(prev => ({ ...prev, tarih: e.target.value }))}
                                            className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="text-xs font-semibold text-slate-600">Araç Plakası</label>
                                        <input
                                            type="text"
                                            value={formData.tir_plaka}
                                            onChange={e => setFormData(prev => ({ ...prev, tir_plaka: e.target.value }))}
                                            placeholder="Örn: 34 ABC 123"
                                            className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                                        />
                                    </div>
                                    <div className="space-y-1.5 sm:col-span-2 lg:col-span-2">
                                        <label className="text-xs font-semibold text-slate-600">Şoför Adı Soyadı</label>
                                        <input
                                            type="text"
                                            value={formData.sofor_adi}
                                            onChange={e => setFormData(prev => ({ ...prev, sofor_adi: e.target.value }))}
                                            placeholder="Örn: Ahmet Yılmaz"
                                            className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                                        />
                                    </div>
                                </div>
                            </section>

                            <hr className="border-slate-100" />

                            {/* Kalemler */}
                            <section>
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                                    <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                                        <Package className="w-4 h-4 text-blue-500" /> Palet / Ürün Kalemleri
                                    </h3>
                                    <button
                                        onClick={kalemEkle}
                                        className="flex items-center justify-center gap-1.5 px-4 py-2 text-sm font-bold text-blue-700 bg-blue-50 border border-blue-100 rounded-xl hover:bg-blue-100 transition-colors"
                                    >
                                        <Plus className="w-4 h-4" /> Yeni Kalem Ekle
                                    </button>
                                </div>

                                {formData.kalemler.length === 0 ? (
                                    <div className="text-center py-10 bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl">
                                        <Package className="w-10 h-10 mx-auto mb-3 text-slate-300" />
                                        <p className="text-slate-500 font-medium text-sm">İrsaliyeye henüz kalem eklemediniz.</p>
                                        <p className="text-slate-400 text-xs mt-1">Gelen ürünleri kaydetmek için yukarıdan kalem ekleyin.</p>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {formData.kalemler.map((kalem, idx) => (
                                            <div key={idx} className="relative p-4 sm:p-5 border border-slate-200 rounded-2xl bg-white shadow-sm group">
                                                <div className="absolute top-4 right-4">
                                                    <button onClick={() => kalemSil(idx)} className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Kalem #{idx + 1}</h4>

                                                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                                                    <input
                                                        type="text"
                                                        placeholder="Palet No *"
                                                        value={kalem.palet_no}
                                                        onChange={e => kalemGuncelle(idx, 'palet_no', e.target.value)}
                                                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                                                    />
                                                    <select
                                                        value={kalem.urun_id}
                                                        onChange={e => kalemGuncelle(idx, 'urun_id', e.target.value)}
                                                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none appearance-none"
                                                    >
                                                        <option value="">Ürün Seçin *</option>
                                                        {urunler.map(u => (
                                                            <option key={u.id} value={u.id}>{u.isim}</option>
                                                        ))}
                                                    </select>
                                                    <input
                                                        type="number"
                                                        placeholder="Miktar *"
                                                        value={kalem.miktar}
                                                        onChange={e => kalemGuncelle(idx, 'miktar', e.target.value)}
                                                        min="1"
                                                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                                                    />
                                                    <input
                                                        type="text"
                                                        placeholder="Lot Numarası"
                                                        value={kalem.lot_no}
                                                        onChange={e => kalemGuncelle(idx, 'lot_no', e.target.value)}
                                                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                                                    />
                                                    <select
                                                        value={kalem.raf_id}
                                                        onChange={e => kalemGuncelle(idx, 'raf_id', e.target.value)}
                                                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none appearance-none"
                                                    >
                                                        <option value="">Raf (Opsiyonel)</option>
                                                        {raflar.map(r => (
                                                            <option key={r.id} value={r.id}>{r.kod}</option>
                                                        ))}
                                                    </select>
                                                    <div className="relative">
                                                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-medium">SKT:</span>
                                                        <input
                                                            type="date"
                                                            value={kalem.son_kullanma_tarihi}
                                                            onChange={e => kalemGuncelle(idx, 'son_kullanma_tarihi', e.target.value)}
                                                            className="w-full pl-10 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </section>
                        </div>

                        {/* Modal Footer */}
                        <div className="p-4 sm:p-5 border-t border-slate-100 bg-slate-50 rounded-b-3xl sm:rounded-b-2xl flex flex-col-reverse sm:flex-row justify-end gap-3 shrink-0">
                            <button
                                onClick={() => setYeniModal(false)}
                                className="w-full sm:w-auto px-6 py-2.5 text-sm font-bold text-slate-600 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors"
                            >
                                Vazgeç
                            </button>
                            <button
                                onClick={handleOlustur}
                                className="w-full sm:w-auto px-6 py-2.5 text-sm font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 shadow-sm shadow-blue-200 transition-colors"
                            >
                                İrsaliyeyi Kaydet
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
