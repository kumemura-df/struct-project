import UploadForm from '../../components/UploadForm';
import AuthGuard from '../../components/AuthGuard';
import AppLayout from '../../components/AppLayout';

export default function UploadPage() {
    return (
        <AuthGuard>
            <AppLayout>
                <div className="max-w-xl mx-auto">
                    <div className="mb-6">
                        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                            議事録アップロード
                        </h1>
                        <p className="text-gray-400 mt-1">
                            会議の議事録をアップロードして自動解析
                        </p>
                    </div>
                    <UploadForm />
                </div>
            </AppLayout>
        </AuthGuard>
    );
}
