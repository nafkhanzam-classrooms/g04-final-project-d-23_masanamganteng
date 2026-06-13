"""Human-readable dynamic text generator for typing challenges.

Generator ini dibuat template-based, bukan sekadar random word choice.
Tujuannya agar teks tetap terdengar manusiawi, logis, dan punya variasi besar.

Pattern system:
- Ada 22 base sentence pattern.
- Setiap base pattern dikombinasikan dengan 10 pattern group.
- Total pattern variant = 22 * 10 = 220 pola.
"""

from __future__ import annotations

import random
from app import config


PATTERN_COUNT = 220


SUBJECTS = [
    "mahasiswa informatika",
    "server kecil",
    "client baru",
    "programmer muda",
    "router kampus",
    "tim final project",
    "aplikasi jaringan",
    "pengguna aktif",
    "sistem real time",
    "browser modern",
    "admin server",
    "operator jaringan",
    "peserta lomba",
    "pemain baru",
    "penguji sistem",
    "dosen pembimbing",
    "asisten praktikum",
    "komputer lab",
    "laptop mahasiswa",
    "terminal lokal",
    "halaman web",
    "ruang pertandingan",
    "room utama",
    "koneksi websocket",
    "layanan backend",
    "mesin scoring",
    "modul validasi",
    "pengirim packet",
    "penerima pesan",
    "monitor latency",
    "game manager",
    "client internal",
    "server utama",
    "simulator beban",
    "proses cleanup",
    "sistem ranking",
    "papan skor",
    "fitur reconnect",
    "engine permainan",
    "adapter tcp",
]

ACTORS = [
    "Dapunta",
    "Rani",
    "Nafkhan",
    "Arif",
    "ITS",
    "Surabaya",
    "Jempol Turbo",
    "Type Racer",
    "Monkeytype",
    "FastAPI",
    "Python",
    "WebSocket",
    "TCP",
    "JSON",
]

VERBS = [
    "mengirim packet",
    "membuka koneksi",
    "menguji latency",
    "menulis kode",
    "menyimpan state",
    "membaca pesan",
    "menangani reconnect",
    "menghitung skor",
    "menampilkan progress",
    "membuat room",
    "menerima command",
    "memvalidasi input",
    "mengatur countdown",
    "menjalankan server",
    "mencatat log",
    "menghapus session",
    "menyusun ranking",
    "mengunci textbox",
    "memulai lomba",
    "mengirim update",
    "membaca payload",
    "menolak packet",
    "mengukur performa",
    "menjaga sinkronisasi",
    "mengelola player",
    "menutup koneksi",
    "membuka halaman",
    "menghubungkan client",
    "menjalankan adapter",
    "mengatur room",
    "menghitung akurasi",
    "menandai timeout",
    "mengunci progress",
    "mengaktifkan input",
    "menunggu lawan",
    "meneruskan event",
    "membuat snapshot",
    "mengirim broadcast",
    "mengatur lifecycle",
    "menjalankan cleanup",
]

OBJECTS = [
    "ke server utama",
    "dengan protokol sederhana",
    "saat jaringan sibuk",
    "untuk demo final project",
    "agar permainan tetap sinkron",
    "sebelum countdown selesai",
    "melalui socket python",
    "dengan data json",
    "tanpa menunggu lama",
    "secara real time",
    "ke seluruh pemain",
    "dari browser menuju backend",
    "dengan koneksi tcp",
    "melalui websocket",
    "pada room yang sama",
    "dengan validasi sederhana",
    "untuk mencegah packet invalid",
    "ketika pemain mengetik cepat",
    "setelah player bergabung",
    "sampai pertandingan selesai",
    "dengan tampilan roket",
    "melalui adapter internal",
    "untuk menjaga ranking",
    "agar hasil tetap adil",
    "dengan batas waktu tertentu",
    "tanpa membuat server berat",
    "sebelum state berubah",
    "ketika koneksi terputus",
    "selama race berlangsung",
    "agar progress tidak kacau",
    "dengan pesan terstruktur",
    "ke game engine",
    "dari websocket layer",
    "saat room masih waiting",
    "setelah tombol mulai ditekan",
    "ketika semua player finish",
    "untuk memperbarui leaderboard",
    "dengan response cepat",
    "tanpa menyimpan database",
    "menggunakan memory sementara",
]

