import { useCallback, useEffect, useMemo, useRef } from 'react';
import toast from 'react-hot-toast';
import {
    DuplicateScanGuard,
    generateIdempotencyKey,
    isZebraDevice,
    sanitizeBarkod,
    scanFeedback,
    validateBarkodFormat,
} from '../utils/barcode';

const INPUT_FOCUS_DELAY_MS = 60;
const DEFAULT_DUPLICATE_COOLDOWN_MS = 3000;

/**
 * Terminal ekranlari icin input-primary Zebra Keyboard Wedge akisi.
 *
 * Bu hook global keydown dinlemez. DataWedge barkodu aktif input'a yazar,
 * Send ENTER key ile bu hook'un onKeyDown handler'i tek islem tetikler.
 */
export default function useTerminalScanInput({
    mode,
    value,
    setValue,
    onSubmit,
    contextKey,
    disabled = false,
    isEnabled = true,
    autoFocus = true,
    inputRef: providedInputRef = null,
    duplicateCooldownMs = DEFAULT_DUPLICATE_COOLDOWN_MS,
    validateFormat = true,
    clearOnSuccess = true,
    clearOnError = true,
}) {
    const ownInputRef = useRef(null);
    const inputRef = providedInputRef || ownInputRef;
    const guardRef = useRef(null);
    const pendingRef = useRef(new Set());
    const onSubmitRef = useRef(onSubmit);
    const valueRef = useRef(value);
    const zebraDetected = useMemo(() => isZebraDevice(), []);

    if (!guardRef.current) {
        guardRef.current = new DuplicateScanGuard(duplicateCooldownMs);
    }

    useEffect(() => {
        onSubmitRef.current = onSubmit;
    }, [onSubmit]);

    useEffect(() => {
        valueRef.current = value;
    }, [value]);

    const focusInput = useCallback(() => {
        if (!autoFocus || !isEnabled || disabled) return;
        window.setTimeout(() => {
            inputRef.current?.focus();
        }, INPUT_FOCUS_DELAY_MS);
    }, [autoFocus, disabled, inputRef, isEnabled]);

    useEffect(() => {
        focusInput();
    }, [contextKey, focusInput, mode]);

    useEffect(() => {
        const handleVisibilityChange = () => {
            if (!document.hidden) {
                focusInput();
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [focusInput]);

    const submitScan = useCallback(async (rawValue, options = {}) => {
        const { force = false } = options;
        if (!force && (!isEnabled || disabled)) return false;

        const raw = rawValue ?? valueRef.current;
        const sanitized = sanitizeBarkod(raw, mode);
        if (!sanitized) {
            setValue('');
            focusInput();
            return false;
        }

        setValue(sanitized);

        if (validateFormat) {
            const validation = validateBarkodFormat(sanitized, mode);
            if (!validation.valid) {
                scanFeedback('error');
                toast.error(validation.error || 'Barkod formatı hatalı.');
                if (clearOnError) setValue('');
                focusInput();
                return false;
            }
        }

        const dedupeKey = `${contextKey || 'terminal'}:${mode}:${sanitized}`;
        if (pendingRef.current.has(dedupeKey) || !guardRef.current.check(dedupeKey)) {
            scanFeedback('warning');
            toast('Tekrar okuma yok sayıldı.');
            if (clearOnError) setValue('');
            focusInput();
            return false;
        }

        pendingRef.current.add(dedupeKey);
        const idempotencyKey = generateIdempotencyKey();

        try {
            const result = await onSubmitRef.current?.(sanitized, {
                idempotencyKey,
                mode,
                contextKey,
            });
            if (result !== false) {
                scanFeedback('success');
                if (clearOnSuccess) setValue('');
            } else if (clearOnError) {
                scanFeedback('error');
                setValue('');
            }
            focusInput();
            return result !== false;
        } catch (error) {
            scanFeedback('error');
            if (clearOnError) setValue('');
            focusInput();
            throw error;
        } finally {
            pendingRef.current.delete(dedupeKey);
        }
    }, [
        clearOnError,
        clearOnSuccess,
        contextKey,
        disabled,
        focusInput,
        isEnabled,
        mode,
        setValue,
        validateFormat,
    ]);

    const handleKeyDown = useCallback((event) => {
        if (event.key !== 'Enter') return;
        event.preventDefault();
        event.stopPropagation();
        void submitScan();
    }, [submitScan]);

    const resetDuplicateGuard = useCallback(() => {
        guardRef.current?.reset();
        pendingRef.current.clear();
    }, []);

    return {
        inputRef,
        zebraDetected,
        focusInput,
        handleKeyDown,
        submitScan,
        resetDuplicateGuard,
    };
}
