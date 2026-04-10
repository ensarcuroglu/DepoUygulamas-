import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Package, User, Lock, LogIn, Eye, EyeOff, AlertCircle, Loader2, Activity, Shield, Zap } from 'lucide-react';
import toast from 'react-hot-toast';
import { hataMetni } from '../utils/hata';


export default function LoginPage() {
    const [kullaniciAdi, setKullaniciAdi] = useState('');
    const [sifre, setSifre] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!kullaniciAdi.trim() || !sifre.trim()) {
            setError('Lütfen tüm alanları doldurun.');
            return;
        }

        setLoading(true);
        try {
            const userData = await login(kullaniciAdi, sifre);
            toast.success('Giriş başarılı! Hoş geldiniz.');
            const target = userData.rol === 'depocu'
                ? '/depocu'
                : userData.rol === 'lojistik'
                    ? '/stok-hareketleri'
                    : userData.rol === 'goruntuleyen'
                        ? '/profil-ayarlari'
                        : '/dashboard';
            navigate(target, { replace: true });
        } catch (err) {
            const message = hataMetni(err, 'Giriş yapılamadı. Lütfen bilgilerinizi kontrol edin.');
            setError(message);
            toast.error(message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <style dangerouslySetInnerHTML={{
                __html: `
                @keyframes float { 
                    0%, 100% { transform: translateY(0px); } 
                    50% { transform: translateY(-15px); } 
                }
                @keyframes float-delayed { 
                    0%, 100% { transform: translateY(0px); } 
                    50% { transform: translateY(-10px); } 
                }
                @keyframes grid-pan {
                    0% { transform: translateY(0); }
                    100% { transform: translateY(32px); }
                }
                @keyframes glow-pulse {
                    0%, 100% { opacity: 0.4; transform: scale(1); }
                    50% { opacity: 0.7; transform: scale(1.1); }
                }
                .animate-float { animation: float 6s ease-in-out infinite; }
                .animate-float-delayed { animation: float-delayed 8s ease-in-out infinite 2s; }
                .bg-grid-tech {
                    background-size: 32px 32px;
                    background-image: 
                        linear-gradient(to right, rgba(59, 130, 246, 0.06) 1px, transparent 1px),
                        linear-gradient(to bottom, rgba(59, 130, 246, 0.06) 1px, transparent 1px);
                    animation: grid-pan 3s linear infinite;
                }
                .glass-card {
                    background: color-mix(in srgb, var(--color-surface, #ffffff) 85%, transparent);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid var(--color-border, rgba(255,255,255,1));
                    box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.08), 0 0 0 1px rgba(15, 23, 42, 0.02);
                }
                input:-webkit-autofill,
                input:-webkit-autofill:hover,
                input:-webkit-autofill:focus,
                input:-webkit-autofill:active {
                    -webkit-box-shadow: 0 0 0 30px var(--color-surface, #ffffff) inset !important;
                    -webkit-text-fill-color: var(--color-text-primary, #0f172a) !important;
                    transition: background-color 5000s ease-in-out 0s;
                }
            `}} />

            <div className="min-h-screen flex relative overflow-hidden font-sans selection:bg-blue-500/30" style={{ backgroundColor: 'var(--color-surface-secondary, #F4F7FA)' }}>

                {/* --- Arka Plan Teknolojik Efektleri (Açık Tema) --- */}
                <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
                    <div className="absolute inset-0 bg-grid-tech" />
                    <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-400/20 rounded-full blur-[100px] mix-blend-multiply" style={{ animation: 'glow-pulse 8s infinite' }} />
                    <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-400/20 rounded-full blur-[100px] mix-blend-multiply" style={{ animation: 'glow-pulse 10s infinite reverse' }} />
                    <div className="absolute top-[40%] left-[50%] w-[20%] h-[20%] bg-cyan-300/20 rounded-full blur-[80px] mix-blend-multiply" />
                </div>

                {/* --- Sol Panel: Marka & Teknoloji (Sadece Masaüstü) --- */}
                <div className="hidden lg:flex lg:w-[50%] xl:w-[55%] relative z-10 flex-col justify-center px-12 xl:px-20">
                    <div className="animate-float">
                        <div className="flex items-center gap-4 mb-8">
                            <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center border border-blue-100 shadow-[0_8px_30px_rgba(59,130,246,0.15)]">
                                <Package className="w-8 h-8 text-blue-600" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-slate-900 to-slate-700 tracking-tight">Depo Yönetim</h1>
                                <p className="text-[14px] font-bold tracking-widest text-blue-600 uppercase mt-1">Endüstriyel Stok Kontrolü</p>
                            </div>
                        </div>

                        <h2 className="text-5xl xl:text-6xl font-extrabold text-slate-900 leading-[1.15] mb-6 tracking-tight">
                            Operasyonlarınızı <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-cyan-500 to-indigo-600">
                                geleceğe
                            </span> taşıyın.
                        </h2>

                        <p className="text-lg text-slate-600 leading-relaxed max-w-lg mb-12 font-medium">
                            Yapay zeka destekli altyapı ile gerçek zamanlı veri analizi, anlık stok takibi ve sıfır hata toleranslı yönetim sistemi.
                        </p>

                        {/* Teknolojik İstatistik Kartları */}
                        <div className="flex gap-5">
                            <div className="glass-card rounded-2xl p-5 w-40 transform hover:-translate-y-2 transition-transform duration-300">
                                <Activity className="w-6 h-6 text-cyan-500 mb-3" />
                                <p className="text-2xl font-bold text-slate-900">7/24</p>
                                <p className="text-[12px] font-semibold text-slate-500 mt-1">Sistem Aktifliği</p>
                            </div>
                            <div className="glass-card rounded-2xl p-5 w-40 transform hover:-translate-y-2 transition-transform duration-300 delay-75">
                                <Shield className="w-6 h-6 text-indigo-500 mb-3" />
                                <p className="text-2xl font-bold text-slate-900">%99.9</p>
                                <p className="text-[12px] font-semibold text-slate-500 mt-1">Doğruluk Oranı</p>
                            </div>
                            <div className="glass-card rounded-2xl p-5 w-40 transform hover:-translate-y-2 transition-transform duration-300 delay-150">
                                <Zap className="w-6 h-6 text-blue-500 mb-3" />
                                <p className="text-2xl font-bold text-slate-900">&lt;10ms</p>
                                <p className="text-[12px] font-semibold text-slate-500 mt-1">Tepki Süresi</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* --- Sağ Panel: Giriş Formu (Mobil ve Masaüstü) --- */}
                <div className="w-full lg:w-[50%] xl:w-[45%] flex items-center justify-center p-6 sm:p-8 lg:p-12 relative z-10">
                    <div className="glass-card w-full max-w-[440px] rounded-[2rem] p-8 sm:p-10 relative overflow-hidden animate-[float-delayed]">

                        {/* Form İçi Dekoratif Işıklar */}
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[80%] h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent opacity-30" />

                        {/* Mobil için Logo Gösterimi */}
                        <div className="lg:hidden flex items-center justify-center gap-3 mb-10">
                            <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center border border-blue-100 shadow-[0_8px_20px_rgba(59,130,246,0.15)]">
                                <Package className="w-6 h-6 text-blue-600" />
                            </div>
                            <div>
                                <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Depo Yönetim</h1>
                                <p className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">Sistem Girişi</p>
                            </div>
                        </div>

                        {/* Başlık Alanı */}
                        <div className="mb-8">
                            <h2 className="text-[28px] font-extrabold text-slate-900 tracking-tight">
                                Giriş Yap
                            </h2>
                            <p className="text-[15px] text-slate-500 font-medium mt-2">
                                Güvenli ağa bağlanmak için kimliğinizi doğrulayın.
                            </p>
                        </div>

                        {/* Hata Mesajı */}
                        {error && (
                            <div className="mb-6 flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-2xl animate-[fadeIn_0.3s_ease-out]">
                                <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                                <p className="text-[13px] font-semibold text-red-700 leading-relaxed">{error}</p>
                            </div>
                        )}

                        {/* Giriş Formu */}
                        <form onSubmit={handleSubmit} className="space-y-6">

                            {/* Kullanıcı Adı */}
                            <div className="space-y-2">
                                <label className="text-[13px] font-bold text-slate-700 ml-1 tracking-wide">Kullanıcı Adı</label>
                                <div className="relative group">
                                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-600 transition-colors duration-300">
                                        <User className="w-[18px] h-[18px]" />
                                    </div>
                                    <input
                                        type="text"
                                        value={kullaniciAdi}
                                        onChange={(e) => setKullaniciAdi(e.target.value)}
                                        placeholder="Kullanıcı adınızı girin"
                                        autoComplete="username"
                                        autoFocus
                                        className="w-full h-[54px] pl-12 pr-4 text-[15px] font-medium rounded-2xl 
                                                   bg-white/60 border-2 border-slate-200/80 text-slate-900 placeholder-slate-400
                                                   focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10
                                                   transition-all duration-300 hover:border-slate-300"
                                    />
                                </div>
                            </div>

                            {/* Şifre */}
                            <div className="space-y-2">
                                <label className="text-[13px] font-bold text-slate-700 ml-1 tracking-wide">Şifre</label>
                                <div className="relative group">
                                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-600 transition-colors duration-300">
                                        <Lock className="w-[18px] h-[18px]" />
                                    </div>
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        value={sifre}
                                        onChange={(e) => setSifre(e.target.value)}
                                        placeholder="Şifrenizi girin"
                                        autoComplete="current-password"
                                        className="w-full h-[54px] pl-12 pr-14 text-[15px] font-medium rounded-2xl 
                                                   bg-white/60 border-2 border-slate-200/80 text-slate-900 placeholder-slate-400
                                                   focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10
                                                   transition-all duration-300 hover:border-slate-300"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-blue-600 transition-colors p-1"
                                        tabIndex={-1}
                                    >
                                        {showPassword ? <EyeOff className="w-[18px] h-[18px]" /> : <Eye className="w-[18px] h-[18px]" />}
                                    </button>
                                </div>
                            </div>

                            {/* Giriş Butonu */}
                            <button
                                type="submit"
                                disabled={loading}
                                className="group relative w-full h-[54px] mt-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-[15px] font-bold tracking-wide
                                           rounded-2xl shadow-[0_8px_20px_-5px_rgba(59,130,246,0.5)] overflow-hidden
                                           hover:shadow-[0_12px_25px_-5px_rgba(59,130,246,0.6)] hover:-translate-y-0.5
                                           disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-none
                                           transition-all duration-300 active:scale-[0.98]"
                            >
                                <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/0 via-white/20 to-cyan-400/0 -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
                                <style>{`@keyframes shimmer { 100% { transform: translateX(100%); } }`}</style>

                                <span className="relative z-10 flex items-center justify-center gap-2.5">
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin text-blue-200" />
                                            Sistem Doğrulanıyor...
                                        </>
                                    ) : (
                                        <>
                                            <LogIn className="w-5 h-5 transition-transform group-hover:translate-x-1 duration-300" />
                                            Yetkilendirme İste
                                        </>
                                    )}
                                </span>
                            </button>
                        </form>

                        {/* Alt Bilgi */}
                        <div className="mt-8 pt-6 border-t border-slate-200">
                            <div className="flex items-center justify-center gap-2">
                                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
                                <p className="text-[12px] text-slate-500 font-semibold tracking-wide">
                                    Sistem Çevrimiçi • 256-bit Şifreleme Aktif
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}