PLACES = [
    "di laboratorium jaringan",
    "di ruang kelas",
    "di browser pemain",
    "di server lokal",
    "di halaman room",
    "di terminal penguji",
    "di dashboard permainan",
    "di jaringan kampus",
    "di sesi praktikum",
    "di komputer utama",
    "di websocket layer",
    "di tcp core server",
    "di dalam game engine",
    "di halaman home",
    "di race progress",
    "di typing area",
    "di bagian result",
    "di room pertandingan",
    "di sistem backend",
    "di proses cleanup",
]

TIMES = [
    "pagi ini",
    "siang ini",
    "malam ini",
    "sebelum demo",
    "ketika countdown berjalan",
    "saat lomba dimulai",
    "setelah pemain masuk",
    "ketika server sibuk",
    "sebelum timeout",
    "saat koneksi stabil",
    "ketika progress berubah",
    "setelah state running",
    "saat player mengetik",
    "sebelum hasil global muncul",
    "ketika room penuh",
    "setelah halaman direfresh",
]

ADVERBS = [
    "dengan cepat",
    "secara hati hati",
    "tanpa panik",
    "dengan stabil",
    "secara konsisten",
    "dengan teliti",
    "tanpa delay besar",
    "secara bertahap",
    "dengan ringan",
    "tanpa membuat cpu berat",
    "dengan rapi",
    "secara otomatis",
    "dengan aman",
    "tanpa mengulang session",
    "secara sinkron",
    "dengan response halus",
]

REASONS = [
    "agar pemain tidak tertinggal",
    "agar ranking tetap adil",
    "agar server tidak overload",
    "agar packet mudah diparsing",
    "agar state tidak rusak",
    "agar reconnect berjalan mulus",
    "agar demo terlihat jelas",
    "agar progress tetap akurat",
    "agar typo bisa dihitung",
    "agar room tidak bocor memory",
    "agar pengalaman bermain nyaman",
    "agar hasil global tidak terkunci",
    "agar player leave tetap tercatat",
    "agar countdown tidak terlewat",
    "agar update berjalan real time",
]

CONDITIONS = [
    "jika koneksi sempat putus",
    "jika pemain menutup tab",
    "jika room belum penuh",
    "jika server menerima packet salah",
    "jika user menekan tombol mulai",
    "jika semua player selesai",
    "jika waktu lomba habis",
    "jika halaman direfresh",
    "jika progress sudah seratus persen",
    "jika nama pemain sudah dipakai",
    "jika packet terlalu besar",
    "jika input tidak sesuai target",
    "jika client mengirim data cepat",
    "jika typing area masih terkunci",
]

CONNECTORS = [
    "lalu",
    "sementara itu",
    "setelah itu",
    "kemudian",
    "di sisi lain",
    "pada ronde berikutnya",
    "beberapa saat kemudian",
    "pada waktu yang sama",
    "sebelum itu",
    "sesudahnya",
    "karena itu",
    "dengan begitu",
    "akhirnya",
    "selanjutnya",
]

QUALITIES = [
    "cepat",
    "stabil",
    "ringan",
    "responsif",
    "rapi",
    "aman",
    "jelas",
    "akurat",
    "sinkron",
    "halus",
    "terukur",
    "kuat",
    "mudah diuji",
    "nyaman",
    "konsisten",
]

NOUNS = [
    "packet",
    "socket",
    "room",
    "player",
    "session",
    "latency",
    "progress",
    "ranking",
    "countdown",
    "textbox",
    "payload",
    "event",
    "state",
    "server",
    "client",
    "browser",
    "adapter",
    "protocol",
    "score",
    "akurasi",
    "typo",
    "broadcast",
    "leaderboard",
    "connection",
    "message",
    "log",
]


