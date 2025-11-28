import Dashboard from '../components/Dashboard';
import AuthGuard from '../components/AuthGuard';

export default function Home() {
  return (
    <AuthGuard>
      <main className="min-h-screen p-8">
        <div className="max-w-7xl mx-auto">
          <Dashboard />
        </div>
      </main>
    </AuthGuard>
  );
}
