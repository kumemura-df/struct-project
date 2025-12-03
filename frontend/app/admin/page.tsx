'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  listUsers,
  updateUserRole,
  deleteUser,
  getCurrentUser,
  User,
  UserRole,
  CurrentUser,
} from '../../lib/api';
import { toast } from '../../lib/toast';

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [usersData, userData] = await Promise.all([
        listUsers(),
        getCurrentUser(),
      ]);
      setUsers(usersData);
      setCurrentUser(userData);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load users. Admin access required.');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (email: string, newRole: UserRole) => {
    try {
      setUpdating(email);
      await updateUserRole(email, newRole);
      toast.success(`Role updated to ${newRole}`);
      await loadData();
    } catch (error) {
      console.error('Failed to update role:', error);
      toast.error('Failed to update role');
    } finally {
      setUpdating(null);
    }
  };

  const handleDelete = async (email: string) => {
    if (!confirm(`Are you sure you want to delete user ${email}?`)) {
      return;
    }

    try {
      await deleteUser(email);
      toast.success('User deleted');
      await loadData();
    } catch (error) {
      console.error('Failed to delete user:', error);
      toast.error('Failed to delete user');
    }
  };

  const getRoleBadgeColor = (role: UserRole) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-red-500';
      case 'PM':
        return 'bg-blue-500';
      case 'MEMBER':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse text-gray-400">Loading...</div>
        </div>
      </div>
    );
  }

  if (currentUser?.role !== 'ADMIN') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="text-6xl mb-4">403</div>
          <h1 className="text-2xl font-bold text-white mb-4">Access Denied</h1>
          <p className="text-gray-400 mb-8">Admin access is required to view this page.</p>
          <Link
            href="/"
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              User Management
            </h1>
            <p className="text-gray-400 mt-1">
              Manage user roles and permissions
            </p>
          </div>
          <Link
            href="/"
            className="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors"
          >
            Back
          </Link>
        </div>

        {/* Role Legend */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50 mb-6">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Role Permissions</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-1 rounded text-xs font-medium text-white bg-red-500">
                ADMIN
              </span>
              <span className="text-sm text-gray-400">Full access</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-1 rounded text-xs font-medium text-white bg-blue-500">
                PM
              </span>
              <span className="text-sm text-gray-400">Project management</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-1 rounded text-xs font-medium text-white bg-gray-500">
                MEMBER
              </span>
              <span className="text-sm text-gray-400">View & upload</span>
            </div>
          </div>
        </div>

        {/* User List */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden">
          <div className="p-4 border-b border-gray-700">
            <h2 className="text-lg font-semibold text-white">
              Users ({users.length})
            </h2>
          </div>

          <div className="divide-y divide-gray-700">
            {users.map((user) => (
              <div
                key={user.user_id}
                className="p-4 flex items-center justify-between hover:bg-gray-700/30"
              >
                <div className="flex items-center space-x-4">
                  {user.picture ? (
                    <img
                      src={user.picture}
                      alt={user.name || user.email}
                      className="w-10 h-10 rounded-full"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-gray-600 flex items-center justify-center text-white font-medium">
                      {(user.name || user.email).charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <div className="text-white font-medium">
                      {user.name || 'No name'}
                      {user.email === currentUser?.email && (
                        <span className="ml-2 text-xs text-gray-400">(you)</span>
                      )}
                    </div>
                    <div className="text-sm text-gray-400">{user.email}</div>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <select
                    value={user.role}
                    onChange={(e) => handleRoleChange(user.email, e.target.value as UserRole)}
                    disabled={
                      updating === user.email ||
                      user.email === currentUser?.email
                    }
                    className={`px-3 py-1 rounded-lg border border-gray-600 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 ${getRoleBadgeColor(
                      user.role
                    )}`}
                  >
                    <option value="ADMIN" className="bg-gray-800">
                      ADMIN
                    </option>
                    <option value="PM" className="bg-gray-800">
                      PM
                    </option>
                    <option value="MEMBER" className="bg-gray-800">
                      MEMBER
                    </option>
                  </select>

                  <button
                    onClick={() => handleDelete(user.email)}
                    disabled={user.email === currentUser?.email}
                    className="px-3 py-1 rounded-lg bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white text-sm transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>

          {users.length === 0 && (
            <div className="p-8 text-center text-gray-400">
              No users found
            </div>
          )}
        </div>

        {/* Info */}
        <div className="mt-6 text-sm text-gray-500">
          <p>* First user to log in automatically becomes ADMIN</p>
          <p>* Cannot delete or demote the last admin</p>
          <p>* Cannot modify your own role</p>
        </div>
      </div>
    </div>
  );
}
