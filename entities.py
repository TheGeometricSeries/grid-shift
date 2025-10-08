import pygame
import random
import math
from config import *
from utils import has_line_of_sight

class Particle:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.size = random.randint(4, 7)
        self.vel = pygame.Vector2(random.uniform(-2, 2), random.uniform(-3, -1))
        self.lifespan = 20
    def update(self):
        self.pos += self.vel; self.lifespan -= 1
    def draw(self, screen, camera_x, camera_y):
        pygame.draw.rect(screen, DIRT_COLOR, (self.pos.x-camera_x, self.pos.y-camera_y, self.size, self.size))

class Tile:
    def __init__(self, x, y, tile_type):
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.type = tile_type
        if self.type == 3: # 타입이 3(돌)이면
            self.max_health = 200 # 체력을 200으로 설정 (흙보다 2배 단단함)
        #elif self.type == ?:
        #    self.max_health = 300
        else:
            self.max_health = 100 # 나머지는 100
        
        self.health = self.max_health
        self.crack_lines = None
        self.time_covered = 0

    def draw(self, screen, camera_x, camera_y, world_grid, x, y):
        screen_x, screen_y = self.rect.x - camera_x, self.rect.y - camera_y
        # 타일 타입에 따라 기본 색상을 결정
        if self.type == 1 or self.type == 2: # 흙 또는 잔디
            block_color = DIRT_COLOR
        elif self.type == 3: # 돌
            block_color = STONE_COLOR
        else: # 혹시 모를 기본값
            block_color = DIRT_COLOR
            
        pygame.draw.rect(screen, block_color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        
        # 잔디 블록이면 위에 잔디를 덧그림 (기존과 동일)
        if self.type == 2:
            pygame.draw.rect(screen, GRASS_COLOR, (screen_x, screen_y, TILE_SIZE, 10))
        if self.health < self.max_health and self.crack_lines:
            crack_progress = 1 - (self.health / self.max_health)
            lines_to_draw = int(len(self.crack_lines) * crack_progress)
            for i in range(lines_to_draw):
                start_pos = self.crack_lines[i][0]; end_pos = self.crack_lines[i][1]
                pygame.draw.line(screen, CRACK_COLOR, (start_pos.x + screen_x, start_pos.y + screen_y), (end_pos.x + screen_x, end_pos.y + screen_y), 2)
            
    def take_damage(self, amount):
        if self.health == self.max_health: self._generate_crack()
        self.health -= amount
        return self.health <= 0
    
    def _generate_crack(self):
        self.crack_lines = []
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top': point = pygame.Vector2(random.randint(0, TILE_SIZE), 0)
        elif edge == 'bottom': point = pygame.Vector2(random.randint(0, TILE_SIZE), TILE_SIZE)
        elif edge == 'left': point = pygame.Vector2(0, random.randint(0, TILE_SIZE))
        else: point = pygame.Vector2(TILE_SIZE, random.randint(0, TILE_SIZE))
        center_point = pygame.Vector2(TILE_SIZE/2, TILE_SIZE/2)
        direction_vector = center_point - point
        angle = direction_vector.angle_to(pygame.Vector2(1, 0))
        for _ in range(15):
            start_point = point.copy()
            angle += random.uniform(-45, 45)
            length = random.uniform(5, 10)
            point.x += length * math.cos(math.radians(angle))
            point.y -= length * math.sin(math.radians(angle))
            point.x = max(0, min(TILE_SIZE, point.x))
            point.y = max(0, min(TILE_SIZE, point.y))
            end_point = point.copy()
            self.crack_lines.append((start_point, end_point))

class Entity:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.vel = pygame.Vector2(0, 0)
        self.is_on_ground, self.jump_count = False, 0
        self.friction, self.gravity = 0.88, 0.6
        self.max_health = 100
        self.health = self.max_health
        self.fall_start_y = None # ✨ 낙하 시작 높이 기록 변수 추가

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0: self.health = 0

    def apply_friction(self):
        """땅 위에 있을 때만 마찰력을 적용합니다."""
        if self.is_on_ground:
            self.vel.x *= self.friction
            # 속도가 매우 느려지면 완전히 멈추도록 처리
            if abs(self.vel.x) < 0.1:
                self.vel.x = 0

    def update_physics(self, colliders):
        # 1. 가로 방향 움직임 및 충돌 처리
        self.rect.x += self.vel.x
        for collider in colliders:
            if self.rect.colliderect(collider):
                if self.vel.x > 0: # 오른쪽으로 이동 중 충돌
                    self.rect.right = collider.left
                elif self.vel.x < 0: # 왼쪽으로 이동 중 충돌
                    self.rect.left = collider.right
        
        # 2. 낙하 감지
        # 땅에 있지 않고, 아래로 떨어지는 중이며, 아직 낙하 시작점을 기록하지 않았다면
        if not self.is_on_ground and self.vel.y > 0 and self.fall_start_y is None:
            self.fall_start_y = self.rect.bottom # 현재 발밑 높이를 기록

        # 3. 세로 방향 움직임 (중력 적용)
        self.vel.y += self.gravity
        self.rect.y += self.vel.y
        self.is_on_ground = False # 매번 초기화

        # 4. 세로 방향 충돌 처리
        for collider in colliders:
            if self.rect.colliderect(collider):
                # 아래로 떨어지다 충돌 (착지)
                if self.vel.y > 0:
                    self.rect.bottom = collider.top
                    self.is_on_ground = True
                    self.jump_count = 0
                    self.vel.y = 0

                    # ✨ 착지 시 낙하 데미지 계산 ✨
                    if self.fall_start_y is not None:
                        fall_distance = self.rect.bottom - self.fall_start_y
                        if fall_distance > SAFE_FALL_DISTANCE:
                            damage = (fall_distance - SAFE_FALL_DISTANCE) * FALL_DAMAGE_SCALAR
                            self.take_damage(damage)
                            print(f"낙하! 거리: {fall_distance:.0f}, 데미지: {damage:.1f}") # 디버깅용 출력
                        self.fall_start_y = None # 낙하 상태 초기화

                # 위로 점프하다 충돌 (천장에 닿음)
                elif self.vel.y < 0:
                    self.rect.top = collider.bottom
                    self.vel.y = 0
        
        # 만약 땅에 닿았다면, 낙하 상태를 확실히 초기화
        if self.is_on_ground:
            self.fall_start_y = None

class Debris(Entity):
    def __init__(self, x, y, width, height, color):
        super().__init__(x, y, width, height)
        self.color = color
        self.vel = pygame.Vector2(random.uniform(-8, 8), random.uniform(-15, -5))
        self.friction = 0.7 # ✨ 강한 마찰력 설정 (값이 낮을수록 강함)

    def update(self, colliders):
        self.update_physics(colliders)
        self.apply_friction() # ✨ 마찰력 적용

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.rect(screen, self.color, (self.rect.x - camera_x, self.rect.y - camera_y, self.rect.width, self.rect.height))


class ItemDrop(Entity):
    def __init__(self, x, y, item_type):
        size = 15
        super().__init__(x - size/2, y - size/2, size, size)
        self.item_type = item_type
        self.vel = pygame.Vector2(random.uniform(-1.5, 1.5), random.uniform(-4, -1))
        self.angle = 0
        self.angular_velocity = 0
        self.friction = 0.7 # ✨ 강한 마찰력 설정

    def update(self, colliders, player):
        # 1. 아이템과 플레이어의 각 신체 부위 위치를 가져옵니다.
        item_pos = pygame.math.Vector2(self.rect.center)
        head_pos = pygame.math.Vector2(player.head_rect.center)
        torso_pos = pygame.math.Vector2(player.torso_rect.center)
        feet_pos = pygame.math.Vector2(player.rect.centerx, player.rect.bottom - 5)

        # 2. 아이템과 세 지점 사이의 거리를 각각 계산합니다.
        distance_to_head = item_pos.distance_to(head_pos)
        distance_to_torso = item_pos.distance_to(torso_pos)
        distance_to_feet = item_pos.distance_to(feet_pos)

        # 3. 세 거리 중 하나라도 자석 반경 안에 들어오는지 확인합니다.
        is_in_magnet_range = (
            distance_to_head < ITEM_MAGNET_RADIUS or
            distance_to_torso < ITEM_MAGNET_RADIUS or
            distance_to_feet < ITEM_MAGNET_RADIUS
        )

        # 4. 자석 반경 안에 있다면, '몸통'을 목표로 아이템을 끌어당깁니다.
        if is_in_magnet_range:
            pull_target = torso_pos # 목표 지점은 몸통 중심
            direction = pull_target - item_pos
            if direction.length() > 0:
                direction.normalize_ip()
            
            self.vel = direction * ITEM_MAGNET_SPEED
            self.rect.x += self.vel.x
            self.rect.y += self.vel.y
            self.angular_velocity = 0

        # 5. 반경 밖에 있다면, 일반 물리 로직(중력, 충돌, 마찰)을 실행합니다.
        else:
            self.update_physics(colliders) # 중력 및 충돌
            self.apply_friction()         # 마찰력 (미끄러짐 방지)

            # 회전 로직 (구르는 효과는 없음)
            self.angle += self.angular_velocity
            self.angular_velocity *= 0.95
            if abs(self.angular_velocity) < 0.05:
                self.angular_velocity = 0

    def check_stability(self, potential_supporters):
        # 1. 공중에 떠 있다면 안정성 검사를 할 필요가 없음
        if not self.is_on_ground:
            return

        # 2. 아이템 바로 아래에 받침대가 있는지 찾아봄
        my_feet_rect = self.rect.move(0, 1)
        supporters = [s for s in potential_supporters if my_feet_rect.colliderect(s)]

        # 3. 받침대가 있는 경우에만 안정성 검사를 수행
        if supporters:
            # 받침대의 왼쪽 끝과 오른쪽 끝 좌표를 구함
            support_min_x = min(s.left for s in supporters)
            support_max_x = max(s.right for s in supporters)
            
            # 아이템의 중심이 받침대 범위를 벗어났는지 확인
            is_unstable = self.rect.centerx < support_min_x or self.rect.centerx > support_max_x
            
            # 만약 불안정하다면 회전력을 적용
            if is_unstable:
                torque = 0.5 # 회전력
                if self.rect.centerx < support_min_x:
                    self.angular_velocity -= torque
                else:
                    self.angular_velocity += torque
        
        # 4. 받침대가 전혀 없는 경우 (낭떠러지에서 완전히 밀려난 경우)
        else:
            self.is_on_ground = False # 아래로 떨어지기 시작
    
    def draw(self, screen, camera_x, camera_y):
        # 1. 원본 이미지 서피스를 만듭니다. (매번 만들지 않고 __init__에서 만들어두는 게 더 효율적)
        original_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        if self.item_type == "grass":
            color = GRASS_COLOR
        elif self.item_type == "stone":
            color = STONE_COLOR
        else: # 기본값은 흙
            color = DIRT_COLOR
        pygame.draw.rect(original_surf, color, original_surf.get_rect())
        pygame.draw.rect(original_surf, BLACK, original_surf.get_rect(), 2)

        # 2. 원본 이미지를 현재 각도(self.angle)만큼 회전시킵니다.
        rotated_surf = pygame.transform.rotate(original_surf, self.angle)

        # 3. 회전된 이미지의 새 사각 영역을 얻고, 중심점을 아이템의 실제 위치에 맞춥니다.
        rotated_rect = rotated_surf.get_rect(center = self.rect.center)

        # 4. 최종적으로 회전된 이미지를 화면에 그립니다. (카메라 위치 반영)
        screen.blit(rotated_surf, (rotated_rect.x - camera_x, rotated_rect.y - camera_y))

class Player(Entity):
    def __init__(self, x, y, width, height):
        self.scale_factor = 0.7
        self.leg_length = int(40 * self.scale_factor)
        self.torso_height = int(50*self.scale_factor)
        player_width = int(30 * self.scale_factor)
        player_height = self.leg_length + self.torso_height
        super().__init__(x, y, player_width, player_height)
        self.friction = 0.88

        self.torso_rect = pygame.Rect(0,0,self.rect.width,self.torso_height)
        self.head_rect = pygame.Rect(0,0,int(25*self.scale_factor),int(25*self.scale_factor))
        self.left_arm_rect = pygame.Rect(0,0,int(10*self.scale_factor),int(35*self.scale_factor))
        self.right_arm_rect = pygame.Rect(0,0,int(10*self.scale_factor),int(35*self.scale_factor))
        self.left_leg_rect = pygame.Rect(0,0,int(12*self.scale_factor),self.leg_length)
        self.right_leg_rect = pygame.Rect(0,0,int(12*self.scale_factor),self.leg_length)
        
        self.facing_direction, self.walk_cycle_timer = 1, 0
        self.max_swing_angle, self.swing_angle = 40, 0
        self.animation_speed, self.invincible_timer = 0.0, 0

        # ✨ 1. 인벤토리를 빈 딕셔너리로 초기화
        self.inventory = {}
        # ✨ 2. 핫바 슬롯을 모두 빈 공간(None)으로 초기화
        self.item_slots = [None, None, None, None, None]
        self.selected_slot = 0
        
        self.is_breaking = False
        self.breaking_animation_timer = 0
        self.place_animation_timer = 0
        self.place_animation_duration = 15
    
    @property
    def selected_item(self):
        """선택된 슬롯에 있는 아이템의 이름을 반환합니다."""
        if 0 <= self.selected_slot < len(self.item_slots):
            return self.item_slots[self.selected_slot]
        return None
    
    def add_item_to_hotbar(self, item_name):
        """아이템을 핫바의 빈 슬롯에 추가합니다 (이미 있다면 무시)."""
        if item_name not in self.item_slots:
            try:
                # 핫바에서 첫 번째 빈 슬롯(None)의 인덱스를 찾음
                empty_slot_index = self.item_slots.index(None)
                # 해당 위치에 아이템 이름을 넣음
                self.item_slots[empty_slot_index] = item_name
            except ValueError:
                # 빈 슬롯이 없으면 아무것도 하지 않음 (나중에 인벤토리 UI에서 교체)
                pass

    def change_slot(self, direction):
        """마우스 휠 스크롤로 슬롯을 변경합니다 (순환)."""
        self.selected_slot = (self.selected_slot + direction) % len(self.item_slots)

    def select_slot(self, slot_index):
        """숫자 키로 특정 슬롯을 직접 선택합니다."""
        if 0 <= slot_index < len(self.item_slots):
            self.selected_slot = slot_index

    def start_breaking(self):
        """블록 파괴 애니메이션을 시작합니다."""
        self.is_breaking = True

    def stop_breaking(self):
        """블록 파괴 애니메이션을 중지하고 타이머를 리셋합니다."""
        self.is_breaking = False
        self.breaking_animation_timer = 0

    def start_placing(self):
        """블록 설치 애니메이션을 시작합니다."""
        if self.place_animation_timer <= 0 and not self.is_breaking:
            self.place_animation_timer = self.place_animation_duration

    def take_damage(self, amount):
        if self.invincible_timer <= 0:
            super().take_damage(amount); self.invincible_timer = 90

    def handle_input(self):
        keys = pygame.key.get_pressed()
        acceleration, max_speed = 0.5, 3
        if keys[pygame.K_a]: self.vel.x -= acceleration; self.facing_direction = -1
        if keys[pygame.K_d]: self.vel.x += acceleration; self.facing_direction = 1
        if self.vel.x > max_speed: self.vel.x = max_speed
        if self.vel.x < -max_speed: self.vel.x = -max_speed
        if not (keys[pygame.K_a] or keys[pygame.K_d]):
            self.apply_friction() # ✨ 새로운 메서드 호출로 변경

    def jump(self):
        if self.jump_count < 2:
            self.vel.y, self.jump_count, self.is_on_ground = -10, self.jump_count + 1, False
            return True
        return False
    
    def update_animation(self):
        is_moving = abs(self.vel.x) > 0.1 and self.is_on_ground
        if is_moving:
            self.walk_cycle_timer += 0.3 + abs(self.vel.x) * 0.005
            self.swing_angle = math.sin(self.walk_cycle_timer) * self.max_swing_angle
        else:
            self.swing_angle += (0 - self.swing_angle) * 0.1
            if abs(self.swing_angle) < 0.5: self.swing_angle, self.walk_cycle_timer = 0, 0

    def update(self, tile_rects):
        if self.invincible_timer > 0: self.invincible_timer -= 1
        
        # 애니메이션 타이머 업데이트
        if self.place_animation_timer > 0:
            self.place_animation_timer -= 1
        if self.is_breaking:
            self.breaking_animation_timer += 0.2 # 이 값으로 스윙 속도 조절

        # 나머지 업데이트 로직 (한 번만 호출)
        self.handle_input()
        self.update_physics(tile_rects)
        self.update_animation()
        # --- ✨ 추가: 매 프레임 신체 부위 위치를 업데이트 ✨ ---
        # 이 로직을 draw()가 아닌 update()의 마지막에 두어 항상 최신 위치를 유지합니다.
        self.torso_rect.bottomleft = self.rect.bottomleft
        self.torso_rect.y -= self.leg_length
        self.head_rect.midbottom = self.torso_rect.midtop
        self.head_rect.x += 5 * self.facing_direction * self.scale_factor

    def draw(self, screen, camera_x, camera_y):
        if self.invincible_timer > 0 and self.invincible_timer % 10 < 5: return
        #self.torso_rect.bottomleft=self.rect.bottomleft; self.torso_rect.y -= self.leg_length
        #self.head_rect.midbottom=self.torso_rect.midtop; self.head_rect.x += 5 * self.facing_direction * self.scale_factor
        left_hip_pos = (self.torso_rect.midbottom[0] - 6*self.scale_factor, self.torso_rect.midbottom[1])
        right_hip_pos = (self.torso_rect.midbottom[0] + 6*self.scale_factor, self.torso_rect.midbottom[1])
        left_shoulder_pos, right_shoulder_pos = (self.torso_rect.topleft[0] + 3, self.torso_rect.topleft[1] + 5), (self.torso_rect.topright[0] - 3, self.torso_rect.topright[1] + 5)
        
        # 기본 걷기 각도를 베이스로 설정
        back_arm_angle = self.swing_angle
        front_arm_angle = -self.swing_angle

        # 1. 파괴 애니메이션 (최우선)
        if self.is_breaking:
            swing = math.sin(self.breaking_animation_timer) * 60
            base_angle = -45 + swing # 왼쪽 기준 기본 각도
            
            # ✨✨✨ 핵심 수정: 오른쪽을 볼 땐 각도를 좌우로 뒤집어줍니다 ✨✨✨
            if self.facing_direction == 1:
                front_arm_angle = -base_angle
            else:
                front_arm_angle = base_angle
        
        # 2. 설치 애니메이션
        elif self.place_animation_timer > 0:
            progress = self.place_animation_timer / self.place_animation_duration
            reach_extension = math.sin((1 - progress) * math.pi) * -70
            base_angle = reach_extension # 왼쪽 기준 기본 각도

            # ✨✨✨ 핵심 수정: 오른쪽을 볼 땐 각도를 좌우로 뒤집어줍니다 ✨✨✨
            if self.facing_direction == 1:
                front_arm_angle = -base_angle
            else:
                front_arm_angle = base_angle

        def draw_rotated_limb(original_rect, pivot_pos, angle, color):
            limb_surf = pygame.Surface((original_rect.width, original_rect.height*2), pygame.SRCALPHA)
            pygame.draw.rect(limb_surf, color, (0, original_rect.height, original_rect.width, original_rect.height))
            rotated_limb_surf = pygame.transform.rotate(limb_surf, angle)
            rotated_limb_rect = rotated_limb_surf.get_rect(center=pivot_pos)
            screen.blit(rotated_limb_surf, (rotated_limb_rect.x - camera_x, rotated_limb_rect.y - camera_y))

        back_arm_color, front_arm_color = ((255,200,160), (255,220,180))
        
        # 1. 오른쪽을 보고 있을 때
        if self.facing_direction == 1:
            # 1-1. 배경이 되는 '왼쪽' 팔과 다리를 먼저 그립니다.
            # ✨✨✨ 핵심 수정: 뒷팔인 '왼팔'에 애니메이션 각도(front_arm_angle)를 적용! ✨✨✨
            draw_rotated_limb(self.left_arm_rect, left_shoulder_pos, front_arm_angle, back_arm_color)
            draw_rotated_limb(self.left_leg_rect, left_hip_pos, -self.swing_angle, (40,40,40))
            
            # 1-2. 그 위에 몸통과 머리를 그립니다.
            pygame.draw.rect(screen,(0,0,255),(self.torso_rect.x-camera_x,self.torso_rect.y-camera_y,self.torso_rect.width,self.torso_rect.height))
            pygame.draw.rect(screen,(255,220,180),(self.head_rect.x-camera_x,self.head_rect.y-camera_y,self.head_rect.width,self.head_rect.height))
            
            # 1-3. 가장 앞에 있는 '오른쪽' 팔과 다리를 마지막에 그립니다.
            # ✨✨✨ 핵심 수정: 앞팔인 '오른팔'에는 기본 각도(back_arm_angle)를 적용! ✨✨✨
            draw_rotated_limb(self.right_leg_rect, right_hip_pos, self.swing_angle, (60,60,60))
            draw_rotated_limb(self.right_arm_rect, right_shoulder_pos, back_arm_angle, front_arm_color)
        
        # 2. 왼쪽을 보고 있을 때 (이 부분은 원래 로직과 동일)
        else:
            # 2-1. 배경이 되는 '오른쪽' 팔과 다리를 먼저 그립니다.
            draw_rotated_limb(self.right_arm_rect, right_shoulder_pos, back_arm_angle, back_arm_color)
            draw_rotated_limb(self.right_leg_rect, right_hip_pos, self.swing_angle, (60,60,60))

            # 2-2. 그 위에 몸통과 머리를 그립니다.
            pygame.draw.rect(screen,(0,0,255),(self.torso_rect.x-camera_x,self.torso_rect.y-camera_y,self.torso_rect.width,self.torso_rect.height))
            pygame.draw.rect(screen,(255,220,180),(self.head_rect.x-camera_x,self.head_rect.y-camera_y,self.head_rect.width,self.head_rect.height))
            
            # 2-3. 가장 앞에 있는 '왼쪽' 팔과 다리를 마지막에 그립니다.
            draw_rotated_limb(self.left_leg_rect, left_hip_pos, -self.swing_angle, (40,40,40))
            # 앞팔인 '왼팔'에 애니메이션 각도(front_arm_angle) 적용
            draw_rotated_limb(self.left_arm_rect, left_shoulder_pos, front_arm_angle, front_arm_color)

class Enemy(Entity):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.scale_factor = 0.75
        self.leg_length, self.torso_height = int(30*self.scale_factor), int(40*self.scale_factor)
        self.torso_rect = pygame.Rect(0,0,int(35*self.scale_factor), self.torso_height)
        self.head_rect, self.left_leg_rect, self.right_leg_rect = pygame.Rect(0,0,int(30*self.scale_factor),int(30*self.scale_factor)), pygame.Rect(0,0,int(10*self.scale_factor),self.leg_length), pygame.Rect(0,0,int(10*self.scale_factor),self.leg_length)
        self.club_rect, self.club_world_rect = pygame.Rect(0,0,int(10*self.scale_factor),int(40*self.scale_factor)), None
        self.facing_direction, self.walk_cycle_timer = -1, 0
        self.max_swing_angle, self.swing_angle = 50, 0
        self.direction, self.speed, self.chase_speed, self.jump_power = -1, 1.0, 2.2, -13
        self.state, self.detection_radius, self.last_seen_pos = 'patrol', 250, None
        self.search_timer, self.search_duration, self.patrol_turn_timer, self.patrol_turn_interval = 0, 180, 0, 240
        self.attack_range, self.attack_timer, self.attack_cooldown = 45, 0, 120
        self.attack_animation_timer, self.attack_animation_duration = 0, 30
        self.can_see_player = False # ✨ 시야 상태 저장 변수 추가

    def jump(self):
        if self.is_on_ground: self.vel.y = self.jump_power; self.is_on_ground = False
        
    def update_animation(self):
        is_moving = abs(self.vel.x) > 0.1 and self.is_on_ground
        if is_moving:
            self.walk_cycle_timer += 0.05 + abs(self.vel.x) * 0.00325
            self.swing_angle = math.sin(self.walk_cycle_timer) * self.max_swing_angle
        else:
            self.swing_angle += (0 - self.swing_angle) * 0.1
            if abs(self.swing_angle) < 0.5: self.swing_angle, self.walk_cycle_timer = 0, 0
            
    def update(self, tile_rects, player, world_grid):
        if self.attack_timer > 0: self.attack_timer -= 1
        distance = pygame.math.Vector2(self.rect.center).distance_to(player.rect.center)
        # 1. 시야 확인을 위한 그리드 좌표들을 가져옵니다.
        start_grid_pos = (self.head_rect.centerx // TILE_SIZE, self.head_rect.centery // TILE_SIZE)
        head_grid_pos = (player.head_rect.centerx // TILE_SIZE, player.head_rect.centery // TILE_SIZE)
        torso_grid_pos = (player.torso_rect.centerx // TILE_SIZE, player.torso_rect.centery // TILE_SIZE)
        feet_pos = (player.rect.centerx, player.rect.bottom - 5)
        feet_grid_pos = (feet_pos[0] // TILE_SIZE, feet_pos[1] // TILE_SIZE)

        # 2. world.py의 정확한 함수를 사용하여 세 지점 모두 검사합니다.
        can_see_head = has_line_of_sight(start_grid_pos, head_grid_pos, world_grid)
        can_see_torso = has_line_of_sight(start_grid_pos, torso_grid_pos, world_grid)
        can_see_feet = has_line_of_sight(start_grid_pos, feet_grid_pos, world_grid)

        # 3. 하나라도 보이면 can_see는 True가 됩니다.
        can_see = can_see_head or can_see_torso or can_see_feet
        self.can_see_player = can_see
        is_player_in_front = (self.facing_direction * (player.rect.centerx - self.rect.centerx) > 0)

        if self.state == 'attack':
            if self.attack_animation_timer > 0: self.attack_animation_timer -= 1
            else: self.state, self.attack_timer = 'chase', self.attack_cooldown
        else:
            if self.state == 'patrol':
                if is_player_in_front and can_see and distance < self.detection_radius: self.state = 'chase'
            elif self.state == 'chase':
                if not can_see or distance > self.detection_radius * 1.5: self.state, self.search_timer = 'search', self.search_duration
                elif self.rect.move(self.direction*20,0).collidelist(tile_rects) == -1 and distance < self.attack_range and self.attack_timer <= 0:
                    self.state, self.attack_animation_timer = 'attack', self.attack_animation_duration
                else: self.last_seen_pos = player.rect.center
            elif self.state == 'search':
                if can_see and distance < self.detection_radius: self.state = 'chase'
                else:
                    self.search_timer -= 1
                    if self.search_timer <= 0 or (self.last_seen_pos and self.rect.collidepoint(self.last_seen_pos)): self.state = 'patrol'

        self.vel.x = 0
        if self.state != 'attack':
            if self.is_on_ground:
                is_wall = self.rect.move(self.direction * 5, 0).collidelist(tile_rects) != -1
                is_ground = any(pygame.Rect(self.rect.centerx+(self.rect.width/2+5)*self.direction,self.rect.bottom,5,5).colliderect(t) for t in tile_rects)
                if self.state == 'patrol':
                    self.patrol_turn_timer += 1
                    if self.patrol_turn_timer > self.patrol_turn_interval and random.random()<0.5: self.direction*=-1; self.patrol_turn_timer=0
                    if is_wall: self.jump()
                elif self.state in ['chase', 'search']:
                    if is_wall: self.jump()
                    elif not is_ground and player.rect.centery < self.rect.bottom: self.jump()
            
            if self.state == 'chase': self.direction = 1 if player.rect.centerx>self.rect.centerx else -1; self.vel.x = self.chase_speed*self.direction
            elif self.state == 'search':
                if self.last_seen_pos and abs(self.last_seen_pos[0]-self.rect.centerx)>5:
                    self.direction=1 if self.last_seen_pos[0]>self.rect.centerx else -1; self.vel.x = self.speed*self.direction
            else: self.vel.x = self.speed * self.direction
        
        self.facing_direction = self.direction
        self.update_physics(tile_rects); self.update_animation()

    def draw(self, screen, camera_x, camera_y, player_rect):
        self.torso_rect.bottomleft = self.rect.bottomleft; self.torso_rect.y -= self.leg_length
        self.head_rect.midbottom = self.torso_rect.midtop; self.head_rect.x += 3 * self.facing_direction
        left_hip_pos = (self.torso_rect.midbottom[0] - 5*self.scale_factor, self.torso_rect.midbottom[1])
        right_hip_pos = (self.torso_rect.midbottom[0] + 5*self.scale_factor, self.torso_rect.midbottom[1])
        GOBLIN_SKIN, GOBLIN_ARMOR, CLUB_COLOR = (80,140,80), (100,80,60), (139,69,19)
        
        def draw_rotated_limb(original_rect, pivot_pos, angle, color):
            limb_surf = pygame.Surface((original_rect.width, original_rect.height*2), pygame.SRCALPHA)
            pygame.draw.rect(limb_surf, color, (0, original_rect.height, original_rect.width, original_rect.height))
            rotated_limb_surf = pygame.transform.rotate(limb_surf, angle)
            rotated_limb_rect = rotated_limb_surf.get_rect(center=pivot_pos)
            screen.blit(rotated_limb_surf, (rotated_limb_rect.x-camera_x, rotated_limb_rect.y-camera_y))

        if self.facing_direction == 1:
            draw_rotated_limb(self.left_leg_rect, left_hip_pos, -self.swing_angle, GOBLIN_SKIN)
            pygame.draw.rect(screen, GOBLIN_ARMOR, (self.torso_rect.x-camera_x, self.torso_rect.y-camera_y, self.torso_rect.width, self.torso_rect.height))
            pygame.draw.rect(screen, GOBLIN_SKIN, (self.head_rect.x-camera_x, self.head_rect.y-camera_y, self.head_rect.width, self.head_rect.height))
            draw_rotated_limb(self.right_leg_rect, right_hip_pos, self.swing_angle, GOBLIN_SKIN)
        else:
            draw_rotated_limb(self.right_leg_rect, right_hip_pos, self.swing_angle, GOBLIN_SKIN)
            pygame.draw.rect(screen, GOBLIN_ARMOR, (self.torso_rect.x-camera_x, self.torso_rect.y-camera_y, self.torso_rect.width, self.torso_rect.height))
            pygame.draw.rect(screen, GOBLIN_SKIN, (self.head_rect.x-camera_x, self.head_rect.y-camera_y, self.head_rect.width, self.head_rect.height))
            draw_rotated_limb(self.left_leg_rect, left_hip_pos, -self.swing_angle, GOBLIN_SKIN)
            
        self.club_world_rect = None
        if self.state == 'attack':
            progress = (self.attack_animation_duration - self.attack_animation_timer) / self.attack_animation_duration
            angle = math.sin(progress * math.pi) * -90 * self.facing_direction
            club_surf = pygame.Surface(self.club_rect.size, pygame.SRCALPHA); club_surf.fill(CLUB_COLOR)
            pivot_pos = self.torso_rect.topright if self.facing_direction == 1 else self.torso_rect.topleft
            rotated_club_surf, club_display_rect = pygame.transform.rotate(club_surf, angle), pygame.transform.rotate(club_surf, angle).get_rect(center=pivot_pos)
            screen.blit(rotated_club_surf, (club_display_rect.x-camera_x, club_display_rect.y-camera_y))
            self.club_world_rect = pygame.Rect(club_display_rect.x, club_display_rect.y, club_display_rect.width, club_display_rect.height)
        else:
            club_held_rect = self.club_rect.copy()
            if self.facing_direction == 1: club_held_rect.midleft = self.torso_rect.midright
            else: club_held_rect.midright = self.torso_rect.midleft
            club_held_rect.y -= 5; pygame.draw.rect(screen, CLUB_COLOR, (club_held_rect.x-camera_x, club_held_rect.y-camera_y, club_held_rect.width, club_held_rect.height))

        indicator_text, indicator_color = (("!",ORANGE) if self.state=='chase' else ("?",YELLOW)) if self.state in ['chase','search'] else (None,None)
        if indicator_text:
            text_surf = indicator_font.render(indicator_text, True, indicator_color)
            screen.blit(text_surf, text_surf.get_rect(center=(self.rect.centerx-camera_x, self.rect.top-20-camera_y)))
            
        # 3. ✨ 디버깅용 시야 레이저 그리기 (새로 추가된 부분)
        # 적이 추격 또는 수색 상태일 때만 레이저를 그림
        if self.state in ['chase', 'search']:
            # 시야가 확보되었으면 초록색, 아니면 빨간색으로 설정
            laser_color = (0, 255, 0) if self.can_see_player else (255, 0, 0)
            
            # 시작점(적 중심)과 끝점(플레이어 중심)의 화면 좌표 계산
            start_pos = (self.head_rect.centerx - camera_x, self.head_rect.centery - camera_y) # 적의 머리 위치
            end_pos = (player_rect.centerx - camera_x, player_rect.centery - camera_y)
            
            # 선 그리기
            pygame.draw.line(screen, laser_color, start_pos, end_pos, 2)