def _choice(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def _maybe_actor(rng: random.Random, allow_caps: bool) -> str:
    if allow_caps and rng.random() < 0.28:
        return _choice(rng, ACTORS)
    return _choice(rng, SUBJECTS)


def _base_sentence(pattern: int, rng: random.Random, *, add_punctuation: bool, allow_caps: bool) -> str:
    subject = _maybe_actor(rng, allow_caps)
    subject2 = _maybe_actor(rng, allow_caps)
    verb = _choice(rng, VERBS)
    verb2 = _choice(rng, VERBS)
    obj = _choice(rng, OBJECTS)
    obj2 = _choice(rng, OBJECTS)
    place = _choice(rng, PLACES)
    time_part = _choice(rng, TIMES)
    adverb = _choice(rng, ADVERBS)
    reason = _choice(rng, REASONS)
    condition = _choice(rng, CONDITIONS)
    connector = _choice(rng, CONNECTORS)
    quality = _choice(rng, QUALITIES)
    noun = _choice(rng, NOUNS)

    base_patterns = [
        f"{subject} {verb} {obj}",
        f"{subject} {verb} {obj} {adverb}",
        f"{subject} {verb} {obj} {place}",
        f"{time_part} {subject} {verb} {obj}",
        f"{subject} {verb} {obj} {reason}",
        f"{condition} {subject} {verb} {obj}",
        f"{subject} {verb} {obj} {connector} {subject2} {verb2}",
        f"{subject} {verb} {obj} {connector} {subject2} {verb2} {obj2}",
        f"{subject} {verb} {obj} {place} {reason}",
        f"{time_part} {subject} {verb} {obj} {adverb}",
        f"{subject} menjaga {noun} tetap {quality}",
        f"{subject} membuat {noun} menjadi lebih {quality}",
        f"{subject} memeriksa {noun} sebelum {subject2} {verb2}",
        f"{subject} {verb} {obj} ketika {subject2} {verb2}",
        f"{subject} {verb} {obj} supaya {subject2} tetap {quality}",
        f"{subject} {verb} {obj} tanpa membuat {noun} bermasalah",
        f"{subject} memakai {noun} untuk {verb} {obj}",
        f"{subject} dan {subject2} {verb} {obj} bersama sama",
        f"{place} {subject} {verb} {obj}",
        f"{subject} {verb} {obj} selama {noun} masih {quality}",
        f"{subject} memperbaiki {noun} agar sistem tetap {quality}",
        f"{subject} {verb} {obj} sebelum {subject2} menyelesaikan ronde",
    ]

    return base_patterns[pattern % len(base_patterns)]


def _sentence(rng: random.Random, *, add_punctuation: bool, allow_caps: bool) -> str:
    pattern_index = rng.randrange(PATTERN_COUNT)
    base_pattern_count = 22
    pattern_group = pattern_index // base_pattern_count
    pattern = pattern_index % base_pattern_count

    sentence = _base_sentence(
        pattern,
        rng,
        add_punctuation=add_punctuation,
        allow_caps=allow_caps,
    )

    if add_punctuation:
        # Pattern group memberi variasi bentuk kalimat tanpa membuatnya random mentah.
        if pattern_group in {1, 4, 7} and rng.random() < 0.75:
            sentence += f", {rng.choice(CONNECTORS)} {_choice(rng, SUBJECTS)} {_choice(rng, VERBS)} {_choice(rng, OBJECTS)}"
        elif pattern_group in {2, 5, 8} and rng.random() < 0.7:
            sentence += f", {rng.choice(REASONS)}"
        elif pattern_group in {3, 6, 9} and rng.random() < 0.7:
            sentence += f", {rng.choice(CONDITIONS)}"

    if allow_caps and sentence:
        sentence = sentence[0].upper() + sentence[1:]

    if add_punctuation:
        ending = rng.choice([".", ".", ".", "!", "?"]) if rng.random() < 0.18 else "."
        sentence += ending

    return sentence


def _word_count(text: str) -> int:
    cleaned = (
        text.replace(".", " ")
        .replace(",", " ")
        .replace("!", " ")
        .replace("?", " ")
        .replace(";", " ")
        .replace(":", " ")
    )
    return len(cleaned.split())


def _trim_to_word_count(text: str, target_words: int) -> str:
    words = text.split()
    return " ".join(words[:target_words])


def _clean_easy_text(text: str) -> str:
    remove_chars = ".,!?;:"
    for char in remove_chars:
        text = text.replace(char, "")
    return " ".join(text.lower().split())


def _ensure_final_punctuation(text: str) -> str:
    text = text.strip()
    if text and text[-1] not in ".!?":
        text += "."
    return text


def generate_text(game_type: str = config.DEFAULT_GAME_TYPE, *, seed: int | None = None) -> str:
    if game_type not in config.GAME_TYPES:
        game_type = config.DEFAULT_GAME_TYPE

    rule = config.GAME_TYPES[game_type]
    rng = random.Random(seed)

    target_words = rng.randint(rule["word_min"], rule["word_max"])
    add_punctuation = bool(rule["add_punctuation"])
    all_lowercase = bool(rule["all_lowercase"])
    allow_caps = not all_lowercase

    parts: list[str] = []

    while _word_count(" ".join(parts)) < target_words:
        parts.append(
            _sentence(
                rng,
                add_punctuation=add_punctuation,
                allow_caps=allow_caps,
            )
        )

    text = _trim_to_word_count(" ".join(parts), target_words)

    if all_lowercase:
        return _clean_easy_text(text)

    if add_punctuation:
        text = _ensure_final_punctuation(text)

    return " ".join(text.split())