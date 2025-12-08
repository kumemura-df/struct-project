'use client';

import { useState } from 'react';
import { uploadFile, uploadText, uploadAudio } from '../lib/api';
import { toast } from '../lib/toast';
import LoadingSpinner from './LoadingSpinner';
import { useRouter } from 'next/navigation';

type InputMode = 'file' | 'text' | 'audio';

// Supported transcript sources
const TRANSCRIPT_SOURCES = [
    { id: 'auto', name: '自動検出', description: '形式を自動判別' },
    { id: 'otter', name: 'Otter.ai', description: 'Otter.aiからのエクスポート' },
    { id: 'tldv', name: 'tl;dv', description: 'tl;dvからのエクスポート' },
    { id: 'zoom', name: 'Zoom', description: 'Zoomの文字起こし' },
    { id: 'plain', name: 'プレーンテキスト', description: '通常のテキスト' },
];

// Supported audio formats
const AUDIO_FORMATS = ['.mp3', '.m4a', '.wav', '.flac', '.webm', '.ogg', '.opus'];

export default function UploadForm() {
    const router = useRouter();
    const [inputMode, setInputMode] = useState<InputMode>('text');
    const [file, setFile] = useState<File | null>(null);
    const [text, setText] = useState('');
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [title, setTitle] = useState('');
    const [uploading, setUploading] = useState(false);
    const [sourceType, setSourceType] = useState('auto');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (inputMode === 'file' && !file) return;
        if (inputMode === 'text' && !text.trim()) return;
        if (inputMode === 'audio' && !file) return;

        setUploading(true);
        try {
            let result;
            if (inputMode === 'file' && file) {
                result = await uploadFile(file, date, title, sourceType);
            } else if (inputMode === 'text') {
                result = await uploadText(text, date, title, sourceType);
            } else if (inputMode === 'audio' && file) {
                result = await uploadAudio(file, date, title);
            }
            
            // Show success message based on result type
            if (inputMode === 'audio' && result?.transcription) {
                const speakers = result.transcription.speakers?.length || 0;
                const duration = Math.round(result.transcription.duration_seconds || 0);
                toast.success(`音声処理完了！話者: ${speakers}人, 長さ: ${duration}秒`);
            } else if (result?.transcript_format) {
                const formatName = TRANSCRIPT_SOURCES.find(s => s.id === result.transcript_format)?.name || result.transcript_format;
                toast.success(`アップロード成功！形式: ${formatName}`);
            } else {
                toast.success('アップロード成功！処理を開始しました。');
            }

            // Reset form
            setFile(null);
            setText('');
            setTitle('');
            setSourceType('auto');
            const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
            if (fileInput) fileInput.value = '';

            // Redirect to dashboard after short delay
            setTimeout(() => {
                router.push('/');
            }, 2000);
        } catch (error) {
            console.error(error);
            toast.error(error instanceof Error ? error.message : 'アップロードに失敗しました。もう一度お試しください。');
        } finally {
            setUploading(false);
        }
    };

    const isSubmitDisabled = uploading || 
        (inputMode === 'file' ? !file : inputMode === 'audio' ? !file : !text.trim());

    return (
        <div className="p-6 glass rounded-xl">
            <h2 className="text-2xl font-bold mb-6 text-white">議事録アップロード</h2>

            {/* Input Mode Tabs */}
            <div className="flex mb-6 bg-white/5 rounded-lg p-1">
                <button
                    type="button"
                    onClick={() => setInputMode('text')}
                    className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                        inputMode === 'text'
                            ? 'bg-blue-600 text-white shadow-md'
                            : 'text-gray-400 hover:text-white'
                    }`}
                >
                    📝 テキスト
                </button>
                <button
                    type="button"
                    onClick={() => setInputMode('file')}
                    className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                        inputMode === 'file'
                            ? 'bg-blue-600 text-white shadow-md'
                            : 'text-gray-400 hover:text-white'
                    }`}
                >
                    📄 字幕ファイル
                </button>
                <button
                    type="button"
                    onClick={() => setInputMode('audio')}
                    className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                        inputMode === 'audio'
                            ? 'bg-purple-600 text-white shadow-md'
                            : 'text-gray-400 hover:text-white'
                    }`}
                >
                    🎤 音声ファイル
                </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                    <label className="block text-sm font-medium text-gray-200 mb-2">会議日</label>
                    <input
                        type="date"
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
                        className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-200 mb-2">タイトル (任意)</label>
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Weekly Sync"
                    />
                </div>

                {/* Conditional Input based on mode */}
                {/* Source Type Selection */}
                <div>
                    <label className="block text-sm font-medium text-gray-200 mb-2">
                        文字起こしソース
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {TRANSCRIPT_SOURCES.map((source) => (
                            <button
                                key={source.id}
                                type="button"
                                onClick={() => setSourceType(source.id)}
                                className={`p-3 rounded-lg text-left transition-all ${
                                    sourceType === source.id
                                        ? 'bg-blue-600/30 border-2 border-blue-500'
                                        : 'bg-white/5 border border-white/10 hover:bg-white/10'
                                }`}
                            >
                                <div className="text-sm font-medium text-white">{source.name}</div>
                                <div className="text-xs text-gray-400 mt-0.5">{source.description}</div>
                            </button>
                        ))}
                    </div>
                </div>

                {inputMode === 'text' ? (
                    <div>
                        <label className="block text-sm font-medium text-gray-200 mb-2">
                            議事録テキスト
                        </label>
                        <textarea
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono text-sm"
                            placeholder={`文字起こしテキストをペーストしてください...

