import { useState, useRef, useEffect } from 'react';
import { Scan, CheckCircle, AlertTriangle, X, Loader2, Package } from 'lucide-react';
import toast from 'react-hot-toast';
import { hataMetni } from '../utils/hata';
import { uretimPaletiKabulEt } from '../services/api';

// ── Durum tipi ────────────────────────────────────────────────────────────────

const SONUC = {
    BASARI: 'basari',
    HATA: 'hata',
};

// ── Bileşen ───────────────────────────────────────────────────────────────────

export default function UretimPaletiKabulPage() {
    const [paletNo, setPaletNo] = useState('');
    const [yukleniyor, setYukleniyor] = useState(false);
    const [sonuc, setSonuc] = useState(null); // { tip, mesaj, palet }
    const [gecmis, setGecmis] = useState([]);

    const inputRef = useRef(null);

    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    const okut = async (e) => {
        e.preventDefault();
        const no = paletNo.trim();
        if (!no) return;

        setYukleniyor(true);
        setSonuc(null);

        try {
            const res = await uretimPaletiKabulEt(no);
            const palet = res.data;
            const yeniSonuc = {
                tip: SONUC.BASARI,
                mesaj: `Kabul edildi — ${palet.koli_adedi} koli`,
                palet,
            };
            setSonuc(yeniSonuc);
            setGecmis((prev) => [
                { ...yeniSonuc, no, zaman: new Date().toLocaleTimeString('tr-TR') },
                ...prev.slice(0, 9),
            ]);
            toast.success(`${no} kabul edildi`);
        } catch (err) {
            const mesaj = hataMetni(err, 'Kabul işlemi başarısız');
            const yeniSonuc = { tip: SONUC.HATA, mesaj };
            setSonuc(yeniSonuc);
            setGecmis((prev) => [
                { ...yeniSonuc, no, zaman: new Date().toLocaleTimeString('tr-TR') },
                ...prev.slice(0, 9),
            ]);
            toast.error(mesaj);
        } finally {
            setYukleniyor(false);
            setPaletNo('');
            setTimeout(() => inputRef.current?.focus(), 50);
        }
    };

    return (
        <div className="p-6 max-w-2xl mx-auto space-y-6">
            {/* Başlık */}
            <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-xl">
                    <Scan className="w-6 h-6 text-blue-700" />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-gray-900">Üretimden Kabul</h1>
                    <p className="text-sm text-gray-500">Barkod okutun veya palet numarası girin</p>
                </div>
            </div>

            {/* Okutma Formu */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
                <form onSubmit={okut} className="space-y-4">
                    <div className="relative">
                        <Scan className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            ref={inputRef}
                            type="text"
                            value={paletNo}
                            onChange={(e) => setPaletNo(e.target.value)}
                            placeholder="PRD-YYYYMMDD-NNNN"
                            disabled={yukleniyor}
                            className="w-full pl-12 pr-4 py-4 text-xl font-mono border-2 border-gray-200 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50"
                        />
                        {paletNo && (
                            <button
                                type="button"
                                onClick={() => setPaletNo('')}
                                className="absolute right-4 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-gray-100"
                            >
                                <X className="w-4 h-4 text-gray-400" />
                            </button>
                        )}
                    </div>
                    <button
                        type="submit"
                        disabled={!paletNo.trim() || yukleniyor}
                        className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                    >
                        {yukleniyor ? (
                            <><Loader2 className="w-5 h-5 animate-spin" /> İşleniyor...</>
                        ) : (
                            <><CheckCircle className="w-5 h-5" /> Kabul Et</>
                        )}
                    </button>
                </form>

                {/* Sonuç */}
                {sonuc && (
                    <div className={`mt-4 flex items-start gap-3 p-4 rounded-xl border ${
                        sonuc.tip === SONUC.BASARI
                            ? 'bg-emerald-50 border-emerald-200'
                            : 'bg-red-50 border-red-200'
                    }`}>
                        {sonuc.tip === SONUC.BASARI ? (
                            <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                        ) : (
                            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                        )}
                        <div>
                            <p className={`font-semibold text-sm ${sonuc.tip === SONUC.BASARI ? 'text-emerald-800' : 'text-red-800'}`}>
                                {sonuc.tip === SONUC.BASARI ? 'Başarılı' : 'Hata'}
                            </p>
                            <p className={`text-sm mt-0.5 ${sonuc.tip === SONUC.BASARI ? 'text-emerald-700' : 'text-red-700'}`}>
                                {sonuc.mesaj}
                            </p>
                            {sonuc.palet && (
                                <p className="text-xs text-emerald-600 mt-1 font-mono">
                                    {sonuc.palet.palet_no} · Lot #{sonuc.palet.lot_id} · {sonuc.palet.koli_adedi} koli
                                </p>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Oturum Geçmişi */}
            {gecmis.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                    <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
                        <span className="text-sm font-semibold text-gray-700">Son İşlemler</span>
                        <span className="text-xs text-gray-400">{gecmis.length} kayıt</span>
                    </div>
                    <ul className="divide-y divide-gray-50">
                        {gecmis.map((g, i) => (
                            <li key={i} className="flex items-center gap-3 px-5 py-3">
                                {g.tip === SONUC.BASARI ? (
                                    <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                                ) : (
                                    <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
                                )}
                                <span className="font-mono text-sm text-gray-800 flex-1">{g.no}</span>
                                <span className="text-xs text-gray-400">{g.zaman}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {gecmis.length === 0 && (
                <div className="text-center py-10 text-gray-300">
                    <Package className="w-10 h-10 mx-auto mb-2" />
                    <p className="text-sm">Henüz işlem yapılmadı</p>
                </div>
            )}
        </div>
    );
}
