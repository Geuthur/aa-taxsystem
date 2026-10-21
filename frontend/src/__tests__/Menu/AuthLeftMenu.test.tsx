// React
import { MemoryRouter } from 'react-router-dom';

// Third Party
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

// AA TaxSystem
// AA Example
import AuthLeftMenu from '@/Menu/AuthLeftMenu';

vi.mock('react-i18next', async (importOriginal) => {
    const actual = await importOriginal<typeof import('react-i18next')>();
    return {
        ...actual,
        useTranslation: () => ({
            t: (key: string) => key,
        }),
    };
});

const renderMenu = (data: Parameters<typeof AuthLeftMenu>[0]['data']) => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter initialEntries={['/taxsystem/']}>
                <AuthLeftMenu data={data} isLoading={false} error={false} />
            </MemoryRouter>
        </QueryClientProvider>
    );
};

describe('AuthLeftMenu', () => {
    it('should render internal navigation links', () => {
        // Test Data
        const testData = [
            { name: 'Dashboard', link: 'dashboard' },
            { name: 'Settings', link: '/settings/' },
        ];

        // Test Action
        renderMenu(testData);

        // Expected Result
        const dashboardLink = screen.getByText('Dashboard');
        expect(dashboardLink).toBeDefined();
        expect(dashboardLink.getAttribute('href')).toBe('/taxsystem/dashboard/');

        const settingsLink = screen.getByText('Settings');
        expect(settingsLink).toBeDefined();
        expect(settingsLink.getAttribute('href')).toBe('/taxsystem/settings/');
    });

    it('should render external links with standard href', () => {
        // Test Data
        const testData = [
            { name: 'External Docs', link: 'https://docs.example.com', is_external: true },
        ];

        // Test Action
        renderMenu(testData);

        // Expected Result
        const externalLink = screen.getByText('External Docs');
        expect(externalLink).toBeDefined();
        expect(externalLink.getAttribute('href')).toBe('https://docs.example.com');
    });

    it('should filter out items without links or handle empty list', () => {
        // Test Data
        const testData = [
            { name: 'No Link Category' },
        ];

        // Test Action
        const { container } = renderMenu(testData);

        // Expected Result
        expect(container.querySelectorAll('li')).toHaveLength(0);
    });

    it('should render Settings link with pulse when has_errors is true or an owner has an error', async () => {
        // Test Data
        const testData = [
            { name: 'Settings', link: '/settings/', has_errors: true },
        ];

        // Test Action
        renderMenu(testData);

        // Expected Result
        const settingsLink = screen.getByTestId('settings-nav-link');
        expect(settingsLink).toBeDefined();
        expect(settingsLink.classList.contains('aa-order-nav-pulse')).toBe(false);
        expect(settingsLink.querySelector('.aa-pending-dot-container')).toBeInTheDocument();
        expect(settingsLink.querySelector('.aa-danger-dot-ping')).toBeInTheDocument();
    });
});

