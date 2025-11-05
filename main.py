import os
import random
from config import *
from ui import title_screen, play_menu_screen, world_creation_screen, load_selection_screen, game_over_screen, loading_screen
from world import generate_map_data, create_world_grid, load_map
from game import main_game

def run_game():
    game_state = "TITLE"
    world_grid, world_name, player_start_pos = None, None, None
    loaded_data = None # 재시작 시 초기 위치를 기억하기 위함

    while True:
        if game_state == "TITLE":
            game_state = title_screen()
        
        elif game_state == "PLAY_MENU":
            game_state = play_menu_screen()

        elif game_state == "LOAD_SELECTION":
            result = load_selection_screen()

            if result == "PLAY_MENU": game_state = "PLAY_MENU"

            elif result is not None:
                loading_screen(STRINGS.get("loading_world", "월드 불러오는 중..."))
                loaded_data = load_map(result)

                if loaded_data and "map_data" in loaded_data:
                    world_grid = create_world_grid(loaded_data["map_data"])
                    player_start_pos = loaded_data.get("player_pos")
                    world_name = os.path.basename(result).replace(".json", "")
                    game_state = "GAMEPLAY"

                else: game_state = "TITLE" # 로드 실패
        
        elif game_state == "WORLD_CREATION":
            result = world_creation_screen()

            if result:
                world_name, seed = result
                loading_screen(f"'{world_name}' 생성 중...")
                # 1. 맵 너비를 10000으로 늘려 거대한 맵 데이터 생성
                MAP_WIDTH, MAP_HEIGHT = 10000, 80
                map_data = generate_map_data(MAP_WIDTH, MAP_HEIGHT, seed, 0.05, 4)
                
                # 2. 'world_grid'는 여기서 만들지 않음! create_world_grid 호출 삭제
                # world_grid = create_world_grid(map_data) # <- 이 줄 삭제

                # 3. 플레이어 시작 위치 찾기 (map_data 기준)
                player_start_pos = None
                spawn_x_col = random.randint(2500, 7500) # 스폰 위치
                for y in range(MAP_HEIGHT):
                    if map_data[y][spawn_x_col] != 0:
                        player_start_pos = (spawn_x_col * BASE_TILE_SIZE, (y - 3) * BASE_TILE_SIZE)
                        break
                
                loaded_data = {"map_data": map_data} # ✨ 가벼운 map_data를 전달하기 위해 저장
                game_state = "GAMEPLAY"
            else:
                game_state = "PLAY_MENU"

        elif game_state == "GAMEPLAY":
            # main_game에 world_grid 대신 map_data를 전달
            if loaded_data and "map_data" in loaded_data:
                game_state = main_game(loaded_data["map_data"], world_name, start_pos=player_start_pos)
            else:
                game_state = "TITLE" # 로드할 데이터가 없는 경우

        elif game_state == "GAME_OVER":
            next_action = game_over_screen()

            if next_action == "RESTART":
                # 불러온 맵에서 죽었다면 해당 맵의 시작 위치에서, 새로 만든 맵이면 기본 위치에서 재시작
                player_start_pos = loaded_data.get("player_pos") if loaded_data else None
                game_state = "GAMEPLAY"

            else: game_state = "TITLE"

if __name__ == '__main__':
    run_game()