import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Package, User, Lock, Eye, EyeOff, AlertCircle, Loader2, Activity, Shield, ArrowRight } from 'lucide-react';
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

    // Daha yumuşak Framer Motion Animasyon Varyantları
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.08, delayChildren: 0.05 }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { 
            opacity: 1, 
            y: 0, 
            transition: { type: 'spring', stiffness: 250, damping: 25 } 
        }
    };

    return (
        <>
            {/* Minimal Autofill Reset - Yeni kavisli tasarıma uygun güncellendi */}
            <style dangerouslySetInnerHTML={{
                __html: `
                input:-webkit-autofill,
                input:-webkit-autofill:hover,
                input:-webkit-autofill:focus,
                input:-webkit-autofill:active {
                    -webkit-box-shadow: 0 0 0 30px #ffffff inset !important;
                    -webkit-text-fill-color: #0f172a !important;
                    transition: background-color 5000s ease-in-out 0s;
                    border-radius: 1rem !important;
                }
            `}} />

            {/* Arka plan: Çok yumuşak bir degrade */}
            <div className="min-h-screen flex w-full font-sans bg-gradient-to-br from-slate-50 to-slate-100 text-slate-900 selection:bg-blue-100 selection:text-blue-900">
                
                {/* --- Sol Panel: Kurumsal Bilgi & İstatistikler (Desktop) --- */}
                <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 xl:p-20 relative overflow-hidden">
                    {/* Modern, soft arka plan deseni */}
                    <div className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none" style={{
                        backgroundImage: `radial-gradient(circle at 2px 2px, #0f172a 1px, transparent 0)`,
                        backgroundSize: '32px 32px'
                    }} />

                    <div className="relative z-10 flex flex-col gap-6 max-w-xl mt-10">
                        <motion.div 
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.6 }}
                            className="flex items-center gap-4"
                        >
                            <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100">
                                <Package className="w-7 h-7 text-blue-600" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold tracking-tight text-slate-900">Depo Yönetim</h1>
                                <p className="text-xs font-bold tracking-widest text-slate-400 uppercase mt-0.5">Enterprise Edition</p>
                            </div>
                        </motion.div>

                        <motion.div 
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.1 }}
                            className="mt-16 space-y-6"
                        >
                            <h2 className="text-4xl xl:text-5xl font-extrabold tracking-tight text-slate-900 leading-[1.15]">
                                Operasyonlarınızı <br />
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
                                    veri ile yönetin.
                                </span>
                            </h2>
                            <p className="text-lg text-slate-500 leading-relaxed font-medium max-w-md">
                                Gelişmiş analitik altyapısı ile stok takibini otomatikleştirin, insan hatasını sıfıra indirin.
                            </p>
                        </motion.div>
                    </div>

                    {/* Enterprise İstatistik Kartları (Soft Glassmorphism) */}
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className="relative z-10 grid grid-cols-2 gap-5 max-w-lg mb-10"
                    >
                        <div className="p-6 rounded-3xl bg-white/60 backdrop-blur-md border border-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] flex flex-col gap-3 transition-transform hover:-translate-y-1 duration-300">
                            <Activity className="w-6 h-6 text-blue-500" />
                            <div>
                                <p className="text-3xl font-bold text-slate-900 tracking-tight">7/24</p>
                                <p className="text-sm font-medium text-slate-500 mt-1">Sistem Erişilebilirliği</p>
                            </div>
                        </div>
                        <div className="p-6 rounded-3xl bg-white/60 backdrop-blur-md border border-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] flex flex-col gap-3 transition-transform hover:-translate-y-1 duration-300">
                            <Shield className="w-6 h-6 text-emerald-500" />
                            <div>
                                <p className="text-3xl font-bold text-slate-900 tracking-tight">%99.9</p>
                                <p className="text-sm font-medium text-slate-500 mt-1">Veri Doğruluğu</p>
                            </div>
                        </div>
                    </motion.div>
                </div>

                {/* --- Sağ Panel: Form (Mobil & Desktop) --- */}
                <div className="w-full lg:w-1/2 flex items-center justify-center p-4 sm:p-8 relative">
                    
                    {/* Arka plan parlama efekti (Sadece masaüstünde ince bir estetik katar) */}
                    <div className="hidden lg:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-400/10 rounded-full blur-3xl pointer-events-none" />

                    <motion.div 
                        variants={containerVariants}
                        initial="hidden"
                        animate="visible"
                        className="w-full max-w-[420px] bg-white rounded-[2.5rem] p-8 sm:p-10 shadow-[0_8px_40px_rgb(0,0,0,0.04)] border border-slate-100 relative z-10"
                    >
                        {/* Mobil için Logo */}
                        <motion.div variants={itemVariants} className="lg:hidden flex flex-col items-center gap-4 mb-10 text-center">
                            <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center border border-blue-100/50">
                                <Package className="w-8 h-8 text-blue-600" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold tracking-tight text-slate-900">Depo Yönetim</h1>
                                <p className="text-[11px] font-bold tracking-widest text-slate-400 uppercase mt-1">Sistem Girişi</p>
                            </div>
                        </motion.div>

                        <motion.div variants={itemVariants} className="mb-8 lg:text-left text-center">
                            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">Hoş Geldiniz</h2>
                            <p className="text-sm text-slate-500 mt-2.5 font-medium">Lütfen sistem bilgilerinizi giriniz.</p>
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
                                    <div className="flex items-start gap-3 p-4 bg-red-50/80 border border-red-100 rounded-2xl">
                                        <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                                        <p className="text-sm font-medium text-red-700 leading-relaxed">{error}</p>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        <form onSubmit={handleSubmit} className="space-y-5">
                            <motion.div variants={itemVariants} className="space-y-2">
                                <label className="block text-[13px] font-semibold text-slate-700 ml-1">Kullanıcı Adı</label>
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-blue-600 transition-colors duration-300">
                                        <User className="w-5 h-5" />
                                    </div>
                                    <input
                                        type="text"
                                        value={kullaniciAdi}
                                        onChange={(e) => setKullaniciAdi(e.target.value)}
                                        placeholder="Kullanıcı adınızı girin"
                                        autoComplete="username"
                                        autoFocus
                                        className="block w-full pl-12 pr-4 py-3.5 sm:py-4 text-sm font-medium bg-slate-50/50 hover:bg-slate-50 border border-slate-200/60 rounded-2xl text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all duration-300"
                                    />
                                </div>
                            </motion.div>

                            <motion.div variants={itemVariants} className="space-y-2">
                                <label className="block text-[13px] font-semibold text-slate-700 ml-1">Şifre</label>
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-blue-600 transition-colors duration-300">
                                        <Lock className="w-5 h-5" />
                                    </div>
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        value={sifre}
                                        onChange={(e) => setSifre(e.target.value)}
                                        placeholder="Şifrenizi girin"
                                        autoComplete="current-password"
                                        className="block w-full pl-12 pr-12 py-3.5 sm:py-4 text-sm font-medium bg-slate-50/50 hover:bg-slate-50 border border-slate-200/60 rounded-2xl text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all duration-300"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
                                        tabIndex={-1}
                                    >
                                        {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                    </button>
                                </div>
                            </motion.div>

                            <motion.div variants={itemVariants} className="pt-4">
                                <motion.button
                                    whileHover={{ scale: loading ? 1 : 1.01, y: loading ? 0 : -1 }}
                                    whileTap={{ scale: loading ? 1 : 0.98 }}
                                    type="submit"
                                    disabled={loading}
                                    className="relative w-full flex items-center justify-center gap-2 py-4 px-4 bg-slate-900 text-white rounded-2xl text-sm font-semibold shadow-[0_8px_20px_-6px_rgba(15,23,42,0.3)] hover:shadow-[0_12px_25px_-6px_rgba(15,23,42,0.4)] hover:bg-slate-800 focus:outline-none focus:ring-4 focus:ring-slate-900/20 disabled:opacity-70 disabled:cursor-not-allowed transition-all duration-300 overflow-hidden"
                                >
                                    {/* Buton içi ince parlama efekti */}
                                    <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full hover:animate-[shimmer_1.5s_infinite]" />
                                    
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin text-slate-300" />
                                            <span>Doğrulanıyor...</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>Sisteme Giriş Yap</span>
                                            <ArrowRight className="w-4 h-4 ml-1" />
                                        </>
                                    )}
                                </motion.button>
                            </motion.div>
                        </form>

                        <motion.div variants={itemVariants} className="mt-10 flex items-center justify-center gap-2">
                            <span className="relative flex h-2.5 w-2.5">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                            </span>
                            <p className="text-xs text-slate-500 font-medium">
                                Güvenli Bağlantı Aktif
                            </p>
                        </motion.div>
                    </motion.div>
                </div>
            </div>
        </>
    );
}