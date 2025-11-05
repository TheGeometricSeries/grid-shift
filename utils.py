# utils.py

from config import TILE_SIZE

def has_line_of_sight(start_grid_pos, end_grid_pos, world_grid):
    # 이 함수는 grid 좌표를 받습니다.
    # 시야선이 시작하는 정확한 픽셀 좌표를 계산합니다.
    # player.torso_rect.center를 사용하므로 facing_direction의 영향을 받지 않습니다.
    start_pixel_x = start_grid_pos[0] * TILE_SIZE + TILE_SIZE // 2
    start_pixel_y = start_grid_pos[1] * TILE_SIZE + TILE_SIZE // 2

    # 시야선이 끝나는 정확한 픽셀 좌표를 계산합니다.
    end_pixel_x = end_grid_pos[0] * TILE_SIZE + TILE_SIZE // 2
    end_pixel_y = end_grid_pos[1] * TILE_SIZE + TILE_SIZE // 2

    # 브레젠험(Bresenham) 알고리즘을 사용하여 선 위의 모든 타일을 확인합니다.
    x0, y0 = start_pixel_x, start_pixel_y
    x1, y1 = end_pixel_x, end_pixel_y

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        # 현재 픽셀 위치를 그리드 좌표로 변환
        current_grid_x = x0 // TILE_SIZE
        current_grid_y = y0 // TILE_SIZE

        # 시작점이나 끝점은 확인하지 않고, 그 사이에 있는 블록만 확인
        # 현재 타일이 목표 타일과 동일하지 않고, 시작 타일과도 동일하지 않을 때만 블록 확인
        if (current_grid_x, current_grid_y) != start_grid_pos and \
           (current_grid_x, current_grid_y) != end_grid_pos:
            if 0 <= current_grid_y < len(world_grid) and \
               0 <= current_grid_x < len(world_grid[0]):
                # 해당 그리드 위치에 블록이 있고, 그 블록이 '통과할 수 없는' 블록이라면 시야를 가립니다.
                # 현재는 None이 아니면 모두 통과 불가로 가정합니다.
                if world_grid[current_grid_y][current_grid_x] is not None:
                    return False # 블록이 시야를 가림

        if x0 == x1 and y0 == y1:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

    return True # 시야를 가리는 블록이 없음