import pygame
import sys
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pygame 초기화
pygame.init()
pygame.mixer.init()

# 화면 설정
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
BASE_FPS = 60
BASE_TILE_SIZE = 40

# 색상
SKY_COLOR, GRASS_COLOR, DIRT_COLOR, STONE_COLOR, WOOD_COLOR, LEAF_COLOR = (135, 206, 235), (34, 139, 34), (139, 69, 19), (130, 130, 130), (139, 90, 43), (0, 154, 23)
CRACK_COLOR = (max(0, DIRT_COLOR[0]-50), max(0, DIRT_COLOR[1]-30), max(0, DIRT_COLOR[2]-10), 180)
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
ORANGE, YELLOW = (255, 165, 0), (255, 255, 0)

# 아이템 타입 번호
AIR = 0
DIRT = 1
GRASS = 2
STONE = 3
WOOD = 4
LEAF = 5

# 파일 및 폴더 경로
SAVE_FOLDER = os.path.join(BASE_DIR, "saved_worlds")
FONT_FILE = os.path.join(BASE_DIR, "NanumGothic.ttf")

# 월드 저장 폴더 생성
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

# 화면 및 시계 객체 생성
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Blocky World")
clock = pygame.time.Clock()

# === 텍스처 생성 함수 ===
def create_block_textures():
    textures = {}

    # 1. 단색 텍스처 (흙, 돌, 나무)
    textures[DIRT] = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE))
    textures[DIRT].fill(DIRT_COLOR)
    
    textures[STONE] = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE))
    textures[STONE].fill(STONE_COLOR)
    
    textures[WOOD] = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE))
    textures[WOOD].fill(WOOD_COLOR)

    # 2. 잔디 텍스처 (위쪽 10픽셀만 초록색)
    textures[GRASS] = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE))
    textures[GRASS].fill(DIRT_COLOR)
    pygame.draw.rect(textures[GRASS], GRASS_COLOR, (0, 0, BASE_TILE_SIZE, 10))

    # 3. 나뭇잎 텍스처 (구멍 뚫기)
    # pygame.SRCALPHA 플래그를 줘서 투명도를 지원하는 Surface 생성
    leaf_surf = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE), pygame.SRCALPHA)
    leaf_surf.fill(LEAF_COLOR) # 일단 꽉 채우고
    
    # (0, 0, 0, 0)은 완전히 투명한 색상입니다.
    # 투명한 사각형을 그려서 "구멍"을 뚫습니다.
    pygame.draw.rect(leaf_surf, (0, 0, 0, 0), (5, 5, 10, 10))
    pygame.draw.rect(leaf_surf, (0, 0, 0, 0), (25, 10, 8, 8))
    pygame.draw.rect(leaf_surf, (0, 0, 0, 0), (10, 25, 15, 10))
    textures[LEAF] = leaf_surf

    return textures

# 게임 시작 시 텍스처 로드
BLOCK_TEXTURES = create_block_textures()

# 폰트 로딩
try:
    title_font = pygame.font.Font(FONT_FILE, 80)
    button_font = pygame.font.Font(FONT_FILE, 35)
    input_font = pygame.font.Font(FONT_FILE, 45)
    small_font = pygame.font.Font(FONT_FILE, 20)
    indicator_font = pygame.font.Font(FONT_FILE, 40)
except pygame.error:
    print(f"오류: {FONT_FILE} 폰트 파일을 찾을 수 없습니다.")
    sys.exit()

# 언어 데이터 로딩
try:
    with open(os.path.join(BASE_DIR, 'strings.json'), 'r', encoding='utf-8') as f:
        LANG_DATA = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    print("오류: strings.json 파일이 없거나 내용이 비어있습니다.")
    sys.exit()

LANGUAGE = "ko"
STRINGS = LANG_DATA[LANGUAGE]

# 버튼 크기
BTN_LARGE_W, BTN_LARGE_H = 240, 60
BTN_MEDIUM_W, BTN_MEDIUM_H = 240, 55
BTN_SMALL_W, BTN_SMALL_H = 100, 45

# 월드 상수
BREAK_COOLDOWN = 15
MAX_BREAK_TIME = 60
GRASS_SPREAD_COOLDOWN = 30
GRASS_DECAY_TIME = 45

# 아이템 자석 효과 상수
ITEM_MAGNET_RADIUS = 40  # 플레이어로부터 40픽셀(블록 1칸) 반경
ITEM_MAGNET_SPEED = 3   # 초당 3픽셀의 속도로 끌어당김

# 낙하 데미지 상수
SAFE_FALL_DISTANCE = BASE_TILE_SIZE * 4  # 4칸 (160픽셀)까지는 안전
FALL_DAMAGE_SCALAR = 0.1                # 안전 높이를 초과한 픽셀당 0.1의 데미지

# 적 데미지 상수
ENEMY_DAMAGE = 10 # 적의 공격 한 방당 데미지

# 청크 시스템 상수
CHUNK_SIZE = 32  # 맵을 32x32 타일 크기의 청크로 나눔

# 통과 가능한 블록 타입 정의 (플레이어가 충돌하지 않음)
NON_SOLID_BLOCKS = {WOOD, LEAF}