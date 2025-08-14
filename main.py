import pygame
import sys

# === CONFIGURATION ===
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.8
PLAYER_JUMP_SPEED = -15
PLAYER_SPEED = 5
SCROLL_THRESH = 200

# === COLORS ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Retro Mario-Like Platformer")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)


# === GAME CLASSES ===

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 50))
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_y = 0
        self.jumping = False
        self.score = 0
        self.lives = 3
        self.start_x = x
        self.start_y = y

    def update(self, platforms, enemies, coins, scroll):
        dx = 0
        dy = 0
        keys = pygame.key.get_pressed()

        # Horizontal movement
        if keys[pygame.K_LEFT]:
            dx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            dx = PLAYER_SPEED

        # Jumping
        if keys[pygame.K_SPACE] and not self.jumping:
            self.vel_y = PLAYER_JUMP_SPEED
            self.jumping = True

        # Apply gravity
        self.vel_y += GRAVITY
        dy += self.vel_y

        # Collision with platforms
        for platform in platforms:
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                if self.vel_y > 0:
                    dy = platform.rect.top - self.rect.bottom
                    self.vel_y = 0
                    self.jumping = False

        # Update position
        self.rect.x += dx
        self.rect.y += dy

        # Scrolling
        if self.rect.right > SCREEN_WIDTH - SCROLL_THRESH:
            scroll[0] = self.rect.right - (SCREEN_WIDTH - SCROLL_THRESH)
            self.rect.right = SCREEN_WIDTH - SCROLL_THRESH
        elif self.rect.left < SCROLL_THRESH:
            scroll[0] = self.rect.left - SCROLL_THRESH
            self.rect.left = SCROLL_THRESH
        else:
            scroll[0] = 0

        # Enemy collision
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                self.lives -= 1
                self.rect.topleft = (self.start_x, self.start_y)

        # Coin collection
        for coin in coins[:]:
            if self.rect.colliderect(coin.rect):
                self.score += 1
                coins.remove(coin)

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface, scroll):
        surface.blit(self.image, (self.rect.x - scroll[0], self.rect.y))


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, path_length=100):
        super().__init__()
        self.image = pygame.Surface((40, 50))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x = x
        self.move_dir = 1
        self.path_length = path_length

    def update(self):
        self.rect.x += self.move_dir * 2
        if self.rect.x > self.start_x + self.path_length or self.rect.x < self.start_x:
            self.move_dir *= -1

    def draw(self, surface, scroll):
        surface.blit(self.image, (self.rect.x - scroll[0], self.rect.y))


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface, scroll):
        surface.blit(self.image, (self.rect.x - scroll[0], self.rect.y))


# === SETUP LEVEL ===

player = Player(100, 500)
platforms = [
    Platform(0, SCREEN_HEIGHT - 40, 2000, 40),
    Platform(300, 450, 100, 20),
    Platform(450, 350, 100, 20),
    Platform(650, 250, 100, 20),
    Platform(900, 400, 100, 20),
]

enemies = [
    Enemy(500, SCREEN_HEIGHT - 90),
    Enemy(950, 350),
]

coins = [
    Coin(320, 420),
    Coin(470, 320),
    Coin(670, 220),
    Coin(920, 370),
]

scroll = [0]


# === MAIN LOOP ===

def draw_hud():
    score_text = font.render(f"Coins: {player.score}", True, BLACK)
    lives_text = font.render(f"Lives: {player.lives}", True, BLACK)
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (10, 40))


def main():
    while True:
        clock.tick(FPS)
        screen.fill(SKY_BLUE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Update entities
        player.update(platforms, enemies, coins, scroll)
        for enemy in enemies:
            enemy.update()

        # Draw level
        for platform in platforms:
            platform.draw(screen, scroll)

        for coin in coins:
            coin.draw(screen, scroll)

        for enemy in enemies:
            enemy.draw(screen, scroll)

        player.draw(screen)
        draw_hud()

        # Game Over
        if player.lives <= 0:
            game_over_text = font.render("Game Over! Press ESC to quit", True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                pygame.quit()
                sys.exit()

        pygame.display.update()


if __name__ == "__main__":
    main()
