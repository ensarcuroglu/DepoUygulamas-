import sharp from 'sharp';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ICONS_DIR = join(__dirname, '..', 'public', 'icons');

const TARGETS = [
  { src: 'depo-icon.svg', out: 'icon-192.png', size: 192 },
  { src: 'depo-icon.svg', out: 'icon-512.png', size: 512 },
  { src: 'depo-icon.svg', out: 'apple-touch-icon-180.png', size: 180 },
  { src: 'depo-icon-maskable.svg', out: 'icon-512-maskable.png', size: 512 },
];

for (const { src, out, size } of TARGETS) {
  const svg = await readFile(join(ICONS_DIR, src));
  const png = await sharp(svg, { density: 384 })
    .resize(size, size, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png({ compressionLevel: 9 })
    .toBuffer();
  await writeFile(join(ICONS_DIR, out), png);
  console.log(`✓ ${out} (${size}x${size})`);
}
