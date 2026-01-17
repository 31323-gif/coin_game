import pygame
import sys
import random
import os
import math

# 初始化 Pygame
pygame.init()

# --- 常數設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "太空捕手 - 豪華進化版 (狀態機架構)"

# 顏色定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (150, 150, 150)
GOLD = (255, 215, 0)
BLUE = (50, 150, 255)
PURPLE = (180, 100, 255)
GREEN = (50, 255, 50)
STAR_YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# 角色與物理設定
PLAYER_SIZE = 120 
PLAYER_SPEED_BASE = 13   
GRAVITY = 0.9      
JUMP_STRENGTH = -18 

# 物件設定
COIN_BASE_SIZE = 140
STAR_SIZE = 70  
FLOWER_SIZE = 80
COIN_SPEED_BASE = 11

# 軌道系統
NUM_LANES = 6
LANE_WIDTH = SCREEN_WIDTH // NUM_LANES

# --- 全局狀態 (存檔/商店數據) ---
total_tokens = 0  
shop_items = {
    'magnet': {'level': 0, 'max': 5, 'cost': 100, 'desc': '磁鐵：吸引金幣範圍'},
    'shield': {'level': 0, 'max': 3, 'cost': 200, 'desc': '護盾：抵擋次數上限'},
    'speed':  {'level': 0, 'max': 10, 'cost': 50, 'desc': '動力：提升基本移動'}
}

# --- 資源管理器 ---
assets = {}

