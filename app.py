import array
import math
import os
import pygame
import random

# Mixer mono dipersiapkan sebelum pygame.init agar buffer nada sederhana
# terbaca dengan benar
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

# Status audio: jika mixer gagal, permainan tetap berjalan tanpa suara
audioAvailable = pygame.mixer.get_init() is not None
muted = False
soundEffects = {}

# Dimensions of the screen
WIDTH, HEIGHT = 600, 500

# Palet "Midnight Elegant"
NAVY = (11, 16, 32)
INDIGO = (26, 27, 58)
TEAL = (79, 179, 191)
VIOLET = (139, 127, 214)
ROSE_GOLD = (224, 160, 139)
GOLD = (242, 200, 121)
TEXT_SOFT = (232, 236, 245)
TEXT_DIM = (138, 146, 168)

# Warna lama dipertahankan sebagai alias agar logika tetap sama
BLACK = (0, 0, 0)
WHITE = TEXT_SOFT
GREEN = TEAL
RED = ROSE_GOLD
BLUE = TEAL
YELLOW = GOLD
ORANGE = ROSE_GOLD

# Tema warna tampilan
DARK_BLUE = NAVY
DARK_PURPLE = INDIGO
BLOCK_DARK = (20, 22, 44)
BLOCK_BORDER = (48, 52, 82)
BLOCK_GREEN_TOP = (120, 215, 214)
BLOCK_GREEN_BOTTOM = (43, 130, 142)
BLOCK_WHITE_TOP = (176, 164, 236)
BLOCK_WHITE_BOTTOM = (104, 92, 170)
BLOCK_RED_TOP = (243, 190, 168)
BLOCK_RED_BOTTOM = (176, 108, 92)
BLOCK_TEAL_TOP = BLOCK_GREEN_TOP
BLOCK_TEAL_BOTTOM = BLOCK_GREEN_BOTTOM
BLOCK_VIOLET_TOP = BLOCK_WHITE_TOP
BLOCK_VIOLET_BOTTOM = BLOCK_WHITE_BOTTOM
BLOCK_ROSE_TOP = BLOCK_RED_TOP
BLOCK_ROSE_BOTTOM = BLOCK_RED_BOTTOM
STRIKER_COLOR = (74, 120, 160)
STRIKER_HIGHLIGHT = (190, 225, 235)
STRIKER_BORDER = (120, 200, 215)
BALL_GLOW = (120, 205, 215)
BALL_TRAIL = (150, 200, 220)
BALL_COLOR = (240, 246, 252)

# Tata letak "Midnight Elegant"
HUD_TOP_H = 54
HUD_MARGIN = 32
GRID_COLUMNS = 10
GRID_ROWS = 8
GRID_TOP = 80
BLOCK_W, BLOCK_H = 40, 15
BLOCK_GAP_X, BLOCK_GAP_Y = 15, 14
STRIKER_Y = HEIGHT - 50
HEART_SIZE = 16
HEART_COLOR = ROSE_GOLD

# Cache font dan teks agar tidak ada Surface baru tiap frame
fontCache = {}
textCache = {}

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Block Breaker")


# Memuat font sistem dengan fallback dan cache
def loadFont(size, bold=False):
    key = (size, bold)
    if key not in fontCache:
        fontCache[key] = pygame.font.SysFont(
            ["Montserrat", "Poppins", "Helvetica Neue",
             "Segoe UI", "Arial"], size, bold=bold)
    return fontCache[key]


# Teks yang sudah dirender dan di-cache
def renderTextCached(text, size, color, bold=False):
    key = (text, size, color, bold, 255)
    if key not in textCache:
        textCache[key] = loadFont(size, bold).render(
            text, True, color).convert_alpha()
    return textCache[key]


# Teks dengan alpha tertentu (untuk animasi fade)
def renderTextAlphaCached(text, size, color, alpha, bold=False):
    alpha = max(0, min(255, int(alpha)))
    key = (text, size, color, bold, alpha)
    if key not in textCache:
        surface = loadFont(size, bold).render(
            text, True, color).convert_alpha()
        surface.set_alpha(alpha)
        textCache[key] = surface
    return textCache[key]


# Alias font lama diganti dengan sistem font baru
font = loadFont(15)
titleFont = loadFont(42, True)

# to control the frame rate
clock = pygame.time.Clock()
FPS = 60

# Kecepatan awal bola dan batas maksimal kecepatannya
BALL_SPEED = 2.5
MAX_BALL_SPEED = 4.5
SPEED_INCREMENT = 0.25

# Pengaturan power-up
POWERUP_CHANCE = 0.2
POWERUP_DURATION = 8 * FPS
PADDLE_WIDTH = 100
WIDE_PADDLE_WIDTH = 160
SLOW_FACTOR = 0.6
MAX_LIVES = 5
POWERUP_SPEED = 1.5
POWERUP_W, POWERUP_H = 34, 18
BALL_GLOW_FRAMES = 12

# Jenis power-up dan warnanya
POWERUP_PADDLE = "paddle"
POWERUP_SLOW = "slow"
POWERUP_LIFE = "life"
POWERUP_COLORS = {
    POWERUP_PADDLE: TEAL,
    POWERUP_SLOW: VIOLET,
    POWERUP_LIFE: ROSE_GOLD
}

# Pengaturan tampilan
BLOCK_RADIUS = 5
BALL_TRAIL_LENGTH = 12
PARTICLE_COUNT = 12
PARTICLE_LIFE = 22
SHAKE_TIME = 12
SHAKE_STRENGTH = 4
STRIKER_FLASH_TIME = 6
FLOATING_TEXT_LIFE = 30

# Background dinamis: aksen berganti tiap level, lalu berulang
LEVEL_ACCENTS = ((52, 96, 140), VIOLET, TEAL, ROSE_GOLD)
BG_FADE_FRAMES = 48
VIGNETTE_ALPHA = 150

# Starfield 3 lapis: (jumlah, kecepatan, ukuran, alpha dasar)
STAR_LAYERS = ((34, 0.10, 1, 80),
               (20, 0.20, 2, 130),
               (10, 0.34, 2, 190))
STAR_TWINKLE_SPEED = (0.018, 0.030, 0.045)

# Lokasi file high score (di folder yang sama dengan file program)
HIGHSCORE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "highscore.txt")

# Cache permukaan balok agar gradasi tidak dibuat ulang tiap frame
blockSurfaceCache = {}

# Cache ikon hati anti-aliased
heartCache = {}

# Cache surface bergaya (dibuat sekali, dipakai berulang)
roundedSurfaceCache = {}
crackSurfaceCache = {}
paddleSurfaceCache = {}
paddleGlowCache = {}
powerUpSurfaceCache = {}
powerUpGlowCache = {}
ballSurfaceCache = {}
trailCircleCache = {}


