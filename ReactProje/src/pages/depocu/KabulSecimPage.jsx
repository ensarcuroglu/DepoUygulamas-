import { useNavigate } from 'react-router-dom';
import { FileText, Factory } from 'lucide-react';

const SECENEKLER = [
    {
        to: '/depocu/kabul/irsaliyeli',
        label: 'İrsaliyeli Kabul',
        aciklama: 'Tedarikçi irsaliyesi ile gelen mal',
        icon: FileText,
        renk: 'text-emerald-700',
        bg: 'bg-emerald-50',
        border: 'border-emerald-200',
    },
    ...(import.meta.env.VITE_FEATURE_URETIM_PALET_ENABLED === 'true' ? [{
        to: '/depocu/kabul/uretimden',
        label: 'Üretimden Kabul',
        aciklama: 'Üretim hattından barkod ile kabul',
        icon: Factory,
        renk: 'text-amber-700',
        bg: 'bg-amber-50',
        border: 'border-amber-200',
    }] : []),
];

export default function KabulSecimPage() {
    const navigate = useNavigate();

    return (
        <div className="p-4 max-w-md mx-auto space-y-4 pt-6">
            <div>
                <p className="text-xs font-bold tracking-widest text-slate-400 uppercase mb-1">Kabul İşlemi</p>
                <h1 className="text-2xl font-black text-slate-900">Kabul Tipi Seç</h1>
            </div>
            <div className="space-y-3">
                {SECENEKLER.map(({ to, label, aciklama, icon: Icon, renk, bg, border }) => (
                    <button
                        key={to}
                        onClick={() => navigate(to)}
                        className={`w-full flex items-center gap-4 p-5 rounded-2xl border-2 ${border} ${bg} active:scale-[0.98] transition-transform text-left`}
                    >
                        <div className={`w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0 bg-white border ${border}`}>
                            <Icon className={`w-7 h-7 ${renk}`} strokeWidth={2} />
                        </div>
                        <div>
                            <p className={`text-base font-black ${renk}`}>{label}</p>
                            <p className="text-sm text-slate-500 mt-0.5">{aciklama}</p>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
}
