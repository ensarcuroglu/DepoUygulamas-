/**
 * imageCropper — Belge fotoğrafları için Canvas tabanlı kırpma yardımcıları.
 *
 * Strateji:
 *  - autoCropDocument(blob): Görseli grayscale'e çevirip her satır/sütun için
 *    parlaklık varyansını hesaplar; arka plana göre belirgin bir blok varsa
 *    (varyans > threshold) o satır/sütun "içerik" sayılır. İlk ve son içerik
 *    satır/sütunu bbox olur. İçerik bulunamazsa orijinal görsel döner.
 *  - cropToBlob(blob, rect): Verilen dikdörtgenle blob'u yeniden çizip JPEG döner.
 *
 * opencv.js dağıtılmadığı için tamamen vanilla Canvas. Mükemmel değil ama
 * arka planı koyu, belgeyi açık (veya tersi) çoğu sahada makul sonuç verir.
 */

const OUTPUT_MIME = 'image/jpeg';
const OUTPUT_QUALITY = 0.9;
const SAMPLE_MAX_DIM = 800;
const VARIANCE_RATIO = 0.35;
const MIN_BBOX_RATIO = 0.4;
const PADDING_RATIO = 0.015;

const loadImage = (source) => new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('Görsel yüklenemedi.'));
    if (source instanceof Blob) {
        img.src = URL.createObjectURL(source);
    } else if (typeof source === 'string') {
        img.src = source;
    } else {
        reject(new Error('Geçersiz görsel kaynağı.'));
    }
});

const canvasToBlob = (canvas, mime = OUTPUT_MIME, quality = OUTPUT_QUALITY) =>
    new Promise((resolve, reject) => {
        canvas.toBlob(
            (blob) => (blob ? resolve(blob) : reject(new Error('Canvas blob üretemedi.'))),
            mime,
            quality,
        );
    });

const drawSampled = (image, maxDim) => {
    const scale = Math.min(1, maxDim / Math.max(image.width, image.height));
    const w = Math.max(1, Math.round(image.width * scale));
    const h = Math.max(1, Math.round(image.height * scale));
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(image, 0, 0, w, h);
    return { canvas, ctx, scale, width: w, height: h };
};

const computeRowColVariance = (data, width, height) => {
    const rowSum = new Float32Array(height);
    const rowSumSq = new Float32Array(height);
    const colSum = new Float32Array(width);
    const colSumSq = new Float32Array(width);

    for (let y = 0; y < height; y += 1) {
        let rs = 0;
        let rss = 0;
        for (let x = 0; x < width; x += 1) {
            const idx = (y * width + x) * 4;
            // Rec.601 luma — RGB → Y
            const luma = (data[idx] * 299 + data[idx + 1] * 587 + data[idx + 2] * 114) / 1000;
            rs += luma;
            rss += luma * luma;
            colSum[x] += luma;
            colSumSq[x] += luma * luma;
        }
        rowSum[y] = rs;
        rowSumSq[y] = rss;
    }

    const rowVar = new Float32Array(height);
    for (let y = 0; y < height; y += 1) {
        const mean = rowSum[y] / width;
        rowVar[y] = Math.max(0, rowSumSq[y] / width - mean * mean);
    }
    const colVar = new Float32Array(width);
    for (let x = 0; x < width; x += 1) {
        const mean = colSum[x] / height;
        colVar[x] = Math.max(0, colSumSq[x] / height - mean * mean);
    }
    return { rowVar, colVar };
};

const findBounds = (arr, threshold) => {
    let start = -1;
    let end = -1;
    for (let i = 0; i < arr.length; i += 1) {
        if (arr[i] >= threshold) {
            if (start === -1) start = i;
            end = i;
        }
    }
    return { start, end };
};

const maxValue = (arr) => {
    let max = 0;
    for (let i = 0; i < arr.length; i += 1) {
        if (arr[i] > max) max = arr[i];
    }
    return max;
};

/**
 * Görseldeki belge bbox'unu varyans heuristiği ile bulup kırpar.
 * Otomatik kırpma başarısız olursa orijinal blob'u (ya da yeniden encode edilmişini) döner.
 */
export async function autoCropDocument(blob, options = {}) {
    const padding = options.padding ?? PADDING_RATIO;
    const varianceRatio = options.varianceRatio ?? VARIANCE_RATIO;
    const minBoxRatio = options.minBoxRatio ?? MIN_BBOX_RATIO;

    const image = await loadImage(blob);
    try {
        const sample = drawSampled(image, SAMPLE_MAX_DIM);
        const { data } = sample.ctx.getImageData(0, 0, sample.width, sample.height);
        const { rowVar, colVar } = computeRowColVariance(data, sample.width, sample.height);

        const rowMax = maxValue(rowVar);
        const colMax = maxValue(colVar);
        const rowThreshold = rowMax * varianceRatio;
        const colThreshold = colMax * varianceRatio;

        const rows = findBounds(rowVar, rowThreshold);
        const cols = findBounds(colVar, colThreshold);

        const widthRatio = (cols.end - cols.start + 1) / sample.width;
        const heightRatio = (rows.end - rows.start + 1) / sample.height;

        if (
            rows.start === -1 || cols.start === -1 ||
            widthRatio < minBoxRatio || heightRatio < minBoxRatio
        ) {
            return {
                blob: await reencode(image),
                cropped: false,
                rect: { x: 0, y: 0, width: image.width, height: image.height },
            };
        }

        const padX = Math.round(image.width * padding);
        const padY = Math.round(image.height * padding);
        const inverseScale = 1 / sample.scale;
        const rect = {
            x: Math.max(0, Math.round(cols.start * inverseScale) - padX),
            y: Math.max(0, Math.round(rows.start * inverseScale) - padY),
            width: 0,
            height: 0,
        };
        rect.width = Math.min(
            image.width - rect.x,
            Math.round((cols.end - cols.start + 1) * inverseScale) + padX * 2,
        );
        rect.height = Math.min(
            image.height - rect.y,
            Math.round((rows.end - rows.start + 1) * inverseScale) + padY * 2,
        );

        return {
            blob: await cropImageToBlob(image, rect),
            cropped: true,
            rect,
        };
    } finally {
        revokeIfObjectUrl(image);
    }
}

/**
 * Manuel dikdörtgen kırpma — rect orijinal görsel piksel koordinatlarındadır.
 */
export async function cropToBlob(blob, rect) {
    const image = await loadImage(blob);
    try {
        return await cropImageToBlob(image, rect);
    } finally {
        revokeIfObjectUrl(image);
    }
}

async function cropImageToBlob(image, rect) {
    const w = Math.max(1, Math.round(rect.width));
    const h = Math.max(1, Math.round(rect.height));
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(image, rect.x, rect.y, w, h, 0, 0, w, h);
    return await canvasToBlob(canvas);
}

async function reencode(image) {
    const canvas = document.createElement('canvas');
    canvas.width = image.width;
    canvas.height = image.height;
    canvas.getContext('2d').drawImage(image, 0, 0);
    return await canvasToBlob(canvas);
}

function revokeIfObjectUrl(image) {
    if (image?.src?.startsWith('blob:')) {
        try { URL.revokeObjectURL(image.src); } catch { /* ignore */ }
    }
}

export default autoCropDocument;
