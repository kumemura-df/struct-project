import { describe, it, expect } from 'vitest';
import { render, screen } from '../../test/utils';
import LoadingSpinner from '../LoadingSpinner';

describe('LoadingSpinner', () => {
    it('renders without text by default', () => {
        const { container } = render(<LoadingSpinner />);
        // Should render spinner div but no text
        const spinnerDiv = container.querySelector('div.animate-spin');
        expect(spinnerDiv).toBeTruthy();
    });

    it('renders with custom text', () => {
        render(<LoadingSpinner text="読み込み中..." />);
        expect(screen.getByText('読み込み中...')).toBeInTheDocument();
    });

    it('renders small size correctly', () => {
        const { container } = render(<LoadingSpinner size="small" />);
        const spinnerDiv = container.querySelector('.h-6');
        expect(spinnerDiv).toBeTruthy();
    });

    it('renders medium size correctly', () => {
        const { container } = render(<LoadingSpinner size="medium" />);
        const spinnerDiv = container.querySelector('.h-12');
        expect(spinnerDiv).toBeTruthy();
    });

    it('renders large size correctly', () => {
        const { container } = render(<LoadingSpinner size="large" />);
        const spinnerDiv = container.querySelector('.h-16');
        expect(spinnerDiv).toBeTruthy();
    });

    it('renders with overlay', () => {
        const { container } = render(<LoadingSpinner overlay />);
        const overlayDiv = container.querySelector('.fixed.inset-0');
        expect(overlayDiv).toBeTruthy();
    });

    it('renders without overlay by default', () => {
        const { container } = render(<LoadingSpinner />);
        const overlayDiv = container.querySelector('.fixed.inset-0');
        expect(overlayDiv).toBeNull();
    });
});
