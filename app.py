import pygame
import random

pygame.init()

# Dimensions of the screen
WIDTH, HEIGHT = 600, 500

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 140, 0)

# Tema warna tampilan
DARK_BLUE = (14, 20, 55)
DARK_PURPLE = (52, 16, 78)
BLOCK_DARK = (25, 28, 45)
BLOCK_BORDER = (12, 14, 26)
BLOCK_GREEN_TOP = (120, 255, 150)
BLOCK_GREEN_BOTTOM = (20, 160, 70)
BLOCK_WHITE_TOP = (245, 248, 255)
BLOCK_WHITE_BOTTOM = (175, 190, 215)
BLOCK_RED_TOP = (255, 140, 140)
BLOCK_RED_BOTTOM = (180, 25, 45)
STRIKER_COLOR = (60, 170, 255)
STRIKER_HIGHLIGHT = (170, 220, 255)
STRIKER_BORDER = (220, 240, 255)
BALL_GLOW = (90, 200, 255)
BALL_TRAIL = (140, 210, 255)

font = pygame.font.Font('freesansbold.ttf', 15)

# Font lebih besar untuk judul dan layar status
titleFont = pygame.font.Font('freesansbold.ttf', 40)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Block Breaker")

# to control the frame rate
clock = pygame.time.Clock()
FPS = 30

# Kecepatan awal bola dan batas maksimal kecepatannya
BALL_SPEED = 5
MAX_BALL_SPEED = 9

# Pengaturan power-up
POWERUP_CHANCE = 0.2
POWERUP_DURATION = 8 * FPS
PADDLE_WIDTH = 100
WIDE_PADDLE_WIDTH = 160
SLOW_FACTOR = 0.6
MAX_LIVES = 5

# Jenis power-up dan warnanya
POWERUP_PADDLE = "paddle"
POWERUP_SLOW = "slow"
POWERUP_LIFE = "life"
POWERUP_COLORS = {
    POWERUP_PADDLE: BLUE,
    POWERUP_SLOW: YELLOW,
    POWERUP_LIFE: ORANGE
}

# Pengaturan tampilan
BLOCK_RADIUS = 4
BALL_TRAIL_LENGTH = 8

# Cache permukaan balok agar gradasi tidak dibuat ulang tiap frame
blockSurfaceCache = {}


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


# Membuat permukaan gradasi vertikal dengan sudut membulat
def createRoundedGradientSurface(width, height,
                                 topColor, bottomColor, radius):
    gradient = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        factor = y / max(1, height - 1)
        pygame.draw.line(gradient, blendColor(topColor, bottomColor, factor),
                         (0, y), (width, y))

    # Masking sudut membulat
    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                     border_radius=radius)
    gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return gradient


# Warna balok sesuai jenis dan sisa health
def blockColors(color, healthRatio):
    if color == RED:
        topColor, bottomColor = BLOCK_RED_TOP, BLOCK_RED_BOTTOM
    elif color == WHITE:
        topColor, bottomColor = BLOCK_WHITE_TOP, BLOCK_WHITE_BOTTOM
    else:
        topColor, bottomColor = BLOCK_GREEN_TOP, BLOCK_GREEN_BOTTOM

    # Semakin kecil health, warna makin gelap
    darken = 0.45 + 0.55 * healthRatio
    return (blendColor(topColor, BLOCK_DARK, 1 - darken),
            blendColor(bottomColor, BLOCK_DARK, 1 - darken))


# Mengambil permukaan balok dari cache (dibuat sekali per warna/health)
def getBlockSurface(color, healthRatio, width, height):
    key = (color, round(healthRatio, 2), width, height)
    if key not in blockSurfaceCache:
        topColor, bottomColor = blockColors(color, healthRatio)
        blockSurfaceCache[key] = createRoundedGradientSurface(
            width, height, topColor, bottomColor, BLOCK_RADIUS)
    return blockSurfaceCache[key]


# Membuat efek glow bola sekali saja
def createGlowSurface(radius):
    size = radius * 6
    glow = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    for glowRadius, alpha in ((radius * 3, 25),
                              (radius * 2, 45),
                              (radius + 2, 90)):
        pygame.draw.circle(glow, (BALL_GLOW[0], BALL_GLOW[1],
                                  BALL_GLOW[2], alpha),
                           (center, center), glowRadius)
    return glow


