import { describe, it, expect, beforeEach, vi } from 'vitest';
import { toast, ToastMessage } from '../toast';

describe('toast', () => {
    it('calls subscriber with success toast', () => {
        const listener = vi.fn();
        const unsubscribe = toast.subscribe(listener);
        
        toast.success('Success message');
        
        expect(listener).toHaveBeenCalledOnce();
        const receivedToast = listener.mock.calls[0][0] as ToastMessage;
        expect(receivedToast.type).toBe('success');
        expect(receivedToast.message).toBe('Success message');
        
        unsubscribe();
    });

    it('calls subscriber with error toast', () => {
        const listener = vi.fn();
        const unsubscribe = toast.subscribe(listener);
        
        toast.error('Error message');
        
        expect(listener).toHaveBeenCalledOnce();
        const receivedToast = listener.mock.calls[0][0] as ToastMessage;
        expect(receivedToast.type).toBe('error');
        expect(receivedToast.message).toBe('Error message');
        
        unsubscribe();
    });

    it('calls subscriber with info toast', () => {
        const listener = vi.fn();
        const unsubscribe = toast.subscribe(listener);
        
        toast.info('Info message');
        
        expect(listener).toHaveBeenCalledOnce();
        const receivedToast = listener.mock.calls[0][0] as ToastMessage;
        expect(receivedToast.type).toBe('info');
        expect(receivedToast.message).toBe('Info message');
        
        unsubscribe();
    });

    it('calls subscriber with warning toast', () => {
        const listener = vi.fn();
        const unsubscribe = toast.subscribe(listener);
        
        toast.warning('Warning message');
        
        expect(listener).toHaveBeenCalledOnce();
        const receivedToast = listener.mock.calls[0][0] as ToastMessage;
        expect(receivedToast.type).toBe('warning');
        expect(receivedToast.message).toBe('Warning message');
        
        unsubscribe();
    });

    it('generates unique IDs for each toast', () => {
        const listener = vi.fn();
        const unsubscribe = toast.subscribe(listener);
        
        toast.success('First');
        toast.success('Second');
        
        expect(listener).toHaveBeenCalledTimes(2);
        const firstToast = listener.mock.calls[0][0] as ToastMessage;
        const secondToast = listener.mock.calls[1][0] as ToastMessage;
        expect(firstToast.id).not.toBe(secondToast.id);
        
        unsubscribe();
    });

    it('unsubscribes correctly', () => {
        const listener = vi.fn();
        const unsubscribe = toast.subscribe(listener);
        
        toast.success('Before unsubscribe');
        expect(listener).toHaveBeenCalledOnce();
        
        unsubscribe();
        
        toast.success('After unsubscribe');
        expect(listener).toHaveBeenCalledOnce(); // Still only called once
    });

    it('includes custom duration', () => {
        const listener = vi.fn();
        const unsubscribe = toast.subscribe(listener);
        
        toast.success('Message', 10000);
        
        const receivedToast = listener.mock.calls[0][0] as ToastMessage;
        expect(receivedToast.duration).toBe(10000);
        
        unsubscribe();
    });
});
