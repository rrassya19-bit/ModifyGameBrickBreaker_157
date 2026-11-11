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
        self.striker = pygame.draw.rect(screen, 
                            self.color, self.strikerRect)

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
            self.brick = pygame.draw.rect(screen, 
                                self.color, self.blockRect)

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
        self.color = color
        self.xFac, self.yFac = 1, 1

        self.ball = pygame.draw.circle(
            screen, self.color, (self.posx,
                                 self.posy), self.radius)

    # Used to display the object on the screen
    def display(self):
        self.ball = pygame.draw.circle(
            screen, self.color, (self.posx, 
                                 self.posy), self.radius)

    # Used to update the state of the object
    def update(self):
        self.posx += self.xFac*self.speed
        self.posy += self.yFac*self.speed

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

    # Used to change the direction along Y axis
    def hit(self):
        self.yFac *= -1

    # Used to change the direction along X axis
    # Dipakai saat bola menabrak sisi samping balok
    def hitSide(self):
        self.xFac *= -1

    # Menambah kecepatan bola sedikit tiap level, dibatasi maksimal
    def speedUp(self, amount, maxSpeed):
        self.speed = min(self.speed + amount, maxSpeed)

    # Returns the rect of the ball based on its
    # current position, so collision is always up to date
    def getRect(self):
        return pygame.Rect(self.posx - self.radius,
                           self.posy - self.radius,
                           self.radius * 2, self.radius * 2)

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

        screen.fill(BLACK)

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

        screen.fill(BLACK)

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

        screen.fill(BLACK)

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

    striker = Striker(0, HEIGHT-50, 100, 20, 10, WHITE)
    strikerXFac = 0

    ball = Ball(0, HEIGHT-150, 7, BALL_SPEED, WHITE)

    blockWidth, blockHeight = 40, 15
    horizontalGap, verticalGap = 20, 20

    listOfBlocks = populateBlocks(
        blockWidth, blockHeight, horizontalGap, verticalGap, level)

    # Tampilkan layar awal sebelum permainan dimulai
    if not startScreen():
        return

    # Bola mulai dari atas striker saat permainan dimulai
    ball.reset(striker)
    paused = False

    # Game loop
    while running:
        screen.fill(BLACK)

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
            ball.speed = BALL_SPEED
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
                    break

            # Update
            lifeLost = ball.update()

            if lifeLost:
                lives -= 1
                ball.reset(striker)

        # Display
        striker.display()
        ball.display()

        for block in listOfBlocks:
            block.display()

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