# Background gradasi dibuat sekali, lalu di-blit tiap frame
backgroundSurface = createGradientSurface(DARK_BLUE, DARK_PURPLE, HEIGHT)


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
    def display(self):
        # Striker dengan sudut membulat dan warna tema
        pygame.draw.rect(screen, STRIKER_COLOR, self.strikerRect,
                         border_radius=8)

        # Kilau di bagian atas agar terlihat lebih menarik
        highlight = pygame.Rect(self.strikerRect.x + 5,
                                self.strikerRect.y + 3,
                                self.strikerRect.width - 10, 5)
        pygame.draw.rect(screen, STRIKER_HIGHLIGHT, highlight,
                         border_radius=3)

        # Garis tepi tipis
        pygame.draw.rect(screen, STRIKER_BORDER, self.strikerRect, 2,
                         border_radius=8)

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

            # Garis tepi tipis
            pygame.draw.rect(screen, BLOCK_BORDER, self.blockRect, 1,
                             border_radius=BLOCK_RADIUS)

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

        # Jejak bola dan efek glow (tampilan saja)
        self.trail = []
        self.glow = createGlowSurface(self.radius)

        self.ball = pygame.draw.circle(
            screen, self.color, (self.posx,
                                 self.posy), self.radius)

    # Used to display the object on the screen
    def display(self):
        # Glow di belakang bola
        screen.blit(self.glow,
                    (self.posx - self.glow.get_width()//2,
                     self.posy - self.glow.get_height()//2))

        # Jejak bola, makin lama makin pudar dan kecil
        for i, (trailX, trailY) in enumerate(self.trail):
            factor = (i + 1) / (len(self.trail) + 1)
            trailColor = blendColor(BALL_TRAIL, DARK_PURPLE, 1 - factor)
            radius = max(2, int(self.radius * factor))
            pygame.draw.circle(screen, trailColor,
                               (int(trailX), int(trailY)), radius)

        # Bola utama
        self.ball = pygame.draw.circle(
            screen, self.color, (int(self.posx),
                                 int(self.posy)), self.radius)

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

        # Reflection from the top most edge of the screen
        if self.posy <= 0:
            self.yFac *= -1

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
        self.width, self.height = 26, 12
        self.speed = 3
        self.kind = kind
        self.color = POWERUP_COLORS[kind]

        # Rect dipakai untuk deteksi tabrakan dengan striker
        self.powerUpRect = pygame.Rect(
            self.posx - self.width//2, self.posy,
            self.width, self.height)

    # Menampilkan power-up sebagai kapsul berwarna
    def display(self):
        pygame.draw.rect(screen, self.color, self.powerUpRect,
                         border_radius=6)

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
# Pola balok berganti tiap level dan berulang setelah 3 pola
def populateBlocks(blockWidth, blockHeight, 
                   horizontalGap, verticalGap, level):
    listOfBlocks = []

    columnCount = len(range(0, WIDTH, blockWidth+horizontalGap))
    rowCount = len(range(0, HEIGHT//2, blockHeight+verticalGap))

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

            posx = column * (blockWidth+horizontalGap)
            posy = row * (blockHeight+verticalGap)

            # Jenis balok acak: hijau (1x), putih (2x), merah (3x)
            listOfBlocks.append(
                Block(posx, posy, blockWidth, blockHeight, 
                      random.choice([WHITE, GREEN, RED])))

    return listOfBlocks


# Layar awal dengan judul game dan petunjuk mulai
def startScreen():
    while True:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True

        screen.blit(backgroundSurface, (0, 0))

        titleText = titleFont.render("BLOCK BREAKER", True, WHITE)
        titleRect = titleText.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        screen.blit(titleText, titleRect)

        startText = font.render("Tekan SPACE untuk mulai", True, GREEN)
        startRect = startText.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
        screen.blit(startText, startRect)

        pygame.display.update()
        clock.tick(FPS)


# Once all the lives are over, this function waits until
# exit or space bar is pressed and does the corresponding action
def gameOver(score):
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

        screen.blit(backgroundSurface, (0, 0))

        overText = titleFont.render("GAME OVER", True, RED)
        overRect = overText.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        screen.blit(overText, overRect)

        finalScoreText = font.render(
            "Skor akhir : " + str(score), True, WHITE)
        finalScoreRect = finalScoreText.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 - 10))
        screen.blit(finalScoreText, finalScoreRect)

        hintText = font.render(
            "Tekan SPACE untuk main lagi / ESC untuk keluar", True, WHITE)
        hintRect = hintText.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
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

        screen.blit(backgroundSurface, (0, 0))

        winText = titleFont.render("YOU WIN", True, GREEN)
        winRect = winText.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70))
        screen.blit(winText, winRect)

        completeText = font.render("Level Complete", True, WHITE)
        completeRect = completeText.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 - 25))
        screen.blit(completeText, completeRect)

        finalScoreText = font.render(
            "Skor : " + str(score), True, WHITE)
        finalScoreRect = finalScoreText.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 + 10))
        screen.blit(finalScoreText, finalScoreRect)

        hintText = font.render(
            "Tekan SPACE untuk lanjut / ESC untuk keluar", True, WHITE)
        hintRect = hintText.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(hintText, hintRect)

        pygame.display.update()
        clock.tick(FPS)


