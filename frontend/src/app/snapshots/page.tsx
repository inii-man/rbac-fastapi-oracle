"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/AuthContext';
import api from '@/lib/api';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

type SnapshotStatus = 'PENDING' | 'COMPLETED' | 'FAILED' | 'EXPIRED';

interface Snapshot {
  id: number;
  snapshot_code: string;
  name: string;
  description: string | null;
  source_table: string;
  record_count: number;
  file_size_bytes: number;
  file_format: string;
  status: SnapshotStatus;
  created_at: string;
  completed_at: string | null;
  expires_at: string | null;
  is_public: string;
  created_by: string | null;
}

interface CreatePayload {
  name: string;
  description: string;
  source_table: string;
  file_format: string;
  is_public: string;
  allowed_roles: string[];
}

// Tabel yang tersedia untuk snapshot
const AVAILABLE_TABLES = [
  { value: 'users',       label: 'Users — Data pengguna sistem' },
  { value: 'roles',       label: 'Roles — Data role / jabatan' },
  { value: 'permissions', label: 'Permissions — Data hak akses' },
  { value: 'model_has_roles',       label: 'Model Has Roles — Relasi user-role' },
  { value: 'role_has_permissions',  label: 'Role Has Permissions — Relasi role-permission' },
];

const AVAILABLE_ROLES = ['admin', 'supervisor', 'worker'];

