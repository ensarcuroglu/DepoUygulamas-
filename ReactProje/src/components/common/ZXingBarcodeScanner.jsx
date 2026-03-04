import React, { useEffect, useRef, useState, useCallback } from 'react';
import { BrowserMultiFormatReader, NotFoundException } from '@zxing/library';
import { X, Camera, RefreshCcw } from 'lucide-react';

const ZXingBarcodeScanner = ({ isOpen, onClose, onScanSuccess }) => {
    const videoRef = useRef(null);
    const codeReaderRef = useRef(null);
    const [error, setError] = useState(null);
    const [isScanning, setIsScanning] = useState(false);

    const stopScanner = useCallback(() => {
        if (codeReaderRef.current) {
            codeReaderRef.current.reset();
            setIsScanning(false);
        }
    }, []);

    useEffect(() => {
        if (!isOpen) {
            stopScanner();
            return;
        }

        const startScanner = async () => {
            try {
                if (!codeReaderRef.current) {
                    codeReaderRef.current = new BrowserMultiFormatReader();
                }

                // Tüm kullanılabilir kameraları al
                const videoInputDevices = await codeReaderRef.current.listVideoInputDevices();

                if (videoInputDevices.length === 0) {
                    throw new Error("Kamera bulunamadı");
                }

                // Tercihen arka kamerayı seç (Eğer varsa 'back' veya 'environment' kelimesi içerenleri bul)
                let selectedDeviceId = videoInputDevices[0].deviceId;
                const backCamera = videoInputDevices.find(device =>
                    device.label.toLowerCase().includes('back') ||
                    device.label.toLowerCase().includes('environment')
                );

                if (backCamera) {
                    selectedDeviceId = backCamera.deviceId;
                }

                setIsScanning(true);
                setError(null);

                codeReaderRef.current.decodeFromVideoDevice(
                    selectedDeviceId,
                    videoRef.current,
                    (result, err) => {
                        if (result) {
                            console.log("ZXing ile BARKOD OKUNDU:", result.getText());
                            onScanSuccess(result.getText());
                            stopScanner();
                            onClose();
                        }
                        if (err && !(err instanceof NotFoundException)) {
                            // Ciddi bir hata oluştuğunda (Sadece kamerada QR bulamamasını ignore et)
                            console.error("Tarama hatası:", err);
                        }
                    }
                );

            } catch (err) {
                console.error("Kamera başlatma hatası:", err);
                setError("Kameraya erişilemedi veya izin reddedildi.");
                setIsScanning(false);
            }
        };

        // Modal'ın DOM'a tam yerleşmesi için kısa bir bekleme
        setTimeout(startScanner, 200);

        return () => stopScanner();
    }, [isOpen, onScanSuccess, onClose, stopScanner]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden relative border border-slate-200">
                {/* Header */}
                <div className="bg-slate-50 px-6 py-4 flex items-center justify-between border-b border-slate-200">
                    <div className="flex items-center space-x-2 text-slate-800">
                        <Camera className="w-5 h-5 text-indigo-600" />
                        <h3 className="font-semibold text-lg">Barkod Okut (ZXing)</h3>
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
                                    // Yeniden başlatmayı denemek için kapat/aç
                                    onClose();
                                }}
                                className="inline-flex items-center space-x-2 text-indigo-600 hover:text-indigo-700 font-medium"
                            >
                                <RefreshCcw className="w-4 h-4" />
                                <span>Kapat ve Tekrar Dene</span>
                            </button>
                        </div>
                    ) : (
                        <div className="relative rounded-xl overflow-hidden shadow-inner border bg-black text-white w-full aspect-square md:h-[300px] flex items-center justify-center">
                            {/* ZXing video elementine yazdırır */}
                            <video
                                ref={videoRef}
                                className="w-full h-full object-cover"
                                autoPlay
                                muted
                                playsInline
                            ></video>

                            {/* Tarama Kılavuz Çizgisi (Görsel Animasyon) */}
                            {isScanning && (
                                <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-center">
                                    <div className="w-[80%] h-[50%] border-2 border-green-500/50 rounded-lg relative overflow-hidden">
                                        <div className="w-full h-0.5 bg-green-500 shadow-[0_0_8px_2px_rgba(34,197,94,0.5)] animate-[scan_2s_ease-in-out_infinite]"></div>
                                    </div>
                                </div>
                            )}

                            <style dangerouslySetInnerHTML={{
                                __html: `
                                @keyframes scan {
                                    0% { transform: translateY(0); }
                                    50% { transform: translateY(140px); }
                                    100% { transform: translateY(0); }
                                }
                            `}} />
                        </div>
                    )}
                    <p className="text-center text-sm text-slate-500 mt-4">
                        Lütfen ürünün barkodunu ekrandaki kılavuz kutuda tutun.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ZXingBarcodeScanner;