# Menggambar ikon hati kecil untuk HUD nyawa
def drawHeart(cx, cy, size, color):
    radius = size // 2

    # Dua lingkaran sebagai lengkung atas hati
    pygame.draw.circle(screen, color,
                       (cx - radius // 2, cy - radius // 2),
                       radius // 2 + 1)
    pygame.draw.circle(screen, color,
                       (cx + radius // 2, cy - radius // 2),
                       radius // 2 + 1)

    # Segitiga sebagai ujung bawah hati
    pygame.draw.polygon(screen, color, [
        (cx - radius, cy - radius // 3),
        (cx + radius, cy - radius // 3),
        (cx, cy + radius)])


# Game Manager
def main():
    running = True
    lives = 3
    score = 0
    level = 1

    striker = Striker(0, HEIGHT-50, PADDLE_WIDTH, 20, 10, WHITE)
    strikerXFac = 0

    ball = Ball(0, HEIGHT-150, 7, BALL_SPEED, WHITE)

    blockWidth, blockHeight = 40, 15
    horizontalGap, verticalGap = 20, 20

    listOfBlocks = populateBlocks(
        blockWidth, blockHeight, horizontalGap, verticalGap, level)

    powerUps = []
    paddleTimer = 0
    slowTimer = 0

    # Tampilkan layar awal sebelum permainan dimulai
    if not startScreen():
        return

    # Bola mulai dari atas striker saat permainan dimulai
    ball.reset(striker)
    paused = False

    # Game loop
    while running:
        screen.blit(backgroundSurface, (0, 0))

        # Semua balok habis: tampilkan layar Level Complete
        if not listOfBlocks and not paused:
            if winScreen(score):
                # Lanjut ke level berikutnya
                level += 1
                # Kecepatan bola naik sedikit, dibatasi maksimal
                ball.speedUp(0.5, MAX_BALL_SPEED)
                listOfBlocks = populateBlocks(
                    blockWidth, blockHeight, horizontalGap, verticalGap,
                    level)
                # Buang power-up yang masih jatuh dari level sebelumnya
                powerUps = []
                ball.reset(striker)
            else:
                running = False
                continue

        # All the lives are over. So, the gameOver() function is called
        if lives <= 0:
            running = gameOver(score)

            # Keluar jika pemain memilih ESC
            if not running:
                continue

            # reset sisa list lalu siapkan permainan baru
            listOfBlocks = []

            lives = 3
            score = 0
            level = 1
            paused = False
            # Kembalikan kecepatan bola ke kecepatan awal
            ball.resetSpeed(BALL_SPEED)
            # Bersihkan semua efek dan power-up yang tersisa
            powerUps = []
            paddleTimer = 0
            slowTimer = 0
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
                        score += block.getScore()

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

            # Timer efek sementara (hanya berjalan saat tidak dijeda)
            if paddleTimer > 0:
                paddleTimer -= 1
                if paddleTimer == 0:
                    striker.setWidth(PADDLE_WIDTH)

            if slowTimer > 0:
                slowTimer -= 1
                if slowTimer == 0:
                    ball.removeSlow()

        # Display
        striker.display()
        ball.display()

        for block in listOfBlocks:
            block.display()

        # Tampilkan power-up yang sedang jatuh
        for powerUp in powerUps:
            powerUp.display()

        # HUD dirender setelah state terbaru dihitung, lalu langsung
        # digambar di frame yang sama agar tidak tertinggal satu frame
        # Skor di kiri bawah
        scoreText = font.render("Score : " + str(score), True, WHITE)
        scoreTextRect = scoreText.get_rect()
        scoreTextRect.bottomleft = (10, HEIGHT - 6)
        screen.blit(scoreText, scoreTextRect)

        # Level di tengah bawah
        levelText = font.render("Level : " + str(level), True, WHITE)
        levelTextRect = levelText.get_rect()
        levelTextRect.midbottom = (WIDTH // 2, HEIGHT - 6)
        screen.blit(levelText, levelTextRect)

        # Nyawa sebagai ikon hati di kanan bawah (berjajar dari kanan)
        for i in range(lives):
            drawHeart(WIDTH - 18 - i * 20, HEIGHT - 18, 14, RED)

        # Status power-up aktif di kiri atas HUD
        statusParts = []
        if paddleTimer > 0:
            statusParts.append("Paddle Besar " +
                               str((paddleTimer + FPS - 1)//FPS) + "s")
        if slowTimer > 0:
            statusParts.append("Slow Ball " +
                               str((slowTimer + FPS - 1)//FPS) + "s")

        if statusParts:
            statusText = font.render(
                " | ".join(statusParts), True, YELLOW)
            statusRect = statusText.get_rect(topleft=(8, 6))
            # Latar hitam agar teks tetap terbaca di atas balok
            pygame.draw.rect(screen, BLACK, statusRect.inflate(8, 4))
            screen.blit(statusText, statusRect)

        # Tulisan PAUSED saat permainan dijeda
        if paused:
            pausedText = titleFont.render("PAUSED", True, WHITE)
            pausedRect = pausedText.get_rect(
                center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(pausedText, pausedRect)

            pauseHint = font.render(
                "Tekan P untuk melanjutkan", True, WHITE)
            pauseHintRect = pauseHint.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 40))
            screen.blit(pauseHint, pauseHintRect)

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
    pygame.quit()