# 📸 Panduan Penggunaan Fitur Snapshot Data

Fitur **Snapshot Data** memungkinkan Anda mengambil *capture* data dari tabel database pada titik waktu tertentu, lalu membagikannya ke pengguna/sistem lain tanpa mengekspos database production secara langsung.

---

## 🔐 Hak Akses

| Role | Buat | Lihat Daftar | Preview Data | Download | Hapus |
|---|:---:|:---:|:---:|:---:|:---:|
| **admin** | ✅ | ✅ (semua) | ✅ | ✅ | ✅ |
| **supervisor** | ✅ | ✅ (milik sendiri + publik) | ✅ | ✅ | ❌ |
| **worker** | ❌ | ✅ (publik saja) | ✅ | ✅ | ❌ |

---

## 🖥️ Cara Pakai via UI (Frontend)

### 1. Akses Halaman Snapshot

Masuk ke aplikasi → klik **"Snapshots"** di sidebar kiri.  
Menu ini hanya muncul jika akun Anda memiliki permission `snapshot.view`.

---

### 2. Membuat Snapshot Baru

1. Klik tombol **"+ Buat Snapshot"** (pojok kanan atas)
2. Isi form:

   | Field | Keterangan | Contoh |
   |---|---|---|
   | **Nama Snapshot** | Nama deskriptif (min. 5 karakter) | `Snapshot Users Q1 2026` |
   | **Deskripsi** | Keterangan tambahan (opsional) | `Data pengguna aktif per Maret 2026` |
   | **Source Table** | Nama tabel di database | `users` |
   | **Custom Query** | SQL kustom — jika kosong, pakai `SELECT * FROM <tabel>` | `SELECT id, username FROM users WHERE is_active = 1` |
   | **Format File** | `json` atau `csv` | `json` |
   | **Akses Publik** | `Private` (hanya pemilik/role tertentu) atau `Public` (semua user) | `Private` |
   | **Allowed Roles** | Role yang boleh akses, pisahkan koma | `admin,supervisor` |

3. Klik **"Generate Snapshot"**

> ⚡ **Penting:** Snapshot **langsung tersimpan dengan status `PENDING`** dan API segera merespons. Proses generate file berjalan di **background task** — tidak perlu menunggu.

---

### 3. Memantau Status Snapshot

Di tabel utama, kolom **Status** menunjukkan kondisi snapshot:

| Status | Artinya |
|---|---|
| 🟡 `PENDING` | Sedang diproses di background |
| 🟢 `COMPLETED` | Selesai, siap diakses |
| 🔴 `FAILED` | Gagal (cek query atau nama tabel) |
| ⚫ `EXPIRED` | Kadaluarsa (otomatis setelah 30 hari) |

Klik tombol **"↻ Refresh"** untuk memperbarui daftar.

---

### 4. Melihat Data Snapshot

Jika status `COMPLETED`, klik tombol **"Lihat"** pada baris snapshot.

- Akan muncul **modal preview** dengan tabel data scrollable
- Menampilkan maksimal **100 baris pertama**
- Kolom `null` ditampilkan dengan tulisan miring abu-abu

---

### 5. Mendownload File Snapshot

Klik tombol **"↓"** pada baris snapshot yang sudah `COMPLETED`.

- File langsung terunduh ke komputer Anda
- Format file sesuai pilihan saat membuat (`users_snapshot.json` atau `users_snapshot.csv`)

---

### 6. Menghapus Snapshot

Klik tombol **"Hapus"** (merah) → konfirmasi → snapshot dan filenya dihapus permanen.

> Hanya **admin** atau **pemilik snapshot** yang bisa menghapus.

---

## 🔌 Cara Pakai via API (untuk Integrasi Sistem)

Base URL: `http://localhost:8000/api`  
Semua endpoint membutuhkan header: `Authorization: Bearer <token>`

### Buat Snapshot

```http
POST /api/snapshots
Content-Type: application/json

{
  "name": "Snapshot Users Maret 2026",
  "source_table": "users",
  "source_query": "SELECT id, username, email FROM users WHERE is_active = 1",
  "file_format": "json",
  "is_public": "N",
  "allowed_roles": "supervisor"
}
```

**Response 201:**
```json
{
  "id": 1,
  "snapshot_code": "SNAP-USERS-20260306082500",
  "status": "PENDING",
  ...
}
```

---

### Cek Status Snapshot

```http
GET /api/snapshots/1
```

Poll endpoint ini sampai `"status": "COMPLETED"`.

---

### Ambil Data sebagai JSON

```http
GET /api/snapshots/1/data?format=json
```

**Response:**
```json
{
  "success": true,
  "data": {
    "snapshot_code": "SNAP-USERS-20260306082500",
    "record_count": 42,
    "data": [
      { "id": 1, "username": "admin", "email": "admin@example.com" },
      ...
    ]
  }
}
```

---

### Download File

```http
GET /api/snapshots/1/data?format=download
```

Response berupa binary file (JSON/CSV) — simpan dengan `Content-Disposition` header.

---

### List Semua Snapshot

```http
GET /api/snapshots?status=COMPLETED&source_table=users&page=1&page_size=20
```

---

### Hapus Snapshot

```http
DELETE /api/snapshots/1
```

---

## ⏰ Expiry & Cleanup Otomatis

- Setiap snapshot otomatis **kadaluarsa dalam 30 hari** setelah dibuat
- Cleanup task akan mengubah status menjadi `EXPIRED` dan **menghapus file** dari server
- Untuk menjalankan cleanup secara manual (dev/testing):

```python
from app.tasks.snapshot_cleanup import cleanup_expired_snapshots
cleanup_expired_snapshots()
```

---

## ❗ Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Status tetap `PENDING` | Background task gagal | Cek log server di terminal uvicorn |
| Status berubah ke `FAILED` | Query SQL salah / tabel tidak ada | Cek nama tabel dan sintaks query |
| Tombol "Lihat"/"↓" tidak muncul | Status bukan `COMPLETED` | Tunggu atau refresh halaman |
| 403 Forbidden | Tidak punya akses ke snapshot | Minta admin ubah `allowed_roles` atau `is_public` |
| 410 Gone | Snapshot sudah kadaluarsa | Buat snapshot baru |
