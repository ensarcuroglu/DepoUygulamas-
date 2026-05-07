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
import { motion } from 'framer-motion';
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
    Clock,
    TrendingUp,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';
import { getBekleyenGorevOzet } from '../../services/api';
import { hataMetni } from '../../utils/hata';

// Operatörün en sık kullandığı ana işlemler (Büyük Grid)
const ANA_ISLEMLER = [
    { label: 'Görevler',   icon: ClipboardList, to: '/terminal/gorevler',          color: 'text-blue-700 dark:text-blue-400',       bg: 'bg-blue-50 dark:bg-blue-500/10'    },
    { label: 'Yerleştir',  icon: Scan,          to: '/terminal/yerlestirme',        color: 'text-indigo-700 dark:text-indigo-400',  bg: 'bg-indigo-50 dark:bg-indigo-500/10'  },
    { label: 'İrsaliyeli', icon: PackageCheck,  to: '/depocu/kabul/irsaliyeli',     color: 'text-emerald-700 dark:text-emerald-400',bg: 'bg-emerald-50 dark:bg-emerald-500/10' },
    ...(import.meta.env.VITE_FEATURE_URETIM_PALET_ENABLED === 'true' ? [
        { label: 'Üretimden', icon: Factory,    to: '/depocu/kabul/uretimden',      color: 'text-amber-700 dark:text-amber-400',    bg: 'bg-amber-50 dark:bg-amber-500/10'   },
    ] : []),
    { label: 'Sevkiyat',   icon: Truck,         to: '/depocu/sevkiyat',             color: 'text-cyan-700 dark:text-cyan-400',      bg: 'bg-cyan-50 dark:bg-cyan-500/10'    },
    { label: 'Sayım',      icon: ClipboardCheck, to: '/depocu/stok-sayim',          color: 'text-violet-700 dark:text-violet-400',  bg: 'bg-violet-50 dark:bg-violet-500/10'  },
    { label: 'Transfer',   icon: ArrowLeftRight, to: '/depocu/stok',                color: 'text-sky-700 dark:text-sky-400',        bg: 'bg-sky-50 dark:bg-sky-500/10'     },
];

// Daha az sıklıkla kullanılan veya izleme amaçlı ekranlar (Liste Görünümü)
const ALT_ISLEMLER = [
    { label: 'Performansım', icon: TrendingUp, to: '/depocu/performansim' },
    { label: 'İrsaliye ve Belgeler', icon: FileText, to: '/depocu/irsaliyeler' },
    { label: 'Destek / Arıza Bildir', icon: HelpCircle, to: '/depocu/destek' },
];

const containerVariants = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: {
            staggerChildren: 0.08
        }
    }
};

