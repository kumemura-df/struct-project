import UploadForm from '../../components/UploadForm';
import AuthGuard from '../../components/AuthGuard';

export default function UploadPage() {
    return (
        <AuthGuard>
            <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 p-8">
                <div className="max-w-md mx-auto">
                    <UploadForm />
                </div>
            </div>
        </AuthGuard>
    );
}