def load_and_clean_assets():
    """載入圖片並進行縮放與去邊處理"""
    to_load = {
        'player': ('player.png', WHITE, 'rect'),
        'player_2': ('player_2.png', BLUE, 'rect'),
        'coin': ('coin.png', GOLD, 'circle'),
        'f_coin': ('f_coin.png', RED, 'circle'),
        'star': ('star.png', STAR_YELLOW, 'star'),
        'flower': ('flower.png', ORANGE, 'flower')
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cwd_dir = os.getcwd()

    for key, (filename, color, shape) in to_load.items():
        if 'player' in key:
            base_size = PLAYER_SIZE
        elif key == 'star' or key == 'flower':
            base_size = STAR_SIZE
        else:
            base_size = COIN_BASE_SIZE

        paths_to_check = [
            os.path.join(script_dir, filename),
            os.path.join(script_dir, 'assets', filename),
            os.path.join(cwd_dir, filename),
            os.path.join(cwd_dir, 'assets', filename),
            filename
        ]
        
        found_path = None
        for path in paths_to_check:
            if os.path.exists(path):
                found_path = path
                break
        
        if found_path:
            try:
                img = pygame.image.load(found_path).convert_alpha()
                orig_w, orig_h = img.get_size()
                aspect_ratio = orig_w / orig_h
                
                if aspect_ratio > 1:
                    target_w = base_size
                    target_h = int(base_size / aspect_ratio)
                else:
                    target_h = base_size
                    target_w = int(base_size * aspect_ratio)
                
                img = pygame.transform.scale(img, (target_w, target_h))
                assets[key] = img
            except:
                create_fallback(key, color, shape, base_size)
        else:
            create_fallback(key, color, shape, base_size)

def create_fallback(key, color, shape, size):
    surf = pygame.Surface([size, size], pygame.SRCALPHA)
    if shape == 'rect':
        pygame.draw.rect(surf, color, [0, 0, size, size], border_radius=15)
        label_text = "P2" if key == "player_2" else "P1"
        try:
            temp_font = pygame.font.SysFont('Arial', 20)
            label = temp_font.render(label_text, True, BLACK)
            surf.blit(label, (size//2 - label.get_width()//2, size//2 - label.get_height()//2))
        except: pass
    elif shape == 'star':
        points = []
        for i in range(10):
            r = size//2 if i % 2 == 0 else size//4
            angle = i * 36
            x = size//2 + r * math.cos(math.radians(angle - 90))
            y = size//2 + r * math.sin(math.radians(angle - 90))
            points.append((x, y))
        pygame.draw.polygon(surf, color, points)
    elif shape == 'flower':
        pygame.draw.circle(surf, RED, (size//2, size//2), size//2)
        pygame.draw.circle(surf, ORANGE, (size//2, size//2), size//3)
        pygame.draw.circle(surf, STAR_YELLOW, (size//2, size//2), size//5)
    else:
        pygame.draw.circle(surf, color, (size // 2, size // 2), size // 2)
    assets[key] = surf

# --- 實體類別 ---

class FireParticle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = random.randint(15, 30)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (random.randint(200, 255), random.randint(50, 150), 0), (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_y = random.uniform(-15, -8)
        self.vel_x = random.uniform(-2, 2)
        self.life = 30
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.life -= 1
        if self.life <= 0:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self, character_key='player'):
        super().__init__()
        self.image = assets[character_key]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.ground_y = SCREEN_HEIGHT - self.rect.height - 20 
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.y = self.ground_y
        self.vel_y = 0
        self.is_jumping = False
        self.base_speed = PLAYER_SPEED_BASE + shop_items['speed']['level'] * 1.5
        self.max_shields = shop_items['shield']['level']
        self.shields = self.max_shields
        self.invincible_timer = 0 
        self.fire_timer = 0

    def update(self, current_score):
        current_speed = self.base_speed + (current_score // 100)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: self.rect.x -= current_speed
        if keys[pygame.K_RIGHT]: self.rect.x += current_speed
        if keys[pygame.K_SPACE] and not self.is_jumping:
            self.vel_y = JUMP_STRENGTH
            self.is_jumping = True

        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        if self.rect.y >= self.ground_y:
            self.rect.y = self.ground_y
            self.vel_y = 0
            self.is_jumping = False

        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH
        
        if self.invincible_timer > 0: self.invincible_timer -= 1
        if self.fire_timer > 0: self.fire_timer -= 1

class FallingObject(pygame.sprite.Sprite):
    def __init__(self, type='coin'):
        super().__init__()
        self.type = type
        self.image = assets[type]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.is_active = False
        self.speed = COIN_SPEED_BASE

    def spawn(self, lane, y_offset, speed_bonus):
        lane_start = lane * LANE_WIDTH
        self.rect.centerx = lane_start + (LANE_WIDTH // 2)
        self.rect.y = -self.rect.height - y_offset
        self.speed = COIN_SPEED_BASE + speed_bonus
        self.is_active = True

    def handle_movement(self, target_player, game_ref):
        if self.is_active:
            if self.type == 'coin' and shop_items['magnet']['level'] > 0:
                dist_x = target_player.rect.centerx - self.rect.centerx
                dist_y = target_player.rect.centery - self.rect.centery
                distance = (dist_x**2 + dist_y**2)**0.5
                magnet_range = 100 + shop_items['magnet']['level'] * 100
                if distance < magnet_range and distance > 5:
                    self.rect.x += (dist_x / distance) * 8
                    self.rect.y += (dist_y / distance) * 4

            self.rect.y += self.speed
            if self.rect.top > SCREEN_HEIGHT:
                self.is_active = False
                if self.type == 'coin':
                    game_ref.score = max(0, game_ref.score - 5)
                    game_ref.combo = 0

class WaveSystem:
    def __init__(self, all_sprites_grp):
        self.coins_group = pygame.sprite.Group()
        self.f_coins_group = pygame.sprite.Group()
        self.stars_group = pygame.sprite.Group()
        self.flowers_group = pygame.sprite.Group()
        self.all_sprites = all_sprites_grp
        self.all_falling_objects = []
        
        # 核心結構：1 顆真金幣
        c = FallingObject('coin')
        self.all_falling_objects.append(c) # index 0
        self.coins_group.add(c)
        self.all_sprites.add(c)
        
        # 假金幣：3 顆 (index 1, 2, 3)
        for _ in range(3):
            f = FallingObject('f_coin')
            self.all_falling_objects.append(f)
            self.f_coins_group.add(f)
            self.all_sprites.add(f)
            
        # 特殊道具：星星 (物件池位置 4)
        s = FallingObject('star')
        self.all_falling_objects.append(s)
        self.stars_group.add(s)
        self.all_sprites.add(s)

        # 特殊道具：火焰花 (物件池位置 5)
        fl = FallingObject('flower')
        self.all_falling_objects.append(fl)
        self.flowers_group.add(fl)
        self.all_sprites.add(fl)

    def update(self, player, game_ref):
        # 檢查核心物件 (1真金+3假金) 是否都失效了才刷下一波
        if not any(obj.is_active for obj in self.all_falling_objects[:4]):
            self.spawn_wave(game_ref.score, player)
        for obj in self.all_falling_objects:
            obj.handle_movement(player, game_ref)

    def spawn_wave(self, current_score, player):
        lanes = random.sample(range(NUM_LANES), NUM_LANES)
        speed_bonus = current_score // 150 
        
        # 記錄被佔用的軌道與高度，防止道具重疊
        occupied_data = []

        # 每一波固定刷出 1 顆真金幣 (index 0) 與 3 顆假金幣 (index 1-3)
        for i in range(4):
            obj = self.all_falling_objects[i]
            lane = lanes[i]
            y_off = random.randint(0, 400)
            obj.spawn(lane, y_off, speed_bonus)
            occupied_data.append({'lane': lane, 'y': obj.rect.y})
            
        # 道具邏輯優化：降低生成機率，且不能在當前效果結束前生成
        prop_chance = 0.10 # 從 0.15 降至 0.10
        
        # 只有在玩家沒有任何特殊效果時，才允許生成新道具
        if player.invincible_timer <= 0 and player.fire_timer <= 0:
            if random.random() < prop_chance:
                # 隨機選擇生成星星或火焰花（互斥）
                prop_to_spawn = random.choice([self.all_falling_objects[4], self.all_falling_objects[5]])
                self.spawn_prop_safely(prop_to_spawn, speed_bonus, occupied_data)

    def spawn_prop_safely(self, prop_obj, speed_bonus, occupied_data):
        for _ in range(10): # 嘗試尋找不衝突位置
            l = random.randint(0, NUM_LANES-1)
            y_o = random.randint(0, 400)
            temp_y = -prop_obj.rect.height - y_o
            
            conflict = False
            for data in occupied_data:
                if data['lane'] == l and abs(data['y'] - temp_y) < 150:
                    conflict = True
                    break
            
            if not conflict:
                prop_obj.spawn(l, y_o, speed_bonus)
                occupied_data.append({'lane': l, 'y': prop_obj.rect.y})
                break

# --- 核心遊戲類別 ---

class SpaceCatcherGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        
        load_and_clean_assets()
        self.setup_fonts()
        
        self.stars_bg = [[random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.random()*2 + 1] for _ in range(50)]
        self.state = "MENU" 
        self.reset_game_state()

    def setup_fonts(self):
        try:
            font_path = pygame.font.match_font('microsoftjhenghei', 'arial')
            self.font_large = pygame.font.Font(font_path, 72)
            self.font_medium = pygame.font.Font(font_path, 36)
            self.font_small = pygame.font.Font(font_path, 24)
        except:
            self.font_large = pygame.font.SysFont('Arial', 72)
            self.font_medium = pygame.font.SysFont('Arial', 36)
            self.font_small = pygame.font.SysFont('Arial', 24)

    def reset_game_state(self):
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.game_over = False
        self.paused = False
        self.selected_char = 'player'
        self.all_sprites = pygame.sprite.Group()
        self.fire_group = pygame.sprite.Group()
        self.player = None
        self.wave_system = None

    def init_playing_session(self):
        self.all_sprites = pygame.sprite.Group()
        self.fire_group = pygame.sprite.Group()
        self.player = Player(self.selected_char)
        self.all_sprites.add(self.player)
        self.wave_system = WaveSystem(self.all_sprites)
        self.score = 0
        self.combo = 0
        self.game_over = False

    def draw_background(self):
        self.screen.fill(BLACK)
        for star in self.stars_bg:
            star[1] += star[2] * 0.5
            if star[1] > SCREEN_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, SCREEN_WIDTH)
            pygame.draw.circle(self.screen, WHITE, (int(star[0]), int(star[1])), 1)

    def draw_text_centered(self, text, y, font, color=WHITE):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH//2, y))
        self.screen.blit(surf, rect)
        return rect

    def handle_menu(self):
        self.draw_background()
        self.draw_text_centered("太空捕手", 100, self.font_large, GOLD)
        self.draw_text_centered(f"總代幣: {total_tokens}", 180, self.font_small, WHITE)
        options = [("1. 開始遊戲", 300), ("2. 進入商店", 380), ("3. 結束程式", 460)]
        buttons = []
        for text, y in options:
            rect = self.draw_text_centered(text, y, self.font_medium, WHITE)
            buttons.append((rect, text))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: self.state = "CHAR_SELECT"
                if event.key == pygame.K_2: self.state = "SHOP"
                if event.key == pygame.K_3: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, text in buttons:
                    if rect.collidepoint(event.pos):
                        if "1" in text: self.state = "CHAR_SELECT"
                        if "2" in text: self.state = "SHOP"
                        if "3" in text: pygame.quit(); sys.exit()

    def handle_shop(self):
        global total_tokens
        self.draw_background()
        self.draw_text_centered("太空物資商店", 50, self.font_large, GOLD)
        self.draw_text_centered(f"目前擁有代幣: {total_tokens}", 130, self.font_medium, WHITE)
        y_offset = 220
        buttons = []
        for key, item in shop_items.items():
            is_max = item['level'] >= item['max']
            color = GREEN if total_tokens >= item['cost'] and not is_max else (GRAY if is_max else RED)
            btn_text = f"{item['desc']} (已達上限)" if is_max else f"{item['desc']} LV:{item['level']} -> 費用: {item['cost']}"
            rect = self.draw_text_centered(btn_text, y_offset, self.font_small, color)
            buttons.append((rect, key))
            y_offset += 70
        self.draw_text_centered("按下 [B] 鍵返回", 520, self.font_small, GRAY)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b: self.state = "MENU" 
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, key in buttons:
                    if rect.collidepoint(event.pos):
                        item = shop_items[key]
                        if total_tokens >= item['cost'] and item['level'] < item['max']:
                            total_tokens -= item['cost']
                            item['level'] += 1
                            item['cost'] = int(item['cost'] * 1.3)

    def handle_char_select(self):
        self.draw_background()
        self.draw_text_centered("選擇你的飛行員", 80, self.font_medium)
        p1_rect = assets['player'].get_rect(center=(SCREEN_WIDTH//3, SCREEN_HEIGHT//2))
        p2_rect = assets['player_2'].get_rect(center=(2*SCREEN_WIDTH//3, SCREEN_HEIGHT//2))
        self.screen.blit(assets['player'], p1_rect)
        self.screen.blit(assets['player_2'], p2_rect)
        sel_rect = p1_rect if self.selected_char == 'player' else p2_rect
        pygame.draw.rect(self.screen, GOLD, sel_rect.inflate(20, 20), 4, border_radius=10)
        self.draw_text_centered("方向鍵選擇 | [空白鍵] 開始任務 | [Esc] 返回", 500, self.font_small, WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT: self.selected_char = 'player'
                if event.key == pygame.K_RIGHT: self.selected_char = 'player_2'
                if event.key == pygame.K_ESCAPE: self.state = "MENU"
                if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    self.init_playing_session(); self.state = "PLAYING"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if p1_rect.collidepoint(event.pos): 
                    self.selected_char = 'player'; self.init_playing_session(); self.state = "PLAYING"
                elif p2_rect.collidepoint(event.pos): 
                    self.selected_char = 'player_2'; self.init_playing_session(); self.state = "PLAYING"

    def handle_playing(self):
        global total_tokens
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if not self.game_over:
                    if event.key == pygame.K_p: self.paused = not self.paused
                    if event.key == pygame.K_s: self.state = "SHOP" 
                else:
                    if event.key == pygame.K_SPACE: self.init_playing_session()
                    if event.key == pygame.K_c or event.key == pygame.K_ESCAPE: self.state = "MENU"

        if not self.game_over and not self.paused:
            self.player.update(self.score)
            self.wave_system.update(self.player, self)
            
            if self.player.fire_timer > 0:
                if random.random() < 0.4:
                    self.fire_group.add(FireParticle(self.player.rect.centerx, self.player.rect.top))
            self.fire_group.update()
            
            for fire in self.fire_group:
                # 火焰清理假金幣 (100% 擊毀機率)
                hits_f = pygame.sprite.spritecollide(fire, self.wave_system.f_coins_group, False, pygame.sprite.collide_mask)
                for h in hits_f:
                    if h.is_active:
                        h.is_active = False
                        self.score += 2 # 清理假金幣有額外獎勵
                
                # 火焰擊中真金幣 (只有 10% 誤傷機率)
                hits_c = pygame.sprite.spritecollide(fire, self.wave_system.coins_group, False, pygame.sprite.collide_mask)
                for h in hits_c:
                    if h.is_active and random.random() < 0.1: # 誤傷率 10%
                        h.is_active = False

            hits_coin = pygame.sprite.spritecollide(self.player, self.wave_system.coins_group, False, pygame.sprite.collide_mask)
            for hit in hits_coin:
                if hit.is_active:
                    self.combo += 1
                    self.max_combo = max(self.max_combo, self.combo)
                    bonus = min(self.combo // 5, 5)
                    self.score += 10 * (1 + bonus)
                    hit.is_active = False 

            hits_star = pygame.sprite.spritecollide(self.player, self.wave_system.stars_group, False, pygame.sprite.collide_mask)
            for hit in hits_star:
                if hit.is_active:
                    self.player.invincible_timer = 300 
                    hit.is_active = False

            hits_flower = pygame.sprite.spritecollide(self.player, self.wave_system.flowers_group, False, pygame.sprite.collide_mask)
            for hit in hits_flower:
                if hit.is_active:
                    self.player.fire_timer = 400 
                    hit.is_active = False

            for f in self.wave_system.f_coins_group:
                if f.is_active and pygame.sprite.collide_mask(self.player, f):
                    if self.player.invincible_timer > 0: f.is_active = False 
                    elif self.player.shields > 0: self.player.shields -= 1; f.is_active = False
                    else: self.game_over = True; total_tokens += self.score 

        self.draw_background()
        if not self.game_over:
            pygame.draw.line(self.screen, GRAY, (0, self.player.ground_y + self.player.rect.height), (SCREEN_WIDTH, self.player.ground_y + self.player.rect.height), 2)
            for f in self.fire_group: self.screen.blit(f.image, f.rect)
            for sprite in self.all_sprites:
                if isinstance(sprite, FallingObject):
                    if sprite.is_active: self.screen.blit(sprite.image, sprite.rect)
                else:
                    if not (self.player.invincible_timer > 0 and (self.player.invincible_timer // 5) % 2 == 0):
                        self.screen.blit(sprite.image, sprite.rect)
            
            if self.player.invincible_timer > 0:
                pygame.draw.circle(self.screen, STAR_YELLOW, self.player.rect.center, 80, 5)
            elif self.player.shields > 0:
                pygame.draw.circle(self.screen, BLUE, self.player.rect.center, 70, 3)
            
            self.screen.blit(self.font_medium.render(f"得分: {self.score}", True, WHITE), (20, 20))
            self.screen.blit(self.font_medium.render(f"連擊: {self.combo}", True, GOLD if self.combo >= 5 else WHITE), (20, 65))
            self.screen.blit(self.font_small.render(f"護盾: {self.player.shields}", True, BLUE), (SCREEN_WIDTH - 150, 20))
            
            if self.player.invincible_timer > 0:
                self.draw_text_centered(f"無敵中! {self.player.invincible_timer // 60}s", 20, self.font_small, STAR_YELLOW)
            if self.player.fire_timer > 0:
                self.draw_text_centered(f"火焰模式! {self.player.fire_timer // 60}s", 50, self.font_small, ORANGE)
            
            self.draw_text_centered("按 [S] 商店 | [P] 暫停", SCREEN_HEIGHT - 30, self.font_small, GRAY)

            if self.paused:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 150))
                self.screen.blit(overlay, (0,0))
                self.draw_text_centered("遊戲暫停", SCREEN_HEIGHT//2 - 20, self.font_large, WHITE)
                self.draw_text_centered("按下 [P] 繼續遊戲", SCREEN_HEIGHT//2 + 60, self.font_small, GRAY)
        else:
            self.draw_text_centered("任務失敗", SCREEN_HEIGHT//2 - 100, self.font_large, RED)
            self.draw_text_centered(f"最終得分: {self.score}", SCREEN_HEIGHT//2, self.font_medium, WHITE)
            self.draw_text_centered("[空白鍵] 重玩 | [C] 回主選單", SCREEN_HEIGHT//2 + 110, self.font_small, GRAY)

    def run(self):
        while True:
            if self.state == "MENU": self.handle_menu()
            elif self.state == "SHOP": self.handle_shop()
            elif self.state == "CHAR_SELECT": self.handle_char_select()
            elif self.state == "PLAYING": self.handle_playing()
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    game = SpaceCatcherGame()
    game.run()