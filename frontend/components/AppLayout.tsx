'use client';

import { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import UserMenu from './UserMenu';
import GlobalSearch from './GlobalSearch';
import AIChatWidget from './AIChatWidget';
import ProductTour from './ProductTour';
import MobileNav from './MobileNav';
import { useSSE, useNotificationPermission } from '../lib/hooks';

interface AppLayoutProps {
    children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [isMobile, setIsMobile] = useState(false);

    // Enable SSE for real-time updates
    useSSE(true);
    
    // Request notification permission
    useNotificationPermission();

    // Responsive layout detection
    useEffect(() => {
        const checkMobile = () => {
            const mobile = window.innerWidth < 1024;
            setIsMobile(mobile);
            setSidebarCollapsed(mobile);
        };
        
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    return (
        <div className="min-h-screen">
            {/* Desktop Sidebar - hidden on mobile */}
            {!isMobile && <Sidebar />}

            {/* Main Content */}
            <div className={`transition-all duration-300 ${
                isMobile 
                    ? 'ml-0 pb-20' // No sidebar margin on mobile, add bottom padding for mobile nav
                    : sidebarCollapsed 
                        ? 'ml-16' 
                        : 'ml-64'
            }`}>
                {/* Top Bar */}
                <header className="sticky top-0 z-30 bg-gray-900/80 backdrop-blur-lg border-b border-white/10">
                    <div className="flex items-center justify-between h-14 lg:h-16 px-4 lg:px-6">
                        {/* Mobile: Logo + Search */}
                        {isMobile && (
                            <div className="flex items-center gap-2 mr-2">
                                <span className="text-xl">📋</span>
                                <span className="font-bold text-sm text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                                    Progress DB
                                </span>
                            </div>
                        )}
                        
                        <div className={`${isMobile ? 'flex-1 max-w-[200px]' : 'flex-1'}`}>
                            <GlobalSearch />
                        </div>
                        
                        <UserMenu />
                    </div>
                </header>

                {/* Page Content */}
                <main className={`p-4 lg:p-6 ${isMobile ? 'safe-area-bottom' : ''}`}>
                    {children}
                </main>
            </div>

            {/* Mobile Bottom Navigation */}
            {isMobile && <MobileNav />}

            {/* AI Chat Widget - adjusted position on mobile */}
            <div className={isMobile ? 'mb-16' : ''}>
                <AIChatWidget />
            </div>
            
            {/* Product Tour - only on desktop */}
            {!isMobile && <ProductTour />}
        </div>
    );
}
