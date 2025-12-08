import Dashboard from '../components/Dashboard';
import AuthGuard from '../components/AuthGuard';
import AppLayout from '../components/AppLayout';

export default function Home() {
  return (
    <AuthGuard>
      <AppLayout>
        <Dashboard />
      </AppLayout>
    </AuthGuard>
  );
}
