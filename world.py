import json
import os
import random
from perlin_noise import PerlinNoise
from entities import Tile
from config import *

def get_nearby_tiles(entity_rect, world_grid):
    nearby_tiles = []
    start_x = max(0, entity_rect.left // BASE_TILE_SIZE - 2)
    end_x = min(len(world_grid[0]), entity_rect.right // BASE_TILE_SIZE + 3)
    start_y = max(0, entity_rect.top // BASE_TILE_SIZE - 2)
    end_y = min(len(world_grid), entity_rect.bottom // BASE_TILE_SIZE + 3)

    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            if world_grid[y][x]:
                nearby_tiles.append(world_grid[y][x])

    return nearby_tiles

def generate_map_data(width, height, seed, frequency, octaves):
    # 1단계: 펄린 노이즈로 기본 지형 생성
    map_data = [[0 for _ in range(width)] for _ in range(height)]
    surface_noise = PerlinNoise(octaves=2, seed=seed)
    
    for x in range(width):
        noise_val = surface_noise(x * 0.05)
        # terrain_height 계산을 안정적인 값으로 조정
        terrain_height = int(height / 2 + noise_val * (height / 4))
        terrain_height = max(5, min(height - 5, terrain_height)) # 최소/최대 높이 보장
        stone_layer_start_y = terrain_height + random.randint(8, 12)

        for y in range(terrain_height, height):
            # 설정된 깊이보다 깊으면 돌(type=3), 아니면 흙(type=1)으로 채움
            if y >= stone_layer_start_y:
                map_data[y][x] = 3 # 3번 타입은 돌
            else:
                map_data[y][x] = 1 # 1번 타입은 흙
            
    # 2단계: 지하 동굴 생성 (펄린 노이즈 방식)
    cave_noise = PerlinNoise(octaves=octaves, seed=seed + 1)
    cave_frequency = frequency * 2
    # 동굴이 너무 넓게 생성되지 않도록 threshold 조정
    cave_threshold = 0.3

    for y in range(height):
        for x in range(width):
            # 지표면에서 최소 5칸 아래부터 동굴 생성
            if y > terrain_height + 8:
                noise_val = cave_noise([x * cave_frequency, y * cave_frequency])
                if abs(noise_val) > cave_threshold:
                    map_data[y][x] = 0 # 동굴 파기

    # 3단계: 지형 위에 나무 생성하기 (새로 추가된 부분)
    for x in range(width):
        surface_y = -1
        # 지표면(가장 윗칸의 흙) 찾기
        for y in range(height):
            if map_data[y][x] == DIRT: # 흙(1)을 찾으면
                surface_y = y
                break

        # 지표면을 찾았고, 10% 확률로 나무 생성
        if surface_y != -1 and random.random() < 0.1: 
            tree_height = random.randint(4, 7) # 나무 기둥 높이
            
            # 나무 기둥 생성 (지표면 *위*부터)
            for i in range(tree_height):
                if surface_y - 1 - i >= 0: # 맵 상단을 벗어나지 않게
                    map_data[surface_y - 1 - i][x] = WOOD # 나무(4)

            # 나뭇잎 생성 (기둥 꼭대기 주변)
            leaf_top_y = surface_y - tree_height
            leaf_radius = 2 # 나뭇잎 반경
            for ly in range(-leaf_radius, leaf_radius + 1):
                for lx in range(-leaf_radius, leaf_radius + 1):
                    # 원 모양으로 잎 배치
                    if lx**2 + ly**2 < (leaf_radius + 0.5)**2:
                        # 맵 경계를 벗어나지 않는지 확인
                        if 0 <= leaf_top_y + ly < height and 0 <= x + lx < width:
                            # 기존 블록이 공기(0)일 때만 잎으로 덮기
                            if map_data[leaf_top_y + ly][x + lx] == AIR:
                                map_data[leaf_top_y + ly][x + lx] = LEAF # 잎(5)

    return map_data

def create_world_grid(map_data):
    world_grid = []
    for y, row in enumerate(map_data):
        grid_row = []
        for x, tile_type in enumerate(row):
            if tile_type != 0:
                is_exposed = (y == 0 or map_data[y-1][x] == 0)
                block_type = 2 if is_exposed else 1
                grid_row.append(Tile(x, y, block_type))

            else:
                grid_row.append(None)
        world_grid.append(grid_row)

    return world_grid

def grid_to_map_data(world_grid):
    return [[tile.type if tile else 0 for tile in row] for row in world_grid]

def save_map(world_grid, world_name, player_rect):
    map_data = grid_to_map_data(world_grid)
    save_data = {"map_data": map_data, "player_pos": (player_rect.x, player_rect.y)}
    filename = os.path.join(SAVE_FOLDER, f"{world_name}.json")

    with open(filename, 'w') as f: json.dump(save_data, f)

def load_map(filename):
    try:
        with open(filename, 'r') as f: return json.load(f)

    except (FileNotFoundError, json.JSONDecodeError):
        return None