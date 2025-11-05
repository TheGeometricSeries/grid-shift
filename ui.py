import pygame
import sys
import os
import random
from config import *

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, font=button_font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text, self.color, self.hover_color = text, color, hover_color
        self.is_hovered, self.font = False, font
    def draw(self, screen):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect, border_radius=10)
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered

def loading_screen(message):
    screen.fill(SKY_COLOR)
    loading_text = button_font.render(message, True, WHITE)
    screen.blit(loading_text, loading_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)))
    pygame.display.update()

def title_screen():
    play_btn = Button(SCREEN_WIDTH/2-BTN_LARGE_W/2, 320, BTN_LARGE_W, BTN_LARGE_H, STRINGS["play_game"], GRAY, BLACK)
    quit_btn = Button(SCREEN_WIDTH/2-BTN_LARGE_W/2, 410, BTN_LARGE_W, BTN_LARGE_H, STRINGS["quit"], GRAY, BLACK)
    while True:
        mouse_pos = pygame.mouse.get_pos(); play_btn.check_hover(mouse_pos); quit_btn.check_hover(mouse_pos)
        screen.fill(SKY_COLOR)
        title_text = title_font.render(STRINGS["game_title"], True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH/2 - title_text.get_width()/2, 150))
        play_btn.draw(screen); quit_btn.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if play_btn.is_clicked(event): return "PLAY_MENU"
            if quit_btn.is_clicked(event): pygame.quit(); sys.exit()
        pygame.display.update(); clock.tick(BASE_FPS)

def play_menu_screen():
    new_btn = Button(SCREEN_WIDTH/2-BTN_MEDIUM_W/2, 280, BTN_MEDIUM_W, BTN_MEDIUM_H, STRINGS["new_world"], GRAY, BLACK)
    load_btn = Button(SCREEN_WIDTH/2-BTN_MEDIUM_W/2, 360, BTN_MEDIUM_W, BTN_MEDIUM_H, STRINGS["load_world"], GRAY, BLACK)
    back_btn = Button(20, 20, BTN_SMALL_W, BTN_SMALL_H, STRINGS["back_button"], GRAY, BLACK)
    while True:
        mouse_pos = pygame.mouse.get_pos(); new_btn.check_hover(mouse_pos); load_btn.check_hover(mouse_pos); back_btn.check_hover(mouse_pos)
        screen.fill(SKY_COLOR)
        title_text = title_font.render(STRINGS["play_game"], True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH/2 - title_text.get_width()/2, 150))
        new_btn.draw(screen); load_btn.draw(screen); back_btn.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if new_btn.is_clicked(event): return "WORLD_CREATION"
            if load_btn.is_clicked(event): return "LOAD_SELECTION"
            if back_btn.is_clicked(event): return "TITLE"
        pygame.display.update(); clock.tick(BASE_FPS)