# Mencampur dua warna (t = 0..1)
def blendColor(colorA, colorB, t):
    return (int(colorA[0] + (colorB[0] - colorA[0]) * t),
            int(colorA[1] + (colorB[1] - colorA[1]) * t),
            int(colorA[2] + (colorB[2] - colorA[2]) * t))


# Membuat permukaan gradasi vertikal untuk background
def createGradientSurface(topColor, bottomColor, height):
    surface = pygame.Surface((WIDTH, height))
    for y in range(height):
        factor = y / height
        pygame.draw.line(surface, blendColor(topColor, bottomColor, factor),
                         (0, y), (WIDTH, y))
    return surface


# Background per level: gradasi navy-indigo yang diberi aksen warna level
levelBackgroundCache = {}


def getLevelBackground(accentIndex):
    key = accentIndex % len(LEVEL_ACCENTS)
    if key not in levelBackgroundCache:
        accent = LEVEL_ACCENTS[key]
        topColor = blendColor(NAVY, accent, 0.22)
        bottomColor = blendColor(INDIGO, accent, 0.16)
        levelBackgroundCache[key] = createGradientSurface(
            topColor, bottomColor, HEIGHT)
    return levelBackgroundCache[key]


# Bintang kecil yang sudah dihaluskan, di-cache per ukuran dan alpha
starSpriteCache = {}


