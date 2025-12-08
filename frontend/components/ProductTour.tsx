'use client';

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { Step, CallBackProps, STATUS, EVENTS, ACTIONS } from 'react-joyride';

// Dynamically import Joyride to avoid SSR issues
const Joyride = dynamic(() => import('react-joyride'), { ssr: false });

const TOUR_STORAGE_KEY = 'product-tour-completed';

// Tour steps
const tourSteps: Step[] = [
    {
        target: 'body',
        content: (
            <div className="space-y-2">
                <h3 className="text-lg font-bold">🎉 Project Progress DB へようこそ！</h3>
                <p>
                    議事録からタスク・リスク・決定事項を自動抽出するプロジェクト管理ツールです。
                </p>
                <p className="text-sm text-gray-400">
                    このツアーで主要機能をご紹介します。
                </p>
            </div>
        ),
        placement: 'center',
        disableBeacon: true,
    },
    {
        target: 'nav',
        content: (
            <div className="space-y-2">
                <h3 className="text-lg font-bold">📋 サイドバーナビゲーション</h3>
                <p>
                    左側のサイドバーから各機能にアクセスできます。
                </p>
                <ul className="text-sm text-gray-300 list-disc list-inside">
                    <li>ダッシュボード - 全体概要</li>
                    <li>会議 - アップロードした議事録一覧</li>
                    <li>リスク - プロジェクトのリスク管理</li>
                </ul>
            </div>
        ),
        placement: 'right',
        disableBeacon: true,
    },
    {
        target: '[data-tour="upload"]',
        content: (
            <div className="space-y-2">
                <h3 className="text-lg font-bold">📤 議事録アップロード</h3>
                <p>
                    テキストファイルやPDFをアップロードすると、AIが自動で解析します。
                </p>
                <p className="text-sm text-gray-400">
                    タスク、リスク、決定事項が自動抽出されます。
                </p>
            </div>
        ),
        placement: 'bottom',
        disableBeacon: true,
        isFixed: true,
    },
    {
        target: '[data-tour="projects"]',
        content: (
            <div className="space-y-2">
                <h3 className="text-lg font-bold">📁 プロジェクト一覧</h3>
                <p>
                    プロジェクトを選択すると、関連するタスクがフィルタリングされます。
                </p>
                <p className="text-sm text-gray-400">
                    各プロジェクトのタスク数・リスク数も表示されます。
                </p>
            </div>
        ),
        placement: 'right',
        disableBeacon: true,
    },
    {
        target: '[data-tour="tasks"]',
        content: (
            <div className="space-y-2">
                <h3 className="text-lg font-bold">✅ タスク管理</h3>
                <p>
                    タスクのステータスをクリックで変更できます。
                </p>
                <ul className="text-sm text-gray-300 list-disc list-inside">
                    <li>未着手 → 進行中 → 完了</li>
                    <li>期限超過タスクは赤でハイライト</li>
                    <li>フィルタで絞り込み可能</li>
                </ul>
            </div>
        ),
        placement: 'left',
        disableBeacon: true,
    },
    {
        target: '[data-tour="search"]',
        content: (
            <div className="space-y-2">
                <h3 className="text-lg font-bold">🔍 グローバル検索</h3>
                <p>
                    ⌘K でどこからでも検索できます。タスク、リスク、プロジェクトを横断検索。
                </p>
            </div>
        ),
        placement: 'bottom',
        disableBeacon: true,
    },
    {
        target: '[data-tour="ai-chat"]',
        content: (
            <div className="space-y-2">
                <h3 className="text-lg font-bold">🤖 AIアシスタント</h3>
                <p>
                    右下のボタンでAIチャットを開けます。プロジェクトに関する質問ができます。
                </p>
                <p className="text-sm text-gray-400">
                    ⌘J でも開くことができます。
                </p>
            </div>
        ),
        placement: 'top',
        disableBeacon: true,
    },
    {
        target: 'body',
        content: (
            <div className="space-y-2">
                <h3 className="text-lg font-bold">🚀 準備完了！</h3>
                <p>
                    これで基本的な使い方は完了です。
                </p>
                <p className="text-sm text-gray-400">
                    まずは「アップロード」から議事録を登録してみましょう！
                </p>
            </div>
        ),
        placement: 'center',
        disableBeacon: true,
    },
];

// Custom styles for the tour
const joyrideStyles = {
    options: {
        arrowColor: 'rgb(30, 41, 59)',
        backgroundColor: 'rgb(30, 41, 59)',
        overlayColor: 'rgba(0, 0, 0, 0.7)',
        primaryColor: 'rgb(251, 146, 60)',
        textColor: 'rgb(248, 250, 252)',
        zIndex: 10000,
    },
    tooltip: {
        borderRadius: '12px',
        fontSize: '14px',
        padding: '20px',
    },
    tooltipContainer: {
        textAlign: 'left' as const,
    },
    tooltipTitle: {
        fontSize: '16px',
        fontWeight: 'bold',
    },
    buttonNext: {
        backgroundColor: 'rgb(251, 146, 60)',
        color: 'white',
        borderRadius: '8px',
        padding: '8px 16px',
        fontWeight: '600',
    },
    buttonBack: {
        color: 'rgb(148, 163, 184)',
        marginRight: '8px',
    },
    buttonSkip: {
        color: 'rgb(148, 163, 184)',
    },
    buttonClose: {
        display: 'none',
    },
    spotlight: {
        borderRadius: '12px',
    },
};

interface ProductTourProps {
    forceShow?: boolean;
}

export default function ProductTour({ forceShow = false }: ProductTourProps) {
    const [run, setRun] = useState(false);
    const [stepIndex, setStepIndex] = useState(0);

    useEffect(() => {
        // Check if tour has been completed
        const tourCompleted = localStorage.getItem(TOUR_STORAGE_KEY);
        
        if (!tourCompleted || forceShow) {
            // Delay start to allow page to fully render
            const timer = setTimeout(() => {
                setRun(true);
            }, 1000);
            return () => clearTimeout(timer);
        }
    }, [forceShow]);

    const handleJoyrideCallback = useCallback((data: CallBackProps) => {
        const { status, type, index, action } = data;
        
        // Handle step changes
        if (type === EVENTS.STEP_AFTER) {
            if (action === ACTIONS.NEXT) {
                setStepIndex(index + 1);
            } else if (action === ACTIONS.PREV) {
                setStepIndex(index - 1);
            }
        }
        
        // Handle tour completion
        if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
            setRun(false);
            localStorage.setItem(TOUR_STORAGE_KEY, 'true');
        }
    }, []);

    return (
        <Joyride
            steps={tourSteps}
            run={run}
            stepIndex={stepIndex}
            continuous
            showProgress
            showSkipButton
            hideCloseButton
            scrollToFirstStep
            scrollOffset={100}
            spotlightClicks={false}
            disableOverlayClose
            locale={{
                back: '戻る',
                close: '閉じる',
                last: '完了',
                next: '次へ',
                skip: 'スキップ',
            }}
            styles={joyrideStyles}
            callback={handleJoyrideCallback}
        />
    );
}

// Hook to manually trigger the tour
export function useProductTour() {
    const startTour = useCallback(() => {
        localStorage.removeItem(TOUR_STORAGE_KEY);
        window.location.reload();
    }, []);

    const resetTour = useCallback(() => {
        localStorage.removeItem(TOUR_STORAGE_KEY);
    }, []);

    return { startTour, resetTour };
}

