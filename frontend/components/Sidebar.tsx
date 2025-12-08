'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
    href: string;
    label: string;
    icon: string;
    badge?: number;
    group: 'main' | 'management' | 'settings';
}

const navItems: NavItem[] = [
    // Main Features
    { href: '/', label: 'ダッシュボード', icon: '📊', group: 'main' },
    { href: '/meetings', label: '会議', icon: '📅', group: 'main' },
    { href: '/upload', label: 'アップロード', icon: '📤', group: 'main' },
    
    // Management
    { href: '/risks', label: 'リスク', icon: '⚠️', group: 'management' },
    { href: '/decisions', label: '決定事項', icon: '✓', group: 'management' },
    { href: '/diff', label: '差分', icon: '🔄', group: 'management' },
    { href: '/reports', label: 'レポート', icon: '📈', group: 'management' },
    { href: '/health', label: 'ヘルス', icon: '💓', group: 'management' },
    
    // Settings & Admin
    { href: '/admin', label: '管理', icon: '👑', group: 'settings' },
    { href: '/settings/integrations', label: '連携', icon: '🔗', group: 'settings' },
];

const groupLabels: Record<string, string> = {
    main: 'メイン',
    management: '管理',
    settings: '設定',
};

export default function Sidebar() {
    const pathname = usePathname();
    const [isCollapsed, setIsCollapsed] = useState(false);

    const isActive = (href: string) => {
        if (href === '/') return pathname === '/';
        return pathname.startsWith(href);
    };

    const groupedItems = {
        main: navItems.filter(item => item.group === 'main'),
        management: navItems.filter(item => item.group === 'management'),
        settings: navItems.filter(item => item.group === 'settings'),
    };

    return (
        <aside
            className={`fixed left-0 top-0 h-full bg-gray-900/95 backdrop-blur-lg border-r border-white/10 z-40 transition-all duration-300 ${
                isCollapsed ? 'w-16' : 'w-64'
            }`}
        >
            <div className="flex flex-col h-full">
                {/* Logo / Header */}
                <div className="p-4 border-b border-white/10">
                    <div className="flex items-center justify-between">
                        {!isCollapsed && (
                            <Link href="/" className="flex items-center gap-2">
                                <span className="text-2xl">📋</span>
                                <span className="font-bold text-lg text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                                    Progress DB
                                </span>
                            </Link>
                        )}
                        <button
                            onClick={() => setIsCollapsed(!isCollapsed)}
                            className="p-2 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white"
                            title={isCollapsed ? '展開' : '折りたたむ'}
                        >
                            {isCollapsed ? '→' : '←'}
                        </button>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 overflow-y-auto py-4">
                    {Object.entries(groupedItems).map(([group, items]) => (
                        <div key={group} className="mb-6">
                            {!isCollapsed && (
                                <h3 className="px-4 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                    {groupLabels[group]}
                                </h3>
                            )}
                            <ul className="space-y-1 px-2">
                                {items.map((item) => (
                                    <li key={item.href}>
                                        <Link
                                            href={item.href}
                                            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                                                isActive(item.href)
                                                    ? 'bg-blue-600/20 text-blue-400 border-l-4 border-blue-500'
                                                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                                            } ${isCollapsed ? 'justify-center' : ''}`}
                                            title={isCollapsed ? item.label : undefined}
                                            data-tour={item.href === '/upload' ? 'upload' : undefined}
                                        >
                                            <span className="text-lg">{item.icon}</span>
                                            {!isCollapsed && (
                                                <span className="font-medium">{item.label}</span>
                                            )}
                                            {!isCollapsed && item.badge !== undefined && item.badge > 0 && (
                                                <span className="ml-auto px-2 py-0.5 text-xs font-bold rounded-full bg-red-500 text-white">
                                                    {item.badge}
                                                </span>
                                            )}
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </nav>

                {/* Footer / Help */}
                {!isCollapsed && (
                    <div className="p-4 border-t border-white/10">
                        <div className="text-xs text-gray-500 text-center">
                            <p>⌘K で検索</p>
                            <p className="mt-1">⌘J でAIチャット</p>
                        </div>
                    </div>
                )}
            </div>
        </aside>
    );
}

