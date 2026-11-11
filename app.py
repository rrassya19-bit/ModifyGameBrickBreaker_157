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

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Block Breaker")

# to control the frame rate
clock = pygame.time.Clock()
FPS = 30


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

        # The white blocks have the health of 200. So, 
        # the ball must hit it twice to break
        if color == WHITE:
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
def populateBlocks(blockWidth, blockHeight, 
                   horizontalGap, verticalGap):
    listOfBlocks = []

    for i in range(0, WIDTH, blockWidth+horizontalGap):
        for j in range(0, HEIGHT//2, blockHeight+verticalGap):
            listOfBlocks.append(
                Block(i, j, blockWidth, blockHeight, 
                      random.choice([WHITE, GREEN])))

    return listOfBlocks


# Once all the lives are over, this function waits until
# exit or space bar is pressed and does the corresponding action
def gameOver():
    gameOver = True

    while gameOver:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True


# Game Manager
def main():
    running = True
    lives = 3
    score = 0

    scoreText = font.render("score", True, WHITE)
    scoreTextRect = scoreText.get_rect()
    scoreTextRect.center = (20, HEIGHT-10)

    livesText = font.render("Lives", True, WHITE)
    livesTextRect = livesText.get_rect()
    livesTextRect.center = (120, HEIGHT-10)

    striker = Striker(0, HEIGHT-50, 100, 20, 10, WHITE)
    strikerXFac = 0

    ball = Ball(0, HEIGHT-150, 7, 5, WHITE)

    blockWidth, blockHeight = 40, 15
    horizontalGap, verticalGap = 20, 20

    listOfBlocks = populateBlocks(
        blockWidth, blockHeight, horizontalGap, verticalGap)

    # Game loop
    while running:
        screen.fill(BLACK)
        screen.blit(scoreText, scoreTextRect)
        screen.blit(livesText, livesTextRect)

        scoreText = font.render("Score : " + str(score), True, WHITE)
        livesText = font.render("Lives : " + str(lives), True, WHITE)

        # If all the blocks are destroyed, then we repopulate them
        if not listOfBlocks:
            listOfBlocks = populateBlocks(
                blockWidth, blockHeight, horizontalGap, verticalGap)

        # All the lives are over. So, the gameOver() function is called
        if lives <= 0:
            running = gameOver()

            while listOfBlocks:
                listOfBlocks.pop(0)

            lives = 3
            score = 0
            listOfBlocks = populateBlocks(
                blockWidth, blockHeight, horizontalGap, verticalGap)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

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
                    score += 5
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

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
    pygame.quit()