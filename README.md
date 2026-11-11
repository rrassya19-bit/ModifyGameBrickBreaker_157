# Modify Game Brick Breaker

Block Breaker adalah game arkade berbasis Pygame. Pemain menggerakkan papan untuk memantulkan bola dan menghancurkan balok. Proyek ini dikembangkan bertahap dari versi awal hingga memiliki level, power-up, efek visual, suara, dan penyimpanan skor tertinggi.

**Identitas**

- Nama: Ahmad Rassya Maulana
- NIM: 20250140157

> Catatan: entry point yang tersedia di repository bernama `app.py`, bukan `main.py`.

## Demo

> Belum tersedia. Folder `assets/` belum berisi `demo.gif`.

## Sebelum vs Sesudah

| Sebelum | Sesudah |
|---|---|
| Gambar `assets/before.png` belum tersedia di repository. | Gambar `assets/after_game.png` belum tersedia di repository. |

Galeri tambahan belum dapat ditampilkan karena file gambarnya belum ada:

- **Layar awal:** `assets/after_start.png` belum tersedia.
- **Power-up:** `assets/after_powerup.png` belum tersedia.
- **Game over:** `assets/after_gameover.png` belum tersedia.

## Ringkasan Fitur Utama

- Pantulkan bola dengan papan dan hancurkan balok untuk mendapat skor.
- Mainkan level dengan susunan balok penuh, selang-seling, dan piramida.
- Gunakan power-up papan besar, bola lambat, dan tambahan nyawa.
- Lihat skor, level, sisa nyawa, dan high score pada HUD.
- Nikmati latar dinamis, glow, trail bola, partikel, transisi, serta animasi.
- Simpan high score lokal dan kendalikan suara serta kualitas efek.

## Cara Menjalankan

Persyaratan: Python 3 dan Pygame. Pasang Pygame, lalu jalankan file entry point yang ada:

```bash
pip install pygame
python app.py
```

Perintah `python main.py` tidak digunakan karena file `main.py` tidak ada di repository ini.

### Kontrol Keyboard

| Tombol | Fungsi |
|---|---|
| ← / → | Menggerakkan papan ke kiri dan kanan. |
| SPACE | Memulai permainan, memulai ulang dari layar Game Over, atau melanjutkan ke level berikutnya. |
| P | Menjeda atau melanjutkan permainan. |
| M | Mengaktifkan atau menonaktifkan suara. |
| F | Mengganti kualitas efek High/Low. |
| ESC | Keluar dari layar Game Over atau Level Complete. |

## Daftar Perubahan Lengkap

### Logika / Bug Fix

| Fitur | Bagian kode (class/fungsi) | Fungsi dan cara kerjanya |
|---|---|---|
| Pemeriksaan tabrakan | `collisionChecker()` | Memeriksa perpotongan rectangle bola dengan papan, balok, atau power-up. |
| Pantulan berdasarkan sisi balok | `resolveBlockCollision()`, `Ball.hitSide()` | Membandingkan overlap dari empat sisi balok, lalu memantulkan bola pada sumbu yang sesuai. |
| Sudut pantulan papan | `strikerBounce()` | Mengubah arah horizontal berdasarkan titik bola mengenai papan; bagian tengah mengarah lebih tegak. |
| Rectangle bola aktual | `Ball.getRect()` | Membuat batas tabrakan dari posisi dan radius bola saat ini, bukan rectangle gambar awal. |
| Posisi bola saat reset | `Ball.reset()` | Menempatkan bola tepat di atas tengah papan dan meluncurkannya ke atas. |
| Gerak papan mulus | `main()`, `Striker.update()` | Membaca status tombol kiri dan kanan setiap frame sehingga input dapat digabung. |
| Penghapusan balok aman | `main()` | Mengiterasi salinan daftar balok dan menghentikan pemeriksaan setelah satu tabrakan per frame. |

### UI / HUD

| Fitur | Bagian kode (class/fungsi) | Fungsi dan cara kerjanya |
|---|---|---|
| HUD atas | `main()` | Menampilkan Score, Level, dan High Score dalam satu baris dengan garis pemisah. |
| Ikon nyawa | `getHeartSurface()`, `drawHeart()` | Membuat hati vektor anti-aliased, lalu menyimpan hasilnya di cache. |
| Status power-up | `main()` | Menampilkan sisa durasi Paddle dan Slow ketika efek aktif. |
| Menu awal | `startScreen()`, `drawMenuTitle()` | Menampilkan judul beranimasi, instruksi mulai, high score, bola demo, dan balok dekoratif. |
| Panel keadaan permainan | `drawOverlayPanel()`, `gameOver()`, `winScreen()`, `main()` | Menampilkan panel pause, game over, atau ringkasan penyelesaian level. |

