import { useEffect, useRef, useState } from 'react';
import { X, Loader2, Download, Printer, FileText, Tag } from 'lucide-react';
import toast from 'react-hot-toast';
import { QRCodeSVG } from 'qrcode.react';
import JsBarcode from 'jsbarcode';
import jsPDF from 'jspdf';
import {
    getEtiketSablonlari, createPaletEtiketi, yazdirPaletEtiketi,
} from '../../services/api';
import { hataMetni } from '../../utils/hata';

export default function EtiketOlusturModal({ paletNo, onKapat }) {
    const [sablonlar, setSablonlar] = useState([]);
    const [seciliSablonId, setSeciliSablonId] = useState('');
    const [olusturulmusEtiket, setOlusturulmusEtiket] = useState(null);
    const [yukleniyor, setYukleniyor] = useState(true);
    const [islem, setIslem] = useState(false);
    const barkodRef = useRef(null);

    useEffect(() => {
        (async () => {
            try {
                const res = await getEtiketSablonlari({ sadece_aktif: true });
                setSablonlar(res.data);
                const def = res.data.find((s) => s.default_mi) || res.data[0];
                if (def) setSeciliSablonId(String(def.id));
            } catch (err) {
                toast.error(hataMetni(err, 'Şablonlar yüklenemedi'));
            } finally {
                setYukleniyor(false);
            }
        })();
    }, []);

    useEffect(() => {
        // Code128 barkod render
        if (olusturulmusEtiket?.barkod_deger && barkodRef.current) {
            try {
                JsBarcode(barkodRef.current, olusturulmusEtiket.barkod_deger, {
                    format: 'CODE128',
                    height: 60,
                    width: 2,
                    displayValue: true,
                    fontSize: 14,
                    margin: 4,
                });
            } catch (e) {
                console.warn('Barkod render hatası', e);
            }
        }
    }, [olusturulmusEtiket]);

    const etiketOlustur = async () => {
        if (!seciliSablonId) {
            toast.error('Şablon seçin');
            return;
        }
        setIslem(true);
        try {
            const res = await createPaletEtiketi(paletNo, {
                sablon_id: parseInt(seciliSablonId),
            });
            setOlusturulmusEtiket(res.data);
            toast.success('Etiket oluşturuldu');
        } catch (err) {
            toast.error(hataMetni(err, 'Etiket oluşturulamadı'));
        } finally {
            setIslem(false);
        }
    };

    const yazdir = async () => {
        if (!olusturulmusEtiket) return;
        try {
            const res = await yazdirPaletEtiketi(olusturulmusEtiket.id);
            setOlusturulmusEtiket(res.data);
            // Tarayıcı yazdırma
            const icerik = olusturulmusEtiket.render_edilmis_html;
            const pencere = window.open('', '_blank', 'width=600,height=800');
            if (pencere) {
                pencere.document.write(
                    `<!DOCTYPE html><html><head><title>Etiket ${paletNo}</title></head><body>${icerik}<script>window.print();</script></body></html>`
                );
                pencere.document.close();
            }
            toast.success('Yazdırma başlatıldı');
        } catch (err) {
            toast.error(hataMetni(err, 'Yazdırılamadı'));
        }
    };

    const zplIndir = () => {
        if (!olusturulmusEtiket) return;
        const blob = new Blob([olusturulmusEtiket.render_edilmis_zpl], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${paletNo}.zpl`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const pdfIndir = () => {
        if (!olusturulmusEtiket) return;
        const doc = new jsPDF({ unit: 'mm', format: [100, 150] });
        doc.setFontSize(16);
        doc.text('ÜRETİM PALETİ', 10, 15);
        doc.setFontSize(18);
        doc.text(paletNo, 10, 25);
        doc.setFontSize(10);
        const lines = olusturulmusEtiket.render_edilmis_html
            .replace(/<[^>]+>/g, '\n')
            .split('\n')
            .map((l) => l.trim())
            .filter(Boolean);
        let y = 35;
        lines.slice(0, 10).forEach((line) => {
            doc.text(line.substring(0, 40), 10, y);
            y += 6;
        });
        doc.save(`${paletNo}.pdf`);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 flex-shrink-0">
                    <div className="flex items-center gap-2">
                        <Tag className="w-5 h-5 text-indigo-600" />
                        <h2 className="font-semibold text-gray-900">Etiket Oluştur — {paletNo}</h2>
                    </div>
                    <button onClick={onKapat} className="p-1 rounded-lg hover:bg-gray-100">
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                <div className="px-6 py-5 overflow-y-auto space-y-5">
                    {/* Şablon seçimi */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Şablon <span className="text-red-500">*</span>
                        </label>
                        {yukleniyor ? (
                            <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                        ) : sablonlar.length === 0 ? (
                            <p className="text-sm text-gray-400">
                                Aktif şablon bulunamadı. Admin panelinden şablon tanımlayın.
                            </p>
                        ) : (
                            <select
                                value={seciliSablonId}
                                onChange={(e) => setSeciliSablonId(e.target.value)}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            >
                                {sablonlar.map((s) => (
                                    <option key={s.id} value={s.id}>
                                        {s.ad}{s.default_mi ? ' (varsayılan)' : ''} {s.boyut ? `— ${s.boyut}` : ''}
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>

                    {!olusturulmusEtiket ? (
                        <div className="flex justify-end">
                            <button
                                onClick={etiketOlustur}
                                disabled={!seciliSablonId || islem}
                                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium disabled:opacity-50"
                            >
                                {islem && <Loader2 className="w-4 h-4 animate-spin" />}
                                Etiket Oluştur
                            </button>
                        </div>
                    ) : (
                        <>
                            {/* Önizleme */}
                            <div>
                                <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Önizleme</div>
                                <div className="border border-gray-200 rounded-lg p-4 bg-white">
                                    <div
                                        dangerouslySetInnerHTML={{ __html: olusturulmusEtiket.render_edilmis_html }}
                                    />
                                </div>
                            </div>

                            {/* Barkod + QR */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="border border-gray-200 rounded-lg p-3 flex flex-col items-center">
                                    <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Barkod (Code128)</div>
                                    <svg ref={barkodRef}></svg>
                                </div>
                                <div className="border border-gray-200 rounded-lg p-3 flex flex-col items-center">
                                    <div className="text-xs font-semibold text-gray-500 uppercase mb-2">QR Kod</div>
                                    <QRCodeSVG value={olusturulmusEtiket.qr_deger || olusturulmusEtiket.barkod_deger} size={128} />
                                </div>
                            </div>

                            <div className="text-xs text-gray-500">
                                Basım sayısı: <span className="font-semibold">{olusturulmusEtiket.basim_sayisi}</span>
                                {olusturulmusEtiket.son_basim_tarihi && (
                                    <> — Son basım: {new Date(olusturulmusEtiket.son_basim_tarihi).toLocaleString('tr-TR')}</>
                                )}
                            </div>
                        </>
                    )}
                </div>

                {olusturulmusEtiket && (
                    <div className="flex justify-end gap-2 px-6 py-4 border-t border-gray-100 flex-shrink-0">
                        <button onClick={zplIndir}
                            className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">
                            <Download className="w-4 h-4" /> ZPL
                        </button>
                        <button onClick={pdfIndir}
                            className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">
                            <FileText className="w-4 h-4" /> PDF
                        </button>
                        <button onClick={yazdir}
                            className="flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium">
                            <Printer className="w-4 h-4" /> Yazdır
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