def getStarSprite(size, alpha):
    alpha = max(0, min(255, int(alpha)))
    key = (size, alpha)
    if key not in starSpriteCache:
        scale = 4
        big = pygame.Surface((size * scale, size * scale), pygame.SRCALPHA)
        pygame.draw.circle(big, TEXT_SOFT,
                           (size * scale // 2, size * scale // 2),
                           max(1, size * scale // 2))
        sprite = pygame.transform.smoothscale(
            big, (size, size)).convert_alpha()
        sprite.set_alpha(alpha)
        starSpriteCache[key] = sprite
    return starSpriteCache[key]


# Posisi bintang disiapkan sekali agar tidak diacak tiap frame
stars = []
for layer, (count, speed, size, baseAlpha) in enumerate(STAR_LAYERS):
    for _ in range(count):
        stars.append({
            "x": random.randint(0, WIDTH),
            "y": random.randint(0, HEIGHT),
            "layer": layer,
            "phase": random.uniform(0, math.pi * 2),
            "twinkle": STAR_TWINKLE_SPEED[layer] *
                       random.uniform(0.7, 1.3)
        })


# Bintang bergerak pelan ke bawah; yang keluar layar muncul lagi di atas
def updateStars():
    for star in stars:
        _, speed, _, _ = STAR_LAYERS[star["layer"]]
        star["y"] = (star["y"] + speed) % (HEIGHT + 4)
        star["phase"] += star["twinkle"]


# Menggambar bintang dengan kedip halus sesuai fase masing-masing
def drawStars():
    for star in stars:
        _, _, size, baseAlpha = STAR_LAYERS[star["layer"]]
        twinkle = 0.55 + 0.45 * math.sin(star["phase"])
        # Alpha dibulatkan ke kelipatan 16 agar cache tidak terus bertambah
        alpha = int(baseAlpha * twinkle)
        alpha -= alpha % 16
        sprite = getStarSprite(size, alpha)
        screen.blit(sprite, (int(star["x"]), int(star["y"])))


# Vignette tipis: dibuat sekali dari gradasi radial beresolusi kecil
def createVignetteSurface():
    smallW, smallH = WIDTH // 4, HEIGHT // 4
    small = pygame.Surface((smallW, smallH), pygame.SRCALPHA)
    centerX, centerY = smallW / 2, smallH / 2
    maxDist = math.hypot(centerX, centerY)

    for y in range(smallH):
        for x in range(smallW):
            dist = math.hypot(x - centerX, y - centerY) / maxDist
            edge = max(0.0, (dist - 0.55) / 0.45)
            alpha = int(VIGNETTE_ALPHA * edge * edge)
            if alpha > 0:
                small.set_at((x, y), (4, 6, 14, alpha))

    return pygame.transform.smoothscale(
        small, (WIDTH, HEIGHT)).convert_alpha()


vignetteSurface = createVignetteSurface()


# Latar lengkap: gradasi level (dengan crossfade), bintang, lalu vignette
def drawBackground(accentIndex, prevAccentIndex=None, fade=1.0):
    if prevAccentIndex is None or fade >= 1.0:
        screen.blit(getLevelBackground(accentIndex), (0, 0))
    else:
        # Crossfade halus dari warna level lama ke warna level baru
        screen.blit(getLevelBackground(prevAccentIndex), (0, 0))
        incoming = getLevelBackground(accentIndex)
        incoming.set_alpha(int(255 * fade))
        screen.blit(incoming, (0, 0))
        incoming.set_alpha(255)

    drawStars()
    screen.blit(vignetteSurface, (0, 0))



# Membuat permukaan gradasi vertikal dengan sudut membulat (supersampling 3x)
def makeRoundedSurface(width, height, radius, colorTop, colorBottom):
    key = (width, height, radius, colorTop, colorBottom)
    if key in roundedSurfaceCache:
        return roundedSurfaceCache[key]

    scale = 3
    bigW, bigH = width * scale, height * scale

    gradient = pygame.Surface((bigW, bigH), pygame.SRCALPHA)
    for y in range(bigH):
        factor = y / max(1, bigH - 1)
        pygame.draw.line(gradient,
                         blendColor(colorTop, colorBottom, factor),
                         (0, y), (bigW, y))

    # Masking sudut membulat pada resolusi tinggi
    mask = pygame.Surface((bigW, bigH), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                     border_radius=radius * scale)
    gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    surface = pygame.transform.smoothscale(
        gradient, (width, height)).convert_alpha()
    roundedSurfaceCache[key] = surface
    return surface


# Warna balok sesuai jenis dan sisa health
def blockColors(color, healthRatio):
    if color == RED:
        topColor, bottomColor = BLOCK_ROSE_TOP, BLOCK_ROSE_BOTTOM
    elif color == WHITE:
        topColor, bottomColor = BLOCK_VIOLET_TOP, BLOCK_VIOLET_BOTTOM
    else:
        topColor, bottomColor = BLOCK_TEAL_TOP, BLOCK_TEAL_BOTTOM

    # Semakin kecil health, warna makin redup
    darken = 0.55 + 0.45 * healthRatio
    return (blendColor(topColor, BLOCK_DARK, 1 - darken),
            blendColor(bottomColor, BLOCK_DARK, 1 - darken))


# Permukaan balok: gradasi halus, sorotan atas, dan bayangan bawah
def getBlockSurface(color, healthRatio, width, height):
    key = (color, round(healthRatio, 2), width, height)
    if key not in blockSurfaceCache:
        topColor, bottomColor = blockColors(color, healthRatio)
        surface = makeRoundedSurface(
            width, height, BLOCK_RADIUS, topColor, bottomColor).copy()

        # Sorotan tipis di atas
        pygame.draw.line(surface, blendColor(topColor, (255, 255, 255), 0.4),
                         (BLOCK_RADIUS + 1, 2), (width - BLOCK_RADIUS - 2, 2))
        # Bayangan lembut di bawah
        pygame.draw.line(surface, blendColor(bottomColor, (0, 0, 0), 0.5),
                         (BLOCK_RADIUS + 1, height - 2),
                         (width - BLOCK_RADIUS - 2, height - 2))
        # Border tipis ikut di-cache
        pygame.draw.rect(surface, BLOCK_BORDER, surface.get_rect(),
                         1, border_radius=BLOCK_RADIUS)

        blockSurfaceCache[key] = surface
    return blockSurfaceCache[key]


# Retakan tipis untuk balok yang sudah terkena pukulan
def getCrackSurface(width, height):
    key = (width, height)
    if key not in crackSurfaceCache:
        scale = 3
        bigW, bigH = width * scale, height * scale
        surface = pygame.Surface((bigW, bigH), pygame.SRCALPHA)

        crackColor = (240, 244, 252, 130)
        lines = [
            [(0.18, 0.25), (0.42, 0.58), (0.30, 0.85)],
            [(0.58, 0.18), (0.52, 0.48), (0.78, 0.70)]]
        for points in lines:
            pygame.draw.lines(surface, crackColor, False,
                              [(int(x * bigW), int(y * bigH))
                               for x, y in points], 2)

        crackSurfaceCache[key] = pygame.transform.smoothscale(
            surface, (width, height)).convert_alpha()
    return crackSurfaceCache[key]


# Papan bergaya kaca dengan border tipis dan sorotan atas
def getPaddleSurface(width, height):
    key = (width, height)
    if key not in paddleSurfaceCache:
        surface = makeRoundedSurface(
            width, height, height // 2,
            (92, 158, 188), (42, 82, 116)).copy()
        surface.set_alpha(222)

        pygame.draw.rect(surface, STRIKER_BORDER, surface.get_rect(),
                         1, border_radius=height // 2)
        pygame.draw.line(surface, (226, 246, 250),
                         (12, 3), (width - 13, 3))
        paddleSurfaceCache[key] = surface
    return paddleSurfaceCache[key]


# Glow lembut di sekitar papan
def getPaddleGlow(width, height):
    key = (width, height)
    if key not in paddleGlowCache:
        glowW, glowH = width + 30, height + 30
        surface = pygame.Surface((glowW, glowH), pygame.SRCALPHA)
        for shrink, alpha in ((0, 22), (5, 30), (10, 38)):
            rect = pygame.Rect(0, 0, glowW, glowH).inflate(
                -shrink * 2, -shrink * 2)
            pygame.draw.rect(surface, (90, 190, 205, alpha), rect,
                             border_radius=16)
        paddleGlowCache[key] = pygame.transform.smoothscale(
            surface, (glowW // 2, glowH // 2)).convert_alpha()
        paddleGlowCache[key] = pygame.transform.smoothscale(
            paddleGlowCache[key], (glowW, glowH)).convert_alpha()
    return paddleGlowCache[key]


# Bola inti yang halus (anti-aliased) dan di-cache
def getBallSurface(radius, color):
    key = (radius, color)
    if key not in ballSurfaceCache:
        scale = 4
        size = radius * 2 * scale
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        pygame.draw.circle(surface, color, (center, center), radius * scale)
        pygame.draw.circle(surface, (255, 255, 255),
                           (center - radius * scale // 3,
                            center - radius * scale // 3),
                           max(1, radius * scale // 3))
        ballSurfaceCache[key] = pygame.transform.smoothscale(
            surface, (radius * 2, radius * 2)).convert_alpha()
    return ballSurfaceCache[key]


# Lingkaran trail anti-aliased untuk tiap radius dan tingkat alpha
def precomputeTrailCircles():
    scale = 3
    for radius in range(2, 8):
        size = radius * 2 * scale
        base = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(base, BALL_TRAIL,
                           (size // 2, size // 2), radius * scale)
        base = pygame.transform.smoothscale(
            base, (radius * 2, radius * 2)).convert_alpha()

        for step in range(0, 17):
            circle = base.copy()
            circle.set_alpha(int(255 * step / 16 * 0.55))
            trailCircleCache[(radius, step)] = circle


# Power-up: kapsul lebih besar dengan ikon vektor
def getPowerUpSurface(kind):
    if kind in powerUpSurfaceCache:
        return powerUpSurfaceCache[kind]

    width, height = POWERUP_W, POWERUP_H
    color = POWERUP_COLORS[kind]
    surface = makeRoundedSurface(
        width, height, height // 2,
        blendColor(color, (255, 255, 255), 0.3),
        blendColor(color, (10, 12, 24), 0.35)).copy()
    pygame.draw.rect(surface, blendColor(color, (255, 255, 255), 0.45),
                     surface.get_rect(), 1, border_radius=height // 2)

    # Ikon digambar pada resolusi 3x agar tepinya halus
    scale = 3
    icon = pygame.Surface((width * scale, height * scale),
                          pygame.SRCALPHA)
    iconColor = (250, 252, 255)
    cx, cy = width * scale // 2, height * scale // 2
    unit = height * scale // 5

    if kind == POWERUP_PADDLE:
        # Panah ganda kiri-kanan
        for direction in (-1, 1):
            tipX = cx + direction * unit * 2
            pygame.draw.lines(icon, iconColor, False, [
                (tipX - direction * unit, cy - unit),
                (tipX, cy),
                (tipX - direction * unit, cy + unit)], max(1, scale))
    elif kind == POWERUP_SLOW:
        # Jam: lingkaran dengan jarum
        pygame.draw.circle(icon, iconColor, (cx, cy), unit * 2, max(1, scale))
        pygame.draw.line(icon, iconColor, (cx, cy), (cx, cy - unit),
                         max(1, scale))
        pygame.draw.line(icon, iconColor, (cx, cy), (cx + unit, cy),
                         max(1, scale))
    else:
        # Hati untuk tambahan nyawa
        radius = unit
        leftX, rightX = cx - radius * 0.55, cx + radius * 0.55
        pygame.draw.circle(icon, iconColor,
                           (int(leftX), int(cy - unit * 0.4)), radius)
        pygame.draw.circle(icon, iconColor,
                           (int(rightX), int(cy - unit * 0.4)), radius)
        pygame.draw.polygon(icon, iconColor, [
            (int(cx - radius * 1.55), int(cy - unit * 0.2)),
            (int(cx + radius * 1.55), int(cy - unit * 0.2)),
            (int(cx), int(cy + unit * 1.6))])

    icon = pygame.transform.smoothscale(
        icon, (width, height)).convert_alpha()
    surface.blit(icon, (0, 0))
    powerUpSurfaceCache[kind] = surface
    return surface


# Glow kapsul sesuai jenis power-up
def getPowerUpGlow(kind):
    if kind in powerUpGlowCache:
        return powerUpGlowCache[kind]

    color = POWERUP_COLORS[kind]
    glowW, glowH = POWERUP_W + 24, POWERUP_H + 24
    surface = pygame.Surface((glowW, glowH), pygame.SRCALPHA)
    for shrink, alpha in ((0, 24), (4, 34), (8, 44)):
        rect = pygame.Rect(0, 0, glowW, glowH).inflate(
            -shrink * 2, -shrink * 2)
        pygame.draw.rect(surface, (color[0], color[1], color[2], alpha),
                         rect, border_radius=rect.height // 2)

    small = pygame.transform.smoothscale(
        surface, (glowW // 2, glowH // 2))
    powerUpGlowCache[kind] = pygame.transform.smoothscale(
        small, (glowW, glowH)).convert_alpha()
    return powerUpGlowCache[kind]


# Membuat efek glow bola (beberapa tingkat denyut) sekali saja
def createGlowSurface(radius, boost=1.0):
    size = radius * 7
    glow = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    for glowRadius, alpha in ((radius * 3, 24),
                              (radius * 2, 42),
                              (radius + 2, 88)):
        alpha = max(0, min(255, int(alpha * boost)))
        pygame.draw.circle(glow, (BALL_GLOW[0], BALL_GLOW[1],
                                  BALL_GLOW[2], alpha),
                           (center, center), glowRadius)
    return glow.convert_alpha()


# Background gradasi dibuat sekali, lalu di-blit tiap frame
backgroundSurface = createGradientSurface(DARK_BLUE, DARK_PURPLE, HEIGHT)

# Siapkan semua surface trail di awal agar tidak ada Surface baru di loop
precomputeTrailCircles()


# Membuat nada sederhana (gelombang sinus) tanpa file eksternal
def createToneSound(frequency, duration, volume=0.3):
    sampleRate = 44100
    totalSamples = int(sampleRate * duration)
    samples = array.array('h')

    for i in range(totalSamples):
        # Envelope menurun agar suara tidak berhenti mendadak
        envelope = 1 - i / totalSamples
        value = int(32767 * volume * envelope *
                    math.sin(2 * math.pi * frequency * i / sampleRate))
        samples.append(value)

    return pygame.mixer.Sound(buffer=samples.tobytes())


# Menyiapkan semua efek suara; gagal sedikitpun tetap aman
def createSoundEffects():
    if not audioAvailable:
        return

    try:
        soundEffects["bounce"] = createToneSound(440, 0.06, 0.25)
        soundEffects["break"] = createToneSound(700, 0.10, 0.30)
        soundEffects["powerup"] = createToneSound(880, 0.15, 0.30)
        soundEffects["lifeLost"] = createToneSound(220, 0.30, 0.30)
        soundEffects["gameOver"] = createToneSound(140, 0.60, 0.30)
    except Exception:
        # Audio tidak boleh menghentikan permainan
        soundEffects.clear()


# Memainkan efek suara jika tidak di-mute dan tersedia
def playSound(name):
    if muted or name not in soundEffects:
        return

    try:
        soundEffects[name].play()
    except pygame.error:
        # Abaikan jika perangkat audio bermasalah
        pass


# Mengubah status mute/unmute
def toggleMute():
    global muted
    muted = not muted


# Membaca high score dari file, aman jika file belum ada/rusak
def loadHighScore():
    try:
        with open(HIGHSCORE_FILE, "r") as file:
            return int(file.read().strip())
    except (FileNotFoundError, ValueError, OSError):
        return 0


# Menyimpan high score ke file
def saveHighScore(score):
    try:
        with open(HIGHSCORE_FILE, "w") as file:
            file.write(str(score))
    except OSError:
        pass


createSoundEffects()


# Striker class
class Striker:
    def __init__(self, posx, posy, width, height, speed, color):
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.speed = speed
        self.color = color

        # The rect variable is used to handle the placement
        # and the collisions of the object
        self.strikerRect = pygame.Rect(
            self.posx, self.posy, self.width, self.height)
        self.striker = pygame.draw.rect(screen, 
                               self.color, self.strikerRect)

    # Used to render the object on the screen
    def display(self, flash=False):
        width = self.strikerRect.width
        height = self.strikerRect.height

        # Glow lembut di belakang papan kaca
        glow = getPaddleGlow(width, height)
        screen.blit(glow, glow.get_rect(center=self.strikerRect.center))

        # Papan semi-transparan dengan border tipis terang
        surface = getPaddleSurface(width, height)
        screen.blit(surface, self.strikerRect.topleft)

        # Kilau tambahan singkat saat bola memantul
        if flash:
            pygame.draw.rect(screen, (235, 250, 252),
                             self.strikerRect, 1, border_radius=height // 2)

    # Used to update the state of the object
    def update(self, xFac):
        self.posx += self.speed*xFac

        # Restricting the striker to be in between the 
        # left and right edges of the screen
        if self.posx <= 0:
            self.posx = 0
        elif self.posx+self.width >= WIDTH:
            self.posx = WIDTH-self.width

        self.strikerRect = pygame.Rect(
            self.posx, self.posy, self.width, self.height)

    # Mengubah lebar striker (dipakai efek power-up Paddle Besar)
    def setWidth(self, width):
        self.width = width
        self.strikerRect = pygame.Rect(
            self.posx, self.posy, self.width, self.height)

        # Pastikan striker tetap berada di dalam layar
        if self.posx + self.width > WIDTH:
            self.posx = WIDTH - self.width
            self.strikerRect.x = self.posx

    # Returns the rect of the object
    def getRect(self):
        return self.strikerRect


# Block Class
class Block:
    def __init__(self, posx, posy, width, height, color):
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.color = color
        self.damage = 100

        # Balok merah perlu 3x pukul, putih 2x, hijau 1x
        if color == RED:
            self.health = 300
        elif color == WHITE:
            self.health = 200
        else:
            self.health = 100

        # Health maksimal dipakai untuk menentukan warna balok
        self.maxHealth = self.health

        # The rect variable is used to handle the placement 
        # and the collisions of the object
        self.blockRect = pygame.Rect(
            self.posx, self.posy, self.width, self.height)
        self.block = pygame.draw.rect(screen, self.color, 
                                      self.blockRect)

    # Used to render the object on the screen if and only 
    # if its health is greater than 0
    def display(self):
        if self.health > 0:
            # Warna berubah sesuai sisa health
            healthRatio = self.health / self.maxHealth
            surface = getBlockSurface(self.color, healthRatio,
                                      self.width, self.height)
            screen.blit(surface, self.blockRect.topleft)

            # Retakan tipis saat balok sudah terkena pukulan
            if healthRatio < 1:
                screen.blit(getCrackSurface(self.width, self.height),
                            self.blockRect.topleft)

    # Used to decrease the health of the block
    def hit(self):
        self.health -= self.damage

    # Used to get the rect of the object
    def getRect(self):
        return self.blockRect

    # Used to get the health of the object
    def getHealth(self):
        return self.health

    # Skor yang didapat sesuai jenis (warna) balok
    def getScore(self):
        if self.color == RED:
            return 15
        elif self.color == WHITE:
            return 10
        return 5


# Ball Class
class Ball:
    def __init__(self, posx, posy, radius, speed, color):
        self.posx, self.posy = posx, posy
        self.radius = radius
        self.speed = speed
        # Kecepatan dasar (tanpa efek Slow Ball)
        self.baseSpeed = speed
        self.isSlowed = False
        self.color = color
        self.xFac, self.yFac = 1, 1

        # Jejak bola dan beberapa frame glow untuk denyut halus
        self.trail = []
        self.glowFrames = []
        for i in range(BALL_GLOW_FRAMES):
            boost = 0.75 + 0.5 * (i / (BALL_GLOW_FRAMES - 1))
            self.glowFrames.append(createGlowSurface(self.radius, boost))

        self.ball = pygame.draw.circle(
            screen, self.color, (self.posx,
                                 self.posy), self.radius)

    # Used to display the object on the screen
    def display(self):
        # Glow berdenyut mengikuti gelombang sinus
        pulse = (math.sin(pygame.time.get_ticks() / 320.0) + 1) / 2
        glow = self.glowFrames[int(pulse * (BALL_GLOW_FRAMES - 1))]
        screen.blit(glow, glow.get_rect(
            center=(int(self.posx), int(self.posy))))

        # Jejak bola: lingkaran anti-aliased yang mengecil dan memudar
        for i, (trailX, trailY) in enumerate(self.trail):
            factor = (i + 1) / (len(self.trail) + 1)
            radius = max(2, min(7, int(self.radius * factor) + 1))
            circle = trailCircleCache[(radius, int(factor * 16))]
            screen.blit(circle, circle.get_rect(
                center=(int(trailX), int(trailY))))

        # Bola utama yang halus
        core = getBallSurface(self.radius, self.color)
        screen.blit(core, core.get_rect(
            center=(int(self.posx), int(self.posy))))

    # Used to update the state of the object
    def update(self):
        self.posx += self.xFac*self.speed
        self.posy += self.yFac*self.speed

        # Simpan posisi terakhir untuk jejak bola
        self.trail.append((self.posx, self.posy))
        if len(self.trail) > BALL_TRAIL_LENGTH:
            self.trail.pop(0)

        # Reflecting the ball if it touches
        # either of the vertical edges
        if self.posx <= 0 or self.posx >= WIDTH:
            self.xFac *= -1
            playSound("bounce")

        # Reflection from the top most edge of the screen
        if self.posy <= 0:
            self.yFac *= -1
            playSound("bounce")

        # If the ball touches the bottom most edge of 
        # the screen, True value is returned
        if self.posy >= HEIGHT:
            return True

        return False

    # Resets the position of the ball
    # Bola diletakkan tepat di atas tengah striker, bukan di pojok kiri bawah
    def reset(self, striker):
        strikerRect = striker.getRect()
        self.posx = strikerRect.centerx
        self.posy = strikerRect.top - self.radius - 1
        # Luncurkan bola lurus ke atas menjauhi striker
        self.xFac, self.yFac = 0, -1
        # Bersihkan jejak agar tidak menyambung dari posisi lama
        self.trail = []

    # Used to change the direction along Y axis
    def hit(self):
        self.yFac *= -1

    # Used to change the direction along X axis
    # Dipakai saat bola menabrak sisi samping balok
    def hitSide(self):
        self.xFac *= -1

    # Menambah kecepatan bola sedikit tiap level, dibatasi maksimal
    def speedUp(self, amount, maxSpeed):
        self.baseSpeed = min(self.baseSpeed + amount, maxSpeed)
        # Jika sedang slow, kecepatan efektif tetap mengikuti efeknya
        if not self.isSlowed:
            self.speed = self.baseSpeed

    # Memperlambat bola sementara (efek Slow Ball)
    def applySlow(self, factor):
        self.speed = self.baseSpeed * factor
        self.isSlowed = True

    # Mengembalikan kecepatan bola seperti semula
    def removeSlow(self):
        self.speed = self.baseSpeed
        self.isSlowed = False

    # Mengembalikan kecepatan bola ke nilai awal (saat main lagi)
    def resetSpeed(self, speed):
        self.baseSpeed = speed
        self.speed = speed
        self.isSlowed = False

    # Returns the rect of the ball based on its
    # current position, so collision is always up to date
    def getRect(self):
        return pygame.Rect(self.posx - self.radius,
                           self.posy - self.radius,
                           self.radius * 2, self.radius * 2)

# PowerUp Class
class PowerUp:
    def __init__(self, posx, posy, kind):
        self.posx, self.posy = posx, posy
        self.width, self.height = POWERUP_W, POWERUP_H
        self.speed = POWERUP_SPEED
        self.kind = kind
        self.color = POWERUP_COLORS[kind]

        # Rect dipakai untuk deteksi tabrakan dengan striker
        self.powerUpRect = pygame.Rect(
            self.posx - self.width//2, self.posy,
            self.width, self.height)

    # Menampilkan kapsul berikon dengan glow sesuai jenis
    def display(self):
        glow = getPowerUpGlow(self.kind)
        screen.blit(glow, glow.get_rect(center=self.powerUpRect.center))

        surface = getPowerUpSurface(self.kind)
        screen.blit(surface, self.powerUpRect.topleft)

    # Jatuh ke bawah; True jika sudah melewati bawah layar
    def update(self):
        self.posy += self.speed
        self.powerUpRect = pygame.Rect(
            self.posx - self.width//2, self.posy,
            self.width, self.height)

        return self.powerUpRect.top > HEIGHT

    # Returns the rect of the object
    def getRect(self):
        return self.powerUpRect


# Particle Class
class Particle:
    def __init__(self, posx, posy, color):
        self.posx, self.posy = posx, posy
        self.color = color
        self.radius = random.randint(2, 4)
        self.xVel = random.uniform(-3, 3)
        self.yVel = random.uniform(-4, 1)
        self.life = random.randint(PARTICLE_LIFE - 7, PARTICLE_LIFE)
        self.maxLife = self.life

    # Bergerak menyebar dengan gravitasi ringan
    def update(self):
        self.posx += self.xVel
        self.posy += self.yVel
        self.yVel += 0.2
        self.life -= 1

        return self.life <= 0

    # Partikel mengecil dan memudar seiring waktu
    def display(self):
        factor = max(0, self.life / self.maxLife)
        radius = max(1, int(self.radius * factor))
        fadeColor = blendColor(self.color, DARK_PURPLE, 1 - factor)
        pygame.draw.circle(screen, fadeColor,
                           (int(self.posx), int(self.posy)), radius)


# FloatingText Class
class FloatingText:
    def __init__(self, posx, posy, text):
        self.posx, self.posy = posx, posy
        self.text = text
        self.life = FLOATING_TEXT_LIFE
        self.maxLife = FLOATING_TEXT_LIFE

    # Teks naik sedikit lalu memudar
    def update(self):
        self.posy -= 1
        self.life -= 1

        return self.life <= 0

    def display(self):
        alpha = int(255 * self.life / self.maxLife)
        surface = renderTextAlphaCached(
            self.text, 15, GOLD, alpha, True)
        screen.blit(surface, surface.get_rect(
            center=(int(self.posx), int(self.posy))))


# Helper Functions

# Function used to check collisions between any two entities


def collisionChecker(rect, ball):
    if pygame.Rect.colliderect(rect, ball):
        return True

    return False


# Menentukan sisi tabrakan bola dengan balok (atas/bawah atau samping),
# lalu memantulkan bola sesuai sisi tersebut
def resolveBlockCollision(ball, blockRect):
    ballRect = ball.getRect()

    # Kedalaman bola menembus balok dari masing-masing sisi
    overlapLeft = ballRect.right - blockRect.left
    overlapRight = blockRect.right - ballRect.left
    overlapTop = ballRect.bottom - blockRect.top
    overlapBottom = blockRect.bottom - ballRect.top

    # Sisi dengan kedalaman terkecil adalah sisi yang benar-benar ditabrak
    minOverlap = min(overlapLeft, overlapRight, overlapTop, overlapBottom)

    if minOverlap == overlapTop:
        # Tabrakan dari atas: balik arah Y dan dorong bola ke atas
        ball.hit()
        ball.posy -= overlapTop
    elif minOverlap == overlapBottom:
        # Tabrakan dari bawah: balik arah Y dan dorong bola ke bawah
        ball.hit()
        ball.posy += overlapBottom
    elif minOverlap == overlapLeft:
        # Tabrakan dari samping kiri: balik arah X
        ball.hitSide()
        ball.posx -= overlapLeft
    else:
        # Tabrakan dari samping kanan: balik arah X
        ball.hitSide()
        ball.posx += overlapRight


# Menangani pantulan bola pada striker berdasarkan titik pukul
def strikerBounce(ball, strikerRect):
    # Posisi relatif titik pukul terhadap tengah striker
    # (-1 = paling kiri, 0 = tengah, 1 = paling kanan)
    hitOffset = (ball.getRect().centerx -
                 strikerRect.centerx) / (strikerRect.width / 2)
    hitOffset = max(-1, min(1, hitOffset))

    # Tengah striker = bola lurus ke atas, tepi = bola makin miring
    ball.xFac = hitOffset
    ball.yFac = -abs(ball.yFac)

    # Letakkan bola tepat di atas striker agar tidak menempel
    # dan memantul berulang di frame berikutnya
    ball.posy = strikerRect.top - ball.radius - 1


# Function used to populate the blocks
# Grid balok simetris di tengah area bermain, pola berganti tiap level
def populateBlocks(blockWidth, blockHeight, 
                   horizontalGap, verticalGap, level):
    listOfBlocks = []

    columnCount = GRID_COLUMNS
    rowCount = GRID_ROWS

    # Grid dibuat simetris (margin kiri = margin kanan)
    gridWidth = (columnCount * blockWidth +
                 (columnCount - 1) * horizontalGap)
    left = (WIDTH - gridWidth) // 2

    # 0 = penuh, 1 = selang-seling, 2 = piramida
    pattern = (level - 1) % 3
    center = (columnCount - 1) // 2

    for column in range(columnCount):
        for row in range(rowCount):
            # Pola selang-seling: lewati balok bergantian
            if pattern == 1 and (column + row) % 2 != 0:
                continue

            # Pola piramida: melebar ke bawah dari tengah
            if pattern == 2:
                if row > center:
                    continue
                if column < center - row or column > center + row:
                    continue

            posx = left + column * (blockWidth+horizontalGap)
            posy = GRID_TOP + row * (blockHeight+verticalGap)

            # Jenis balok acak: teal (1x), violet (2x), rose (3x)
            listOfBlocks.append(
                Block(posx, posy, blockWidth, blockHeight, 
                      random.choice([WHITE, GREEN, RED])))

    return listOfBlocks


# Layar awal dengan judul game dan petunjuk mulai
def startScreen(highScore):
    while True:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True
                # Tombol M untuk mute/unmute
                if event.key == pygame.K_m:
                    toggleMute()

        updateStars()
        drawBackground(0)

        titleText = renderTextCached("BLOCK BREAKER", 42, TEXT_SOFT, True)
        titleRect = titleText.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        screen.blit(titleText, titleRect)

        startText = renderTextCached("TEKAN SPACE UNTUK MULAI",
                                     14, TEAL, True)
        startRect = startText.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
        screen.blit(startText, startRect)

        # High score terakhir ditampilkan di layar awal
        highText = renderTextCached("HIGH SCORE  " + str(highScore),
                                    13, GOLD, True)
        highRect = highText.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 75))
        screen.blit(highText, highRect)

        # Petunjuk tombol mute beserta statusnya
        muteText = renderTextCached(
            "M  SUARA " + ("MATI" if muted else "NYALA"),
            11, TEXT_DIM, True)
        muteRect = muteText.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 105))
        screen.blit(muteText, muteRect)

        pygame.display.update()
        clock.tick(FPS)


# Once all the lives are over, this function waits until
# exit or space bar is pressed and does the corresponding action
def gameOver(score):
    # Efek suara saat game over
    playSound("gameOver")

    while True:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                # SPACE untuk main lagi, ESC untuk keluar
                if event.key == pygame.K_SPACE:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False
                # Tombol M untuk mute/unmute
                if event.key == pygame.K_m:
                    toggleMute()

        updateStars()
        drawBackground(0)

        overText = renderTextCached("GAME OVER", 38, ROSE_GOLD, True)
        overRect = overText.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        screen.blit(overText, overRect)

        finalScoreLabel = renderTextCached("SKOR AKHIR", 11, TEXT_DIM, True)
        screen.blit(finalScoreLabel, finalScoreLabel.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 - 15)))

        finalScoreText = renderTextCached(str(score), 26, TEXT_SOFT, True)
        finalScoreRect = finalScoreText.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 + 10))
        screen.blit(finalScoreText, finalScoreRect)

        hintText = renderTextCached(
            "SPACE  MAIN LAGI      ESC  KELUAR", 12, TEXT_DIM, True)
        hintRect = hintText.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(hintText, hintRect)

        pygame.display.update()
        # Batasi frame rate agar CPU tidak penuh saat layar game over
        clock.tick(FPS)


# Layar saat semua balok habis (level selesai)
def winScreen(score):
    while True:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False
                # Tombol M untuk mute/unmute
                if event.key == pygame.K_m:
                    toggleMute()

        updateStars()
        drawBackground(0)

        winText = renderTextCached("YOU WIN", 38, TEAL, True)
        winRect = winText.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70))
        screen.blit(winText, winRect)

        completeText = renderTextCached("LEVEL COMPLETE", 12, TEXT_DIM, True)
        completeRect = completeText.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 - 25))
        screen.blit(completeText, completeRect)

        finalScoreText = renderTextCached(str(score), 26, TEXT_SOFT, True)
        finalScoreRect = finalScoreText.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 + 10))
        screen.blit(finalScoreText, finalScoreRect)

        hintText = renderTextCached(
            "SPACE  LANJUT      ESC  KELUAR", 12, TEXT_DIM, True)
        hintRect = hintText.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(hintText, hintRect)

        pygame.display.update()
        clock.tick(FPS)


# Menggambar ikon hati vektor yang halus (anti-aliased, di-cache)
def getHeartSurface(size, color):
    key = (size, color)
    if key not in heartCache:
        scale = 4
        boxW = boxH = size * scale
        surface = pygame.Surface((boxW, boxH), pygame.SRCALPHA)

        radius = boxW // 4
        lobeY = int(boxH * 0.34)
        leftX = int(boxW // 2 - radius * 0.55)
        rightX = int(boxW // 2 + radius * 0.55)

        # Dua lengkung atas dan ujung bawah hati
        pygame.draw.circle(surface, color, (leftX, lobeY), radius)
        pygame.draw.circle(surface, color, (rightX, lobeY), radius)
        pygame.draw.polygon(surface, color, [
            (int(boxW // 2 - radius * 1.55), int(boxH * 0.36)),
            (int(boxW // 2 + radius * 1.55), int(boxH * 0.36)),
            (int(boxW // 2), int(boxH * 0.92))])

        heartCache[key] = pygame.transform.smoothscale(
            surface, (size, size)).convert_alpha()
    return heartCache[key]


def drawHeart(cx, cy, size, color):
    heart = getHeartSurface(size, color)
    screen.blit(heart, heart.get_rect(center=(cx, cy)))


# Game Manager
def main():
    running = True
    lives = 3
    score = 0
    level = 1

    # Status crossfade warna background saat level berganti
    bgAccent = 0
    bgPrevAccent = 0
    bgFade = 1.0

    # High score dibaca dari file saat game mulai
    highScore = loadHighScore()

    striker = Striker(0, STRIKER_Y, PADDLE_WIDTH, 20, 5, WHITE)
    strikerXFac = 0

    ball = Ball(WIDTH // 2, STRIKER_Y - 60, 7, BALL_SPEED, BALL_COLOR)

    blockWidth, blockHeight = BLOCK_W, BLOCK_H
    horizontalGap, verticalGap = BLOCK_GAP_X, BLOCK_GAP_Y

    listOfBlocks = populateBlocks(
        blockWidth, blockHeight, horizontalGap, verticalGap, level)

    powerUps = []
    paddleTimer = 0
    slowTimer = 0

    # Efek visual dinamis
    particles = []
    floatingTexts = []
    strikerFlashTimer = 0
    shakeTimer = 0

    # Tampilkan layar awal sebelum permainan dimulai
    if not startScreen(highScore):
        return

    # Bola mulai dari atas striker saat permainan dimulai
    ball.reset(striker)
    paused = False

    # Game loop
    while running:
        # Crossfade background berjalan sedikit tiap frame
        if bgFade < 1.0:
            bgFade = min(1.0, bgFade + 1.0 / BG_FADE_FRAMES)

        updateStars()
        drawBackground(bgAccent, bgPrevAccent, bgFade)

        # Semua balok habis: tampilkan layar Level Complete
        if not listOfBlocks and not paused:
            if winScreen(score):
                # Lanjut ke level berikutnya
                bgPrevAccent = bgAccent
                level += 1
                bgAccent = (level - 1) % len(LEVEL_ACCENTS)
                bgFade = 0.0
                # Kecepatan bola naik sedikit, dibatasi maksimal
                ball.speedUp(SPEED_INCREMENT, MAX_BALL_SPEED)
                listOfBlocks = populateBlocks(
                    blockWidth, blockHeight, horizontalGap, verticalGap,
                    level)
                # Buang power-up yang masih jatuh dari level sebelumnya
                powerUps = []
                particles = []
                floatingTexts = []
                ball.reset(striker)
            else:
                running = False
                continue

        # All the lives are over. So, the gameOver() function is called
        if lives <= 0:
            # Perbarui dan simpan high score sebelum layar game over
            highScore = max(highScore, score)
            saveHighScore(highScore)

            running = gameOver(score)

            # Keluar jika pemain memilih ESC
            if not running:
                continue

            # reset sisa list lalu siapkan permainan baru
            listOfBlocks = []

            lives = 3
            score = 0
            level = 1
            bgAccent = 0
            bgPrevAccent = 0
            bgFade = 1.0
            paused = False
            # Kembalikan kecepatan bola ke kecepatan awal
            ball.resetSpeed(BALL_SPEED)
            # Bersihkan semua efek dan power-up yang tersisa
            powerUps = []
            particles = []
            floatingTexts = []
            paddleTimer = 0
            slowTimer = 0
            strikerFlashTimer = 0
            shakeTimer = 0
            striker.setWidth(PADDLE_WIDTH)
            listOfBlocks = populateBlocks(
                blockWidth, blockHeight, horizontalGap, verticalGap, level)
            ball.reset(striker)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                # Tombol P menjeda dan melanjutkan permainan
                if event.key == pygame.K_p:
                    paused = not paused
                # Tombol M untuk mute/unmute
                if event.key == pygame.K_m:
                    toggleMute()

        # Game hanya diperbarui jika tidak sedang dijeda
        if not paused:
            # Kontrol striker memakai key.get_pressed() agar gerakan
            # tetap mulus walau dua tombol ditekan bergantian
            keys = pygame.key.get_pressed()
            strikerXFac = 0
            if keys[pygame.K_LEFT]:
                strikerXFac -= 1
            if keys[pygame.K_RIGHT]:
                strikerXFac += 1

            # Update striker lebih dulu supaya posisinya terbaru saat tabrakan dicek
            striker.update(strikerXFac)

            # Collision check
            # Bola memantul dari striker sesuai titik pukul
            if(collisionChecker(striker.getRect(),
                                ball.getRect())):
                strikerBounce(ball, striker.getRect())
                # Kilau singkat pada striker saat bola memantul
                strikerFlashTimer = STRIKER_FLASH_TIME
                playSound("bounce")

            # Iterasi salinan list agar aman saat balok dihapus,
            # dan hanya satu balok diproses per frame
            for block in listOfBlocks[:]:
                if(collisionChecker(block.getRect(), ball.getRect())):
                    resolveBlockCollision(ball, block.getRect())
                    block.hit()

                    if block.getHealth() <= 0:
                        # Hapus dari list asli, bukan saat iterasi list asli
                        listOfBlocks.remove(block)
                        # Skor berbeda sesuai jenis balok
                        points = block.getScore()
                        score += points
                        # Perbarui high score berjalan
                        if score > highScore:
                            highScore = score
                        # Suara balok hancur
                        playSound("break")

                        # Partikel kecil sesuai warna balok
                        particleColor = blockColors(
                            block.color, 1.0)[0]
                        for _ in range(PARTICLE_COUNT):
                            particles.append(Particle(
                                block.getRect().centerx,
                                block.getRect().centery,
                                particleColor))

                        # Teks skor melayang di posisi balok
                        floatingTexts.append(FloatingText(
                            block.getRect().centerx,
                            block.getRect().centery,
                            "+" + str(points)))

                        # Peluang sekitar 20% menjatuhkan power-up
                        if random.random() < POWERUP_CHANCE:
                            powerUps.append(PowerUp(
                                block.getRect().centerx,
                                block.getRect().centery,
                                random.choice([POWERUP_PADDLE,
                                               POWERUP_SLOW,
                                               POWERUP_LIFE])))
                    break

            # Update
            lifeLost = ball.update()

            if lifeLost:
                lives -= 1
                ball.reset(striker)
                # Screen shake ringan saat nyawa berkurang
                shakeTimer = SHAKE_TIME
                # Suara nyawa hilang
                playSound("lifeLost")

            # Update power-up: jatuh, diambil striker, atau hilang
            for powerUp in powerUps[:]:
                if powerUp.update():
                    # Hilang karena sudah lewat bawah layar
                    powerUps.remove(powerUp)
                elif collisionChecker(powerUp.getRect(),
                                      striker.getRect()):
                    # Aktifkan efek sesuai jenis power-up
                    if powerUp.kind == POWERUP_PADDLE:
                        striker.setWidth(WIDE_PADDLE_WIDTH)
                        paddleTimer = POWERUP_DURATION
                    elif powerUp.kind == POWERUP_SLOW:
                        ball.applySlow(SLOW_FACTOR)
                        slowTimer = POWERUP_DURATION
                    else:
                        lives = min(lives + 1, MAX_LIVES)
                    powerUps.remove(powerUp)
                    # Suara mengambil power-up
                    playSound("powerup")

            # Timer efek sementara (hanya berjalan saat tidak dijeda)
            if paddleTimer > 0:
                paddleTimer -= 1
                if paddleTimer == 0:
                    striker.setWidth(PADDLE_WIDTH)

            if slowTimer > 0:
                slowTimer -= 1
                if slowTimer == 0:
                    ball.removeSlow()

            # Timer efek visual
            if strikerFlashTimer > 0:
                strikerFlashTimer -= 1

            if shakeTimer > 0:
                shakeTimer -= 1

            # Update partikel dan teks skor melayang
            for particle in particles[:]:
                if particle.update():
                    particles.remove(particle)

            for floatingText in floatingTexts[:]:
                if floatingText.update():
                    floatingTexts.remove(floatingText)

        # Display
        striker.display(strikerFlashTimer > 0)
        ball.display()

        for block in listOfBlocks:
            block.display()

        # Tampilkan power-up yang sedang jatuh
        for powerUp in powerUps:
            powerUp.display()

        # Partikel dan teks skor melayang di atas balok
        for particle in particles:
            particle.display()

        for floatingText in floatingTexts:
            floatingText.display()

        # Top bar tipis: Score (kiri), Level (tengah), High Score (kanan)
        pygame.draw.line(screen, (58, 64, 94),
                         (HUD_MARGIN, HUD_TOP_H),
                         (WIDTH - HUD_MARGIN, HUD_TOP_H), 1)

        scoreLabel = renderTextCached("SCORE", 11, TEXT_DIM, True)
        scoreValue = renderTextCached(str(score), 19, TEXT_SOFT, True)
        screen.blit(scoreLabel, (HUD_MARGIN, 11))
        screen.blit(scoreValue, (HUD_MARGIN - 1, 26))

        levelLabel = renderTextCached("LEVEL", 11, TEXT_DIM, True)
        levelValue = renderTextCached("%02d" % level,
                                      16, TEXT_SOFT, True)
        screen.blit(levelLabel, levelLabel.get_rect(
            center=(WIDTH // 2, 18)))
        screen.blit(levelValue, levelValue.get_rect(
            center=(WIDTH // 2, 37)))

        bestLabel = renderTextCached("HIGH SCORE", 11, TEXT_DIM, True)
        bestValue = renderTextCached(str(highScore), 19, GOLD, True)
        screen.blit(bestLabel, bestLabel.get_rect(
            topright=(WIDTH - HUD_MARGIN, 11)))
        screen.blit(bestValue, bestValue.get_rect(
            topright=(WIDTH - HUD_MARGIN + 1, 26)))

        # Nyawa berupa hati vektor di kiri bawah, tidak menempel tepi
        for i in range(lives):
            drawHeart(HUD_MARGIN + 9 + i * 22, HEIGHT - 16,
                      HEART_SIZE, HEART_COLOR)

        # Status power-up aktif di bawah top bar (tidak menimpa balok)
        statusParts = []
        if paddleTimer > 0:
            statusParts.append("PADDLE " +
                               str((paddleTimer + FPS - 1)//FPS) + "s")
        if slowTimer > 0:
            statusParts.append("SLOW " +
                               str((slowTimer + FPS - 1)//FPS) + "s")

        if statusParts:
            statusText = renderTextCached(
                "  ·  ".join(statusParts), 11, TEXT_DIM, True)
            screen.blit(statusText, (HUD_MARGIN, 61))

        # Indikator mute kecil di kanan bawah
        if muted:
            muteText = renderTextCached("MUTE", 11, TEXT_DIM, True)
            screen.blit(muteText, muteText.get_rect(
                midright=(WIDTH - HUD_MARGIN, HEIGHT - 15)))

        # Tulisan PAUSED saat permainan dijeda
        if paused:
            pausedText = renderTextCached("PAUSED", 34, TEXT_SOFT, True)
            pausedRect = pausedText.get_rect(
                center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(pausedText, pausedRect)

            pauseHint = renderTextCached(
                "TEKAN P UNTUK MELANJUTKAN", 12, TEXT_DIM, True)
            pauseHintRect = pauseHint.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 40))
            screen.blit(pauseHint, pauseHintRect)

        # Efek screen shake ringan: geser seluruh frame sesaat
        if shakeTimer > 0:
            shakeX = random.randint(-SHAKE_STRENGTH, SHAKE_STRENGTH)
            shakeY = random.randint(-SHAKE_STRENGTH, SHAKE_STRENGTH)
            frame = screen.copy()
            drawBackground(bgAccent, bgPrevAccent, bgFade)
            screen.blit(frame, (shakeX, shakeY))

        pygame.display.update()
        clock.tick(FPS)

    # Simpan high score terakhir saat keluar dari game
    saveHighScore(max(highScore, score))


if __name__ == "__main__":
    main()
    pygame.quit()