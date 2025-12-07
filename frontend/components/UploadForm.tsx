'use client';

import { useState } from 'react';
import { uploadFile, uploadText } from '../lib/api';
import { toast } from '../lib/toast';
import LoadingSpinner from './LoadingSpinner';
import { useRouter } from 'next/navigation';

type InputMode = 'file' | 'text';

export default function UploadForm() {
    const router = useRouter();
    const [inputMode, setInputMode] = useState<InputMode>('text');
    const [file, setFile] = useState<File | null>(null);
    const [text, setText] = useState('');
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [title, setTitle] = useState('');
    const [uploading, setUploading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (inputMode === 'file' && !file) return;
        if (inputMode === 'text' && !text.trim()) return;

        setUploading(true);
        try {
            if (inputMode === 'file' && file) {
                await uploadFile(file, date, title);
            } else if (inputMode === 'text') {
                await uploadText(text, date, title);
            }
            toast.success('アップロード成功！処理を開始しました。');

            // Reset form
            setFile(null);
            setText('');
            setTitle('');
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

    const isSubmitDisabled = uploading || (inputMode === 'file' ? !file : !text.trim());

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
                    📝 テキスト入力
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
                    📁 ファイルアップロード
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
                {inputMode === 'text' ? (
                    <div>
                        <label className="block text-sm font-medium text-gray-200 mb-2">
                            議事録テキスト
                        </label>
                        <textarea
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                            placeholder="議事録の内容を入力またはペーストしてください..."
                            rows={12}
                            required
                        />
                        <p className="mt-2 text-sm text-gray-400">
                            {text.length > 0 ? `${text.length} 文字` : '直接入力またはコピー＆ペーストできます'}
                        </p>
                    </div>
                ) : (
                    <div>
                        <label className="block text-sm font-medium text-gray-200 mb-2">
                            ファイル (.txt または .md)
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
                            accept=".txt,.md"
                            required={inputMode === 'file'}
                        />
                        {file && (
                            <p className="mt-2 text-sm text-gray-400">
                                選択中: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                            </p>
                        )}
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
