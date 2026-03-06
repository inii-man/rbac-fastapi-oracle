# 📸 Panduan Penggunaan Fitur Snapshot Data

Fitur **Snapshot Data** memungkinkan Anda mengambil *capture* data dari tabel database pada titik waktu tertentu, lalu membagikannya ke pengguna/sistem lain tanpa mengekspos database production secara langsung.

---

## 🔐 Hak Akses

| Role | Buat | Lihat Daftar | Preview Data | Download | Hapus |
|---|:---:|:---:|:---:|:---:|:---:|
| **admin** | ✅ | ✅ (semua) | ✅ | ✅ | ✅ |
| **supervisor** | ✅ | ✅ (milik sendiri + publik) | ✅ | ✅ | ❌ |
| **worker** | ❌ | ✅ (publik saja) | ✅ | ✅ | ❌ |

> Permission yang dibutuhkan: `snapshot.view` (lihat), `snapshot.create` (buat), `snapshot.delete` (hapus)

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
   | **Akses Publik** | `N` (hanya pemilik/role tertentu) atau `Y` (semua user) | `N` |
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
| 🔴 `FAILED` | Gagal (cek query atau nama tabel, lihat log server) |
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
Authorization: Bearer <token>

{
  "name": "Snapshot Users Maret 2026",
  "source_table": "users",
  "source_query": "SELECT id, username, email FROM users WHERE is_active = 1",
  "file_format": "json",
  "is_public": "N",
  "allowed_roles": "supervisor"
}
```

**Validasi field:**
- `name` — wajib, min. 5 karakter, maks. 200 karakter
- `source_table` — wajib, maks. 100 karakter
- `source_query` — opsional; jika kosong akan pakai `SELECT * FROM <source_table>`
- `file_format` — harus `"json"` atau `"csv"` (default: `"json"`)
- `is_public` — harus `"Y"` atau `"N"` (default: `"N"`)
- `allowed_roles` — opsional, comma-separated (contoh: `"admin,supervisor"`)

**Response 201:**
```json
{
  "id": 1,
  "snapshot_code": "SNAP-USERS-20260306082500",
  "name": "Snapshot Users Maret 2026",
  "description": null,
  "source_table": "users",
  "record_count": 0,
  "file_size_bytes": 0,
  "file_format": "json",
  "status": "PENDING",
  "created_at": "2026-03-06T08:25:00",
  "completed_at": null,
  "expires_at": "2026-04-05T08:25:00",
  "is_public": "N",
  "created_by": "admin"
}
```

---

### Cek Status Snapshot

```http
GET /api/snapshots/1
Authorization: Bearer <token>
```

Poll endpoint ini sampai `"status": "COMPLETED"`. Respons menggunakan format yang sama dengan response POST di atas.

---

### List Semua Snapshot

```http
GET /api/snapshots?snapshot_status=COMPLETED&source_table=users&page=1&page_size=20
Authorization: Bearer <token>
```

**Query Parameters (semua opsional):**
| Parameter | Tipe | Keterangan |
|---|---|---|
| `snapshot_status` | string | Filter berdasarkan status (`PENDING`, `COMPLETED`, `FAILED`, `EXPIRED`) |
| `source_table` | string | Filter berdasarkan nama tabel |
| `page` | int | Halaman (default: 1) |
| `page_size` | int | Jumlah per halaman (default: 20) |

> User non-admin hanya melihat snapshot milik sendiri, publik, atau yang sesuai role-nya.

---

### Ambil Data sebagai JSON

```http
GET /api/snapshots/1/data?format=json
Authorization: Bearer <token>
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
Authorization: Bearer <token>
```

Response berupa binary file (JSON/CSV) — simpan dengan nama dari `Content-Disposition` header.

---

### Hapus Snapshot

```http
DELETE /api/snapshots/1
Authorization: Bearer <token>
```

**Response 200:**
```json
{ "success": true, "message": "Snapshot 1 deleted" }
```

---

## ⏰ Expiry & Cleanup Otomatis

- Setiap snapshot otomatis **kadaluarsa dalam 30 hari** setelah dibuat
- Cleanup task akan mengubah status menjadi `EXPIRED` dan **menghapus file** dari server
- File disimpan di direktori `./data/snapshots/` (relatif terhadap root backend)
- Untuk menjalankan cleanup secara manual (dev/testing):

```python
from app.tasks.snapshot_cleanup import cleanup_expired_snapshots
cleanup_expired_snapshots()
```

---

## 🗄️ Catatan Oracle Database

Model `DataSnapshot` didesain kompatibel dengan Oracle:

| Aspek | Implementasi |
|---|---|
| **Auto-increment ID** | Menggunakan `Sequence("data_snapshots_id_seq")` eksplisit |
| **Status kolom** | `VARCHAR(20)` dengan `CheckConstraint` (bukan ENUM native) |
| **Indeks PK** | Tidak menggunakan `index=True` — Oracle otomatis buat indeks untuk PK |
| **`is_public`** | Disimpan sebagai `VARCHAR(10)` dengan nilai `"Y"` atau `"N"` |
| **Datetime** | Kolom `DateTime(timezone=True)` — perbandingan menggunakan naive UTC datetime |

---

## ❗ Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Status tetap `PENDING` | Background task gagal | Cek log server di terminal uvicorn |
| Status berubah ke `FAILED` | Query SQL salah / tabel tidak ada | Cek nama tabel dan sintaks query; error detail ada di kolom `description` |
| Tombol "Lihat"/"↓" tidak muncul | Status bukan `COMPLETED` | Tunggu atau refresh halaman |
| 400 Bad Request | Snapshot belum `COMPLETED` | Tunggu proses background selesai |
| 403 Forbidden | Tidak punya akses ke snapshot | Minta admin ubah `allowed_roles` atau `is_public` |
| 410 Gone | Snapshot sudah kadaluarsa (>30 hari) | Buat snapshot baru |
| 500 Internal Server Error | File tidak ada di server | File mungkin terhapus manual; buat ulang snapshot |
| ORA-01400 | Kolom NOT NULL tanpa value | Pastikan semua field wajib terisi saat membuat snapshot |
| ORA-01408 | Index duplikat di Oracle | Jangan gunakan `index=True` pada kolom dengan `unique=True` atau PK |