### Gameplay (Level, Balok, Power-up)

| Fitur | Bagian kode (class/fungsi) | Fungsi dan cara kerjanya |
|---|---|---|
| Pola dan progres level | `populateBlocks()`, `main()` | Membuat grid simetris; pola penuh, selang-seling, dan piramida bergantian per level. |
| Ketahanan balok | `Block` | Balok teal memerlukan satu pukulan, violet dua pukulan, dan rose tiga pukulan. |
| Skor per balok | `Block.getScore()` | Memberi 5, 10, atau 15 poin berdasarkan jenis balok. |
| Papan besar | `PowerUp`, `Striker.setWidth()` | Memperlebar papan sementara saat power-up Paddle diambil. |
| Bola lambat | `PowerUp`, `Ball.applySlow()`, `Ball.removeSlow()` | Mengurangi kecepatan bola sementara dan mengembalikannya setelah durasi selesai. |
| Tambahan nyawa | `PowerUp`, `main()` | Menambah nyawa hingga batas `MAX_LIVES`. |
| Kesempatan power-up | `main()` | Saat balok hancur, game menggunakan `POWERUP_CHANCE` untuk menentukan apakah power-up jatuh. |

### Visual (Balok, Papan, Bola, Background)

| Fitur | Bagian kode (class/fungsi) | Fungsi dan cara kerjanya |
|---|---|---|
| Permukaan bersudut halus | `makeRoundedSurface()` | Membuat gradien bersudut bulat dengan supersampling dan menyimpan hasilnya di cache. |
| Balok bergradasi dan retak | `blockColors()`, `getBlockSurface()`, `getCrackSurface()`, `Block.display()` | Membedakan balok menurut health, memberi highlight, border, bayangan, dan retakan. |
| Papan kaca | `getPaddleSurface()`, `getPaddleGlow()`, `Striker.display()` | Menggambar papan semi-transparan dengan border, sorotan, dan glow. |
| Bola, glow, dan trail | `getBallSurface()`, `createGlowSurface()`, `precomputeTrailCircles()`, `Ball.display()` | Menampilkan bola halus, glow berdenyut, serta jejak lingkaran yang mengecil. |
| Power-up berikon | `getPowerUpSurface()`, `getPowerUpGlow()`, `PowerUp.display()` | Menggambar kapsul dengan ikon panah, jam, atau hati serta glow sesuai jenis. |
| Background dinamis | `createGradientSurface()`, `getLevelBackground()`, `drawBackground()`, `updateStars()`, `drawStars()` | Menggambar gradien, bintang tiga lapis yang bergerak dan berkedip, vignette, serta aksen warna per level. |
| Bloom | `drawBloom()` | Menghaluskan glow bola, papan, dan power-up melalui buffer resolusi rendah yang dipakai ulang. |

### Animasi dan Efek

| Fitur | Bagian kode (class/fungsi) | Fungsi dan cara kerjanya |
|---|---|---|
| Easing dan intro level | `easeOutCubic()`, `easeOutBack()`, `Block.updateAnimation()`, `Block.display()` | Memunculkan balok berurutan dengan jeda per baris; bola menunggu intro selesai. |
| Reaksi saat kena pukul | `Block.hit()`, `Block.display()` | Memberi kilatan singkat, goyangan skala, dan retakan pada balok yang masih bertahan. |
| Shockwave | `precomputeShockwaves()`, `Shockwave` | Menggambar cincin yang membesar dan memudar ketika balok hancur. |
| Squash papan | `Striker.display()`, `Striker.update()` | Mengubah lebar dan tinggi papan sementara saat bola memantul. |
| Teks skor dan combo | `FloatingText`, `ComboText`, `main()` | Menghitung skor tampilan secara bertahap, melayangkan poin, dan menampilkan combo beruntun. |
| Partikel dan screen shake | `Particle`, `main()` | Menyebarkan partikel saat balok pecah dan mengguncang layar dengan peluruhan saat nyawa hilang. |
| Fade dan panel | `fadeOutCurrent()`, `drawFadeOverlay()`, `drawOverlayPanel()` | Menghaluskan perpindahan keadaan dan kemunculan panel. |

### Suara dan Data

