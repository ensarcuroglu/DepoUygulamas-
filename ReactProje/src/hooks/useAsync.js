import { useState, useCallback } from 'react';

/**
 * Asenkron işlemlerde loading state'ini merkezi yöneten hook.
 *
 * `run(asyncFn)` çağrısı:
 *   - loading'i true yapar
 *   - asyncFn'yi await eder
 *   - sonucu (veya hatayı) aynen iletir
 *   - finally bloğunda loading'i false yapar
 *
 * @param {boolean} baslangicYukleniyor
 *   Sayfa ilk açıldığında iskelet animasyonunu hemen göstermek için `true` verin.
 *
 * @returns {{ loading: boolean, run: (asyncFn: () => Promise<T>) => Promise<T> }}
 *
 * @example
 *   const { loading, run } = useAsync(true);
 *
 *   const fetchData = async () => {
 *     try {
 *       const [res1, res2] = await run(() => Promise.all([api1(), api2()]));
 *       setState1(res1.data);
 *       setState2(res2.data);
 *     } catch {
 *       toast.error('Veriler yüklenemedi');
 *     }
 *   };
 */
export function useAsync(baslangicYukleniyor = false) {
    const [loading, setLoading] = useState(baslangicYukleniyor);

    const run = useCallback(async (asyncFn) => {
        setLoading(true);
        try {
            return await asyncFn();
        } finally {
            setLoading(false);
        }
    }, []);

    return { loading, run };
}
