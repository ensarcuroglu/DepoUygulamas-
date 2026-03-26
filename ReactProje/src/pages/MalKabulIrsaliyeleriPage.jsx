import { useState, useEffect } from 'react';
import {
    Plus, Search, Loader2, X, Truck, Package, CheckCircle, Clock,
    ChevronDown, ChevronUp, Trash2, FileCheck
} from 'lucide-react';
import {
    getMalKabulIrsaliyeleri, createMalKabulIrsaliye, updateMalKabulIrsaliye,
    deleteMalKabulIrsaliye, getTedarikciler, getDepolar, getUrunler, getRaflar
} from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const durumRenkleri = {
    'Taslak': 'bg-slate-100 text-slate-800 border border-slate-300',
    'Onaylandi': 'bg-blue-100 text-blue-800 border border-blue-300',
    'Tamamlandi': 'bg-emerald-100 text-emerald-800 border border-emerald-300',
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

    const [formData, setFormData] = useState({
        tedarikci_id: '',
        depo_id: '',
        tarih: new Date().toISOString().split('T')[0],
        tir_plaka: '',
        sofor_adi: '',
        kalemler: [],
    });

    const bosKalem = { palet_no: '', urun_id: '', lot_no: '', miktar: '', raf_id: '', uretim_tarihi: '', son_kullanma_tarihi: '' };

    // ===== REFERANS VERİLERİ (bir kez yükle) =====
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

    useEffect(() => { yukle(); }, [durumFiltre]);

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
        if (!confirm('Bu irsaliyeyi silmek istediğinize emin misiniz?')) return;
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
        <div className="space-y-6">
            {/* BAŞLIK + KONTROLLER */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Mal Kabul İrsaliyeleri</h1>
                    <p className="text-sm text-slate-500 mt-1">Tedarikçilerden gelen mal kabul belgelerini yönetin</p>
                </div>
                <button
                    onClick={() => setYeniModal(true)}
                    className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                    <Plus className="w-4 h-4" />
                    Yeni İrsaliye
                </button>
            </div>

            {/* FİLTRELER */}
            <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        placeholder="İrsaliye no, plaka, şoför ara..."
                        value={aramaMetni}
                        onChange={e => setAramaMetni(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && yukle()}
                        className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                </div>
                <select
                    value={durumFiltre}
                    onChange={e => setDurumFiltre(e.target.value)}
                    className="px-4 py-2.5 border border-slate-200 rounded-lg text-sm bg-white"
                >
                    <option value="">Tüm Durumlar</option>
                    <option value="Taslak">Taslak</option>
                    <option value="Onaylandi">Onaylandı</option>
                    <option value="Tamamlandi">Tamamlandı</option>
                </select>
            </div>

            {/* LİSTE */}
            {loading ? (
                <div className="flex justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                </div>
            ) : irsaliyeler.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                    <Truck className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>Henüz mal kabul irsaliyesi bulunmuyor</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {irsaliyeler.map(irs => (
                        <div key={irs.id} className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                            {/* HEADER */}
                            <div
                                className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50 transition-colors"
                                onClick={() => setExpandedId(expandedId === irs.id ? null : irs.id)}
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                                        <FileCheck className="w-5 h-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <div className="font-semibold text-slate-900">{irs.irsaliye_no}</div>
                                        <div className="text-xs text-slate-500 mt-0.5">
                                            {tedarikciAdi(irs.tedarikci_id)} | {depoAdi(irs.depo_id)} | {irs.tarih}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${durumRenkleri[irs.durum] || ''}`}>
                                        {durumEtiketleri[irs.durum] || irs.durum}
                                    </span>
                                    <span className="text-xs text-slate-500">{irs.kalemler?.length || 0} palet</span>
                                    {expandedId === irs.id ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                                </div>
                            </div>

                            {/* DETAY (EXPANDED) */}
                            {expandedId === irs.id && (
                                <div className="border-t border-slate-100 p-4">
                                    {/* Meta bilgi */}
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 text-sm">
                                        {irs.tir_plaka && (
                                            <div><span className="text-slate-500">Plaka:</span> <span className="font-medium">{irs.tir_plaka}</span></div>
                                        )}
                                        {irs.sofor_adi && (
                                            <div><span className="text-slate-500">Şoför:</span> <span className="font-medium">{irs.sofor_adi}</span></div>
                                        )}
                                    </div>

                                    {/* Kalemler tablosu */}
                                    {irs.kalemler && irs.kalemler.length > 0 && (
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="text-left text-slate-500 border-b border-slate-100">
                                                        <th className="pb-2 font-medium">Palet No</th>
                                                        <th className="pb-2 font-medium">Ürün</th>
                                                        <th className="pb-2 font-medium">Lot No</th>
                                                        <th className="pb-2 font-medium text-right">Miktar</th>
                                                        <th className="pb-2 font-medium">Raf</th>
                                                        <th className="pb-2 font-medium">SKT</th>
                                                        <th className="pb-2 font-medium">Durum</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {irs.kalemler.map(kalem => (
                                                        <tr key={kalem.id} className="border-b border-slate-50">
                                                            <td className="py-2 font-mono text-xs font-semibold text-blue-700">{kalem.palet_no}</td>
                                                            <td className="py-2">{urunAdi(kalem.urun_id)}</td>
                                                            <td className="py-2 text-slate-500">{kalem.lot_no || '-'}</td>
                                                            <td className="py-2 text-right font-medium">{kalem.miktar}</td>
                                                            <td className="py-2 text-slate-500">{kalem.raf_id ? rafKodu(kalem.raf_id) : '-'}</td>
                                                            <td className="py-2 text-slate-500">{kalem.son_kullanma_tarihi || '-'}</td>
                                                            <td className="py-2">
                                                                {kalem.durum === 'GirisYapildi' ? (
                                                                    <span className="inline-flex items-center gap-1 text-emerald-700 text-xs font-medium">
                                                                        <CheckCircle className="w-3.5 h-3.5" /> Giriş Yapıldı
                                                                    </span>
                                                                ) : (
                                                                    <span className="inline-flex items-center gap-1 text-amber-700 text-xs font-medium">
                                                                        <Clock className="w-3.5 h-3.5" /> Bekliyor
                                                                    </span>
                                                                )}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}

                                    {/* Aksiyonlar */}
                                    <div className="flex gap-2 mt-4 pt-3 border-t border-slate-100">
                                        {irs.durum === 'Taslak' && (
                                            <>
                                                <button
                                                    onClick={() => durumDegistir(irs.id, 'Onaylandi')}
                                                    className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition-colors"
                                                >
                                                    <CheckCircle className="w-3.5 h-3.5" /> Onayla
                                                </button>
                                                <button
                                                    onClick={() => handleSil(irs.id)}
                                                    className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-700 rounded-lg text-xs font-medium hover:bg-red-100 transition-colors"
                                                >
                                                    <Trash2 className="w-3.5 h-3.5" /> Sil
                                                </button>
                                            </>
                                        )}
                                        {irs.durum === 'Onaylandi' && (
                                            <button
                                                onClick={() => durumDegistir(irs.id, 'Tamamlandi')}
                                                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 transition-colors"
                                            >
                                                <CheckCircle className="w-3.5 h-3.5" /> Tamamla
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* YENİ İRSALİYE MODAL */}
            {yeniModal && (
                <div className="fixed inset-0 bg-black/50 flex items-start justify-center pt-10 z-50 overflow-y-auto">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl mx-4 mb-10">
                        {/* Modal Header */}
                        <div className="flex items-center justify-between p-5 border-b border-slate-200">
                            <h2 className="text-lg font-bold text-slate-900">Yeni Mal Kabul İrsaliyesi</h2>
                            <button onClick={() => setYeniModal(false)} className="p-1 hover:bg-slate-100 rounded-lg">
                                <X className="w-5 h-5 text-slate-500" />
                            </button>
                        </div>

                        <div className="p-5 space-y-5">
                            {/* Ana bilgiler */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Tedarikçi *</label>
                                    <select
                                        value={formData.tedarikci_id}
                                        onChange={e => setFormData(prev => ({ ...prev, tedarikci_id: e.target.value }))}
                                        className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm"
                                    >
                                        <option value="">Seçin...</option>
                                        {tedarikciler.map(t => (
                                            <option key={t.id} value={t.id}>{t.firma_adi}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Depo *</label>
                                    <select
                                        value={formData.depo_id}
                                        onChange={e => setFormData(prev => ({ ...prev, depo_id: e.target.value }))}
                                        className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm"
                                    >
                                        <option value="">Seçin...</option>
                                        {depolar.map(d => (
                                            <option key={d.id} value={d.id}>{d.isim}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Tarih *</label>
                                    <input
                                        type="date"
                                        value={formData.tarih}
                                        onChange={e => setFormData(prev => ({ ...prev, tarih: e.target.value }))}
                                        className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">TIR Plakası</label>
                                    <input
                                        type="text"
                                        value={formData.tir_plaka}
                                        onChange={e => setFormData(prev => ({ ...prev, tir_plaka: e.target.value }))}
                                        placeholder="34 ABC 123"
                                        className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Şoför Adı</label>
                                    <input
                                        type="text"
                                        value={formData.sofor_adi}
                                        onChange={e => setFormData(prev => ({ ...prev, sofor_adi: e.target.value }))}
                                        className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm"
                                    />
                                </div>
                            </div>

                            {/* Kalemler */}
                            <div>
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="text-sm font-bold text-slate-700">Palet Kalemleri</h3>
                                    <button
                                        onClick={kalemEkle}
                                        className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                                    >
                                        <Plus className="w-3.5 h-3.5" /> Kalem Ekle
                                    </button>
                                </div>

                                {formData.kalemler.length === 0 ? (
                                    <div className="text-center py-8 border-2 border-dashed border-slate-200 rounded-xl">
                                        <Package className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                                        <p className="text-sm text-slate-400">Henüz kalem eklenmedi</p>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {formData.kalemler.map((kalem, idx) => (
                                            <div key={idx} className="p-3 border border-slate-200 rounded-lg bg-slate-50">
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="text-xs font-bold text-slate-500">Kalem #{idx + 1}</span>
                                                    <button onClick={() => kalemSil(idx)} className="p-1 hover:bg-red-50 rounded">
                                                        <Trash2 className="w-3.5 h-3.5 text-red-500" />
                                                    </button>
                                                </div>
                                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                                    <input
                                                        type="text"
                                                        placeholder="Palet No *"
                                                        value={kalem.palet_no}
                                                        onChange={e => kalemGuncelle(idx, 'palet_no', e.target.value)}
                                                        className="px-2.5 py-2 border border-slate-200 rounded-lg text-sm"
                                                    />
                                                    <select
                                                        value={kalem.urun_id}
                                                        onChange={e => kalemGuncelle(idx, 'urun_id', e.target.value)}
                                                        className="px-2.5 py-2 border border-slate-200 rounded-lg text-sm"
                                                    >
                                                        <option value="">Ürün *</option>
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
                                                        className="px-2.5 py-2 border border-slate-200 rounded-lg text-sm"
                                                    />
                                                    <input
                                                        type="text"
                                                        placeholder="Lot No"
                                                        value={kalem.lot_no}
                                                        onChange={e => kalemGuncelle(idx, 'lot_no', e.target.value)}
                                                        className="px-2.5 py-2 border border-slate-200 rounded-lg text-sm"
                                                    />
                                                    <select
                                                        value={kalem.raf_id}
                                                        onChange={e => kalemGuncelle(idx, 'raf_id', e.target.value)}
                                                        className="px-2.5 py-2 border border-slate-200 rounded-lg text-sm"
                                                    >
                                                        <option value="">Raf (opsiyonel)</option>
                                                        {raflar.map(r => (
                                                            <option key={r.id} value={r.id}>{r.kod}</option>
                                                        ))}
                                                    </select>
                                                    <input
                                                        type="date"
                                                        placeholder="SKT"
                                                        value={kalem.son_kullanma_tarihi}
                                                        onChange={e => kalemGuncelle(idx, 'son_kullanma_tarihi', e.target.value)}
                                                        className="px-2.5 py-2 border border-slate-200 rounded-lg text-sm"
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Modal Footer */}
                        <div className="flex justify-end gap-3 p-5 border-t border-slate-200">
                            <button
                                onClick={() => setYeniModal(false)}
                                className="px-4 py-2.5 text-sm font-medium text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50"
                            >
                                İptal
                            </button>
                            <button
                                onClick={handleOlustur}
                                className="px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                            >
                                Oluştur
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
