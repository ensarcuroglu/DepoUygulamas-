import { useState, useEffect, useCallback } from 'react';
import {
    Tag, Plus, Edit3, Trash2, X, Search, RefreshCw, Loader2, Star, StarOff, Check,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import {
    getEtiketSablonlari, createEtiketSablonu, updateEtiketSablonu, deleteEtiketSablonu,
} from '../services/api';

const ZPL_DEFAULT = `^XA
^CF0,30
^FO20,20^FDURETIM PALETI^FS
^CF0,60
^FO20,60^FD{palet_no}^FS
^BY3,2,100
^FO20,130^BC^FD{barkod}^FS
^CF0,25
^FO20,250^FDUrun: {urun_isim}^FS
^FO20,280^FDLot: {lot_no}^FS
^FO20,310^FDSKT: {skt}^FS
^FO20,340^FDKoli: {koli} adet^FS
^FO20,370^FDVardiya: {vardiya}^FS
^XZ`;

const HTML_DEFAULT = `<div style="font-family: sans-serif; border: 2px solid #000; padding: 16px; width: 400px;">
  <h2 style="margin: 0 0 8px">ÜRETİM PALETİ</h2>
  <div style="font-size: 22px; font-weight: 700">{palet_no}</div>
  <hr />
  <p><strong>Ürün:</strong> {urun_isim}</p>
  <p><strong>Lot:</strong> {lot_no}</p>
  <p><strong>SKT:</strong> {skt}</p>
  <p><strong>Koli:</strong> {koli} adet</p>
  <p><strong>Vardiya:</strong> {vardiya}</p>
  <p><strong>Üretim:</strong> {uretim_tarihi}</p>
</div>`;

const PLACEHOLDERS = [
    '{palet_no}', '{lot_no}', '{urun_isim}', '{skt}',
    '{koli}', '{vardiya}', '{uretim_tarihi}', '{barkod}', '{qr}',
];

export default function EtiketSablonlariPage() {
    const { loading, run } = useAsync(true);
    const [sablonlar, setSablonlar] = useState([]);
    const [arama, setArama] = useState('');
    const [modal, setModal] = useState(null); // { tip: 'yeni'|'duzenle', sablon? }
    const [form, setForm] = useState(bosForm());
    const [kaydediyor, setKaydediyor] = useState(false);

    function bosForm() {
        return {
            ad: '', boyut: '100x150mm',
            zpl_template: ZPL_DEFAULT,
            html_template: HTML_DEFAULT,
            default_mi: false, aktif: true,
        };
    }

    const veriYukle = useCallback(async () => {
        await run(async () => {
            const res = await getEtiketSablonlari({ sadece_aktif: false });
            setSablonlar(res.data);
        });
    }, [run]);

    useEffect(() => { veriYukle(); }, [veriYukle]);

    const filtrelenmis = sablonlar.filter(
        (s) => !arama || s.ad.toLowerCase().includes(arama.toLowerCase())
    );

    const modaliAc = (tip, sablon = null) => {
        if (tip === 'duzenle' && sablon) {
            setForm({
                ad: sablon.ad,
                boyut: sablon.boyut || '',
                zpl_template: sablon.zpl_template,
                html_template: sablon.html_template,
                default_mi: sablon.default_mi,
                aktif: sablon.aktif,
            });
        } else {
            setForm(bosForm());
        }
        setModal({ tip, sablon });
    };

    const kaydet = async (e) => {
        e.preventDefault();
        setKaydediyor(true);
        try {
            if (modal.tip === 'yeni') {
                await createEtiketSablonu(form);
                toast.success('Şablon oluşturuldu');
            } else {
                await updateEtiketSablonu(modal.sablon.id, form);
                toast.success('Şablon güncellendi');
            }
            setModal(null);
            veriYukle();
        } catch (err) {
            toast.error(hataMetni(err, 'Kaydedilemedi'));
        } finally {
            setKaydediyor(false);
        }
    };

    const sil = async (id) => {
        if (!window.confirm('Şablon pasife alınsın mı?')) return;
        try {
            await deleteEtiketSablonu(id);
            toast.success('Şablon silindi');
            veriYukle();
        } catch (err) {
            toast.error(hataMetni(err, 'Silinemedi'));
        }
    };

    const defaultYap = async (s) => {
        try {
            await updateEtiketSablonu(s.id, { default_mi: true });
            toast.success('Varsayılan şablon atandı');
            veriYukle();
        } catch (err) {
            toast.error(hataMetni(err, 'Atanamadı'));
        }
    };

    const placeholderEkle = (alan, ph) => {
        setForm((f) => ({ ...f, [alan]: (f[alan] || '') + ph }));
    };

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-100 rounded-xl">
                        <Tag className="w-6 h-6 text-indigo-700" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-gray-900">Etiket Şablonları</h1>
                        <p className="text-sm text-gray-500">Palet etiketleri için ZPL + HTML şablonları</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button onClick={veriYukle} className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50">
                        <RefreshCw className="w-4 h-4 text-gray-600" />
                    </button>
                    <button onClick={() => modaliAc('yeni')}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium">
                        <Plus className="w-4 h-4" />
                        Yeni Şablon
                    </button>
                </div>
            </div>

            <div className="relative max-w-xs">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                    value={arama}
                    onChange={(e) => setArama(e.target.value)}
                    placeholder="Şablon ara..."
                    className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                {loading ? (
                    <div className="flex justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                    </div>
                ) : filtrelenmis.length === 0 ? (
                    <div className="text-center py-20 text-gray-400">
                        <Tag className="w-12 h-12 mx-auto mb-3 opacity-30" />
                        <p>Şablon bulunamadı</p>
                    </div>
                ) : (
                    <table className="w-full text-sm">
                        <thead className="bg-gray-50 border-b border-gray-100">
                            <tr>
                                {['Ad', 'Boyut', 'Durum', 'Varsayılan', 'İşlemler'].map((h) => (
                                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {filtrelenmis.map((s) => (
                                <tr key={s.id} className="hover:bg-gray-50/50">
                                    <td className="px-4 py-3 font-medium text-gray-900">{s.ad}</td>
                                    <td className="px-4 py-3 text-gray-600">{s.boyut || '—'}</td>
                                    <td className="px-4 py-3">
                                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                                            s.aktif ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-500'
                                        }`}>
                                            {s.aktif ? 'Aktif' : 'Pasif'}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">
                                        {s.default_mi ? (
                                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                                                <Star className="w-3 h-3" /> Varsayılan
                                            </span>
                                        ) : (
                                            <button onClick={() => defaultYap(s)}
                                                disabled={!s.aktif}
                                                className="text-xs text-gray-500 hover:text-gray-700 inline-flex items-center gap-1 disabled:opacity-40">
                                                <StarOff className="w-3 h-3" /> Varsayılan yap
                                            </button>
                                        )}
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-1">
                                            <button onClick={() => modaliAc('duzenle', s)}
                                                className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-600" title="Düzenle">
                                                <Edit3 className="w-4 h-4" />
                                            </button>
                                            <button onClick={() => sil(s.id)}
                                                className="p-1.5 hover:bg-red-50 rounded-lg text-red-600" title="Sil">
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {modal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
                        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                            <h2 className="font-semibold text-gray-900">
                                {modal.tip === 'yeni' ? 'Yeni Etiket Şablonu' : `Düzenle: ${modal.sablon.ad}`}
                            </h2>
                            <button onClick={() => setModal(null)} className="p-1 rounded-lg hover:bg-gray-100">
                                <X className="w-5 h-5 text-gray-500" />
                            </button>
                        </div>
                        <form onSubmit={kaydet} className="px-6 py-5 overflow-y-auto space-y-4">
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Ad <span className="text-red-500">*</span>
                                    </label>
                                    <input required value={form.ad} onChange={(e) => setForm({ ...form, ad: e.target.value })}
                                        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Boyut</label>
                                    <input value={form.boyut} onChange={(e) => setForm({ ...form, boyut: e.target.value })}
                                        placeholder="100x150mm"
                                        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                                </div>
                            </div>

                            <div className="flex gap-3 text-sm">
                                <label className="inline-flex items-center gap-2">
                                    <input type="checkbox" checked={form.default_mi}
                                        onChange={(e) => setForm({ ...form, default_mi: e.target.checked })} />
                                    Varsayılan
                                </label>
                                <label className="inline-flex items-center gap-2">
                                    <input type="checkbox" checked={form.aktif}
                                        onChange={(e) => setForm({ ...form, aktif: e.target.checked })} />
                                    Aktif
                                </label>
                            </div>

                            <div>
                                <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Placeholder'lar</div>
                                <div className="flex flex-wrap gap-1">
                                    {PLACEHOLDERS.map((ph) => (
                                        <button key={ph} type="button"
                                            onClick={() => placeholderEkle('zpl_template', ph)}
                                            className="px-2 py-0.5 text-xs bg-slate-100 hover:bg-slate-200 rounded">
                                            {ph}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    ZPL Template <span className="text-red-500">*</span>
                                </label>
                                <textarea required value={form.zpl_template}
                                    onChange={(e) => setForm({ ...form, zpl_template: e.target.value })}
                                    rows={8}
                                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    HTML Template (önizleme için) <span className="text-red-500">*</span>
                                </label>
                                <textarea required value={form.html_template}
                                    onChange={(e) => setForm({ ...form, html_template: e.target.value })}
                                    rows={8}
                                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                            </div>

                            <div className="flex justify-end gap-2 pt-2 border-t border-gray-100">
                                <button type="button" onClick={() => setModal(null)}
                                    className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">
                                    İptal
                                </button>
                                <button type="submit" disabled={kaydediyor}
                                    className="flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium disabled:opacity-50">
                                    {kaydediyor ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                                    Kaydet
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