| Fitur | Bagian kode (class/fungsi) | Fungsi dan cara kerjanya |
|---|---|---|
| Efek suara sintetis | `createToneSound()`, `createSoundEffects()`, `playSound()` | Membuat nada dengan gelombang sinus untuk pantulan, balok, power-up, nyawa, dan game over. |
| Mute | `toggleMute()` | Mengaktifkan atau mematikan pemutaran suara dengan tombol M. |
| High score lokal | `loadHighScore()`, `saveHighScore()` | Membaca dan menyimpan skor tertinggi pada `highscore.txt` di folder proyek. |
| Rekor baru | `gameOver()`, `winScreen()` | Menampilkan badge `NEW HIGH SCORE` jika skor melampaui rekor sebelumnya. |

### Kualitas Kode

| Fitur | Bagian kode (class/fungsi) | Fungsi dan cara kerjanya |
|---|---|---|
| Desain Midnight Elegant | Konstanta palet dan tata letak | Mengumpulkan warna, ukuran, durasi, dan parameter visual sebagai konstanta. |
| Cache font dan teks | `loadFont()`, `renderTextCached()`, `renderTextAlphaCached()` | Menggunakan cache untuk font sistem dan surface teks yang telah dirender. |
| Cache permukaan visual | `getBlockSurface()`, `getPaddleSurface()`, `getBallSurface()`, dan fungsi `get*Surface()` lain | Menyimpan surface hasil render agar dapat dipakai kembali. |
| Persiapan cache animasi | `prewarmAnimationCaches()`, `precomputeShockwaves()`, `precomputeTrailCircles()` | Menyiapkan variasi surface visual sebelum gameplay. |
| Pilihan kualitas | `main()`, `drawStars()`, `drawBloom()` | Tombol F beralih antara High dan Low; Low mematikan bloom dan mengurangi bintang serta partikel yang digambar. |

## Bug Game Awal yang Diperbaiki

| Masalah di game awal | Penyebab | Solusi |
|---|---|---|
| Pantulan pada sisi balok tidak mengikuti sisi yang terkena. | Semua tabrakan balok memanggil `Ball.hit()` yang hanya membalik arah Y. | `resolveBlockCollision()` menentukan overlap minimum dan membalik sumbu X atau Y yang sesuai. |
| Bola selalu memantul dengan arah yang sama dari papan. | Pantulan papan hanya membalik arah Y. | `strikerBounce()` mengatur arah berdasarkan posisi relatif bola pada lebar papan. |
| Bola kembali dari posisi yang tidak wajar setelah nyawa hilang. | `Ball.reset()` menempatkan bola di koordinat kiri bawah (0, HEIGHT). | Reset memposisikan bola tepat di atas tengah papan dan mengarahkan bola ke atas. |
| Batas tabrakan bola tidak mengikuti posisi terkininya. | `Ball.getRect()` sebelumnya mengembalikan rectangle hasil gambar awal. | `Ball.getRect()` menghitung rectangle dari koordinat bola saat ini. |
| Input gerak dapat terasa kurang mulus dan sulit menggabungkan dua arah. | Arah gerak hanya berubah melalui event KEYDOWN/KEYUP. | `main()` membaca `pygame.key.get_pressed()` setiap frame dan menghitung arah kiri/kanan. |
| Menghapus balok saat iterasi dapat melewati elemen berikutnya. | Elemen dihapus dari list yang sedang diiterasi. | Loop memakai salinan list, menghapus dari list asli, dan berhenti setelah satu tabrakan. |

## Perbandingan Sebelum vs Sesudah

Perbandingan ini memakai implementasi awal pada commit `8802652` dan kode saat ini.

| Aspek | Awal | Sekarang |
|---|---|---|
| Class Python di tingkat modul | 3: `Striker`, `Block`, `Ball` | 8: ditambah `PowerUp`, `Particle`, `FloatingText`, `Shockwave`, `ComboText` |
| Tombol keyboard yang dipakai | 3 jenis: ←, →, SPACE | 7 jenis: ←, →, SPACE, P, M, F, ESC |
| Level | Belum ada progres level dan pola balok | Level berulang dengan tiga pola balok bergantian |
| Jenis balok | Balok dasar | Tiga ketahanan: satu, dua, atau tiga pukulan |
| Power-up | Belum ada | Tiga: papan besar, bola lambat, tambahan nyawa |
| Antarmuka | Tampilan permainan dasar | Menu, HUD, pause, game over, level complete |
| Visual | Bentuk dasar | Gradien, glow, trail, starfield, vignette, bloom, dan panel kaca |
| Animasi | Gerak permainan dasar | Intro level, hit flash, shockwave, partikel, combo, transisi, dan shake |
| Audio dan penyimpanan skor | Belum ditambahkan pada implementasi awal | Efek suara sintetis, mute, dan high score lokal |

