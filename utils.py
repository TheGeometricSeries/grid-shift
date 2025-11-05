# utils.py

from config import TILE_SIZE

def has_line_of_sight(start_pos, end_pos, world_grid):
    """
    브레즈네햄 선 알고리즘을 사용해 두 그리드 좌표 사이에 시야가 확보되는지 확인합니다.
    맵 경계를 벗어나는지 확인하는 로직이 추가되었습니다.
    """
    # ✨ 맵의 가로, 세로 크기를 미리 구해둡니다.
    height = len(world_grid)
    if height == 0: return True # 맵이 비어있으면 항상 시야 확보
    width = len(world_grid[0])

    x0, y0 = start_pos
    x1, y1 = end_pos
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    
    if x0 == x1 and y0 == y1: return True
    
    while True:
        if x0 == x1 and y0 == y1:
            break

        # ✨ 맵 경계를 벗어나는지 먼저 확인합니다.
        if not (0 <= y0 < height and 0 <= x0 < width):
            return False # 시야선이 맵 밖으로 나가면 막힌 것으로 간주

        # 경계 안쪽에 있을 때만 타일 존재 여부를 확인합니다.
        if (x0, y0) != start_pos and world_grid[y0][x0] is not None:
            return False

        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
            
    return True