const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 400, damping: 30 } }
};

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
        <motion.div 
            className="mx-auto max-w-md space-y-6 p-4 sm:max-w-2xl sm:p-6 pb-32"
            variants={containerVariants}
            initial="hidden"
            animate="show"
        >
            
            {/* ÜST BİLGİ ALANI: Sadece kim olduğu ve saat */}
            <motion.header variants={itemVariants} className="flex items-center justify-between px-2">
                <div>
                    <p className="text-sm font-bold tracking-wider text-slate-400 dark:text-slate-500 uppercase">
                        Kullanıcı
                    </p>
                    <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
                        {operatorAdi}
                    </h1>
                </div>
                <div className="flex flex-col items-end">
                    <p className="text-sm font-bold tracking-wider text-slate-400 dark:text-slate-500 uppercase flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" /> Saat
                    </p>
                    <p className="text-xl font-black tracking-tight text-slate-900 dark:text-white">
                        {new Intl.DateTimeFormat('tr-TR', { hour: '2-digit', minute: '2-digit' }).format(new Date())}
                    </p>
                </div>
            </motion.header>

            {/* ANA AKSİYON ALANI (Status Orb) - Operatörün bakacağı ilk yer */}
            <motion.section 
                variants={itemVariants}
                onClick={() => navigate('/terminal/gorevler')}
                className={`group relative overflow-hidden rounded-[32px] p-1 cursor-pointer transition-transform active:scale-[0.97]`}
            >
                {/* Animated Gradient Border */}
                <div className={`absolute inset-0 bg-gradient-to-br ${hasAcil ? 'from-rose-500 to-rose-700' : 'from-blue-500 to-blue-700'} opacity-80`} />
                
                <div className="relative bg-white/10 dark:bg-black/20 backdrop-blur-xl h-full w-full rounded-[28px] border border-white/20 dark:border-white/10 p-6 flex items-center justify-between overflow-hidden">
                    
                    {/* Breathing Orb Effect */}
                    <motion.div 
                        className={`absolute -left-10 -top-10 w-48 h-48 rounded-full blur-3xl opacity-50 ${hasAcil ? 'bg-rose-500' : 'bg-blue-500'}`}
                        animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.6, 0.3] }}
                        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    />

                    <div className="relative z-10 w-full">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-2xl bg-white/20 dark:bg-black/20 backdrop-blur-md`}>
                                <DurumIcon className="h-7 w-7 text-white" strokeWidth={2.5} />
                            </div>
                            <h2 className="text-2xl font-black tracking-tight text-white drop-shadow-sm">
                                {durumBasligi}
                            </h2>
                        </div>
                        <p className="mt-2 text-sm font-medium text-white/90">
                            {durumAltMetni}
                        </p>
                        
                        <div className="mt-8 flex items-center justify-between rounded-xl bg-black/20 dark:bg-white/10 px-4 py-3 backdrop-blur-md text-white border border-white/10">
                            <span className="font-bold tracking-wide">
                                {hasAcil ? "HEMEN BAŞLA" : "GÖREV LİSTESİNİ AÇ"}
                            </span>
                            <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" strokeWidth={2.5} />
                        </div>
                    </div>
                    
                    {/* Watermark Icon */}
                    <div className="absolute -right-6 -bottom-6 opacity-10 pointer-events-none">
                        <DurumIcon className="w-48 h-48 text-white" />
                    </div>
                </div>
            </motion.section>

            {/* HIZLI ERİŞİM GRİDİ (Glassmorphic Buttonlar) */}
            <motion.section variants={itemVariants}>
                <p className="mb-3 text-[11px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400 px-2">
                    Saha İşlemleri
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {ANA_ISLEMLER.map((islem) => {
                        const IconComponent = islem.icon;
                        return (
                            <motion.button
                                key={islem.to}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => navigate(islem.to)}
                                className="group relative flex flex-col items-center justify-center gap-3 rounded-[24px] border border-slate-200/60 dark:border-slate-800/60 bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md p-5 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] transition-all hover:bg-white dark:hover:bg-[#1A1C20]"
                            >
                                <div className={`flex h-14 w-14 items-center justify-center rounded-[18px] transition-transform duration-300 group-hover:scale-110 ${islem.bg} ${islem.color}`}>
                                    <IconComponent className="h-7 w-7" strokeWidth={2.5} />
                                </div>
                                <span className="text-[13px] font-bold text-slate-700 dark:text-slate-300">
                                    {islem.label}
                                </span>
                            </motion.button>
                        );
                    })}
                </div>
            </motion.section>

            {/* ALT LİSTE (Destek ve Belgeler) */}
            <motion.section variants={itemVariants}>
                <p className="mb-3 text-[11px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400 px-2">
                    Sistem & Destek
                </p>
                <div className="flex flex-col gap-3">
                    {ALT_ISLEMLER.map((islem) => {
                        const IconComponent = islem.icon;
                        return (
                            <motion.button
                                key={islem.to}
                                whileTap={{ scale: 0.97 }}
                                onClick={() => navigate(islem.to)}
                                className="group flex items-center justify-between rounded-[20px] border border-slate-200/60 dark:border-slate-800/60 bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md p-4 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] transition-all hover:bg-white dark:hover:bg-[#1A1C20]"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="flex h-12 w-12 items-center justify-center rounded-[14px] bg-slate-100 dark:bg-slate-800/50 text-slate-600 dark:text-slate-400 transition-colors group-hover:bg-blue-50 dark:group-hover:bg-blue-500/10 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                                        <IconComponent className="h-6 w-6" strokeWidth={2} />
                                    </div>
                                    <span className="text-sm font-bold text-slate-700 dark:text-slate-300">
                                        {islem.label}
                                    </span>
                                </div>
                                <ArrowRight className="h-5 w-5 text-slate-300 dark:text-slate-600 transition-transform group-hover:translate-x-1 group-hover:text-blue-500" />
                            </motion.button>
                        );
                    })}
                </div>
            </motion.section>

        </motion.div>
    );
}