def world_creation_screen():
    name_box = pygame.Rect(SCREEN_WIDTH/2 - 250, 250, 500, 60)
    seed_box = pygame.Rect(SCREEN_WIDTH/2 - 250, 380, 500, 60)
    create_btn = Button(SCREEN_WIDTH/2 - BTN_LARGE_W/2, 480, BTN_LARGE_W, BTN_LARGE_H, STRINGS["create_button"], GRAY, BLACK)
    back_btn = Button(20, 20, BTN_SMALL_W, BTN_SMALL_H, STRINGS["back_button"], GRAY, BLACK)
    
    name_text, seed_text, active_box = "", "", "name"

    while True:
        mouse_pos = pygame.mouse.get_pos()
        create_btn.check_hover(mouse_pos)
        back_btn.check_hover(mouse_pos)

        # --- 그리기 로직 (기존과 동일) ---
        screen.fill(SKY_COLOR)
        title_text = button_font.render(STRINGS["create_world_title"], True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH/2 - title_text.get_width()/2, 100))
        
        name_label = small_font.render(STRINGS["world_name_label"], True, WHITE)
        screen.blit(name_label, (name_box.x, name_box.y - 30))
        seed_label = small_font.render(STRINGS["seed_label"], True, WHITE)
        screen.blit(seed_label, (seed_box.x, seed_box.y - 30))

        pygame.draw.rect(screen, WHITE, name_box, border_radius=5)
        pygame.draw.rect(screen, WHITE, seed_box, border_radius=5)
        pygame.draw.rect(screen, YELLOW, name_box if active_box == "name" else seed_box, 4, border_radius=5)
        
        name_surf = input_font.render(name_text, True, BLACK)
        seed_surf = input_font.render(seed_text, True, BLACK)
        screen.blit(name_surf, (name_box.x + 15, name_box.y + 10))
        screen.blit(seed_surf, (seed_box.x + 15, seed_box.y + 10))
        
        create_btn.draw(screen)
        back_btn.draw(screen)
        
        # --- 이벤트 처리 로직 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # 생성하기 버튼 클릭 이벤트를 독립적으로 처리
            if create_btn.is_clicked(event) or back_btn.is_clicked(event):
                if create_btn.is_hovered: # 생성하기 버튼이 눌렸다면
                    final_name = name_text if name_text else f"World-{random.randint(100, 999)}"
                    final_seed = int(seed_text) if seed_text.isdigit() else random.randint(0, 1000)
                    return final_name, final_seed
                else: # 뒤로가기 버튼이 눌렸다면
                    return None

            if event.type == pygame.MOUSEBUTTONDOWN:
                if name_box.collidepoint(event.pos):
                    active_box = "name"
                elif seed_box.collidepoint(event.pos):
                    active_box = "seed"

            if event.type == pygame.KEYDOWN:
                # 엔터 키를 눌러도 월드 생성
                if event.key == pygame.K_RETURN:
                    final_name = name_text if name_text else f"World-{random.randint(100, 999)}"
                    final_seed = int(seed_text) if seed_text.isdigit() else random.randint(0, 1000)
                    return final_name, final_seed
                
                if event.key == pygame.K_TAB:
                    active_box = "seed" if active_box == "name" else "name"
                elif event.key == pygame.K_BACKSPACE:
                    if active_box == "name":
                        name_text = name_text[:-1]
                    else:
                        seed_text = seed_text[:-1]
                else:
                    if active_box == "name":
                        name_text += event.unicode
                    elif active_box == "seed" and event.unicode.isdigit():
                        seed_text += event.unicode
        
        pygame.display.update()
        clock.tick(BASE_FPS)

def load_selection_screen():
    back_btn = Button(20, 20, BTN_SMALL_W, BTN_SMALL_H, STRINGS["back_button"], GRAY, BLACK)
    while True:
        saved_files = sorted([f for f in os.listdir(SAVE_FOLDER) if f.endswith('.json')])
        world_buttons = []
        for i, filename in enumerate(saved_files):
            world_name = filename.replace(".json", "")
            load_btn = Button(SCREEN_WIDTH/2-220, 150+i*75, 360, 60, world_name, GRAY, BLACK)
            del_btn = Button(load_btn.rect.right+10, 150+i*75, 70, 60, "X", (200,50,50), (255,0,0), font=input_font)
            world_buttons.append({'load': load_btn, 'delete': del_btn, 'file': os.path.join(SAVE_FOLDER, filename)})
        
        mouse_pos = pygame.mouse.get_pos(); back_btn.check_hover(mouse_pos)
        for btn_group in world_buttons: btn_group['load'].check_hover(mouse_pos); btn_group['delete'].check_hover(mouse_pos)
        screen.fill(SKY_COLOR)
        title_text = title_font.render(STRINGS["load_title"], True, WHITE); screen.blit(title_text, (SCREEN_WIDTH/2 - title_text.get_width()/2, 50))
        for btn_group in world_buttons: btn_group['load'].draw(screen); btn_group['delete'].draw(screen)
        back_btn.draw(screen)
        
        action_taken = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if back_btn.is_clicked(event): return "PLAY_MENU"
            for btn_group in world_buttons:
                if btn_group['load'].is_clicked(event): return btn_group['file']
                if btn_group['delete'].is_clicked(event): os.remove(btn_group['file']); action_taken=True; break
        if action_taken: continue
        pygame.display.update(); clock.tick(BASE_FPS)

