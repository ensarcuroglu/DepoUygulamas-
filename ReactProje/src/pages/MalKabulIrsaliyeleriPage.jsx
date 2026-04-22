import { useState, useEffect, useRef } from 'react';
import {
    Plus, Search, Loader2, X, Truck, Package, CheckCircle, Clock,
    ChevronDown, Trash2, FileCheck, Calendar, MapPin, User,
    ArrowRight, Lock, AlertTriangle, Info
} from 'lucide-react';
import {
    getMalKabulIrsaliyeleri, createMalKabulIrsaliye,
    deleteMalKabulIrsaliye, getTedarikciler, getDepolar, getUrunler, getRaflar,
    onaylaMalKabulIrsaliye, malKabulKalemiIstisnaGuncelle, updateMalKabulIrsaliye
} from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

const durumRenkleri = {
    'Taslak': 'bg-slate-100 text-slate-700 border-slate-200/60',
    'Onaylandi': 'bg-blue-50 text-blue-700 border-blue-200/60',
    'Kapandi': 'bg-emerald-50 text-emerald-700 border-emerald-200/60',
};

const durumEtiketleri = {
    'Taslak': 'Taslak',
    'Onaylandi': 'Onaylandı',
    'Kapandi': 'Kapandı',
};

export default function MalKabulIrsaliyeleriPage() {
    const { loading, run } = useAsync(true);
    const { user } = useAuth();
    const navigate = useNavigate();
    const [irsaliyeler, setIrsaliyeler] = useState([]);
    const [tedarikciler, setTedarikciler] = useState([]);
    const [depolar, setDepolar] = useState([]);
    const [urunler, setUrunler] = useState([]);
    const [raflar, setRaflar] = useState([]);

    const [aramaMetni, setAramaMetni] = useState('');
    const [durumFiltre, setDurumFiltre] = useState('');
    const [yeniModal, setYeniModal] = useState(false);
    const [aktifIrsaliyeId, setAktifIrsaliyeId] = useState(null);
    const [duzenlemeSnapshot, setDuzenlemeSnapshot] = useState(null);
    const [expandedId, setExpandedId] = useState(null);
    const [onayOzet, setOnayOzet] = useState(null);
    const aramaMetniRef = useRef(aramaMetni);
    const [istisnaAcikKalem, setIstisnaAcikKalem] = useState(null);
    const [istisnaForm, setIstisnaForm] = useState({ istisna_tip: '', istisna_aciklama: '', gerceklesen_miktar: '' });

    const [formData, setFormData] = useState({
        tedarikci_id: '',
        depo_id: '',
        tarih: new Date().toISOString().split('T')[0],
        tir_plaka: '',
        sofor_adi: '',
        kalemler: [],
    });

    const bosKalem = { palet_no: '', urun_id: '', lot_no: '', miktar: '', raf_id: '', uretim_tarihi: '', son_kullanma_tarihi: '' };
    const kullaniciRolu = user?.rol;
    const canCreateOrApprove = kullaniciRolu === 'admin' || kullaniciRolu === 'depocu';
    const canDelete = kullaniciRolu === 'admin';

    const formuSifirla = () => {
        setFormData({
            tedarikci_id: '',
            depo_id: '',
            tarih: new Date().toISOString().split('T')[0],
            tir_plaka: '',
            sofor_adi: '',
            kalemler: [],
        });
    };

    const modalKapat = () => {
        setYeniModal(false);
        setAktifIrsaliyeId(null);
        setDuzenlemeSnapshot(null);
        formuSifirla();
    };

    const yeniIrsaliyeModalAc = () => {
        setAktifIrsaliyeId(null);
        setDuzenlemeSnapshot(null);
        formuSifirla();
        setYeniModal(true);
    };

    const duzenlemeModalAc = (irs) => {
        const normalizeKalem = (kalem) => ({
            palet_no: kalem.palet_no || '',
            urun_id: String(kalem.urun_id ?? ''),
            lot_no: kalem.lot_no || '',
            miktar: String(kalem.miktar ?? ''),
            raf_id: kalem.raf_id ? String(kalem.raf_id) : '',
            uretim_tarihi: kalem.uretim_tarihi || '',
            son_kullanma_tarihi: kalem.son_kullanma_tarihi || '',
        });

        const snapshot = {
            tedarikci_id: String(irs.tedarikci_id ?? ''),
            depo_id: String(irs.depo_id ?? ''),
            tarih: irs.tarih || '',
            tir_plaka: irs.tir_plaka || '',
            sofor_adi: irs.sofor_adi || '',
            kalemler: (irs.kalemler || []).map(normalizeKalem),
        };

        setAktifIrsaliyeId(irs.id);
        setDuzenlemeSnapshot(snapshot);
        setFormData({
            ...snapshot,
            tarih: snapshot.tarih || new Date().toISOString().split('T')[0],
        });
        setYeniModal(true);
    };

    const alanDegistiMi = (alan) => {
        if (!duzenlemeSnapshot) return false;
        return String(formData[alan] ?? '') !== String(duzenlemeSnapshot[alan] ?? '');
    };

    const kalemAlandegistiMi = (index, alan) => {
        if (!duzenlemeSnapshot) return false;
        const snapshotKalem = duzenlemeSnapshot.kalemler?.[index];
        if (!snapshotKalem) return false;
        return String(formData.kalemler?.[index]?.[alan] ?? '') !== String(snapshotKalem[alan] ?? '');
    };

    const degisenAlanSinifi = (degisti) =>
        degisti ? 'border-amber-300 ring-2 ring-amber-200 bg-amber-50/40' : '';

    // ===== REFERANS VERİLERİ =====
    useEffect(() => {
        const referansYukle = async () => {
            try {
                const [tedRes, depRes, urnRes, rafRes] = await Promise.all([
                    getTedarikciler({ limit: 500 }),
                    getDepolar({ limit: 500 }),
                    getUrunler({ limit: 500 }),
                    getRaflar({ limit: 1000 }),
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
        // Mobilde yeni kalem eklenince hafif bir scroll hissi için timeout eklenebilir
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
        if (!canCreateOrApprove) {
            toast.error('Bu işlem için yetkiniz yok');
            return;
        }
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

            if (aktifIrsaliyeId) {
                await updateMalKabulIrsaliye(aktifIrsaliyeId, payload);
                toast.success('Mal kabul irsaliyesi güncellendi');
            } else {
                await createMalKabulIrsaliye(payload);
                toast.success('Mal kabul irsaliyesi oluşturuldu');
            }
            modalKapat();
            yukle();
        } catch (err) {
            toast.error(hataMetni(err, aktifIrsaliyeId ? 'İrsaliye güncellenemedi' : 'İrsaliye oluşturulamadı'));
        }
    };

    // ===== ONAYLA =====
    const handleOnayla = async (irs) => {
        if (!canCreateOrApprove) {
            toast.error('Bu işlem için yetkiniz yok');
            return;
        }
        try {
            const res = await onaylaMalKabulIrsaliye(irs.id);
            const veri = res?.data ?? {};
            setOnayOzet({
                irsaliye_no: veri.irsaliye_no ?? irs.irsaliye_no,
                palet_sayisi: veri.kalemler?.length ?? irs.kalemler?.length ?? 0,
                gorev_sayisi: veri.olusturulan_gorev_sayisi ?? veri.kalemler?.length ?? 0,
            });
            yukle();
        } catch (err) {
            toast.error(hataMetni(err, 'İrsaliye onaylanamadı'));
        }
    };

    // ===== İSTİSNA BİLDİR =====
    const handleIstisnaBildir = async (irsaliyeId, kalemId) => {
        if (!canCreateOrApprove) {
            toast.error('Bu işlem için yetkiniz yok');
            return;
        }
        if (!istisnaForm.istisna_tip) {
            toast.error('İstisna tipi seçilmesi zorunludur');
            return;
        }
        try {
            await malKabulKalemiIstisnaGuncelle(irsaliyeId, kalemId, {
                istisna_tip: istisnaForm.istisna_tip,
                istisna_aciklama: istisnaForm.istisna_aciklama || null,
                gerceklesen_miktar: istisnaForm.gerceklesen_miktar ? Number(istisnaForm.gerceklesen_miktar) : null,
            });
            toast.success('Fark/hasar kaydedildi');
            setIstisnaAcikKalem(null);
            setIstisnaForm({ istisna_tip: '', istisna_aciklama: '', gerceklesen_miktar: '' });
            yukle();
        } catch (err) {
            toast.error(hataMetni(err, 'İstisna kaydedilemedi'));
        }
    };

    // ===== SİL =====
    const handleSil = async (id) => {
        if (!canDelete) {
            toast.error('Bu işlem için yetkiniz yok');
            return;
        }
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
        <div className="min-h-screen bg-slate-50/50 pb-20 md:pb-10 font-sans text-slate-800">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 md:pt-8 space-y-6">
                
                {/* BAŞLIK + YENİ BUTONU */}
                <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">İrsaliyeli Kabul</h1>
                        <p className="text-sm md:text-base text-slate-500 mt-1">Tedarikçilerden gelen irsaliyeleri ve depo girişlerini yönetin</p>
                    </div>
                    {canCreateOrApprove && (
                        <button
                            onClick={yeniIrsaliyeModalAc}
                            className="flex items-center justify-center gap-2 h-12 px-6 bg-blue-600 text-white rounded-2xl hover:bg-blue-700 active:bg-blue-800 transition-all shadow-md shadow-blue-600/20 text-sm font-semibold w-full sm:w-auto"
                        >
                            <Plus className="w-5 h-5" />
                            Yeni İrsaliye
                        </button>
                    )}
                </div>

                {/* ONAYLA SONRASI ÖZET BANNER */}
                {onayOzet && (
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/60 rounded-2xl p-5 shadow-sm">
                        <div className="flex items-start gap-4">
                            <div className="w-12 h-12 rounded-2xl bg-white shadow-sm flex items-center justify-center shrink-0">
                                <CheckCircle className="w-6 h-6 text-blue-600" />
                            </div>
                            <div>
                                <p className="font-extrabold text-blue-950 text-base">
                                    {onayOzet.irsaliye_no} onaylandı
                                </p>
                                <p className="text-blue-800/80 text-sm mt-1 leading-relaxed">
                                    <span className="font-semibold text-blue-900">{onayOzet.palet_sayisi} palet</span> kabul edildi
                                    <span className="mx-2 opacity-50">•</span>
                                    <span className="font-semibold text-blue-900">{onayOzet.gorev_sayisi} yerleştirme görevi</span> oluşturuldu
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => navigate('/yerlestirme-gorevleri')}
                                className="flex-1 sm:flex-none flex items-center justify-center gap-2 h-11 px-5 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors shadow-sm"
                            >
                                Yerleştirmeye Başla <ArrowRight className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => setOnayOzet(null)}
                                className="p-2.5 text-blue-400 hover:text-blue-700 bg-white rounded-xl shadow-sm hover:bg-blue-50 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                )}

                {/* FİLTRELER */}
                <div className="bg-white p-2 rounded-2xl shadow-sm border border-slate-200/60 flex flex-col sm:flex-row gap-2">
                    <div className="relative flex-1">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                        <input
                            type="text"
                            placeholder="İrsaliye no, plaka, şoför ara..."
                            value={aramaMetni}
                            onChange={e => setAramaMetni(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && yukle()}
                            className="w-full pl-11 pr-4 h-12 bg-transparent text-sm focus:ring-0 focus:outline-none placeholder:text-slate-400"
                        />
                    </div>
                    <div className="w-full sm:w-56 border-t sm:border-t-0 sm:border-l border-slate-100">
                        <div className="relative">
                            <select
                                value={durumFiltre}
                                onChange={e => setDurumFiltre(e.target.value)}
                                className="w-full h-12 pl-4 pr-10 bg-transparent text-sm focus:ring-0 focus:outline-none appearance-none cursor-pointer text-slate-700 font-medium"
                            >
                                <option value="">Tüm Durumlar</option>
                                <option value="Taslak">Taslak</option>
                                <option value="Onaylandi">Onaylandı</option>
                                <option value="Kapandi">Kapandı</option>
                            </select>
                            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                        </div>
                    </div>
                </div>

                {/* LİSTE */}
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-32">
                        <Loader2 className="w-10 h-10 animate-spin text-blue-600 mb-4" />
                        <p className="text-slate-500 font-medium animate-pulse">İrsaliyeler yükleniyor...</p>
                    </div>
                ) : irsaliyeler.length === 0 ? (
                    <div className="text-center py-24 bg-white border border-slate-200/60 rounded-3xl shadow-sm">
                        <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-5">
                            <FileCheck className="w-10 h-10 text-slate-300" />
                        </div>
                        <h3 className="text-slate-900 font-extrabold text-lg">Kayıt Bulunamadı</h3>
                        <p className="text-slate-500 mt-2 max-w-sm mx-auto text-sm leading-relaxed">Arama kriterlerinize uygun mal kabul irsaliyesi bulunmuyor veya henüz sisteme giriş yapılmamış.</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {irsaliyeler.map(irs => (
                            <div key={irs.id} className={`bg-white border transition-all duration-200 rounded-2xl shadow-sm overflow-hidden group ${expandedId === irs.id ? 'border-blue-200 ring-1 ring-blue-100' : 'border-slate-200/70 hover:border-slate-300'}`}>
                                {/* HEADER - Tıklanabilir Alan */}
                                <div
                                    className="flex flex-col sm:flex-row sm:items-center justify-between p-4 sm:p-5 cursor-pointer select-none"
                                    onClick={() => setExpandedId(expandedId === irs.id ? null : irs.id)}
                                >
                                    <div className="flex items-start sm:items-center gap-4">
                                        <div className={`hidden sm:flex w-14 h-14 rounded-2xl items-center justify-center shrink-0 transition-colors ${expandedId === irs.id ? 'bg-blue-600 text-white shadow-md shadow-blue-200' : 'bg-slate-50 text-slate-400 border border-slate-100 group-hover:bg-blue-50 group-hover:text-blue-600 group-hover:border-blue-100'}`}>
                                            <FileCheck className="w-6 h-6" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-3 mb-1.5">
                                                <h3 className="font-extrabold text-slate-900 text-lg tracking-tight truncate">{irs.irsaliye_no}</h3>
                                                <span className={`px-2.5 py-1 rounded-lg border text-[11px] font-bold tracking-wide uppercase ${durumRenkleri[irs.durum] || ''}`}>
                                                    {durumEtiketleri[irs.durum] || irs.durum}
                                                </span>
                                            </div>
                                            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-slate-500 font-medium">
                                                <span className="flex items-center gap-1.5"><User className="w-4 h-4 text-slate-400" /> <span className="truncate max-w-[120px] sm:max-w-none">{tedarikciAdi(irs.tedarikci_id)}</span></span>
                                                <span className="flex items-center gap-1.5"><MapPin className="w-4 h-4 text-slate-400" /> <span className="truncate max-w-[100px] sm:max-w-none">{depoAdi(irs.depo_id)}</span></span>
                                                <span className="flex items-center gap-1.5"><Calendar className="w-4 h-4 text-slate-400" /> {irs.tarih}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between sm:justify-end gap-4 mt-5 sm:mt-0 pt-4 sm:pt-0 border-t sm:border-0 border-slate-100">
                                        <div className="flex items-center gap-3">
                                            <div className="text-sm font-bold text-slate-700 bg-slate-100/70 px-3.5 py-1.5 rounded-xl border border-slate-200/50">
                                                {irs.kalemler?.length || 0} <span className="text-slate-500 font-medium">Palet</span>
                                            </div>
                                            {irs.istisna_sayisi > 0 && (
                                                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 border border-amber-200/60 text-amber-700 rounded-xl text-xs font-bold shadow-sm">
                                                    <AlertTriangle className="w-4 h-4" />
                                                    {irs.istisna_sayisi} Fark
                                                </div>
                                            )}
                                        </div>
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${expandedId === irs.id ? 'bg-blue-100 text-blue-600 rotate-180' : 'bg-slate-50 text-slate-400 group-hover:bg-slate-100 group-hover:text-slate-600'}`}>
                                            <ChevronDown className="w-5 h-5" />
                                        </div>
                                    </div>
                                </div>

                                {/* DETAY (EXPANDED) */}
                                {expandedId === irs.id && (
                                    <div className="border-t border-slate-100 bg-slate-50/30">
                                        <div className="p-4 sm:p-6">
                                            
                                            {/* Operasyon İlerleme Çubuğu */}
                                            {irs.durum !== 'Taslak' && irs.toplam_kalem > 0 && (
                                                <div className="mb-6 bg-white border border-slate-200/60 rounded-2xl p-4 sm:p-5 shadow-sm">
                                                    <div className="flex items-end justify-between mb-3">
                                                        <div>
                                                            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 block">Yerleştirme Durumu</span>
                                                            <div className="flex items-baseline gap-2">
                                                                <span className="text-2xl font-black text-slate-800">{irs.yerlestirilen}</span>
                                                                <span className="text-sm font-medium text-slate-400">/ {irs.toplam_kalem}</span>
                                                            </div>
                                                        </div>
                                                        <span className="text-xl font-bold text-slate-300">
                                                            {irs.toplam_kalem > 0 ? Math.round((irs.yerlestirilen / irs.toplam_kalem) * 100) : 0}%
                                                        </span>
                                                    </div>
                                                    <div className="w-full bg-slate-100 rounded-full h-3 p-0.5 border border-slate-200/50">
                                                        <div
                                                            className={`h-full rounded-full transition-all duration-700 ease-out ${
                                                                irs.yerlestirilen === irs.toplam_kalem ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]' : 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.3)]'
                                                            }`}
                                                            style={{ width: `${irs.toplam_kalem > 0 ? (irs.yerlestirilen / irs.toplam_kalem) * 100 : 0}%` }}
                                                        />
                                                    </div>
                                                    <div className="flex flex-wrap items-center gap-4 mt-4 text-xs font-medium">
                                                        <span className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-md">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                                            {irs.yerlestirilen} Yerleşti
                                                        </span>
                                                        <span className="flex items-center gap-1.5 text-amber-600 bg-amber-50 px-2.5 py-1 rounded-md">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                                                            {irs.bekleyen} Bekliyor
                                                        </span>
                                                        {irs.istisna_sayisi > 0 && (
                                                            <span className="flex items-center gap-1.5 text-red-600 bg-red-50 px-2.5 py-1 rounded-md ml-auto">
                                                                <AlertTriangle className="w-3.5 h-3.5" />
                                                                {irs.istisna_sayisi} İstisna
                                                            </span>
                                                        )}
                                                    </div>

                                                    {irs.durum === 'Kapandi' && irs.kapanma_ozeti && (
                                                        <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-4 gap-3">
                                                            <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                                                                <div className="text-[10px] text-slate-400 uppercase font-bold mb-1">Ort. Süre</div>
                                                                <div className="text-sm font-semibold text-slate-700">{irs.kapanma_ozeti.ort_yerlestirme_sure_dk || '-'} dk</div>
                                                            </div>
                                                            {irs.kapanma_ozeti.iptal_edilen > 0 && (
                                                                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                                                                    <div className="text-[10px] text-slate-400 uppercase font-bold mb-1">İptal Edilen</div>
                                                                    <div className="text-sm font-semibold text-slate-700">{irs.kapanma_ozeti.iptal_edilen}</div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            )}

                                            {/* Meta Bilgi Kartları (Plaka, Şoför) */}
                                            <div className="flex flex-wrap gap-3 mb-6">
                                                {irs.tir_plaka && (
                                                    <div className="bg-white border border-slate-200/80 px-4 py-2.5 rounded-xl text-sm flex items-center gap-2.5 shadow-sm">
                                                        <div className="bg-slate-100 p-1.5 rounded-lg"><Truck className="w-4 h-4 text-slate-500" /></div>
                                                        <div>
                                                            <div className="text-[10px] font-bold text-slate-400 uppercase">Araç Plakası</div>
                                                            <div className="font-bold text-slate-800">{irs.tir_plaka}</div>
                                                        </div>
                                                    </div>
                                                )}
                                                {irs.sofor_adi && (
                                                    <div className="bg-white border border-slate-200/80 px-4 py-2.5 rounded-xl text-sm flex items-center gap-2.5 shadow-sm">
                                                        <div className="bg-slate-100 p-1.5 rounded-lg"><User className="w-4 h-4 text-slate-500" /></div>
                                                        <div>
                                                            <div className="text-[10px] font-bold text-slate-400 uppercase">Şoför</div>
                                                            <div className="font-bold text-slate-800">{irs.sofor_adi}</div>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Kalemler - Responsive Render */}
                                            <div className="mb-2">
                                                <h4 className="text-sm font-extrabold text-slate-800 mb-4 flex items-center gap-2">
                                                    <Package className="w-4 h-4 text-slate-400" /> İrsaliye İçeriği
                                                </h4>
                                                
                                                {irs.kalemler && irs.kalemler.length > 0 ? (
                                                    <>
                                                        {/* Desktop Tablo Görünümü */}
                                                        <div className="hidden lg:block overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                                                            <table className="w-full text-sm text-left">
                                                                <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-bold text-xs uppercase tracking-wider">
                                                                    <tr>
                                                                        <th className="px-5 py-4">Palet No</th>
                                                                        <th className="px-5 py-4">Ürün</th>
                                                                        <th className="px-5 py-4">Lot No</th>
                                                                        <th className="px-5 py-4 text-center">Miktar</th>
                                                                        <th className="px-5 py-4">Raf</th>
                                                                        <th className="px-5 py-4">SKT</th>
                                                                        <th className="px-5 py-4">Durum</th>
                                                                        <th className="px-5 py-4 text-right">Aksiyon</th>
                                                                    </tr>
                                                                </thead>
                                                                <tbody className="divide-y divide-slate-100">
                                                                    {irs.kalemler.map(kalem => {
                                                                        const istisnaAcik = istisnaAcikKalem?.irsaliyeId === irs.id && istisnaAcikKalem?.kalemId === kalem.id;
                                                                        return (
                                                                            <tr key={kalem.id} className="hover:bg-slate-50/50 transition-colors group/row">
                                                                                <td className="px-5 py-4 font-mono text-xs font-bold text-blue-700 bg-blue-50/30">{kalem.palet_no}</td>
                                                                                <td className="px-5 py-4 font-semibold text-slate-800">{urunAdi(kalem.urun_id)}</td>
                                                                                <td className="px-5 py-4 text-slate-500 font-medium">{kalem.lot_no || '-'}</td>
                                                                                <td className="px-5 py-4 text-center font-black text-slate-700 text-base">{kalem.miktar}</td>
                                                                                <td className="px-5 py-4 text-slate-500">{kalem.raf_id ? rafKodu(kalem.raf_id) : '-'}</td>
                                                                                <td className="px-5 py-4 text-slate-500">{kalem.son_kullanma_tarihi || '-'}</td>
                                                                                <td className="px-5 py-4">
                                                                                    {kalem.durum === 'GirisYapildi' ? (
                                                                                        <span className="inline-flex items-center gap-1.5 text-emerald-700 bg-emerald-50 border border-emerald-100 px-2.5 py-1 rounded-lg text-xs font-bold">
                                                                                            <CheckCircle className="w-3.5 h-3.5" /> Kabul Edildi
                                                                                        </span>
                                                                                    ) : (
                                                                                        <span className="inline-flex items-center gap-1.5 text-amber-700 bg-amber-50 border border-amber-100 px-2.5 py-1 rounded-lg text-xs font-bold">
                                                                                            <Clock className="w-3.5 h-3.5" /> Bekliyor
                                                                                        </span>
                                                                                    )}
                                                                                </td>
                                                                                <td className="px-5 py-4 text-right">
                                                                                    {kalem.istisna_tip ? (
                                                                                        <div className="inline-flex flex-col items-end">
                                                                                            <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-red-50 border border-red-100 text-red-700 rounded-lg text-xs font-bold mb-1">
                                                                                                <AlertTriangle className="w-3.5 h-3.5" /> {kalem.istisna_tip}
                                                                                            </span>
                                                                                            {kalem.istisna_aciklama && <span className="text-[10px] text-slate-400 max-w-[120px] truncate" title={kalem.istisna_aciklama}>{kalem.istisna_aciklama}</span>}
                                                                                        </div>
                                                                                    ) : canCreateOrApprove && irs.durum !== 'Kapandi' ? (
                                                                                        <div className="relative">
                                                                                            <button
                                                                                                onClick={() => {
                                                                                                    setIstisnaAcikKalem(istisnaAcik ? null : { irsaliyeId: irs.id, kalemId: kalem.id });
                                                                                                    setIstisnaForm({ istisna_tip: '', istisna_aciklama: '', gerceklesen_miktar: '' });
                                                                                                }}
                                                                                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${istisnaAcik ? 'bg-amber-100 text-amber-800' : 'bg-white border border-slate-200 text-slate-600 hover:border-amber-200 hover:text-amber-600 hover:bg-amber-50 shadow-sm'}`}
                                                                                            >
                                                                                                <AlertTriangle className="w-3.5 h-3.5" /> Fark
                                                                                            </button>
                                                                                            
                                                                                            {/* Desktop Popover Form */}
                                                                                            {istisnaAcik && (
                                                                                                <div className="absolute right-0 top-full mt-2 w-72 bg-white rounded-2xl shadow-xl border border-slate-200 p-4 z-10 animate-in fade-in slide-in-from-top-2">
                                                                                                    <div className="mb-3 border-b border-slate-100 pb-2 flex justify-between items-center">
                                                                                                        <span className="font-bold text-sm text-slate-800">Fark Bildir</span>
                                                                                                        <button onClick={() => setIstisnaAcikKalem(null)} className="text-slate-400 hover:text-slate-600"><X className="w-4 h-4"/></button>
                                                                                                    </div>
                                                                                                    <div className="space-y-3 text-left">
                                                                                                        <div>
                                                                                                            <label className="block text-xs font-bold text-slate-600 mb-1">İstisna Tipi *</label>
                                                                                                            <select
                                                                                                                value={istisnaForm.istisna_tip}
                                                                                                                onChange={e => setIstisnaForm(f => ({ ...f, istisna_tip: e.target.value }))}
                                                                                                                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:ring-2 focus:ring-amber-400 outline-none transition-all"
                                                                                                            >
                                                                                                                <option value="">Seçin...</option>
                                                                                                                <option value="Eksik">Eksik Miktar</option>
                                                                                                                <option value="Fazla">Fazla Miktar</option>
                                                                                                                <option value="Hasarlı">Hasarlı Ürün</option>
                                                                                                                <option value="YanlışÜrün">Yanlış Ürün</option>
                                                                                                                <option value="OkunamamazBarkod">Okunamaz Barkod</option>
                                                                                                                <option value="Diğer">Diğer</option>
                                                                                                            </select>
                                                                                                        </div>
                                                                                                        <div>
                                                                                                            <label className="block text-xs font-bold text-slate-600 mb-1">Gerçekleşen Miktar <span className="font-normal text-slate-400">(Sistemde: {kalem.miktar})</span></label>
                                                                                                            <input
                                                                                                                type="number" min="0" placeholder="Opsiyonel"
                                                                                                                value={istisnaForm.gerceklesen_miktar}
                                                                                                                onChange={e => setIstisnaForm(f => ({ ...f, gerceklesen_miktar: e.target.value }))}
                                                                                                                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:ring-2 focus:ring-amber-400 outline-none transition-all"
                                                                                                            />
                                                                                                        </div>
                                                                                                        <div>
                                                                                                            <label className="block text-xs font-bold text-slate-600 mb-1">Açıklama</label>
                                                                                                            <input
                                                                                                                type="text" placeholder="Kısa açıklama..."
                                                                                                                value={istisnaForm.istisna_aciklama}
                                                                                                                onChange={e => setIstisnaForm(f => ({ ...f, istisna_aciklama: e.target.value }))}
                                                                                                                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:ring-2 focus:ring-amber-400 outline-none transition-all"
                                                                                                            />
                                                                                                        </div>
                                                                                                        <button
                                                                                                            onClick={() => handleIstisnaBildir(irs.id, kalem.id)}
                                                                                                            className="w-full mt-2 py-2.5 bg-slate-900 text-white text-sm font-bold rounded-xl hover:bg-slate-800 transition-colors"
                                                                                                        >
                                                                                                            Kaydet
                                                                                                        </button>
                                                                                                    </div>
                                                                                                </div>
                                                                                            )}
                                                                                        </div>
                                                                                    ) : <span className="text-slate-300 text-sm font-medium">—</span>}
                                                                                </td>
                                                                            </tr>
                                                                        );
                                                                    })}
                                                                </tbody>
                                                            </table>
                                                        </div>

                                                        {/* Mobile / Tablet Kart Görünümü */}
                                                        <div className="lg:hidden space-y-4">
                                                            {irs.kalemler.map((kalem, idx) => {
                                                                const istisnaAcikMobil = istisnaAcikKalem?.irsaliyeId === irs.id && istisnaAcikKalem?.kalemId === kalem.id;
                                                                return (
                                                                    <div key={kalem.id || idx} className={`bg-white p-4 rounded-2xl border transition-all shadow-sm flex flex-col gap-4 ${istisnaAcikMobil ? 'border-amber-300 ring-4 ring-amber-50' : 'border-slate-200'}`}>
                                                                        <div className="flex justify-between items-start gap-2">
                                                                            <div className="flex-1">
                                                                                <span className="inline-block px-2.5 py-1 bg-blue-50 text-blue-700 border border-blue-100 font-mono text-xs font-bold rounded-lg mb-2">
                                                                                    {kalem.palet_no}
                                                                                </span>
                                                                                <h4 className="font-extrabold text-slate-800 text-base leading-tight">{urunAdi(kalem.urun_id)}</h4>
                                                                            </div>
                                                                            <div className="shrink-0 mt-1">
                                                                                {kalem.durum === 'GirisYapildi' ? (
                                                                                    <span className="flex items-center justify-center w-8 h-8 bg-emerald-50 rounded-full border border-emerald-100"><CheckCircle className="w-5 h-5 text-emerald-500" /></span>
                                                                                ) : (
                                                                                    <span className="flex items-center justify-center w-8 h-8 bg-amber-50 rounded-full border border-amber-100"><Clock className="w-5 h-5 text-amber-500" /></span>
                                                                                )}
                                                                            </div>
                                                                        </div>
                                                                        
                                                                        <div className="grid grid-cols-2 gap-2 text-sm">
                                                                            <div className="bg-slate-50/80 p-2.5 rounded-xl border border-slate-100 flex flex-col">
                                                                                <span className="text-[10px] uppercase font-bold text-slate-400 mb-0.5">Miktar</span>
                                                                                <span className="font-black text-slate-700 text-base">{kalem.miktar}</span>
                                                                            </div>
                                                                            <div className="bg-slate-50/80 p-2.5 rounded-xl border border-slate-100 flex flex-col">
                                                                                <span className="text-[10px] uppercase font-bold text-slate-400 mb-0.5">Lot No</span>
                                                                                <span className="font-semibold text-slate-700">{kalem.lot_no || '-'}</span>
                                                                            </div>
                                                                            <div className="bg-slate-50/80 p-2.5 rounded-xl border border-slate-100 flex flex-col">
                                                                                <span className="text-[10px] uppercase font-bold text-slate-400 mb-0.5">Raf</span>
                                                                                <span className="font-semibold text-slate-700">{kalem.raf_id ? rafKodu(kalem.raf_id) : '-'}</span>
                                                                            </div>
                                                                            <div className="bg-slate-50/80 p-2.5 rounded-xl border border-slate-100 flex flex-col">
                                                                                <span className="text-[10px] uppercase font-bold text-slate-400 mb-0.5">SKT</span>
                                                                                <span className="font-semibold text-slate-700">{kalem.son_kullanma_tarihi || '-'}</span>
                                                                            </div>
                                                                        </div>

                                                                        {kalem.istisna_tip ? (
                                                                            <div className="bg-red-50 border border-red-100 p-3 rounded-xl flex items-start gap-2.5">
                                                                                <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                                                                                <div>
                                                                                    <div className="font-bold text-red-800 text-sm">{kalem.istisna_tip} Bildirildi</div>
                                                                                    {kalem.istisna_aciklama && <div className="text-xs text-red-600 mt-0.5 leading-relaxed">{kalem.istisna_aciklama}</div>}
                                                                                </div>
                                                                            </div>
                                                                        ) : canCreateOrApprove && irs.durum !== 'Kapandi' && !istisnaAcikMobil && (
                                                                            <button
                                                                                onClick={() => {
                                                                                    setIstisnaAcikKalem({ irsaliyeId: irs.id, kalemId: kalem.id });
                                                                                    setIstisnaForm({ istisna_tip: '', istisna_aciklama: '', gerceklesen_miktar: '' });
                                                                                }}
                                                                                className="flex items-center justify-center gap-2 h-11 w-full border border-slate-200 bg-white text-slate-700 rounded-xl text-sm font-bold shadow-sm hover:bg-slate-50 active:bg-slate-100"
                                                                            >
                                                                                <Info className="w-4 h-4 text-slate-400" /> Eksik/Fark Bildir
                                                                            </button>
                                                                        )}

                                                                        {istisnaAcikMobil && (
                                                                            <div className="flex flex-col gap-3 bg-amber-50/50 border border-amber-200 rounded-xl p-4 mt-2">
                                                                                <div className="flex justify-between items-center mb-1">
                                                                                    <span className="font-bold text-amber-900 text-sm">Durum Bildirimi</span>
                                                                                    <button onClick={() => setIstisnaAcikKalem(null)} className="p-1 text-amber-600/50 hover:text-amber-600 bg-amber-100/50 rounded-lg"><X className="w-4 h-4"/></button>
                                                                                </div>
                                                                                <div className="space-y-3">
                                                                                    <select
                                                                                        value={istisnaForm.istisna_tip}
                                                                                        onChange={e => setIstisnaForm(f => ({ ...f, istisna_tip: e.target.value }))}
                                                                                        className="w-full h-12 px-3 text-sm border border-amber-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-amber-400 font-medium text-slate-700"
                                                                                    >
                                                                                        <option value="">İstisna tipi seçin *</option>
                                                                                        <option value="Eksik">Eksik</option>
                                                                                        <option value="Fazla">Fazla</option>
                                                                                        <option value="Hasarlı">Hasarlı</option>
                                                                                        <option value="YanlışÜrün">Yanlış Ürün</option>
                                                                                        <option value="OkunamamazBarkod">Okunamaz Barkod</option>
                                                                                        <option value="Diğer">Diğer</option>
                                                                                    </select>
                                                                                    <input
                                                                                        type="number" min="0"
                                                                                        placeholder={`Gerçekleşen miktar (Sistem: ${kalem.miktar})`}
                                                                                        value={istisnaForm.gerceklesen_miktar}
                                                                                        onChange={e => setIstisnaForm(f => ({ ...f, gerceklesen_miktar: e.target.value }))}
                                                                                        className="w-full h-12 px-3 text-sm border border-amber-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-amber-400 placeholder-slate-400"
                                                                                    />
                                                                                    <input
                                                                                        type="text"
                                                                                        placeholder="Açıklama (opsiyonel)"
                                                                                        value={istisnaForm.istisna_aciklama}
                                                                                        onChange={e => setIstisnaForm(f => ({ ...f, istisna_aciklama: e.target.value }))}
                                                                                        className="w-full h-12 px-3 text-sm border border-amber-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-amber-400 placeholder-slate-400"
                                                                                    />
                                                                                    <button 
                                                                                        onClick={() => handleIstisnaBildir(irs.id, kalem.id)} 
                                                                                        className="w-full h-12 bg-slate-900 text-white text-sm font-bold rounded-xl active:scale-[0.98] transition-transform shadow-md shadow-slate-900/20"
                                                                                    >
                                                                                        Kaydet ve Kapat
                                                                                    </button>
                                                                                </div>
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                );
                                                            })}
                                                        </div>
                                                    </>
                                                ) : (
                                                    <div className="text-center py-8 text-slate-400 bg-slate-50 rounded-2xl border border-slate-100 text-sm font-medium">Bu irsaliyede henüz kalem bulunmuyor.</div>
                                                )}
                                            </div>

                                            {/* Alt Aksiyonlar */}
                                            <div className="flex flex-col sm:flex-row items-center gap-3 mt-6 pt-6 border-t border-slate-200/60">
                                                {irs.durum === 'Taslak' && (
                                                    <>
                                                        {canCreateOrApprove && (
                                                            <button
                                                                onClick={() => duzenlemeModalAc(irs)}
                                                                className="w-full sm:w-auto flex justify-center items-center gap-2 h-12 px-6 bg-white border-2 border-slate-200 text-slate-600 rounded-xl text-sm font-bold hover:border-blue-200 hover:text-blue-700 hover:bg-blue-50 transition-colors order-1 sm:order-1"
                                                            >
                                                                Düzenle
                                                            </button>
                                                        )}
                                                        {canCreateOrApprove && (
                                                            <button
                                                                onClick={() => handleOnayla(irs)}
                                                                className="w-full sm:w-auto sm:flex-1 flex justify-center items-center gap-2 h-12 px-6 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 active:bg-blue-800 transition-colors shadow-sm shadow-blue-600/20 order-2 sm:order-2"
                                                            >
                                                                <CheckCircle className="w-5 h-5" /> İrsaliyeyi Onayla
                                                            </button>
                                                        )}
                                                        {canDelete && (
                                                            <button
                                                                onClick={() => handleSil(irs.id)}
                                                                className="w-full sm:w-auto flex justify-center items-center gap-2 h-12 px-6 bg-white border-2 border-slate-200 text-slate-600 rounded-xl text-sm font-bold hover:border-red-200 hover:text-red-600 hover:bg-red-50 transition-colors order-3 sm:order-3"
                                                            >
                                                                <Trash2 className="w-5 h-5" /> Sil
                                                            </button>
                                                        )}
                                                    </>
                                                )}
                                                {irs.durum === 'Onaylandi' && (
                                                    <div className="w-full flex flex-col sm:flex-row items-stretch gap-3">
                                                        <div className="flex-1 flex items-center justify-center gap-2 h-12 bg-blue-50 border border-blue-200 text-blue-700 rounded-xl text-sm font-bold">
                                                            <Loader2 className="w-5 h-5 animate-spin" />
                                                            Yerleştirme devam ediyor...
                                                        </div>
                                                        <button
                                                            onClick={() => navigate('/yerlestirme-gorevleri')}
                                                            className="flex items-center justify-center gap-2 h-12 px-6 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 active:bg-blue-800 transition-colors shadow-sm shadow-blue-600/20"
                                                        >
                                                            Yerleştirmeye Git <ArrowRight className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                )}
                                                {irs.durum === 'Kapandi' && (
                                                    <div className="w-full flex items-center justify-center gap-2 h-12 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl text-sm font-bold">
                                                        <Lock className="w-5 h-5" />
                                                        Tüm işlemler tamamlandı
                                                    </div>
                                                )}
                                            </div>

                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* YENİ İRSALİYE MODAL (Mobile First Bottom Sheet -> Desktop Centered Modal) */}
                {yeniModal && canCreateOrApprove && (
                    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-end sm:items-center justify-center z-50 p-0 sm:p-4 transition-opacity">
                        <div className="bg-white w-full sm:max-w-4xl max-h-[92vh] sm:max-h-[85vh] h-full sm:h-auto rounded-t-3xl sm:rounded-3xl shadow-2xl flex flex-col transform transition-transform animate-in slide-in-from-bottom-8 sm:slide-in-from-bottom-0 sm:zoom-in-95 duration-300 overflow-hidden">

                            {/* Modal Header (Sticky) */}
                            <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-white z-10 shrink-0">
                                <div>
                                    <h2 className="text-xl font-extrabold text-slate-900">{aktifIrsaliyeId ? 'İrsaliyeyi Düzenle' : 'Yeni İrsaliye'}</h2>
                                    <p className="text-xs text-slate-500 mt-0.5 font-medium">
                                        {aktifIrsaliyeId ? 'Taslak irsaliye kaydını güncelleyin' : 'Sisteme yeni bir mal kabul kaydı girin'}
                                    </p>
                                    {aktifIrsaliyeId && (
                                        <p className="text-[11px] text-amber-700 mt-1 font-semibold">
                                            Değiştirdiğiniz alanlar sarı ile vurgulanır.
                                        </p>
                                    )}
                                </div>
                                <button onClick={modalKapat} className="w-10 h-10 bg-slate-50 hover:bg-slate-100 text-slate-500 rounded-full flex items-center justify-center transition-colors">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Modal Body (Scrollable) */}
                            <div className="flex-1 overflow-y-auto p-5 sm:p-8 space-y-8 bg-slate-50/50 relative">

                                {/* Ana Bilgiler Formu */}
                                <section className="bg-white p-5 sm:p-6 rounded-2xl border border-slate-200/60 shadow-sm">
                                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-5 flex items-center gap-2">
                                        Genel Bilgiler
                                    </h3>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                                        <div className="space-y-1.5">
                                            <label className="text-xs font-bold text-slate-700 ml-1">Tedarikçi <span className="text-red-500">*</span></label>
                                            <div className="relative">
                                                <select
                                                    value={formData.tedarikci_id}
                                                    onChange={e => setFormData(prev => ({ ...prev, tedarikci_id: e.target.value }))}
                                                    className={`w-full h-12 pl-4 pr-10 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none appearance-none cursor-pointer ${degisenAlanSinifi(alanDegistiMi('tedarikci_id'))}`}
                                                >
                                                    <option value="">Seçiniz...</option>
                                                    {tedarikciler.map(t => (
                                                        <option key={t.id} value={t.id}>{t.firma_adi}</option>
                                                    ))}
                                                </select>
                                                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                                            </div>
                                        </div>
                                        <div className="space-y-1.5">
                                            <label className="text-xs font-bold text-slate-700 ml-1">Depo <span className="text-red-500">*</span></label>
                                            <div className="relative">
                                                <select
                                                    value={formData.depo_id}
                                                    onChange={e => setFormData(prev => ({ ...prev, depo_id: e.target.value }))}
                                                    className={`w-full h-12 pl-4 pr-10 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none appearance-none cursor-pointer ${degisenAlanSinifi(alanDegistiMi('depo_id'))}`}
                                                >
                                                    <option value="">Seçiniz...</option>
                                                    {depolar.map(d => (
                                                        <option key={d.id} value={d.id}>{d.isim}</option>
                                                    ))}
                                                </select>
                                                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                                            </div>
                                        </div>
                                        <div className="space-y-1.5">
                                            <label className="text-xs font-bold text-slate-700 ml-1">Kabul Tarihi <span className="text-red-500">*</span></label>
                                            <input
                                                type="date"
                                                value={formData.tarih}
                                                onChange={e => setFormData(prev => ({ ...prev, tarih: e.target.value }))}
                                                className={`w-full h-12 px-4 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none ${degisenAlanSinifi(alanDegistiMi('tarih'))}`}
                                            />
                                        </div>
                                        <div className="space-y-1.5">
                                            <label className="text-xs font-bold text-slate-700 ml-1">Araç Plakası</label>
                                            <input
                                                type="text"
                                                value={formData.tir_plaka}
                                                onChange={e => setFormData(prev => ({ ...prev, tir_plaka: e.target.value }))}
                                                placeholder="Örn: 34 ABC 123"
                                                className={`w-full h-12 px-4 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none placeholder-slate-400 ${degisenAlanSinifi(alanDegistiMi('tir_plaka'))}`}
                                            />
                                        </div>
                                        <div className="space-y-1.5 sm:col-span-2 lg:col-span-2">
                                            <label className="text-xs font-bold text-slate-700 ml-1">Şoför Adı Soyadı</label>
                                            <input
                                                type="text"
                                                value={formData.sofor_adi}
                                                onChange={e => setFormData(prev => ({ ...prev, sofor_adi: e.target.value }))}
                                                placeholder="Örn: Ahmet Yılmaz"
                                                className={`w-full h-12 px-4 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none placeholder-slate-400 ${degisenAlanSinifi(alanDegistiMi('sofor_adi'))}`}
                                            />
                                        </div>
                                    </div>
                                </section>

                                {/* Kalemler */}
                                <section>
                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider ml-1">
                                            Palet / Ürün Listesi
                                        </h3>
                                        <button
                                            onClick={kalemEkle}
                                            className="flex items-center justify-center gap-2 h-10 px-5 text-sm font-bold text-blue-700 bg-blue-100/50 hover:bg-blue-100 rounded-xl transition-colors"
                                        >
                                            <Plus className="w-4 h-4" /> Kalem Ekle
                                        </button>
                                    </div>

                                    {formData.kalemler.length === 0 ? (
                                        <div className="text-center py-12 bg-white border-2 border-dashed border-slate-200 rounded-2xl">
                                            <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-3">
                                                <Package className="w-8 h-8 text-slate-300" />
                                            </div>
                                            <p className="text-slate-600 font-bold text-sm">Henüz kalem eklenmedi</p>
                                            <p className="text-slate-400 text-xs mt-1 px-4">Gelen ürünleri kaydetmek için yukarıdan yeni kalem ekleyin.</p>
                                        </div>
                                    ) : (
                                        <div className="space-y-4">
                                            {formData.kalemler.map((kalem, idx) => (
                                                <div key={idx} className={`p-4 sm:p-5 border border-slate-200 rounded-2xl bg-white shadow-sm flex flex-col gap-4 relative animate-in fade-in zoom-in-95 duration-200 ${duzenlemeSnapshot?.kalemler?.[idx] ? '' : 'border-blue-200 ring-2 ring-blue-100'}`}>
                                                    <div className="flex justify-between items-center pb-3 border-b border-slate-100">
                                                        <h4 className="text-xs font-extrabold text-blue-600 uppercase bg-blue-50 px-2.5 py-1 rounded-md">Kalem #{idx + 1}</h4>
                                                        <button 
                                                            onClick={() => kalemSil(idx)} 
                                                            className="flex items-center gap-1.5 text-xs font-bold text-red-500 hover:text-red-700 bg-red-50 hover:bg-red-100 px-2.5 py-1.5 rounded-lg transition-colors"
                                                        >
                                                            <Trash2 className="w-3.5 h-3.5" /> Sil
                                                        </button>
                                                    </div>

                                                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                                                        <div className="lg:col-span-1">
                                                            <input
                                                                type="text" placeholder="Palet No *" value={kalem.palet_no}
                                                                onChange={e => kalemGuncelle(idx, 'palet_no', e.target.value)}
                                                                className={`w-full h-11 px-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none ${degisenAlanSinifi(kalemAlandegistiMi(idx, 'palet_no'))}`}
                                                            />
                                                        </div>
                                                        <div className="lg:col-span-2 relative">
                                                            <select
                                                                value={kalem.urun_id}
                                                                onChange={e => kalemGuncelle(idx, 'urun_id', e.target.value)}
                                                                className={`w-full h-11 pl-3 pr-8 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none appearance-none ${degisenAlanSinifi(kalemAlandegistiMi(idx, 'urun_id'))}`}
                                                            >
                                                                <option value="">Ürün Seçin *</option>
                                                                {urunler.map(u => (
                                                                    <option key={u.id} value={u.id}>{u.isim}</option>
                                                                ))}
                                                            </select>
                                                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                                                        </div>
                                                        <div className="lg:col-span-1">
                                                            <input
                                                                type="number" placeholder="Miktar *" value={kalem.miktar} min="1"
                                                                onChange={e => kalemGuncelle(idx, 'miktar', e.target.value)}
                                                                className={`w-full h-11 px-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none ${degisenAlanSinifi(kalemAlandegistiMi(idx, 'miktar'))}`}
                                                            />
                                                        </div>
                                                        <div className="lg:col-span-1">
                                                            <input
                                                                type="text" placeholder="Lot No" value={kalem.lot_no}
                                                                onChange={e => kalemGuncelle(idx, 'lot_no', e.target.value)}
                                                                className={`w-full h-11 px-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none ${degisenAlanSinifi(kalemAlandegistiMi(idx, 'lot_no'))}`}
                                                            />
                                                        </div>
                                                        <div className="lg:col-span-1 relative">
                                                            <select
                                                                value={kalem.raf_id}
                                                                onChange={e => kalemGuncelle(idx, 'raf_id', e.target.value)}
                                                                className={`w-full h-11 pl-3 pr-8 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none appearance-none ${degisenAlanSinifi(kalemAlandegistiMi(idx, 'raf_id'))}`}
                                                            >
                                                                <option value="">Raf (Ops.)</option>
                                                                {raflar.map(r => (
                                                                    <option key={r.id} value={r.id}>{r.kod}</option>
                                                                ))}
                                                            </select>
                                                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                                                        </div>
                                                        <div className="lg:col-span-2 relative">
                                                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-bold bg-white px-1">ÜT:</span>
                                                            <input
                                                                type="date" value={kalem.uretim_tarihi}
                                                                onChange={e => kalemGuncelle(idx, 'uretim_tarihi', e.target.value)}
                                                                className={`w-full h-11 pl-12 pr-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none ${degisenAlanSinifi(kalemAlandegistiMi(idx, 'uretim_tarihi'))}`}
                                                            />
                                                        </div>
                                                        <div className="lg:col-span-2 relative">
                                                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-bold bg-white px-1">SKT:</span>
                                                            <input
                                                                type="date" value={kalem.son_kullanma_tarihi}
                                                                onChange={e => kalemGuncelle(idx, 'son_kullanma_tarihi', e.target.value)}
                                                                className={`w-full h-11 pl-12 pr-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none ${degisenAlanSinifi(kalemAlandegistiMi(idx, 'son_kullanma_tarihi'))}`}
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    {formData.kalemler.length > 0 && (
                                         <button
                                            onClick={kalemEkle}
                                            className="w-full mt-4 flex items-center justify-center gap-2 h-12 text-sm font-bold text-slate-500 bg-transparent border-2 border-dashed border-slate-200 hover:border-slate-300 hover:text-slate-700 rounded-xl transition-colors"
                                        >
                                            <Plus className="w-4 h-4" /> Yeni Satır Ekle
                                        </button>
                                    )}
                                </section>
                            </div>

                            {/* Modal Footer (Sticky) */}
                            <div className="p-4 sm:p-5 border-t border-slate-100 bg-white z-10 shrink-0 flex flex-col sm:flex-row-reverse gap-3 pb-safe">
                                <button
                                    onClick={handleOlustur}
                                    className="w-full sm:w-auto h-12 px-8 text-sm font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 active:bg-blue-800 shadow-sm shadow-blue-600/20 transition-all flex items-center justify-center"
                                >
                                    {aktifIrsaliyeId ? 'Değişiklikleri Kaydet' : 'İrsaliyeyi Kaydet'}
                                </button>
                                <button
                                    onClick={modalKapat}
                                    className="w-full sm:w-auto h-12 px-8 text-sm font-bold text-slate-600 bg-slate-50 hover:bg-slate-100 rounded-xl transition-colors flex items-center justify-center"
                                >
                                    Vazgeç
                                </button>
                            </div>
                            
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}