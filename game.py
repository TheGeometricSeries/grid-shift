import pygame
import sys
import random
from config import *
from entities import *
from world import get_nearby_tiles
from utils import has_line_of_sight
from ui import pause_screen, draw_ui, inventory_screen

# game.py (파일 상단, draw_break_progress 함수 위)

# '들쭉날쭉한 선'을 그리기 위한 헬퍼 함수
def draw_jagged_line(screen, color, start_pos, end_pos, thickness=1, segments=4, jitter=4):
    """
    start_pos에서 end_pos까지 들쭉날쭉한 선을 그립니다.
    - segments: 선을 몇 조각으로 나눌지
    - jitter: 각 조각을 얼마나 무작위로 비틀지
    """
    points = [start_pos]
    dx = (end_pos[0] - start_pos[0]) / segments
    dy = (end_pos[1] - start_pos[1]) / segments

    for i in range(1, segments):
        base_x = start_pos[0] + i * dx
        base_y = start_pos[1] + i * dy
        # 중간 지점들에 무작위 '떨림'을 추가
        jitter_x = base_x + random.randint(-jitter, jitter)
        jitter_y = base_y + random.randint(-jitter, jitter)
        points.append((jitter_x, jitter_y))
    
    points.append(end_pos)
    
    # 여러 개의 점을 선으로 이어 그립니다.
    pygame.draw.lines(screen, color, False, points, thickness)


# --- 기존 함수를 아래와 같이 수정 ---

