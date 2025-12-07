'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { searchAll, SearchResults } from '../lib/api';

interface SearchResultItem {
    entity_type: string;
    id: string;
    title: string;
    description: string;
}

export default function GlobalSearch() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResults | null>(null);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const inputRef = useRef<HTMLInputElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const router = useRouter();

    // Flatten results for keyboard navigation
    const flatResults = results ? [
        ...results.tasks.map(r => ({ ...r, category: 'タスク' })),
        ...results.risks.map(r => ({ ...r, category: 'リスク' })),
        ...results.projects.map(r => ({ ...r, category: 'プロジェクト' })),
        ...results.decisions.map(r => ({ ...r, category: '決定事項' })),
    ] : [];

    // Debounced search
    useEffect(() => {
        if (query.length < 2) {
            setResults(null);
            return;
        }

        const timer = setTimeout(async () => {
            setLoading(true);
            try {
                const data = await searchAll(query, 10);
                setResults(data);
                setSelectedIndex(-1);
            } catch (error) {
                console.error('Search failed:', error);
            } finally {
                setLoading(false);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [query]);

    // Keyboard shortcut (Cmd+K / Ctrl+K)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                inputRef.current?.focus();
                setIsOpen(true);
            }
            if (e.key === 'Escape') {
                setIsOpen(false);
                inputRef.current?.blur();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    // Click outside to close
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const navigateToResult = useCallback((item: SearchResultItem) => {
        setIsOpen(false);
        setQuery('');
        
        switch (item.entity_type) {
            case 'task':
                router.push(`/?task=${item.id}`);
                break;
            case 'risk':
                router.push(`/risks?id=${item.id}`);
                break;
            case 'project':
                router.push(`/?project=${item.id}`);
                break;
            case 'decision':
                router.push(`/decisions?id=${item.id}`);
                break;
        }
    }, [router]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!isOpen || flatResults.length === 0) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setSelectedIndex(prev => 
                    prev < flatResults.length - 1 ? prev + 1 : prev
                );
                break;
            case 'ArrowUp':
                e.preventDefault();
                setSelectedIndex(prev => prev > 0 ? prev - 1 : prev);
                break;
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0 && flatResults[selectedIndex]) {
                    navigateToResult(flatResults[selectedIndex]);
                }
                break;
        }
    };

    const getEntityIcon = (type: string) => {
        switch (type) {
            case 'task': return '📋';
            case 'risk': return '⚠️';
            case 'project': return '📁';
            case 'decision': return '✓';
            default: return '📄';
        }
    };

    const hasResults = results && (
        results.tasks.length > 0 ||
        results.risks.length > 0 ||
        results.projects.length > 0 ||
        results.decisions.length > 0
    );

    return (
        <div ref={containerRef} className="relative">
            <div className="relative">
                <input
                    ref={inputRef}
                    type="text"
                    placeholder="検索... (⌘K)"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => setIsOpen(true)}
                    onKeyDown={handleKeyDown}
                    className="w-64 px-4 py-2 pl-10 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
                <svg
                    className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                </svg>
                {loading && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                        <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                )}
            </div>

            {/* Search Results Dropdown */}
            {isOpen && query.length >= 2 && (
                <div className="absolute top-full mt-2 w-96 max-h-96 overflow-y-auto bg-gray-900 border border-white/20 rounded-xl shadow-2xl z-50">
                    {loading ? (
                        <div className="p-4 text-center text-gray-400">
                            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                            検索中...
                        </div>
                    ) : hasResults ? (
                        <div className="divide-y divide-white/10">
                            {/* Tasks */}
                            {results.tasks.length > 0 && (
                                <div className="p-2">
                                    <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                        タスク
                                    </div>
                                    {results.tasks.map((item, idx) => {
                                        const globalIdx = idx;
                                        return (
                                            <button
                                                key={item.id}
                                                onClick={() => navigateToResult(item)}
                                                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                                                    selectedIndex === globalIdx
                                                        ? 'bg-blue-600/30'
                                                        : 'hover:bg-white/5'
                                                }`}
                                            >
                                                <div className="flex items-center gap-2">
                                                    <span>{getEntityIcon(item.entity_type)}</span>
                                                    <span className="text-white font-medium truncate">
                                                        {item.title}
                                                    </span>
                                                </div>
                                                {item.description && (
                                                    <p className="text-sm text-gray-400 truncate ml-6">
                                                        {item.description}
                                                    </p>
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Risks */}
                            {results.risks.length > 0 && (
                                <div className="p-2">
                                    <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                        リスク
                                    </div>
                                    {results.risks.map((item, idx) => {
                                        const globalIdx = results.tasks.length + idx;
                                        return (
                                            <button
                                                key={item.id}
                                                onClick={() => navigateToResult(item)}
                                                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                                                    selectedIndex === globalIdx
                                                        ? 'bg-blue-600/30'
                                                        : 'hover:bg-white/5'
                                                }`}
                                            >
                                                <div className="flex items-center gap-2">
                                                    <span>{getEntityIcon(item.entity_type)}</span>
                                                    <span className="text-white font-medium truncate">
                                                        {item.title}
                                                    </span>
                                                </div>
                                                {item.description && (
                                                    <p className="text-sm text-gray-400 truncate ml-6">
                                                        {item.description}
                                                    </p>
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Projects */}
                            {results.projects.length > 0 && (
                                <div className="p-2">
                                    <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                        プロジェクト
                                    </div>
                                    {results.projects.map((item, idx) => {
                                        const globalIdx = results.tasks.length + results.risks.length + idx;
                                        return (
                                            <button
                                                key={item.id}
                                                onClick={() => navigateToResult(item)}
                                                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                                                    selectedIndex === globalIdx
                                                        ? 'bg-blue-600/30'
                                                        : 'hover:bg-white/5'
                                                }`}
                                            >
                                                <div className="flex items-center gap-2">
                                                    <span>{getEntityIcon(item.entity_type)}</span>
                                                    <span className="text-white font-medium truncate">
                                                        {item.title}
                                                    </span>
                                                </div>
                                                {item.description && (
                                                    <p className="text-sm text-gray-400 truncate ml-6">
                                                        {item.description}
                                                    </p>
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Decisions */}
                            {results.decisions.length > 0 && (
                                <div className="p-2">
                                    <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                        決定事項
                                    </div>
                                    {results.decisions.map((item, idx) => {
                                        const globalIdx = results.tasks.length + results.risks.length + results.projects.length + idx;
                                        return (
                                            <button
                                                key={item.id}
                                                onClick={() => navigateToResult(item)}
                                                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                                                    selectedIndex === globalIdx
                                                        ? 'bg-blue-600/30'
                                                        : 'hover:bg-white/5'
                                                }`}
                                            >
                                                <div className="flex items-center gap-2">
                                                    <span>{getEntityIcon(item.entity_type)}</span>
                                                    <span className="text-white font-medium truncate">
                                                        {item.title}
                                                    </span>
                                                </div>
                                                {item.description && (
                                                    <p className="text-sm text-gray-400 truncate ml-6">
                                                        {item.description}
                                                    </p>
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="p-6 text-center text-gray-400">
                            <div className="text-3xl mb-2">🔍</div>
                            「{query}」に一致する結果がありません
                        </div>
                    )}

                    {/* Keyboard hints */}
                    <div className="p-2 border-t border-white/10 bg-white/5 text-xs text-gray-500 flex gap-4 justify-center">
                        <span>↑↓ 移動</span>
                        <span>Enter 選択</span>
                        <span>Esc 閉じる</span>
                    </div>
                </div>
            )}
        </div>
    );
}