const STATUS_STYLES: Record<SnapshotStatus, string> = {
  PENDING:   'bg-yellow-100 text-yellow-800',
  COMPLETED: 'bg-green-100 text-green-800',
  FAILED:    'bg-red-100 text-red-800',
  EXPIRED:   'bg-slate-100 text-slate-500',
};

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function SnapshotsPage() {
  const { hasPermission } = useAuth();
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [viewData, setViewData] = useState<{ code: string; records: any[] } | null>(null);
  const [dataLoading, setDataLoading] = useState(false);

  const [form, setForm] = useState<CreatePayload>({
    name: '',
    description: '',
    source_table: '',
    file_format: 'json',
    is_public: 'N',
    allowed_roles: [],
  });

  const fetchSnapshots = async () => {
    try {
      setLoading(true);
      const res = await api.get('/snapshots');
      setSnapshots(res.data);
    } catch (err) {
      console.error('Failed to fetch snapshots', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSnapshots();
  }, []);

  const handleCreate = async () => {
    if (!form.name || form.name.length < 5) {
      alert('Nama snapshot minimal 5 karakter');
      return;
    }
    if (!form.source_table) {
      alert('Pilih tabel sumber terlebih dahulu');
      return;
    }
    try {
      const payload: any = {
        name: form.name,
        source_table: form.source_table,
        file_format: form.file_format,
        is_public: form.is_public,
      };
      if (form.description) payload.description = form.description;
      if (form.allowed_roles.length > 0) payload.allowed_roles = form.allowed_roles.join(',');

      await api.post('/snapshots', payload);
      setForm({ name: '', description: '', source_table: '', file_format: 'json', is_public: 'N', allowed_roles: [] });
      setIsCreateOpen(false);
      fetchSnapshots();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create snapshot');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this snapshot and its file?')) return;
    try {
      await api.delete(`/snapshots/${id}`);
      fetchSnapshots();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete snapshot');
    }
  };

  const handleViewData = async (snap: Snapshot) => {
    if (snap.status !== 'COMPLETED') return;
    setDataLoading(true);
    try {
      const res = await api.get(`/snapshots/${snap.id}/data?format=json`);
      setViewData({ code: snap.snapshot_code, records: res.data.data.data });
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to load snapshot data');
    } finally {
      setDataLoading(false);
    }
  };

  const handleDownload = async (snap: Snapshot) => {
    if (snap.status !== 'COMPLETED') return;
    try {
      const res = await api.get(`/snapshots/${snap.id}/data?format=download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${snap.snapshot_code}.${snap.file_format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: any) {
      alert('Failed to download snapshot');
    }
  };

  const inputClass = "flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950 dark:border-slate-800 dark:bg-slate-950";

  return (
    <div className="flex bg-slate-50 dark:bg-slate-900 min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8">
        {/* Header */}
        <header className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 dark:text-white">Data Snapshots</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1 text-sm">
              Point-in-time capture dataset untuk interkoneksi data antar sistem
            </p>
          </div>

          {hasPermission('snapshot.create') && (
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
              <DialogTrigger asChild>
                <Button>+ Buat Snapshot</Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>Buat Snapshot Baru</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">

                  {/* Tabel Sumber */}
                  <div className="space-y-1">
                    <Label>Tabel Sumber <span className="text-red-500">*</span></Label>
                    <select
                      className={inputClass}
                      value={form.source_table}
                      onChange={e => setForm({ ...form, source_table: e.target.value })}
                    >
                      <option value="">-- Pilih Tabel --</option>
                      {AVAILABLE_TABLES.map(t => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  </div>

                  {/* Nama Snapshot — di-generate otomatis tapi bisa diubah */}
                  <div className="space-y-1">
                    <Label>Nama Snapshot <span className="text-red-500">*</span></Label>
                    <Input
                      placeholder="Contoh: Snapshot Users Maret 2026"
                      value={form.name}
                      onChange={e => setForm({ ...form, name: e.target.value })}
                    />
                    <p className="text-xs text-slate-400">Minimal 5 karakter, deskriptif dan mudah dikenali</p>
                  </div>

                  {/* Deskripsi */}
                  <div className="space-y-1">
                    <Label>Deskripsi</Label>
                    <Input
                      placeholder="Keterangan tambahan (opsional)"
                      value={form.description}
                      onChange={e => setForm({ ...form, description: e.target.value })}
                    />
                  </div>

                  {/* Format & Akses */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <Label>Format File</Label>
                      <select
                        className={inputClass}
                        value={form.file_format}
                        onChange={e => setForm({ ...form, file_format: e.target.value })}
                      >
                        <option value="json">📄 JSON</option>
                        <option value="csv">📊 CSV</option>
                      </select>
                    </div>
                    <div className="space-y-1">
                      <Label>Visibilitas</Label>
                      <select
                        className={inputClass}
                        value={form.is_public}
                        onChange={e => setForm({ ...form, is_public: e.target.value })}
                      >
                        <option value="N">🔒 Private</option>
                        <option value="Y">🌐 Public</option>
                      </select>
                    </div>
                  </div>

                  {/* Allowed Roles — checkbox group, muncul hanya jika Private */}
                  {form.is_public === 'N' && (
                    <div className="space-y-2">
                      <Label>Akses Role (opsional)</Label>
                      <p className="text-xs text-slate-400">Role yang dapat mengakses snapshot ini selain pemilik</p>
                      <div className="flex gap-4">
                        {AVAILABLE_ROLES.map(role => (
                          <label key={role} className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              className="rounded border-slate-300"
                              checked={(form.allowed_roles as string[]).includes(role)}
                              onChange={e => {
                                const current = form.allowed_roles as string[];
                                setForm({
                                  ...form,
                                  allowed_roles: e.target.checked
                                    ? [...current, role]
                                    : current.filter(r => r !== role),
                                });
                              }}
                            />
                            <span className="text-sm capitalize">{role}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  <Button
                    onClick={handleCreate}
                    className="w-full"
                    disabled={!form.source_table || form.name.length < 5}
                  >
                    Generate Snapshot
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </header>

        {/* Stats bar */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {(['COMPLETED', 'PENDING', 'FAILED', 'EXPIRED'] as SnapshotStatus[]).map(s => {
            const count = snapshots.filter(x => x.status === s).length;
            return (
              <Card key={s}>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">{count}</div>
                  <div className="text-sm text-slate-500">{s}</div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Table */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Daftar Snapshot</CardTitle>
            <Button variant="outline" size="sm" onClick={fetchSnapshots}>↻ Refresh</Button>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center text-slate-500 py-8">Memuat data...</p>
            ) : snapshots.length === 0 ? (
              <p className="text-center text-slate-400 py-8">Belum ada snapshot. Buat snapshot pertama Anda!</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Kode</TableHead>
                    <TableHead>Nama</TableHead>
                    <TableHead>Tabel</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Records</TableHead>
                    <TableHead>Ukuran</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Dibuat</TableHead>
                    <TableHead>Aksi</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {snapshots.map(snap => (
                    <TableRow key={snap.id}>
                      <TableCell className="font-mono text-xs text-slate-500">{snap.snapshot_code}</TableCell>
                      <TableCell className="font-semibold max-w-[180px] truncate" title={snap.name}>{snap.name}</TableCell>
                      <TableCell>
                        <span className="bg-slate-100 text-slate-700 text-xs px-2 py-1 rounded">
                          {snap.source_table}
                        </span>
                      </TableCell>
                      <TableCell className="uppercase text-xs font-mono">{snap.file_format}</TableCell>
                      <TableCell>{snap.record_count.toLocaleString()}</TableCell>
                      <TableCell>{formatBytes(snap.file_size_bytes)}</TableCell>
                      <TableCell>
                        <span className={`text-xs font-semibold px-2 py-1 rounded-full ${STATUS_STYLES[snap.status]}`}>
                          {snap.status}
                        </span>
                      </TableCell>
                      <TableCell className="text-xs text-slate-500">
                        {new Date(snap.created_at).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {snap.status === 'COMPLETED' && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleViewData(snap)}
                                disabled={dataLoading}
                              >
                                Lihat
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDownload(snap)}
                              >
                                ↓
                              </Button>
                            </>
                          )}
                          {hasPermission('snapshot.delete') && (
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDelete(snap.id)}
                            >
                              Hapus
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* View Data Modal */}
        {viewData && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-4xl max-h-[80vh] flex flex-col">
              <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                <div>
                  <h2 className="text-lg font-bold">Data Preview</h2>
                  <p className="text-xs text-slate-500 font-mono">{viewData.code}</p>
                </div>
                <div className="flex gap-2 items-center">
                  <span className="text-sm text-slate-500">{viewData.records.length} records</span>
                  <button
                    onClick={() => setViewData(null)}
                    className="text-slate-400 hover:text-slate-700 text-2xl leading-none"
                  >
                    ×
                  </button>
                </div>
              </div>
              <div className="overflow-auto flex-1 p-4">
                {viewData.records.length === 0 ? (
                  <p className="text-slate-400 text-center py-8">Tidak ada data</p>
                ) : (
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-50 dark:bg-slate-800">
                        {Object.keys(viewData.records[0]).map(k => (
                          <th key={k} className="text-left px-3 py-2 border border-slate-200 dark:border-slate-700 font-semibold text-slate-600 dark:text-slate-300 whitespace-nowrap">
                            {k}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {viewData.records.slice(0, 100).map((row, i) => (
                        <tr key={i} className={i % 2 === 0 ? '' : 'bg-slate-50 dark:bg-slate-800/50'}>
                          {Object.values(row).map((val: any, j) => (
                            <td key={j} className="px-3 py-1.5 border border-slate-100 dark:border-slate-800 text-slate-700 dark:text-slate-300 max-w-[200px] truncate">
                              {val === null ? <span className="text-slate-300 italic">null</span> : String(val)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                {viewData.records.length > 100 && (
                  <p className="text-center text-slate-400 text-xs mt-3">
                    Menampilkan 100 dari {viewData.records.length} records
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
