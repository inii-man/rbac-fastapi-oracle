"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { Shield, Users, LayoutDashboard, Key, Settings, LogOut, Database } from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();
  const { hasPermission, logout, user } = useAuth();

  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard, permission: null },
    { name: 'Users', path: '/users', icon: Users, permission: 'user.view' },
    { name: 'Roles', path: '/roles', icon: Shield, permission: 'role.view' },
    { name: 'Permissions', path: '/permissions', icon: Key, permission: 'permission.view' },
    { name: 'Snapshots', path: '/snapshots', icon: Database, permission: 'snapshot.view' },
    { name: 'Worker Page', path: '/worker', icon: Settings, permission: 'worker.access' },
  ];

  if (!user) return null;

  return (
    <div className="w-64 bg-slate-900 text-white min-h-screen flex flex-col transition-all duration-300">
      <div className="p-6 border-b border-slate-800">
        <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">RBAC System</h2>
        <p className="text-sm text-slate-400 mt-2">Logged in as: <span className="font-semibold text-slate-200">{user.username}</span></p>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => {
          // If a permission is required and user does not have it, hide the menu item
          if (item.permission && !hasPermission(item.permission)) return null;

          const isActive = pathname === item.path;
          return (
            <Link
              key={item.path}
              href={item.path}
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                isActive 
                  ? 'bg-blue-600 text-white' 
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button
          onClick={logout}
          className="flex items-center justify-center space-x-2 w-full px-4 py-2 bg-slate-800 hover:bg-red-500 hover:text-white rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}
