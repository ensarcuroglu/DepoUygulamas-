function UrunKarti({ isim, kategori, stok, raf, durum }) {
  // Duruma göre renk belirleme (Kritikse kırmızı, değilse yeşil tonları)
  const isKritik = durum === "Kritik Stok";
  const durumRengi = isKritik ? "#ef4444" : "#10b981";

  // Minimal ve modern kart stilleri
  const kartStili = {
    backgroundColor: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    padding: "20px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    fontFamily: "system-ui, -apple-system, sans-serif"
  };

  const baslikStili = {
    margin: "0",
    fontSize: "16px",
    fontWeight: "600",
    color: "#111827"
  };

  const detayStili = {
    margin: "0",
    fontSize: "14px",
    color: "#6b7280",
    display: "flex",
    justifyContent: "space-between"
  };

  const etiketStili = {
    display: "inline-block",
    padding: "4px 8px",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: "500",
    backgroundColor: isKritik ? "#fef2f2" : "#ecfdf5",
    color: durumRengi,
    alignSelf: "flex-start",
    marginTop: "10px"
  };

  return (
    <div style={kartStili}>
      <h3 style={baslikStili}>{isim}</h3>
      
      <div style={detayStili}>
        <span>Kategori:</span>
        <span style={{ fontWeight: "500", color: "#374151" }}>{kategori}</span>
      </div>
      
      <div style={detayStili}>
        <span>Raf Konumu:</span>
        <span style={{ fontWeight: "500", color: "#374151" }}>{raf}</span>
      </div>

      <div style={detayStili}>
        <span>Stok Miktarı:</span>
        <span style={{ fontWeight: "600", color: isKritik ? "#ef4444" : "#374151" }}>
          {stok} Adet
        </span>
      </div>

      <span style={etiketStili}>
        {isKritik ? "⚠️ Stok Yetersiz" : "✓ Stok Yeterli"}
      </span>
    </div>
  );
}

export default UrunKarti;