import json
import os
import random
from perlin_noise import PerlinNoise
from entities import Tile
from config import TILE_SIZE, SAVE_FOLDER, WOOD, LEAF

def get_nearby_tiles(entity_rect, world_grid):
    nearby_tiles = []
    start_x = max(0, entity_rect.left // TILE_SIZE - 2)
    end_x = min(len(world_grid[0]), entity_rect.right // TILE_SIZE + 3)
    start_y = max(0, entity_rect.top // TILE_SIZE - 2)
    end_y = min(len(world_grid), entity_rect.bottom // TILE_SIZE + 3)

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
        terrain_height = int(height / 2 + noise_val * (height / 4))
        terrain_height = max(5, min(height - 5, terrain_height))
        for y in range(terrain_height, height):
            map_data[y][x] = 1

    # 2단계: 동굴 생성
    cave_noise = PerlinNoise(octaves=octaves, seed=seed)
    cave_frequency = frequency * 2
    cave_threshold = 0.45 

    for y in range(height):
        for x in range(width):
            terrain_height = 0
            for h in range(height):
                if map_data[h][x] != 0:
                    terrain_height = h
                    break
            if y > terrain_height + 5:
                noise_val = cave_noise([x * cave_frequency, y * cave_frequency])
                if abs(noise_val) > cave_threshold:
                    map_data[y][x] = 0

    # ✨ 3단계: 지형 위에 나무 생성하기 (새로 추가된 부분) ✨
    for x in range(width):
        surface_y = -1
        for y in range(height):
            if map_data[y][x] in [1, 2]:
                surface_y = y
                break

        if surface_y != -1 and random.random() < 0.1: # 10% 확률
            # 잔디 블록(2) 위인지 확인 (잔디가 아직 없으므로 흙 블록(1) 위에 심도록 함)
            is_on_surface_soil = (surface_y > 0 and map_data[surface_y-1][x] == 0)
            if map_data[surface_y][x] == 1 and is_on_surface_soil:
                tree_height = random.randint(4, 7)
                
                # 나무 기둥 생성
                for i in range(tree_height):
                    if surface_y - 1 - i >= 0:
                        map_data[surface_y - 1 - i][x] = WOOD

                # 나뭇잎 생성
                leaf_top_y = surface_y - tree_height
                leaf_radius = 2
                for ly in range(-leaf_radius, leaf_radius + 1):
                    for lx in range(-leaf_radius, leaf_radius + 1):
                        if lx**2 + ly**2 < (leaf_radius + 0.5)**2:
                            if 0 <= leaf_top_y + ly < height and 0 <= x + lx < width:
                                if map_data[leaf_top_y + ly][x + lx] == 0:
                                    map_data[leaf_top_y + ly][x + lx] = LEAF
    
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