def pause_screen(world_grid, world_name, player_rect):
    # 이 함수가 호출될 때만 world.py에서 save_map을 불러옵니다.
    from world import save_map
    
    resume_btn = Button(SCREEN_WIDTH/2-BTN_MEDIUM_W/2, 280, BTN_MEDIUM_W,BTN_MEDIUM_H, STRINGS["pause_resume"], GRAY, BLACK)
    save_quit_btn = Button(SCREEN_WIDTH/2-BTN_MEDIUM_W/2, 360, BTN_MEDIUM_W,BTN_MEDIUM_H, STRINGS["pause_save_quit"], GRAY, BLACK)
    overlay = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,150)); screen.blit(overlay, (0, 0))
    while True:
        mouse_pos = pygame.mouse.get_pos(); resume_btn.check_hover(mouse_pos); save_quit_btn.check_hover(mouse_pos)
        resume_btn.draw(screen); save_quit_btn.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or resume_btn.is_clicked(event): return "RESUME"
            if save_quit_btn.is_clicked(event):
                save_map(world_grid, world_name, player_rect)
                return "QUIT_TO_TITLE"
        pygame.display.update(); clock.tick(BASE_FPS)

def draw_ui(player):
    pygame.draw.rect(screen, (200,0,0), (20, 20, 200, 25))
    if player.health > 0:
        pygame.draw.rect(screen, (0,200,0), (20, 20, 200 * (player.health/player.max_health), 25))
    health_text = small_font.render(f"HP: {int(player.health)} / {player.max_health}", True, WHITE); screen.blit(health_text, (25, 22))
    dirt_count = player.inventory.get("dirt", 0)
    #inventory_text = small_font.render(f"흙: {dirt_count}", True, WHITE); screen.blit(inventory_text, (20, 55))
    
    # 핫바 설정 (✨ 수정된 부분)
    slot_size = 30  # 슬롯 크기 줄임 (기존 50)
    slot_margin = 8 # 슬롯 간격 줄임 (기존 10)
    hotbar_width = (slot_size + slot_margin) * len(player.item_slots) - slot_margin
    hotbar_x = (SCREEN_WIDTH - hotbar_width) / 2
    hotbar_y = SCREEN_HEIGHT - slot_size - 15 # 화면 하단과의 간격 조정

    # 각 슬롯을 순회하며 그리기
    for i, item_name in enumerate(player.item_slots):
        slot_x = hotbar_x + i * (slot_size + slot_margin)
        
        # 슬롯 배경
        slot_rect = pygame.Rect(slot_x, hotbar_y, slot_size, slot_size)
        pygame.draw.rect(screen, GRAY, slot_rect, 3) # 배경 테두리 두께 조정

        # 선택된 슬롯이면 노란색으로 하이라이트
        if i == player.selected_slot:
            pygame.draw.rect(screen, YELLOW, slot_rect, 4) # 하이라이트 두께 조정

        # 슬롯에 아이템이 있다면 아이콘과 개수 표시
        if item_name is not None and player.inventory.get(item_name, 0) > 0:
            # 아이템 아이콘 (여기서는 간단히 색상으로 표시)
            if item_name == "dirt" or item_name == "grass":
                item_color = DIRT_COLOR
            elif item_name == "stone":
                item_color = STONE_COLOR
            elif item_name == "wood":
                item_color = WOOD_COLOR
            elif item_name == "leaf":
                item_color = LEAF_COLOR

            # 아이콘 위치 및 크기 조정
            icon_rect = pygame.Rect(slot_x + 7, hotbar_y + 7, slot_size - 14, slot_size - 14)
            pygame.draw.rect(screen, item_color, icon_rect)
            
            # 아이콘에 검정 테두리 추가
            pygame.draw.rect(screen, BLACK, icon_rect, 1)

            # 아이템 개수 텍스트
            count = player.inventory.get(item_name, 0)
            if count > 0:
                count_surf = small_font.render(str(count), True, WHITE)
                count_rect = count_surf.get_rect(bottomright=(slot_x + slot_size - 5, hotbar_y + slot_size - 5))
                screen.blit(count_surf, count_rect)

def game_over_screen():
    restart_btn = Button(SCREEN_WIDTH/2-150, 300, 300, 80, "다시 시작", GRAY, BLACK)
    quit_btn = Button(SCREEN_WIDTH/2-150, 400, 300, 80, "메인 메뉴로", GRAY, BLACK)
    overlay = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,150)); screen.blit(overlay, (0,0))
    while True:
        mouse_pos = pygame.mouse.get_pos(); restart_btn.check_hover(mouse_pos); quit_btn.check_hover(mouse_pos)
        game_over_text = title_font.render("GAME OVER", True, (255,50,50)); screen.blit(game_over_text, (SCREEN_WIDTH/2-game_over_text.get_width()/2, 150))
        restart_btn.draw(screen); quit_btn.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if restart_btn.is_clicked(event): return "RESTART"
            if quit_btn.is_clicked(event): return "TITLE"
        pygame.display.update(); clock.tick(BASE_FPS)