例（Otter.ai形式）:
田中  0:00
本日はプロジェクトの進捗確認を行います。

鈴木  0:15
はい、現在のステータスを報告します。`}
                            rows={12}
                            required
                        />
                        <p className="mt-2 text-sm text-gray-400">
                            {text.length > 0 ? `${text.length} 文字` : 'Otter.ai, tl;dv, Zoomなどの文字起こしテキストをペーストできます'}
                        </p>
                    </div>
                ) : inputMode === 'file' ? (
                    <div>
                        <label className="block text-sm font-medium text-gray-200 mb-2">
                            字幕/テキストファイル (.txt, .md, .vtt, .srt)
                        </label>
                        <input
                            type="file"
                            onChange={(e) => setFile(e.target.files?.[0] || null)}
                            className="w-full text-sm text-gray-300
                                file:mr-4 file:py-2 file:px-4
                                file:rounded-lg file:border-0
                                file:text-sm file:font-semibold
                                file:bg-blue-600 file:text-white
                                hover:file:bg-blue-700 file:cursor-pointer"
                            accept=".txt,.md,.vtt,.srt"
                            required={inputMode === 'file'}
                        />
                        {file && (
                            <p className="mt-2 text-sm text-gray-400">
                                選択中: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                            </p>
                        )}
                        <div className="mt-3 p-3 bg-white/5 rounded-lg">
                            <p className="text-xs text-gray-400">
                                <strong className="text-gray-300">対応形式:</strong>
                            </p>
                            <ul className="mt-1 text-xs text-gray-400 space-y-0.5">
                                <li>• <strong>.vtt</strong> - Zoom, YouTube, Google Meet字幕</li>
                                <li>• <strong>.srt</strong> - 標準字幕形式</li>
                                <li>• <strong>.txt</strong> - Otter.ai, tl;dv, Zoom出力</li>
                            </ul>
                        </div>
                    </div>
                ) : (
                    <div>
                        <label className="block text-sm font-medium text-gray-200 mb-2">
                            🎤 音声ファイル
                        </label>
                        <input
                            type="file"
                            onChange={(e) => setFile(e.target.files?.[0] || null)}
                            className="w-full text-sm text-gray-300
                                file:mr-4 file:py-2 file:px-4
                                file:rounded-lg file:border-0
                                file:text-sm file:font-semibold
                                file:bg-purple-600 file:text-white
                                hover:file:bg-purple-700 file:cursor-pointer"
                            accept={AUDIO_FORMATS.join(',')}
                            required={inputMode === 'audio'}
                        />
                        {file && (
                            <p className="mt-2 text-sm text-gray-400">
                                選択中: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                            </p>
                        )}
                        <div className="mt-3 p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                            <p className="text-xs text-purple-300">
                                <strong>🔊 Speech-to-Text で自動文字起こし</strong>
                            </p>
                            <ul className="mt-2 text-xs text-gray-400 space-y-0.5">
                                <li>• 会議録音を直接アップロード</li>
                                <li>• 話者を自動識別（誰が話しているか）</li>
                                <li>• 日本語に最適化</li>
                            </ul>
                            <p className="mt-2 text-xs text-gray-400">
                                <strong className="text-gray-300">対応形式:</strong> {AUDIO_FORMATS.join(', ')}
                            </p>
                        </div>
                    </div>
                )}

                <button
                    type="submit"
                    disabled={isSubmitDisabled}
                    className="w-full flex justify-center items-center space-x-3 py-3 px-4 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg"
                >
                    {uploading ? (
                        <>
                            <LoadingSpinner size="small" />
                            <span>処理中...</span>
                        </>
                    ) : (
                        <span>📤 議事録を送信</span>
                    )}
                </button>
            </form>
        </div>
    );
}
