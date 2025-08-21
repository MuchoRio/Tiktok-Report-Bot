# 🤖 Tiktok-Report-Bot

Tiktok-Report-Bot adalah sebuah bot berbasis Python yang dirancang untuk mengotomatisasi proses pelaporan (report) postingan di TikTok. Bot ini menggunakan **Selenium** untuk mengendalikan browser, memungkinkan MuchoRio untuk melakukan pelaporan secara massal dengan berbagai konfigurasi, termasuk menggunakan User Agent yang berbeda untuk setiap laporan.

-----

## ✨ Fitur Utama

  - **Antarmuka Pengguna Grafis (GUI)**: Menggunakan `ttkbootstrap` untuk GUI yang intuitif dan modern, memudahkan konfigurasi tanpa perlu mengedit kode.
  - **Dukungan Banyak URL**: Mampu memproses daftar URL postingan TikTok dari sebuah file teks atau input langsung.
  - **Konfigurasi Fleksibel**:
      - **Mode Pelaporan**: Pilih untuk melapor berdasarkan jumlah User Agent yang tersedia, jumlah kustom, atau menggunakan User Agent acak.
      - **Opsi WebDriver**: Kontrol berbagai opsi Chrome WebDriver seperti `headless` mode, `no-sandbox`, dan lainnya.
      - **Jeda Waktu (Sleep)**: Atur jeda acak antar laporan untuk meniru perilaku manusia dan menghindari deteksi.
  - **Manajemen Kesalahan**:
      - Secara otomatis menyimpan URL yang gagal diproses ke dalam file `failed_urls.txt`.
      - Mengambil *screenshot* saat terjadi kesalahan untuk membantu proses *debugging*.
  - **Log Real-time**: Menyediakan log terperinci di dalam GUI untuk memantau status bot secara langsung.
  - **Graceful Shutdown**: Tombol "Hentikan" dan penanganan `CTRL+C` yang aman untuk menghentikan bot kapan saja.

-----

## 🚀 Persyaratan dan Instalasi

Pastikan MuchoRio memiliki Python 3.x terinstal di sistem.

1.  **Clone repository ini:**

    ```bash
    git clone https://github.com/MuchoRio/Tiktok-Report-Bot.git
    cd Tiktok-Report-Bot
    ```

2.  **Instal pustaka yang diperlukan:**

    ```bash
    pip install -r requirements.txt
    ```

    *(Note: Buat file `requirements.txt` dari `report.py` dengan mencatat semua library yang digunakan: `ttkbootstrap`, `selenium`, `webdriver-manager`, `fake-useragent`)*.

3.  **Siapkan file User Agent:**
    Buat file teks bernama `useragent.txt` di direktori yang sama. Isi file ini dengan daftar User Agent, satu per baris. Contoh:

    ```
    Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36
    Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36
    ...
    ```

    *(Jika MuchoRio menggunakan mode "User Agent Acak", file ini tidak diperlukan.)*

-----

## ⚙️ Cara Menggunakan

1.  Jalankan skrip `report.py`:

    ```bash
    python report.py
    ```

2.  **Isi URL Postingan**: Masukkan satu atau beberapa URL postingan TikTok di kotak teks yang tersedia, satu URL per baris.

3.  **Konfigurasi Pengaturan Bot**:

      - **Lokasi User Agent**: Tentukan jalur ke file `useragent.txt`.
      - **Mode Report**: Pilih metode pelaporan yang Anda inginkan.
      - **Pengaturan Waktu**: Sesuaikan `Wait Timeout`, `Sleep`, dan `Jeda Manual Captcha`.
      - **Pengaturan WebDriver**: Centang opsi yang diinginkan untuk mengontrol perilaku browser.

4.  **Mulai Pelaporan**: Klik tombol **Mulai** untuk menjalankan bot.

5.  **Hentikan Pelaporan**: Klik tombol **Hentikan** kapan saja untuk menghentikan proses.

-----

## ⚠️ Penafian

Penggunaan bot ini harus mematuhi **Ketentuan Layanan TikTok**. Penggunaan yang tidak bertanggung jawab dapat mengakibatkan pemblokiran akun. Kami tidak bertanggung jawab atas tindakan apa pun. Gunakan dengan bijak\!