def inventory_screen(screen, player): # ✨ clock 인자 삭제
    """인벤토리 화면을 그리는 함수 (게임 루프 안에서 호출됨)"""
    
    # 뒷배경을 어둡게 만들기 위한 반투명 Surface
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) # 마지막 값(180)이 투명도

    # 인벤토리 창 설정
    inv_width, inv_height = 500, 300
    inv_x = (SCREEN_WIDTH - inv_width) / 2
    inv_y = (SCREEN_HEIGHT - inv_height) / 2
    inv_rect = pygame.Rect(inv_x, inv_y, inv_width, inv_height)

    # 슬롯 설정
    slot_size = 50
    slot_margin = 15
    cols = 8 # 가로 슬롯 개수
    
    # 그리기
    screen.blit(overlay, (0, 0)) # 어두운 뒷배경
    pygame.draw.rect(screen, (50, 50, 50), inv_rect) # 인벤토리 창 배경
    pygame.draw.rect(screen, GRAY, inv_rect, 3)    # 인벤토리 창 테두리

    # 인벤토리에 있는 아이템들을 순서대로 슬롯에 그리기
    item_list = list(player.inventory.items())
    
    # 실제로 아이템이 있는 슬롯만 필터링하여 그립니다.
    # 핫바 슬롯은 draw_ui에서 이미 그려지므로, 인벤토리 창은 일반 인벤토리 슬롯만 그립니다.
    current_col = 0
    current_row = 0
    max_cols = (inv_width - 2 * slot_margin) // (slot_size + slot_margin) # 창 크기에 맞는 최대 컬럼 계산
    max_rows = (inv_height - 2 * slot_margin) // (slot_size + slot_margin) # 창 크기에 맞는 최대 로우 계산

    drawn_count = 0
    for item_name, count in item_list:
        if count <= 0: continue # 개수가 0개 이하면 그리지 않음

        # 핫바 슬롯에 이미 있는 아이템이라면 건너뛰는 로직은 지금은 복잡하므로 일단 생략
        # 나중에 인벤토리 정렬 및 핫바와의 연동 시 추가 고려

        row = drawn_count // max_cols
        col = drawn_count % max_cols
        
        if row >= max_rows: break # 인벤토리 창 범위를 벗어나면 중단

        # 슬롯 위치 계산
        slot_x = inv_x + slot_margin + col * (slot_size + slot_margin)
        slot_y = inv_y + slot_margin + row * (slot_size + slot_margin)
        slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)

        # 슬롯 배경 및 아이콘 그리기
        pygame.draw.rect(screen, (80, 80, 80), slot_rect)
        pygame.draw.rect(screen, GRAY, slot_rect, 2)

        if item_name == "dirt" or item_name == "grass":
            item_color = DIRT_COLOR
        elif item_name == "stone":
            item_color = STONE_COLOR
        elif item_name == "wood":
            item_color = WOOD_COLOR
        else: item_color = WHITE
        
        icon_rect = pygame.Rect(slot_x + 10, slot_y + 10, slot_size - 20, slot_size - 20)
        pygame.draw.rect(screen, item_color, icon_rect)

        # 아이템 개수 텍스트
        count_surf = small_font.render(str(count), True, WHITE)
        count_rect = count_surf.get_rect(bottomright=(slot_x + slot_size - 5, slot_y + slot_size - 5))
        screen.blit(count_surf, count_rect)
        
        drawn_count += 1 # 그려진 아이템 개수 증가

    # 핫바는 draw_ui에서 따로 그려지므로 여기서는 그리지 않습니다.
    # draw_hotbar(screen, player) # 이 부분은 삭제

    # 인벤토리 제목
    title_surf = button_font.render(STRINGS.get("inventory_title", "인벤토리"), True, WHITE)
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH / 2, inv_y - 20))
    screen.blit(title_surf, title_rect)