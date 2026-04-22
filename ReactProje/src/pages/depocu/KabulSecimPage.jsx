import { useNavigate } from 'react-router-dom';
import { FileText, Factory, ArrowRight } from 'lucide-react';

const SECENEKLER = [
    {
        to: '/depocu/kabul/irsaliyeli',
        label: 'İrsaliyeli Kabul',
        aciklama: 'Tedarikçi irsaliyesi ile gelen mal',
        icon: FileText,
        iconRenk: 'text-emerald-700',
        iconBg: 'bg-emerald-100',
        borderAktif: 'border-emerald-300',
        bgHover: 'hover:bg-emerald-50',
    },
    ...(import.meta.env.VITE_FEATURE_URETIM_PALET_ENABLED === 'true' ? [{
        to: '/depocu/kabul/uretimden',
        label: 'Üretimden Kabul',
        aciklama: 'Üretim hattından barkod ile kabul',
        icon: Factory,
        iconRenk: 'text-amber-700',
        iconBg: 'bg-amber-100',
        borderAktif: 'border-amber-300',
        bgHover: 'hover:bg-amber-50',
    }] : []),
];

export default function KabulSecimPage() {
    const navigate = useNavigate();

    return (
        <div className="mx-auto max-w-md space-y-6 p-4 sm:max-w-2xl sm:p-6 pb-24">

            <header>
                <p className="text-sm font-bold tracking-wider text-slate-400 uppercase">
                    Kabul İşlemi
                </p>
                <h1 className="text-2xl font-black tracking-tight text-slate-900">
                    Kabul Tipi Seç
                </h1>
            </header>

            <section className="flex flex-col gap-4">
                {SECENEKLER.map((secenek) => {
                    const Icon = secenek.icon;
                    return (
                        <button
                            key={secenek.to}
                            onClick={() => navigate(secenek.to)}
                            className={`group flex w-full items-center gap-5 rounded-2xl border-2 ${secenek.borderAktif} bg-white p-5 shadow-sm transition-all active:scale-[0.97] ${secenek.bgHover}`}
                        >
                            <div className={`flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-2xl ${secenek.iconBg}`}>
                                <Icon className={`h-8 w-8 ${secenek.iconRenk}`} strokeWidth={2} />
                            </div>

                            <div className="min-w-0 flex-1 text-left">
                                <p className="text-base font-black text-slate-900">{secenek.label}</p>
                                <p className="mt-0.5 text-sm font-medium text-slate-500">{secenek.aciklama}</p>
                            </div>

                            <ArrowRight
                                className="h-5 w-5 flex-shrink-0 text-slate-300 transition-transform group-hover:translate-x-1"
                                strokeWidth={2.5}
                            />
                        </button>
                    );
                })}
            </section>

        </div>
    );
}