## Struktur Proyek

```text
ModifyGameBrickBreaker_157/
├── .gitignore
├── README.md
├── app.py
├── assets/             # Saat ini kosong; belum ada gambar demo/screenshot
└── highscore.txt       # Dibuat atau diperbarui saat game menyimpan skor
```

## Riwayat Commit

| Hash | Pesan commit | Ringkasan |
|---|---|---|
| `baaf971` | `Frist Commit` | Membuat commit awal repository. |
| `8802652` | `Implementasi awal permainan Block Breaker dengan kelas Striker, Block, dan Ball` | Membuat versi awal permainan dengan tiga class inti. |
| `a0f2bc7` | `Tambahkan .gitignore untuk mengecualikan file __pycache__ dan .pyc` | Mengabaikan cache Python dan file bytecode. |
| `aeb01cb` | `Tambahkan file README untuk dokumentasi proyek` | Menambahkan README kosong sebagai awal dokumentasi. |
| `821fcbe` | `perbaikan: meningkatkan logika tabrakan, sudut pantulan pada papan pemukul (paddle), pengaturan ulang posisi bola, serta membuat kontrol lebih mulus` | Memperbaiki pantulan sisi balok, arah pantulan papan, reset bola, rectangle bola, dan input gerak. |
| `656457e` | `fitur: perancangan ulang HUD dengan ikon nyawa dan indikator level` | Memperbarui HUD dengan indikator nyawa dan level. |
| `0b6893e` | `fitur: menambahkan layar awal, jeda, permainan berakhir (game over), dan penyelesaian level` | Menambahkan layar menu, pause, game over, dan level selesai. |
| `a7dacf6` | `fitur: menambahkan sistem level, pola blok, dan blok merah yang lebih tangguh` | Menambahkan progres level, variasi pola, serta ketahanan balok merah. |
| `22fabb9` | `fitur: menambahkan sistem power-up (pemukul besar, bola lambat, nyawa tambahan)` | Menambahkan tiga jenis power-up. |
| `d485a89` | `gaya: rancang ulang visual dengan latar belakang gradien, blok-blok bersudut tumpul, jejak bola, dan efek cahaya (glow)` | Memperbarui bentuk dan efek visual dasar. |
| `a2ede28` | `fitur: menambahkan efek partikel, guncangan layar, dan teks skor yang melayang` | Menambahkan partikel, screen shake, dan teks poin melayang. |
| `898e735` | `fitur: menambahkan efek suara dengan opsi senyap (mute) serta skor tertinggi yang tersimpan` | Menambahkan suara, mute, dan high score lokal. |
| `c12ebd1` | `style: introduce design system, centered layout, top HUD bar, and 60 FPS` | Menambahkan desain Midnight Elegant, tata letak tengah, HUD atas, dan 60 FPS. |
| `9ef56a8` | `style: smooth supersampled rendering for blocks, paddle, ball trail, and power-ups` | Menghaluskan render objek dan ikon dengan supersampling serta cache. |
| `1aeed33` | `style: add parallax starfield, vignette, and per-level background tint` | Menambahkan bintang parallax, vignette, dan aksen background per level. |
| `6d3f788` | `feat: add eased animations (level intro wave, hit flash, shockwave, paddle squash, score count-up)` | Menambahkan animasi easing untuk intro, tabrakan, papan, dan skor. |
| `a0657fa` | `style: polished menu, fade transitions, and glass overlay panels` | Memoles menu, transisi, dan panel overlay. |
| `86540de` | `perf: add bloom effect, quality toggle, and cache audit` | Menambahkan bloom, pilihan kualitas, dan optimasi cache visual. |

## Pemanfaatan AI

opencode dan Codex digunakan sebagai alat bantu coding secara bertahap. Perubahan dicatat dalam commit agar dapat ditinjau per tahap; hasilnya diuji dan dipahami kembali oleh pengembang.

## Catatan Pengembangan Lanjutan

- Tambahkan screenshot dan GIF gameplay ke `assets/` agar dokumentasi menampilkan hasil visual secara langsung.
- Tambahkan pilihan tingkat kesulitan dengan parameter kecepatan dan ketahanan balok.
- Tambahkan layar pengaturan untuk mengubah volume dan kualitas efek.

Terima kasih telah melihat proyek ini. Semoga dokumentasi dan riwayat perubahan membantu memahami proses pengembangan Block Breaker.
