/**
 * DepocuAnaSayfasi — Depo operatörü görev odaklı ana sayfa.
 * * Saha Odaklı UX Prensipleri:
 * - Devasa dokunma alanları (Minimum 64px yükseklik)
 * - Sıfır bilişsel yük (Açıklama metinleri yok, sadece net ikon ve başlık)
 * - Duruma göre değişen tek ve dev ana eylem butonu (Call to Action)
 * - Saf CSS tabanlı yüksek performanslı dokunma geri bildirimi (active:scale)
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    AlertTriangle,
    PackageCheck,
    ArrowLeftRight,
    ClipboardCheck,
    HelpCircle,
    ArrowRight,
    Scan,
    ClipboardList,
    CheckCircle2,
    Truck,
    FileText,
    Factory,
    Clock
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';
import { getBekleyenGorevOzet } from '../../services/api';
import { hataMetni } from '../../utils/hata';

// Operatörün en sık kullandığı ana işlemler (Büyük Grid)
const ANA_ISLEMLER = [
    { label: 'Görevler',   icon: ClipboardList, to: '/terminal/gorevler',          color: 'text-blue-700',    bg: 'bg-blue-50'    },
    { label: 'Yerleştir',  icon: Scan,          to: '/terminal/yerlestirme',        color: 'text-indigo-700',  bg: 'bg-indigo-50'  },
    { label: 'İrsaliyeli', icon: PackageCheck,  to: '/depocu/kabul/irsaliyeli',     color: 'text-emerald-700', bg: 'bg-emerald-50' },
    ...(import.meta.env.VITE_FEATURE_URETIM_PALET_ENABLED === 'true' ? [
        { label: 'Üretimden', icon: Factory,    to: '/depocu/kabul/uretimden',      color: 'text-amber-700',   bg: 'bg-amber-50'   },
    ] : []),
    { label: 'Sevkiyat',   icon: Truck,         to: '/depocu/sevkiyat',             color: 'text-cyan-700',    bg: 'bg-cyan-50'    },
    { label: 'Sayım',      icon: ClipboardCheck, to: '/depocu/stok-sayim',          color: 'text-violet-700',  bg: 'bg-violet-50'  },
    { label: 'Transfer',   icon: ArrowLeftRight, to: '/depocu/stok',                color: 'text-sky-700',     bg: 'bg-sky-50'     },
];

// Daha az sıklıkla kullanılan veya izleme amaçlı ekranlar (Liste Görünümü)
const ALT_ISLEMLER = [
    { label: 'İrsaliye ve Belgeler', icon: FileText, to: '/depocu/irsaliyeler' },
    { label: 'Destek / Arıza Bildir', icon: HelpCircle, to: '/depocu/destek' },
];

export default function DepocuAnaSayfasi() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [ozet, setOzet] = useState(null);

    const yukle = useCallback(() =>
        getBekleyenGorevOzet()
            .then((res) => setOzet(res.data))
            .catch((err) => toast.error(hataMetni(err, 'Görev durumu alınamadı')))
            .finally(() => setLoading(false))
    , []);

    useEffect(() => { void yukle(); }, [yukle]);

    const operatorAdi = user?.ad_soyad?.split(' ')[0] || 'Operatör';
    const acilGorevSayisi = ozet?.acil ?? 0;
    const bekleyenGorevSayisi = ozet?.toplam_bekleyen ?? 0;
    const hasAcil = acilGorevSayisi > 0;

    // Dinamik Durum Kartı Parametreleri
    const DurumIcon = hasAcil ? AlertTriangle : CheckCircle2;
    const durumRengi = hasAcil ? 'bg-rose-600 text-white' : 'bg-blue-600 text-white';
    const durumBasligi = hasAcil ? 'Acil Görevler Var!' : 'Operasyon Akışı Normal';
    const durumAltMetni = hasAcil 
        ? `${acilGorevSayisi} adet öncelikli görev bekliyor.` 
        : bekleyenGorevSayisi > 0 
            ? `${bekleyenGorevSayisi} görev sırada.` 
            : 'Sırada bekleyen görev yok.';

    return (
        <div className="mx-auto max-w-md space-y-6 p-4 sm:max-w-2xl sm:p-6 pb-24">
            
            {/* ÜST BİLGİ ALANI: Sadece kim olduğu ve saat */}
            <header className="flex items-center justify-between">
                <div>
                    <p className="text-sm font-bold tracking-wider text-slate-400 uppercase">
                        Kullanıcı
                    </p>
                    <h1 className="text-2xl font-black tracking-tight text-slate-900">
                        {operatorAdi}
                    </h1>
                </div>
                <div className="flex flex-col items-end">
                    <p className="text-sm font-bold tracking-wider text-slate-400 uppercase flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" /> Saat
                    </p>
                    <p className="text-xl font-black tracking-tight text-slate-900">
                        {new Intl.DateTimeFormat('tr-TR', { hour: '2-digit', minute: '2-digit' }).format(new Date())}
                    </p>
                </div>
            </header>

            {/* ANA AKSİYON ALANI (HERO) - Operatörün bakacağı ilk yer */}
            <section 
                onClick={() => navigate('/terminal/gorevler')}
                className={`group relative flex cursor-pointer flex-col overflow-hidden rounded-[24px] p-6 shadow-sm transition-all active:scale-[0.98] ${durumRengi}`}
            >
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <div className="flex items-center gap-2">
                            <DurumIcon className="h-6 w-6" strokeWidth={2.5} />
                            <h2 className="text-xl font-bold tracking-tight">
                                {durumBasligi}
                            </h2>
                        </div>
                        <p className="mt-2 text-sm font-medium opacity-90">
                            {durumAltMetni}
                        </p>
                    </div>
                </div>

                <div className="mt-8 flex items-center justify-between rounded-xl bg-black/10 px-4 py-3 backdrop-blur-sm">
                    <span className="font-bold tracking-wide">
                        {hasAcil ? "HEMEN BAŞLA" : "GÖREV LİSTESİNİ AÇ"}
                    </span>
                    <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" strokeWidth={2.5} />
                </div>
            </section>

            {/* HIZLI ERİŞİM GRİDİ (Büyük Dokunma Alanları) */}
            <section>
                <p className="mb-3 text-[11px] font-bold uppercase tracking-widest text-slate-400 px-1">
                    Saha İşlemleri
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {ANA_ISLEMLER.map((islem) => {
                        const IconComponent = islem.icon;
                        return (
                            <button
                                key={islem.to}
                                onClick={() => navigate(islem.to)}
                                className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:border-slate-300 hover:bg-slate-50 active:scale-95"
                            >
                                <div className={`flex h-14 w-14 items-center justify-center rounded-2xl ${islem.bg} ${islem.color}`}>
                                    <IconComponent className="h-7 w-7" strokeWidth={2} />
                                </div>
                                <span className="text-[13px] font-bold text-slate-700">
                                    {islem.label}
                                </span>
                            </button>
                        );
                    })}
                </div>
            </section>

            {/* ALT LİSTE (Destek ve Belgeler) */}
            <section>
                <p className="mb-3 text-[11px] font-bold uppercase tracking-widest text-slate-400 px-1">
                    Sistem & Destek
                </p>
                <div className="flex flex-col gap-2">
                    {ALT_ISLEMLER.map((islem) => {
                        const IconComponent = islem.icon;
                        return (
                            <button
                                key={islem.to}
                                onClick={() => navigate(islem.to)}
                                className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition-all hover:bg-slate-50 active:scale-[0.98]"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
                                        <IconComponent className="h-5 w-5" strokeWidth={2} />
                                    </div>
                                    <span className="text-sm font-bold text-slate-700">
                                        {islem.label}
                                    </span>
                                </div>
                                <ArrowRight className="h-5 w-5 text-slate-300" />
                            </button>
                        );
                    })}
                </div>
            </section>

        </div>
    );
}