def draw_break_progress(screen, target_tile_rect, break_timer, max_break_time, camera_x, camera_y):
    if target_tile_rect is None or break_timer <= 0:
        return

    screen_rect = target_tile_rect.move(-camera_x, -camera_y)
    progress = 1 - (break_timer / max_break_time)
    
    # (config.py에 BASE_TILE_SIZE, BLACK, WHITE가 정의되어 있어야 합니다)
    
    # 1. '시드' 고정: 타일의 위치를 시드로 사용하여 항상 같은 패턴이 나오게 함
    #    (주의: 다른 random 로직에 영향을 주지 않기 위해 상태를 저장/복원)
    old_random_state = random.getstate()

    seed_str = f"{target_tile_rect.topleft[0]},{target_tile_rect.topleft[1]}"
    random.seed(seed_str) 

    # 2. '최대 균열' 패턴 미리 생성
    #    중앙에서 사방의 랜덤한 '가장자리'로 뻗어 나가는 균열
    max_cracks = 7 # 최대 7개의 균열 라인
    crack_lines = []
    for _ in range(max_cracks):
        # 중앙점
        start_pos = screen_rect.center
        
        # 가장자리(상/하/좌/우) 중 하나를 랜덤하게 선택
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        
        if edge == 'top':
            end_pos = (random.randint(screen_rect.left, screen_rect.right), screen_rect.top)
        elif edge == 'bottom':
            end_pos = (random.randint(screen_rect.left, screen_rect.right), screen_rect.bottom)
        elif edge == 'left':
            end_pos = (screen_rect.left, random.randint(screen_rect.top, screen_rect.bottom))
        else: # 'right'
            end_pos = (screen_rect.right, random.randint(screen_rect.top, screen_rect.bottom))
        
        crack_lines.append((start_pos, end_pos))

    # 3. 진행도(progress)에 따라 생성된 균열을 '일부만' 그리기
    #    progress가 1.0이면 max_cracks(7개)를 모두 그림
    lines_to_draw = int(progress * max_cracks) + 1 # 최소 1개는 보이도록
    
    # 얼마나 비틀지 (타일 크기에 비례)
    jitter_amount = max(1, BASE_TILE_SIZE // 8) 

    for i in range(lines_to_draw):
        if i < len(crack_lines):
            start, end = crack_lines[i]
            # 직선 대신 '들쭉날쭉한' 균열선 그리기
            draw_jagged_line(screen, BLACK, start, end, 2, 4, jitter_amount)

    # 4. 다른 코드에 영향을 주지 않도록 원래 random 상태로 복원
    random.setstate(old_random_state)
"""
# 블록 파괴 진행도를 시각화하는 함수
def draw_break_progress(screen, target_tile_rect, break_timer, max_break_time, camera_x, camera_y):
    if target_tile_rect is None or break_timer <= 0:
        return

    # 화면에 표시될 사각형 (카메라 위치 반영)
    screen_rect = target_tile_rect.move(-camera_x, -camera_y)

    # 파괴 진행도 계산 (0.0 ~ 1.0)
    progress = 1 - (break_timer / max_break_time)

    line_count = int(progress * 5) # 진행도에 따라 선 개수 증가 (최대 5개)
    for i in range(line_count):
        # 중앙에서 랜덤한 방향으로 짧은 선 그리기
        start_x, start_y = screen_rect.center
        end_x = start_x + random.randint(-BASE_TILE_SIZE // 3, BASE_TILE_SIZE // 3)
        end_y = start_y + random.randint(-BASE_TILE_SIZE // 3, BASE_TILE_SIZE // 3)
        pygame.draw.line(screen, WHITE, (start_x, start_y), (end_x, end_y), 2)

    # 파인 부분의 크기를 진행도에 비례하여 조절
    dig_radius = int((BASE_TILE_SIZE / 3) * progress)
    if dig_radius > 0:
        pygame.draw.circle(screen, BLACK, screen_rect.center, dig_radius)
"""
def main_game(map_data, world_name, start_pos=None):
    MAP_WIDTH = len(map_data[0])
    MAP_HEIGHT = len(map_data)
    map_width_pixels = MAP_WIDTH * BASE_TILE_SIZE
    map_height_pixels = MAP_HEIGHT * BASE_TILE_SIZE

    # 1. 전체 크기를 가지지만 비어있는 world_grid를 생성
    world_grid = [[None for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    # 2. 현재 로드된 청크를 추적하기 위한 set
    loaded_chunks = set()
    ITEM_TO_TILE_TYPE = {
        "dirt": 1,
        "grass": 1, # '잔디' 아이템도 설치 시에는 흙(1)으로 설치됩니다.
        "stone": 3,
        "wood": 4,
        "leaf": 5
    }
    particles, item_drops, grass_spread_timer = [], [], 0
    break_timer = 0
    breaking_tile_coords = None
    player = Player(0, 0, 0, 0)
    if start_pos: player.rect.topleft = start_pos
    else: player.rect.center = (map_width_pixels / 2, map_height_pixels / 2) # 안전장치
    enemies = []
    
    enemy = Enemy(600, 0, int(35 * 0.75), int(70 * 0.75))
    # 적의 시작 y 위치를 땅 위에 맞게 조정
    col_x = enemy.rect.centerx // BASE_TILE_SIZE
    is_on_ground = False
    if 0 <= col_x < len(world_grid[0]):
        # 아래로 내려가면서 첫 번째 땅을 찾음
        for y in range(len(world_grid)):
            if world_grid[y][col_x] is not None:
                # 찾은 땅 위에 적의 발을 맞춤
                enemy.rect.bottom = world_grid[y][col_x].rect.top
                is_on_ground = True
                break

    if is_on_ground:
        enemies.append(enemy)

    INTERACTION_RADIUS_X = 3 # 좌우 상호작용 반경
    INTERACTION_RADIUS_Y = 3 # 상하 상호작용 반경
    EXTRA_REACH_UP = 1       # 위쪽 추가 반경

    # 1. 기본 상호작용 범위를 표시할 Surface (Alpha: 50)
    highlight_surf_primary = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE), pygame.SRCALPHA)
    highlight_surf_primary.fill((200, 200, 255, 40)) 
    # 2. 확장된 범위를 표시할 더 투명한 Surface (Alpha: 25)
    highlight_surf_secondary = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE), pygame.SRCALPHA)
    highlight_surf_secondary.fill((200, 200, 255, 25))

    camera_x, camera_y = 0, 0
    running = True
    while running:
        clock.tick(BASE_FPS)
        mouse_pos = pygame.mouse.get_pos()
        mouse_world_pos = (mouse_pos[0] + camera_x, mouse_pos[1] + camera_y)
        mouse_grid_x, mouse_grid_y = int(mouse_world_pos[0] // BASE_TILE_SIZE), int(mouse_world_pos[1] // BASE_TILE_SIZE)
        selected_tile_rect = pygame.Rect(mouse_grid_x * BASE_TILE_SIZE, mouse_grid_y * BASE_TILE_SIZE, BASE_TILE_SIZE, BASE_TILE_SIZE)
        # 3. 현재 플레이어 위치를 기준으로 필요한 청크 범위를 계산
        player_chunk_x = player.rect.centerx // (CHUNK_SIZE * BASE_TILE_SIZE)
        load_radius = 2 # 플레이어 주변으로 2청크까지 로드 (화면 + 버퍼)

        required_chunks = set()
        for y in range(-load_radius, load_radius + 1):
            for x in range(-load_radius, load_radius + 1):
                chunk_coord = (player_chunk_x + x, 0) # 2D 청크라면 y도 계산해야 함
                required_chunks.add(chunk_coord)

        # 4. 더 이상 필요 없는 청크를 언로드 (메모리에서 삭제)
        chunks_to_unload = loaded_chunks - required_chunks
        for chunk_x, chunk_y in chunks_to_unload:
            start_x = chunk_x * CHUNK_SIZE
            for y in range(MAP_HEIGHT):
                for x in range(CHUNK_SIZE):
                    grid_x = start_x + x
                    if 0 <= grid_x < MAP_WIDTH:
                        world_grid[y][grid_x] = None
        
        # 5. 새로 필요한 청크를 로드 (메모리에 생성)
        chunks_to_load = required_chunks - loaded_chunks
        for chunk_x, chunk_y in chunks_to_load:
            start_x = chunk_x * CHUNK_SIZE
            for y in range(MAP_HEIGHT):
                for x in range(CHUNK_SIZE):
                    grid_x = start_x + x
                    if 0 <= grid_x < MAP_WIDTH:
                        tile_type = map_data[y][grid_x]
                        if tile_type != 0:
                            is_exposed = (y == 0 or map_data[y-1][grid_x] == 0)
                            block_type = 2 if is_exposed and tile_type == 1 else tile_type
                            world_grid[y][grid_x] = Tile(grid_x, y, block_type)

        # 6. 로드된 청크 목록 업데이트
        loaded_chunks = required_chunks

        # ✨ 플레이어의 그리드 좌표를 미리 계산
        player_grid_pos = (player.head_rect.centerx // BASE_TILE_SIZE, player.head_rect.centery // BASE_TILE_SIZE) # 수정된 코드 (머리 기준)
        mouse_grid_pos = (mouse_grid_x, mouse_grid_y)
        
        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    # 1. 플레이어의 실제 경계를 기준으로 상호작용 가능 여부를 정확히 계산
                    player_left_grid = player.rect.left // BASE_TILE_SIZE
                    player_right_grid = player.rect.right // BASE_TILE_SIZE
                    player_top_grid = player.rect.top // BASE_TILE_SIZE
                    player_bottom_grid = player.rect.bottom // BASE_TILE_SIZE

                    is_horizontally_close = (player_left_grid - INTERACTION_RADIUS_X <= mouse_grid_x <= player_right_grid + INTERACTION_RADIUS_X)
                    is_vertically_close = (player_top_grid - (INTERACTION_RADIUS_Y + EXTRA_REACH_UP) <= mouse_grid_y <= player_bottom_grid + INTERACTION_RADIUS_Y)
                    is_close_enough = is_horizontally_close and is_vertically_close
                    
                    # 2. 나머지 모든 조건들을 계산
                    is_valid_grid_pos = 0 <= mouse_grid_y < len(world_grid) and 0 <= mouse_grid_x < len(world_grid[0]) and world_grid[mouse_grid_y][mouse_grid_x] is None
                    is_not_overlapping_player = not player.rect.colliderect(selected_tile_rect)
                    is_in_sight = has_line_of_sight(player_grid_pos, mouse_grid_pos, world_grid)
                    has_item = player.selected_item is not None and player.inventory.get(player.selected_item, 0) > 0 # ✨ 아이템 보유 여부 강화

                    # 3. 지지 블록이 있는지 확인
                    has_support = False
                    if is_valid_grid_pos:
                        if mouse_grid_y + 1 < len(world_grid) and world_grid[mouse_grid_y + 1][mouse_grid_x] is not None: has_support = True
                        else:
                            for offset in [(0, -1), (1, 0), (-1, 0)]:
                                check_x, check_y = mouse_grid_x + offset[0], mouse_grid_y + offset[1]
                                if 0 <= check_y < len(world_grid) and 0 <= check_x < len(world_grid[0]) and world_grid[check_y][check_x] is not None:
                                    has_support = True; break
                    
                    # 4. 최종적으로 모든 조건이 참일 때만 블록을 설치
                    if all([is_valid_grid_pos, is_close_enough, is_not_overlapping_player, has_support, is_in_sight, has_item]):
                        player.start_placing()
                        player.inventory[player.selected_item] -= 1
                        
                        item_type_to_place = player.selected_item
                        tile_type_to_place = ITEM_TO_TILE_TYPE.get(item_type_to_place, 1)
                        world_grid[mouse_grid_y][mouse_grid_x] = Tile(mouse_grid_x, mouse_grid_y, tile_type_to_place)
                
                elif event.button == 4:  # 위로 스크롤
                    player.change_slot(-1)
                elif event.button == 5:  # 아래로 스크롤
                    player.change_slot(1)
                    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump()
                if event.key == pygame.K_ESCAPE:
                    if player.is_inventory_open: # ✨ 인벤토리가 열려있으면 닫음
                        player.is_inventory_open = False
                    else: # 아니면 일시정지 메뉴 호출
                        if pause_screen(world_grid, world_name, player.rect) == "QUIT_TO_TITLE":
                            return "TITLE"
                
                if event.key == pygame.K_e:
                    player.is_inventory_open = not player.is_inventory_open # ✨ 상태 토글
                    # 숫자 키로 슬롯 직접 선택
                if not player.is_inventory_open: # ✨ 조건 추가
                    if event.key == pygame.K_1: player.select_slot(0)
                    if event.key == pygame.K_2: player.select_slot(1)
                    if event.key == pygame.K_3: player.select_slot(2)
                    if event.key == pygame.K_4: player.select_slot(3)
                    if event.key == pygame.K_5: player.select_slot(4)
        # 업데이트
        # 1. 화면에 보이는 타일 목록 계산 (새로 추가되거나 위치 이동)
        start_col = max(0, int(camera_x // BASE_TILE_SIZE))
        end_col = min(len(world_grid[0]), int((camera_x + SCREEN_WIDTH) // BASE_TILE_SIZE) + 2)
        start_row = max(0, int(camera_y // BASE_TILE_SIZE))
        end_row = min(len(world_grid), int((camera_y + SCREEN_HEIGHT) // BASE_TILE_SIZE) + 2)
        visible_tiles = [world_grid[y][x] for y in range(start_row, end_row) for x in range(start_col, end_col) if world_grid[y][x]]

        # 2. 충돌을 검사할 '단단한(solid)' 블록만 필터링하여 사각형 목록을 만듭니다.
        solid_tile_rects = [t.rect for t in visible_tiles if t.type not in NON_SOLID_BLOCKS]

        # 3. 필터링된 '단단한' 블록 목록을 각 객체의 업데이트 함수에 전달합니다.
        player.update(solid_tile_rects)

        # --- ✨ 아이템 업데이트 로직 최종 수정 ✨ ---
        all_item_rects = [item.rect for item in item_drops]
        for item in item_drops:
            # 1. '생각': 불안정한지 확인해서 회전 속도를 결정
            # ✨ 아이템의 지지대 목록에도 solid_tile_rects를 사용해주는 것이 더 정확합니다.
            supporters = [r for r in all_item_rects if r is not item.rect] + solid_tile_rects
            item.check_stability(supporters)

            # ✨ 여기도 solid_tile_rects를 사용합니다.
            colliders = [r for r in all_item_rects if r is not item.rect] + solid_tile_rects
            item.update(colliders, player)

        player_body_grid_pos = (player.rect.centerx // BASE_TILE_SIZE, player.rect.centery // BASE_TILE_SIZE)

        # 플레이어 아이템 획득
        for item in item_drops[:]:
            # 조건 1: 플레이어와 아이템이 물리적으로 충돌했는가?
            if player.rect.colliderect(item.rect):
                
                # 시야 확인을 위한 기준점 3개 설정
                head_grid_pos = (player.head_rect.centerx // BASE_TILE_SIZE, player.head_rect.centery // BASE_TILE_SIZE)
                torso_grid_pos = (player.torso_rect.centerx // BASE_TILE_SIZE, player.torso_rect.centery // BASE_TILE_SIZE)
                feet_pos = (player.rect.centerx, player.rect.bottom - 5) # 발 위치 근사치
                feet_grid_pos = (feet_pos[0] // BASE_TILE_SIZE, feet_pos[1] // BASE_TILE_SIZE)
                
                item_grid_pos = (item.rect.centerx // BASE_TILE_SIZE, item.rect.centery // BASE_TILE_SIZE)

                # 조건 2: 머리, 몸, 발 중 하나라도 시야가 확보되었는가?
                is_sight_clear = (
                    has_line_of_sight(head_grid_pos, item_grid_pos, world_grid) or
                    has_line_of_sight(torso_grid_pos, item_grid_pos, world_grid) or
                    has_line_of_sight(feet_grid_pos, item_grid_pos, world_grid)
                )

                if is_sight_clear:
                    # ✨ 1. 아이템 개수 추가
                    item_type = item.item_type
                    player.inventory[item_type] = player.inventory.get(item_type, 0) + 1
                    
                    # ✨ 2. 핫바에 아이템 추가 시도
                    player.add_item_to_hotbar(item_type)
                    
                    item_drops.remove(item)

        # --- ▼▼▼ 적-플레이어 충돌 확인 코드 추가 ▼▼▼ ---
        for enemy in enemies:
            # 1. 적 주변의 타일 정보를 가져옵니다 (update에 필요).
            # nearby_tile_rects = [t.rect for t in get_nearby_tiles(enemy.rect, world_grid) if t] # <--- 이 줄을 삭제하세요!
            
            # 2. 적의 상태를 업데이트합니다 (player 객체 전체를 전달).
            # 이 안에서 시야 확인(머리,몸,발)이 모두 이루어집니다.
            # enemy.update(nearby_tile_rects, player, world_grid) # <--- 이 줄도 삭제하세요!
            
            # ✨ (수정) 2단계를 반영하여, 이미 계산된 'solid_tile_rects'를 사용합니다.
            enemy.update(solid_tile_rects, player, world_grid)
            
            # 3. 만약 적이 공격 중이고 몽둥이가 플레이어와 닿았다면 데미지를 줍니다.
            if enemy.club_world_rect and player.rect.colliderect(enemy.club_world_rect):
                player.take_damage(ENEMY_DAMAGE)
        
        # 블록 파괴
        mouse_buttons = pygame.mouse.get_pressed()
        player_left_grid = player.rect.left // BASE_TILE_SIZE
        player_right_grid = player.rect.right // BASE_TILE_SIZE
        player_top_grid = player.rect.top // BASE_TILE_SIZE
        player_bottom_grid = player.rect.bottom // BASE_TILE_SIZE

        is_horizontally_close = (player_left_grid - INTERACTION_RADIUS_X <= mouse_grid_x <= player_right_grid + INTERACTION_RADIUS_X)
        is_vertically_close = (player_top_grid - (INTERACTION_RADIUS_Y + EXTRA_REACH_UP) <= mouse_grid_y <= player_bottom_grid + INTERACTION_RADIUS_Y)
        can_interact = is_horizontally_close and is_vertically_close
        is_tile_solid = 0 <= mouse_grid_y < len(world_grid) and 0 <= mouse_grid_x < len(world_grid[0]) and world_grid[mouse_grid_y][mouse_grid_x] is not None
        is_in_sight_for_break = has_line_of_sight(player_grid_pos, mouse_grid_pos, world_grid)

        if mouse_buttons[0] and can_interact and is_tile_solid and is_in_sight_for_break:
            player.start_breaking() # ✨ 애니메이션 시작
            current_breaking_coords = (mouse_grid_x, mouse_grid_y)
            if breaking_tile_coords != current_breaking_coords:
                breaking_tile_coords = current_breaking_coords
                break_timer = MAX_BREAK_TIME
            break_timer -= 1
            if break_timer <= 0:
                tile_to_break = world_grid[mouse_grid_y][mouse_grid_x]
                # 부서진 블록 타입에 따라 드랍할 아이템 결정
                if tile_to_break.type == 1: # 잔디
                    item_to_drop = "dirt"
                elif tile_to_break.type == 2: # 흙
                    item_to_drop = "dirt"
                elif tile_to_break.type == 3: # 돌
                    item_to_drop = "stone"
                elif tile_to_break.type == 4: # 나무
                    item_to_drop = "wood"
                elif tile_to_break.type == 5: # 나뭇잎
                    item_to_drop = "leaf"
                
                item_drops.append(ItemDrop(tile_to_break.rect.centerx, tile_to_break.rect.centery, item_to_drop))
                world_grid[mouse_grid_y][mouse_grid_x] = None
                breaking_tile_coords = None; break_timer = 0
        else:
            player.stop_breaking() # ✨ 애니메이션 중지
            breaking_tile_coords = None; break_timer = 0

        # 그리기
        camera_x = player.rect.centerx - SCREEN_WIDTH / 2
        camera_y = player.rect.centery - SCREEN_HEIGHT / 2
        camera_x = max(0, min(camera_x, map_width_pixels - SCREEN_WIDTH))
        camera_y = max(0, min(camera_y, map_height_pixels - SCREEN_HEIGHT))
        screen.fill(SKY_COLOR)
        start_col, end_row = max(0, int(camera_x // BASE_TILE_SIZE)), min(len(world_grid), int((camera_y + SCREEN_HEIGHT) // BASE_TILE_SIZE) + 2)
        end_col = min(len(world_grid[0]), int((camera_x + SCREEN_WIDTH) // BASE_TILE_SIZE) + 2)
        start_row = max(0, int(camera_y // BASE_TILE_SIZE))

        # --- ▼▼▼ 플레이어 사망 확인 코드 추가 ▼▼▼ ---
        if player.health <= 0:
            running = False # 루프를 중단시켜 사망 애니메이션으로 넘어감

        # 월드 업데이트 (잔디 성장 및 소멸)
        grass_spread_timer += 1
        
        # 1. 잔디 성장 로직
        if grass_spread_timer >= GRASS_SPREAD_COOLDOWN:
            grass_spread_timer = 0
            
            # 화면에 보이는 모든 타일을 순회하며 잔디를 찾음
            for y in range(start_row, end_row):
                for x in range(start_col, end_col):
                    tile = world_grid[y][x]
                    if tile and tile.type == 2: # 잔디 블록이라면
                        # 주변 흙 블록(type==1)을 찾아 일정 확률로 잔디로 바꿈
                        for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nx, ny = x + offset[0], y + offset[1]
                            if 0 <= ny < len(world_grid) and 0 <= nx < len(world_grid[0]):
                                neighbor_tile = world_grid[ny][nx]
                                # 이웃이 흙이고, 그 위가 비어있어야 함
                                if neighbor_tile and neighbor_tile.type == 1 and (ny == 0 or world_grid[ny-1][nx] is None):
                                    if random.random() < 0.2: # 20% 확률로 전파
                                        neighbor_tile.type = 2
                                        break # 한 번만 전파
        
        # 2. 잔디 소멸 로직
        # 화면에 보이는 모든 타일을 순회
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                tile = world_grid[y][x]
                if tile and tile.type == 2: # 잔디 블록이라면
                    is_covered = y > 0 and world_grid[y-1][x] is not None
                    if is_covered:
                        tile.time_covered += 1
                        if tile.time_covered > GRASS_DECAY_TIME:
                            tile.type = 1 # 흙으로 변경
                            tile.time_covered = 0
                    else:
                        tile.time_covered = 0 # 덮여있지 않으면 타이머 리셋
                        
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if world_grid[y][x]: world_grid[y][x].draw(screen, camera_x, camera_y, world_grid, x, y)
        for item in item_drops: item.draw(screen, camera_x, camera_y)
        player.draw(screen, camera_x, camera_y)
        for enemy in enemies:
            enemy.draw(screen, camera_x, camera_y, player.rect)
            
        if player.inventory.get(player.selected_item, 0) > 0:
            # 1. 설치 가능 여부를 판단하기 위한 모든 조건을 계산합니다.
            
            # 거리 조건 (새로운 방식)
            rounded_grid_x = int(round(player.rect.centerx / BASE_TILE_SIZE))
            rounded_grid_y = int(round(player.rect.centery / BASE_TILE_SIZE))
            dist_x = abs(mouse_grid_x - rounded_grid_x)
            y_offset = rounded_grid_y - mouse_grid_y
            is_horizontally_close = (dist_x <= INTERACTION_RADIUS_X)
            is_vertically_close = (-INTERACTION_RADIUS_Y <= y_offset <= INTERACTION_RADIUS_Y + EXTRA_REACH_UP)
            is_close_enough = is_horizontally_close and is_vertically_close

            # 기타 조건
            is_empty_tile = 0 <= mouse_grid_y < len(world_grid) and 0 <= mouse_grid_x < len(world_grid[0]) and world_grid[mouse_grid_y][mouse_grid_x] is None
            is_not_overlapping = not player.rect.colliderect(selected_tile_rect)
            is_in_sight = has_line_of_sight(player_grid_pos, mouse_grid_pos, world_grid)

            # 지지 블록 조건
            has_support = False
            if is_empty_tile:
                if mouse_grid_y + 1 < len(world_grid) and world_grid[mouse_grid_y + 1][mouse_grid_x] is not None:
                    has_support = True
                else:
                    for offset in [(0, -1), (1, 0), (-1, 0)]:
                        check_x, check_y = mouse_grid_x + offset[0], mouse_grid_y + offset[1]
                        if 0 <= check_y < len(world_grid) and 0 <= check_x < len(world_grid[0]) and world_grid[check_y][check_x] is not None:
                            has_support = True
                            break
            
            # 2. 모든 조건을 종합하여 최종적으로 설치 가능한지(can_place_preview)를 결정합니다.
            can_place_preview = all([is_close_enough, is_empty_tile, is_not_overlapping, is_in_sight, has_support])

            # 3. 결과에 따라 미리보기 상자를 그립니다.
            preview_surf = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE), pygame.SRCALPHA)
            color = (0, 255, 0, 120) if can_place_preview else (255, 0, 0, 120)
            preview_surf.fill(color)
            screen.blit(preview_surf, (selected_tile_rect.x - camera_x, selected_tile_rect.y - camera_y))
        if can_interact and is_tile_solid:
            outline_rect = selected_tile_rect.move(-camera_x, -camera_y)
            pygame.draw.rect(screen, YELLOW, outline_rect, 3)
        if breaking_tile_coords is not None:
            breaking_rect = pygame.Rect(breaking_tile_coords[0] * BASE_TILE_SIZE, breaking_tile_coords[1] * BASE_TILE_SIZE, BASE_TILE_SIZE, BASE_TILE_SIZE)
            draw_break_progress(screen, breaking_rect, break_timer, MAX_BREAK_TIME, camera_x, camera_y)

        # 새로운 상호작용 가능 여부 계산 로직 (미리보기와 하이라이트가 공통으로 사용)
        player_left_grid = player.rect.left // BASE_TILE_SIZE
        player_right_grid = player.rect.right // BASE_TILE_SIZE
        player_top_grid = player.rect.top // BASE_TILE_SIZE
        player_bottom_grid = player.rect.bottom // BASE_TILE_SIZE
        
        # Shift 키가 눌렸는지 확인
        keys = pygame.key.get_pressed()
        show_interaction_box_and_xy = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        # Shift 키를 누르고 있을 때만 상호작용 박스와 좌표를 그림
        if show_interaction_box_and_xy:
            # 1. 플레이어의 '실제 경계'를 기준으로 상호작용 범위를 계산 (판정 로직과 동일)
            player_left_grid = player.rect.left // BASE_TILE_SIZE
            player_right_grid = player.rect.right // BASE_TILE_SIZE
            player_top_grid = player.rect.top // BASE_TILE_SIZE
            player_bottom_grid = player.rect.bottom // BASE_TILE_SIZE
            
            start_reach_x = player_left_grid - INTERACTION_RADIUS_X
            end_reach_x = player_right_grid + INTERACTION_RADIUS_X
            start_reach_y = player_top_grid - (INTERACTION_RADIUS_Y + EXTRA_REACH_UP)
            end_reach_y = player_bottom_grid + INTERACTION_RADIUS_Y
            
            # 2. 계산된 범위 내의 모든 타일에 하이라이트를 그림
            for y in range(start_reach_y, end_reach_y + 1):
                for x in range(start_reach_x, end_reach_x + 1):
                    if 0 <= y < len(world_grid) and 0 <= x < len(world_grid[0]):
                        # ✨ 더 간단한 표시를 위해 하나의 하이라이트만 사용
                        screen.blit(highlight_surf_secondary, (x * BASE_TILE_SIZE - camera_x, y * BASE_TILE_SIZE - camera_y))
            # 좌표 표시
            math_pixel_y = SCREEN_HEIGHT - player.rect.bottom
            math_grid_y = math_pixel_y // BASE_TILE_SIZE
            
            pixel_pos_text = f"Pixel: ({player.rect.x}, {math_pixel_y})"
            grid_pos_text = f"Grid: ({player.rect.x // BASE_TILE_SIZE}, {math_grid_y})"

            # 2. 폰트를 사용해 텍스트를 이미지(Surface)로 렌더링합니다.
            pixel_text_surf = small_font.render(pixel_pos_text, True, WHITE)
            grid_text_surf = small_font.render(grid_pos_text, True, WHITE)

            # 3. 화면 우측 상단에 텍스트를 그립니다.
            screen.blit(pixel_text_surf, (SCREEN_WIDTH - pixel_text_surf.get_width() - 10, 10))
            screen.blit(grid_text_surf, (SCREEN_WIDTH - grid_text_surf.get_width() - 10, 10 + pixel_text_surf.get_height()))
        # 설치 미리보기 로직
        # 1. 선택된 아이템이 있고, 그 아이템을 1개 이상 가지고 있을 때만 미리보기를 그림
        if player.selected_item is not None and player.inventory.get(player.selected_item, 0) > 0:
            
            # 2. 설치 가능 여부를 판단하기 위한 모든 조건을 계산
            player_left_grid = player.rect.left // BASE_TILE_SIZE
            player_right_grid = player.rect.right // BASE_TILE_SIZE
            player_top_grid = player.rect.top // BASE_TILE_SIZE
            player_bottom_grid = player.rect.bottom // BASE_TILE_SIZE
            is_horizontally_close = (player_left_grid - INTERACTION_RADIUS_X <= mouse_grid_x <= player_right_grid + INTERACTION_RADIUS_X)
            is_vertically_close = (player_top_grid - (INTERACTION_RADIUS_Y + EXTRA_REACH_UP) <= mouse_grid_y <= player_bottom_grid + INTERACTION_RADIUS_Y)
            is_close_enough = is_horizontally_close and is_vertically_close
            
            is_empty_tile = 0 <= mouse_grid_y < len(world_grid) and 0 <= mouse_grid_x < len(world_grid[0]) and world_grid[mouse_grid_y][mouse_grid_x] is None
            is_not_overlapping = not player.rect.colliderect(selected_tile_rect)
            is_in_sight = has_line_of_sight(player_grid_pos, mouse_grid_pos, world_grid)

            has_support = False
            if is_empty_tile:
                if mouse_grid_y + 1 < len(world_grid) and world_grid[mouse_grid_y + 1][mouse_grid_x] is not None: has_support = True
                else:
                    for offset in [(0, -1), (1, 0), (-1, 0)]:
                        check_x, check_y = mouse_grid_x + offset[0], mouse_grid_y + offset[1]
                        if 0 <= check_y < len(world_grid) and 0 <= check_x < len(world_grid[0]) and world_grid[check_y][check_x] is not None:
                            has_support = True; break
            
            # 3. 모든 조건을 종합하여 최종적으로 설치 가능한지(can_place_preview)를 결정
            can_place_preview = all([is_close_enough, is_empty_tile, is_not_overlapping, is_in_sight, has_support])

            # 4. 결과에 따라 미리보기 상자를 그림
            preview_surf = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE), pygame.SRCALPHA)
            color = (0, 255, 0, 120) if can_place_preview else (255, 0, 0, 120)
            preview_surf.fill(color)
            screen.blit(preview_surf, (selected_tile_rect.x - camera_x, selected_tile_rect.y - camera_y))

        # --- ✨ 디버깅용 시야 레이저 그리기 시작 ✨ ---
        # 1. 플레이어와 마우스 위치 사이에 시야가 확보되었는지 확인합니다.
        is_sight_clear = has_line_of_sight(player_grid_pos, mouse_grid_pos, world_grid)
        
        # 2. 시야 확보 여부에 따라 색상을 결정합니다 (초록: 확보, 빨강: 막힘).
        laser_color = (0, 255, 0) if is_sight_clear else (255, 0, 0)
        
        # 3. 레이저의 시작점(플레이어 중심)과 끝점(마우스)의 화면 좌표를 계산합니다.
        start_laser_pos = (player.head_rect.centerx - camera_x, player.head_rect.centery - camera_y) # 수정된 코드 (머리 기준)
        # 마우스 위치(mouse_pos)는 이미 화면 좌표이므로 그대로 사용합니다.
        end_laser_pos = mouse_pos 
        
        # 4. 계산된 위치와 색상으로 화면에 얇은 선을 그립니다.
        pygame.draw.line(screen, laser_color, start_laser_pos, end_laser_pos, 2)
        # --- 디버깅용 시야 레이저 그리기 끝 ---

        # 인벤토리가 열려있을 때만 inventory_screen을 호출하여 그림
        if player.is_inventory_open:
            inventory_screen(screen, player) # ✨ 수정된 inventory_screen 함수 호출 (clock 인자 삭제)

        draw_ui(player)
        pygame.display.update()

    # 사망 애니메이션
    # 1. 죽는 순간의 신체 부위별 정확한 위치를 계산합니다.
    # (Player.draw() 메서드의 위치 계산 로직을 가져와 사용)
    scale_factor = player.scale_factor
    
    # 어깨와 엉덩이의 기준점을 계산
    left_hip_pos = (player.torso_rect.midbottom[0] - 6*scale_factor, player.torso_rect.midbottom[1])
    right_hip_pos = (player.torso_rect.midbottom[0] + 6*scale_factor, player.torso_rect.midbottom[1])
    left_shoulder_pos = (player.torso_rect.topleft[0] + 3, player.torso_rect.topleft[1] + 5)
    right_shoulder_pos = (player.torso_rect.topright[0] - 3, player.torso_rect.topright[1] + 5)

    # 기준점을 바탕으로 팔다리의 최종 Rect를 생성
    final_left_arm_rect = player.left_arm_rect.copy()
    final_left_arm_rect.midtop = left_shoulder_pos

    final_right_arm_rect = player.right_arm_rect.copy()
    final_right_arm_rect.midtop = right_shoulder_pos

    final_left_leg_rect = player.left_leg_rect.copy()
    final_left_leg_rect.midtop = left_hip_pos

    final_right_leg_rect = player.right_leg_rect.copy()
    final_right_leg_rect.midtop = right_hip_pos

    # 2. 계산된 위치를 기반으로 Debris 객체를 생성합니다.
    debris = [Debris(r.x, r.y, r.w, r.h, c) for r, c in [
        (player.head_rect, (255,220,180)), 
        (player.torso_rect, (0,0,255)),
        (final_left_arm_rect, (255,200,160)), 
        (final_right_arm_rect, (255,220,180)), 
        (final_left_leg_rect, (40,40,40)), 
        (final_right_leg_rect, (60,60,60))
    ]]
    
    # 3. 애니메이션을 재생합니다. (이하 코드는 동일)
    for _ in range(240):
        # 1. 모든 파편 조각을 업데이트합니다.
        for d in debris:
            # 각 파편 주변의 지형을 감지하여 충돌 정보로 넘겨줍니다.
            colliders = [t.rect for t in get_nearby_tiles(d.rect, world_grid) if t]
            d.update(colliders)
        
        # 2. 화면을 다시 그립니다. (이하 코드는 동일)
        screen.fill(SKY_COLOR)
        start_col_death = max(0, int(camera_x // BASE_TILE_SIZE))
        end_col_death = min(len(world_grid[0]), int((camera_x + SCREEN_WIDTH) // BASE_TILE_SIZE) + 2)
        start_row_death = max(0, int(camera_y // BASE_TILE_SIZE))
        end_row_death = min(len(world_grid), int((camera_y + SCREEN_HEIGHT) // BASE_TILE_SIZE) + 2)
        for y in range(start_row_death, end_row_death):
            for x in range(start_col_death, end_col_death):
                if world_grid[y][x]: world_grid[y][x].draw(screen, camera_x, camera_y, world_grid, x, y)
        for d in debris: d.draw(screen, camera_x, camera_y)
        draw_ui(player)
        pygame.display.update(); clock.tick(BASE_FPS)
    
    return "GAME_OVER"