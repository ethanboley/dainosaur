import pygame
import sys
import random
from math import ceil

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)

class Dinosaur:
    def __init__(self):
        self.width_normal = 44
        self.height_normal = 47
        self.width_duck = 59
        self.height_duck = 30
        
        self.x = 50
        self.ground_y = SCREEN_HEIGHT - 20
        self.y = self.ground_y - self.height_normal
        
        self.vel_y = 0
        self.jump_power = -12
        self.gravity = 0.6
        
        self.is_jumping = False
        self.is_ducking = False
        
        self.rect = pygame.Rect(self.x, self.y, self.width_normal, self.height_normal)

    def update(self, keys):
        # Ducking logic
        if keys[pygame.K_DOWN] and not self.is_jumping:
            self.is_ducking = True
        else:
            self.is_ducking = False

        # Jumping logic
        if keys[pygame.K_UP] and not self.is_jumping and not self.is_ducking:
            self.vel_y = self.jump_power
            self.is_jumping = True

        # Apply gravity
        self.vel_y += self.gravity
        self.y += self.vel_y

        # Ground collision
        current_height = self.height_duck if self.is_ducking else self.height_normal
        if self.y > self.ground_y - current_height:
            self.y = self.ground_y - current_height
            self.vel_y = 0
            self.is_jumping = False

        # Update rect
        current_width = self.width_duck if self.is_ducking else self.width_normal
        self.rect = pygame.Rect(self.x, self.y, current_width, current_height)

    def draw(self, screen, color):
        pygame.draw.rect(screen, color, self.rect)
        # Add a small "eye" or detail to make it look slightly more like a dino
        eye_color = WHITE if color == BLACK else BLACK
        eye_rect = pygame.Rect(self.rect.x + self.rect.width - 10, self.rect.y + 5, 5, 5)
        pygame.draw.rect(screen, eye_color, eye_rect)

class Obstacle:
    def __init__(self, x, game_speed, type='cactus', score=0):
        self.type = type
        self.x = x
        self.game_speed = game_speed
        self.is_bird = (type == 'bird')
        self.has_passed = False # Track if dino successfully cleared this
        
        if self.is_bird:
            self.width = 40
            self.height = 30
            # Three heights: 0 (high - run under), 1 (mid - duck or jump), 2 (low - jump)
            h_type = random.randint(0, 2)
            if h_type == 0: self.y = SCREEN_HEIGHT - 150 # Raised to be un-jumpable
            elif h_type == 1: self.y = SCREEN_HEIGHT - 75 # Mid
            else: self.y = SCREEN_HEIGHT - 45 # Low
            
            # Speed logic: After 2000, 50% chance to be slow (game_speed * 0.85)
            if score > 2000 and random.random() < 0.5:
                self.speed = ceil(game_speed * 0.85)
            else:
                self.speed = ceil(game_speed * 1.1)
        else:
            # Cactus clusters
            is_large = random.choice([True, False])
            if is_large:
                self.width = random.randint(1, 2) * 25
                self.height = 50
            else:
                self.width = random.randint(1, 3) * 15
                self.height = 35
            self.y = SCREEN_HEIGHT - 20 - self.height
            self.speed = game_speed

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self):
        self.x -= self.speed
        self.rect.x = self.x

    def draw(self, screen, color):
        pygame.draw.rect(screen, color, self.rect)
        if self.is_bird:
            # Draw wings to differentiate from cactus
            wing_width = 15
            wing_height = 8
            # Top wing
            pygame.draw.rect(screen, color, (self.rect.x + 10, self.rect.y - 10, wing_width, wing_height))
            # Bottom wing
            pygame.draw.rect(screen, color, (self.rect.x + 10, self.rect.y + self.rect.height + 2, wing_width, wing_height))

class DinoGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Chrome Dino Clone")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier", 20, bold=True)
        self.high_score = 0 # Track session high score for rewards
        self.reset()

    def reset(self):
        self.dino = Dinosaur()
        self.obstacles = []
        self.game_speed = 7
        self.score = 0
        self.total_reward = 0 
        self.running = True
        self.bg_color = WHITE
        self.fg_color = BLACK
        self.next_spawn_dist = random.randint(300, 500)
        self.distance_traveled = 0
        return self.get_state()

    def toggle_day_night(self):
        if self.bg_color == WHITE:
            self.bg_color = BLACK
            self.fg_color = WHITE
        else:
            self.bg_color = WHITE
            self.fg_color = BLACK

    def get_state(self):
        # Find the next obstacle
        next_obs = None
        for obs in self.obstacles:
            if obs.x + obs.width > self.dino.x:
                next_obs = obs
                break
        
        if next_obs:
            obs_dist = next_obs.x - self.dino.x
            obs_width = next_obs.width
            obs_y = next_obs.y
            obs_type = 1 if next_obs.is_bird else 0 
            obs_speed = next_obs.speed
        else:
            obs_dist = SCREEN_WIDTH
            obs_width = 0
            obs_y = 0
            obs_type = 0
            obs_speed = self.game_speed

        return [
            self.dino.y / SCREEN_HEIGHT,
            self.dino.vel_y / 15,
            obs_dist / SCREEN_WIDTH,
            obs_width / 100,
            obs_y / SCREEN_HEIGHT,
            obs_type,
            self.game_speed / 20
        ]

    def step(self, action, render=True):
        keys = {pygame.K_UP: False, pygame.K_DOWN: False}
        if action == 1: keys[pygame.K_UP] = True
        if action == 2: keys[pygame.K_DOWN] = True

        if render:
            self.screen.fill(self.bg_color)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        self.score += 1
        if self.game_speed < 20:
            if self.game_speed < 12:
                if self.score % 100 == 0: self.game_speed += 0.2
            elif self.game_speed < 16:
                if self.score % 100 == 0: self.game_speed += 0.1
            else:
                if self.score % 500 == 0: self.game_speed += 0.05
            if self.game_speed > 20: self.game_speed = 20
        
        if self.score > 0 and self.score % 700 == 0:
            self.toggle_day_night()

        was_busy = self.dino.is_jumping or self.dino.is_ducking

        # Find threat BEFORE update for reward context
        next_obs = None
        for obs in self.obstacles:
            if obs.x + obs.width > self.dino.x:
                next_obs = obs
                break

        self.dino.update(keys)

        self.distance_traveled += self.game_speed
        if self.distance_traveled > self.next_spawn_dist:
            obs_type = 'cactus'
            if self.score > 1000 and random.random() < 0.3: obs_type = 'bird'
            self.obstacles.append(Obstacle(SCREEN_WIDTH, self.game_speed, obs_type, self.score))
            self.distance_traveled = 0
            self.next_spawn_dist = random.randint(350, 750) + (self.game_speed * 10)

        reward = 0.01 
        
        if not was_busy:
            if action == 1: # JUMP
                is_justified = False
                if next_obs:
                    frames_to_hit = (next_obs.x - self.dino.x) / self.game_speed
                    if 12 < frames_to_hit < 28 and not (next_obs.is_bird and next_obs.y < SCREEN_HEIGHT - 120):
                        is_justified = True
                reward += 3.0 if is_justified else -5.0
            elif action == 2: # DUCK
                is_justified = False
                if next_obs:
                    frames_to_hit = (next_obs.x - self.dino.x) / self.game_speed
                    if 5 < frames_to_hit < 35 and next_obs.is_bird and next_obs.y == SCREEN_HEIGHT - 75:
                        is_justified = True
                reward += 1.2 if is_justified else -3.0
        
        if self.dino.is_jumping or self.dino.is_ducking:
            reward -= 0.01
        
        done = False
        for obstacle in self.obstacles[:]:
            obstacle.update()
            if not obstacle.has_passed and obstacle.x + obstacle.width < self.dino.x:
                obstacle.has_passed = True
                if self.dino.is_jumping: reward = 4.0 
                elif self.dino.is_ducking: reward = 5.0 
                else: reward = 3.0 
            if obstacle.x < -obstacle.width:
                self.obstacles.remove(obstacle)
            if self.dino.rect.colliderect(obstacle.rect):
                inner_rect = self.dino.rect.inflate(-10, -10)
                if inner_rect.colliderect(obstacle.rect):
                    if self.score > self.high_score:
                        self.high_score = self.score
                        reward = 5.0 + (self.score // 100)
                        print(f"NEW RECORD: {self.high_score}! Reward: +{reward:.2f}")
                    else:
                        reward = -10.0 
                    done = True
                    self.running = False

        self.total_reward += reward

        if render:
            pygame.draw.line(self.screen, self.fg_color, (0, SCREEN_HEIGHT - 20), (SCREEN_WIDTH, SCREEN_HEIGHT - 20), 2)
            self.dino.draw(self.screen, self.fg_color)
            for obstacle in self.obstacles: obstacle.draw(self.screen, self.fg_color)
            score_text = self.font.render(str(self.score).zfill(5), True, self.fg_color)
            self.screen.blit(score_text, (SCREEN_WIDTH - 80, 20))
            # Diagnostics
            self.screen.blit(self.font.render(f"Speed: {self.game_speed:.2f}", True, GRAY), (20, 20))
            self.screen.blit(self.font.render(f"Reward: {reward:.2f}", True, GRAY), (20, 45))
            self.screen.blit(self.font.render(f"Total: {self.total_reward:.2f}", True, GRAY), (20, 70))
            pygame.display.flip()
            self.clock.tick(FPS)

        return self.get_state(), reward, done

if __name__ == "__main__":
    game = DinoGame()
    while True:
        state = game.reset()
        done = False
        while not done:
            keys = pygame.key.get_pressed()
            action = 0
            if keys[pygame.K_UP]: action = 1
            if keys[pygame.K_DOWN]: action = 2
            _, _, done = game.step(action)
        # Game over loop logic omitted for brevity in standalone run
