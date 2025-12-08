'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
    href: string;
    label: string;
    icon: string;
}

const navItems: NavItem[] = [
    { href: '/', label: 'ホーム', icon: '📊' },
    { href: '/meetings', label: '会議', icon: '📅' },
    { href: '/upload', label: 'アップロード', icon: '📤' },
    { href: '/risks', label: 'リスク', icon: '⚠️' },
];

export default function MobileNav() {
    const pathname = usePathname();
    const [isVisible, setIsVisible] = useState(false);
    const [lastScrollY, setLastScrollY] = useState(0);

    // Hide nav on scroll down, show on scroll up
    useEffect(() => {
        const handleScroll = () => {
            const currentScrollY = window.scrollY;
            if (currentScrollY < 50) {
                setIsVisible(true);
            } else if (currentScrollY > lastScrollY && currentScrollY > 100) {
                setIsVisible(false);
            } else if (currentScrollY < lastScrollY) {
                setIsVisible(true);
            }
            setLastScrollY(currentScrollY);
        };

        setIsVisible(true);
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, [lastScrollY]);

    const isActive = (href: string) => {
        if (href === '/') return pathname === '/';
        return pathname.startsWith(href);
    };

    return (
        <nav
            className={`fixed bottom-0 left-0 right-0 lg:hidden z-50 transition-transform duration-300 ${
                isVisible ? 'translate-y-0' : 'translate-y-full'
            }`}
        >
            <div className="bg-gray-900/95 backdrop-blur-lg border-t border-white/10 px-4 py-2 safe-area-bottom">
                <div className="flex justify-around items-center">
                    {navItems.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex flex-col items-center py-2 px-3 rounded-lg transition-all ${
                                isActive(item.href)
                                    ? 'text-orange-400 bg-orange-500/10'
                                    : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            <span className="text-xl mb-1">{item.icon}</span>
                            <span className="text-xs font-medium">{item.label}</span>
                        </Link>
                    ))}
                    <button
                        className="flex flex-col items-center py-2 px-3 rounded-lg text-gray-400 hover:text-white transition-all"
                        onClick={() => {
                            // Open more menu or navigate to menu page
                            window.location.href = '/admin';
                        }}
                    >
                        <span className="text-xl mb-1">☰</span>
                        <span className="text-xs font-medium">メニュー</span>
                    </button>
                </div>
            </div>
        </nav>
    );
}

