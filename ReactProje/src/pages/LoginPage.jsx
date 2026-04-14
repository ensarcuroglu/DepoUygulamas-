import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Package, User, Lock, Eye, EyeOff, AlertCircle, Loader2, Activity, Shield, Zap, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { hataMetni } from '../utils/hata';
import { motion, AnimatePresence } from 'framer-motion';

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

    // Framer Motion Animasyon Varyantları
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.1, delayChildren: 0.1 }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 15 },
        visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } }
    };

    return (
        <>
            {/* Tarayıcıların otomatik doldurma (sarı/mavi arka plan) sorununu çözen minimal reset */}
            <style dangerouslySetInnerHTML={{
                __html: `
                input:-webkit-autofill,
                input:-webkit-autofill:hover,
                input:-webkit-autofill:focus,
                input:-webkit-autofill:active {
                    -webkit-box-shadow: 0 0 0 30px #ffffff inset !important;
                    -webkit-text-fill-color: #0f172a !important;
                    transition: background-color 5000s ease-in-out 0s;
                }
            `}} />

            <div className="min-h-screen flex w-full font-sans bg-slate-50 text-slate-900 selection:bg-blue-100 selection:text-blue-900">
                
                {/* --- Sol Panel: Kurumsal Bilgi & İstatistikler (Desktop) --- */}
                <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 xl:p-20 bg-white border-r border-slate-200 relative overflow-hidden">
                    {/* Arka plan deseni (Subtle Grid) */}
                    <div className="absolute inset-0 z-0 pointer-events-none" style={{
                        backgroundImage: `url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0h40v40H0V0zm1 1h38v38H1V1z' fill='%23f8fafc' fill-opacity='1' fill-rule='evenodd'/%3E%3C/svg%3E")`,
                    }} />

                    <div className="relative z-10 flex flex-col gap-6 max-w-xl mt-10">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
                                <Package className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold tracking-tight text-slate-900">Depo Yönetim</h1>
                                <p className="text-[11px] font-semibold tracking-widest text-slate-500 uppercase">Enterprise Edition</p>
                            </div>
                        </div>

                        <div className="mt-12 space-y-6">
                            <h2 className="text-4xl xl:text-5xl font-extrabold tracking-tight text-slate-900 leading-[1.1]">
                                Operasyonlarınızı <br />
                                <span className="text-blue-600">veri ile yönetin.</span>
                            </h2>
                            <p className="text-lg text-slate-600 leading-relaxed font-medium">
                                Gelişmiş analitik altyapısı ile stok takibini otomatikleştirin, insan hatasını sıfıra indirin ve tedarik zincirinizi optimize edin.
                            </p>
                        </div>
                    </div>

                    {/* Enterprise İstatistik Kartları */}
                    <div className="relative z-10 grid grid-cols-2 gap-4 max-w-lg mb-10">
                        <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col gap-2">
                            <Activity className="w-5 h-5 text-blue-600" />
                            <div>
                                <p className="text-2xl font-bold text-slate-900">7/24</p>
                                <p className="text-sm font-medium text-slate-500">Sistem Erişilebilirliği</p>
                            </div>
                        </div>
                        <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col gap-2">
                            <Shield className="w-5 h-5 text-emerald-600" />
                            <div>
                                <p className="text-2xl font-bold text-slate-900">%99.9</p>
                                <p className="text-sm font-medium text-slate-500">Veri Doğruluğu</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* --- Sağ Panel: Form (Mobil & Desktop) --- */}
                <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12">
                    <motion.div 
                        variants={containerVariants}
                        initial="hidden"
                        animate="visible"
                        className="w-full max-w-[440px]"
                    >
                        {/* Mobil için Logo */}
                        <motion.div variants={itemVariants} className="lg:hidden flex items-center gap-3 mb-10">
                            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center shadow-sm">
                                <Package className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-lg font-bold tracking-tight text-slate-900">Depo Yönetim</h1>
                                <p className="text-[10px] font-semibold tracking-widest text-slate-500 uppercase">Sistem Girişi</p>
                            </div>
                        </motion.div>

                        <motion.div variants={itemVariants} className="mb-8">
                            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">Hesabınıza giriş yapın</h2>
                            <p className="text-sm text-slate-500 mt-2 font-medium">Lütfen yetkilendirilmiş kurumsal kimlik bilgilerinizi girin.</p>
                        </motion.div>

                        {/* Hata Mesajı Yönetimi (Smooth Slide & Fade) */}
                        <AnimatePresence>
                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                                    animate={{ opacity: 1, height: 'auto', marginBottom: 24 }}
                                    exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                                    className="overflow-hidden"
                                >
                                    <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-100 rounded-xl">
                                        <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                                        <p className="text-sm font-medium text-red-800 leading-relaxed">{error}</p>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        <form onSubmit={handleSubmit} className="space-y-5">
                            <motion.div variants={itemVariants} className="space-y-1.5">
                                <label className="block text-sm font-semibold text-slate-700">Kullanıcı Adı</label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                                        <User className="w-5 h-5" />
                                    </div>
                                    <input
                                        type="text"
                                        value={kullaniciAdi}
                                        onChange={(e) => setKullaniciAdi(e.target.value)}
                                        placeholder="Kullanıcı adınızı girin"
                                        autoComplete="username"
                                        autoFocus
                                        className="block w-full pl-11 pr-4 py-3 sm:py-3.5 text-sm font-medium bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 transition-all shadow-sm"
                                    />
                                </div>
                            </motion.div>

                            <motion.div variants={itemVariants} className="space-y-1.5">
                                <label className="block text-sm font-semibold text-slate-700">Şifre</label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                                        <Lock className="w-5 h-5" />
                                    </div>
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        value={sifre}
                                        onChange={(e) => setSifre(e.target.value)}
                                        placeholder="Şifrenizi girin"
                                        autoComplete="current-password"
                                        className="block w-full pl-11 pr-12 py-3 sm:py-3.5 text-sm font-medium bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 transition-all shadow-sm"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
                                        tabIndex={-1}
                                    >
                                        {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                    </button>
                                </div>
                            </motion.div>

                            <motion.div variants={itemVariants} className="pt-2">
                                <motion.button
                                    whileHover={{ scale: loading ? 1 : 1.01 }}
                                    whileTap={{ scale: loading ? 1 : 0.98 }}
                                    type="submit"
                                    disabled={loading}
                                    className="w-full flex items-center justify-center gap-2 py-3.5 px-4 bg-blue-600 text-white rounded-xl text-sm font-semibold shadow-[0_4px_14px_0_rgb(37,99,235,0.39)] hover:shadow-[0_6px_20px_rgba(37,99,235,0.23)] hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-600 disabled:opacity-70 disabled:cursor-not-allowed transition-all duration-200"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin text-blue-100" />
                                            <span>Sistem Doğrulanıyor...</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>Devam Et</span>
                                            <ArrowRight className="w-4 h-4" />
                                        </>
                                    )}
                                </motion.button>
                            </motion.div>
                        </form>

                        <motion.div variants={itemVariants} className="mt-8 flex items-center justify-center gap-2">
                            <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                            <p className="text-xs text-slate-500 font-medium">
                                Sistem Çevrimiçi • Güvenli Bağlantı Aktif
                            </p>
                        </motion.div>
                    </motion.div>
                </div>
            </div>
        </>
    );
}