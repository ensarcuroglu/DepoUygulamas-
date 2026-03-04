import React, { useEffect, useRef, useState } from 'react';
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode';
import { X, Camera, RefreshCcw } from 'lucide-react';

/**
 * Html5Qrcode kütüphanesi sarmalayıcısı: Kamerayı açıp karekod/barkod arar.
 */
const BarcodeScannerModal = ({ isOpen, onClose, onScanSuccess }) => {
    const [error, setError] = useState(null);
    const scannerRef = useRef(null); // Ekranda kameranın render olacağı div
    const html5QrCode = useRef(null); // Kütüphane nesnesi referansı

    useEffect(() => {
        // Modal kapalıysa veya zaten kameramız çalışıyorsa hiçbir şey yapma
        if (!isOpen) {
            stopScanner();
            return;
        }

        // Modal açıldığında tarayıcıyı (scanner instance) ayağa kaldır
        // timeout ile render olmasını bekliyoruz.
        const startScanner = async () => {
            try {
                // Zaten aynı id kuruluysa tekrar kurmaya çalışma
                if (!html5QrCode.current) {
                    html5QrCode.current = new Html5Qrcode('reader', { verbose: true }); // Detaylı loglama (verbose: true)
                }

                await html5QrCode.current.start(
                    { facingMode: 'environment' }, // Arka kamerayı kullan (mobilde)
                    {
                        fps: 20,       // Tarama hızı maksimuma çıkartıldı
                        qrbox: { width: 300, height: 150 }, // Çizgi barkodlara uygun daha ince bir dikdörtgen
                        disableFlip: false, // Ayna görüntüsüne de duyarlı
                        formatsToSupport: [
                            Html5QrcodeSupportedFormats.QR_CODE,
                            Html5QrcodeSupportedFormats.EAN_13,
                            Html5QrcodeSupportedFormats.EAN_8,
                            Html5QrcodeSupportedFormats.CODE_128,
                            Html5QrcodeSupportedFormats.CODE_39,
                            Html5QrcodeSupportedFormats.UPC_A
                        ]
                    },
                    (decodedText, decodedResult) => {
                        // Başarılı okuma olduğunda kapanıp Callback döndür
                        console.log("BARKOD OKUNDU:", decodedText, decodedResult);
                        stopScanner();
                        onScanSuccess(decodedText);
                        onClose();
                    },
                    (errorMessage) => {
                        // Tarama sırasında barkod görülmüyorsa sessizce yoksay (spam logları engelle)
                        // console.warn("Tarama uyarısı:", errorMessage);
                    }
                );
                setError(null);
            } catch (err) {
                console.error("Kamera başlatma hatası:", err);
                setError("Kameraya erişilemedi veya izin reddedildi.");
            }
        };

        setTimeout(startScanner, 200);

        return () => {
            stopScanner();
        };
    }, [isOpen, onScanSuccess, onClose]);

    const stopScanner = () => {
        if (html5QrCode.current && html5QrCode.current.isScanning) {
            html5QrCode.current
                .stop()
                .then(() => {
                    html5QrCode.current.clear();
                })
                .catch(console.error);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden relative border border-slate-200">

                {/* Header */}
                <div className="bg-slate-50 px-6 py-4 flex items-center justify-between border-b border-slate-200">
                    <div className="flex items-center space-x-2 text-slate-800">
                        <Camera className="w-5 h-5 text-indigo-600" />
                        <h3 className="font-semibold text-lg">Barkod Okut</h3>
                    </div>
                    <button
                        onClick={() => {
                            stopScanner();
                            onClose();
                        }}
                        className="text-slate-400 hover:text-red-500 hover:bg-slate-200 p-2 rounded-full transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body (Kamera) */}
                <div className="p-6">
                    {error ? (
                        <div className="text-center py-8">
                            <div className="bg-red-50 text-red-600 rounded-lg p-4 mb-4">
                                {error}
                            </div>
                            <button
                                onClick={() => {
                                    setError(null);
                                    stopScanner();
                                    // Sayfayı tazelemek / yeniden açmak için...
                                    setTimeout(() => {
                                        if (html5QrCode.current && !html5QrCode.current.isScanning) {
                                            html5QrCode.current = new Html5Qrcode('reader');
                                        }
                                    }, 100);
                                }}
                                className="inline-flex items-center space-x-2 text-indigo-600 hover:text-indigo-700 font-medium"
                            >
                                <RefreshCcw className="w-4 h-4" />
                                <span>Tekrar Dene</span>
                            </button>
                        </div>
                    ) : (
                        <>
                            {/* html5-qrcode kütüphanesi kamerayı bu id="reader" içine gömer */}
                            <div id="reader" className="rounded-xl overflow-hidden shadow-inner border bg-black text-white w-full h-[300px]" />
                            <p className="text-center text-sm text-slate-500 mt-4">
                                Lütfen ürünün barkodunu ekrandaki kare içine hizalayın.
                            </p>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default BarcodeScannerModal;
