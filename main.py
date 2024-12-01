import pygame
import os
import random

class RPGTile:
    WIDTH = 64  # 單元寬度
    HEIGHT = 64  # 單元高度

    def __init__(self, image_path):
        try:
            self.image = pygame.image.load(image_path)
            self.image = pygame.transform.scale(self.image, (self.WIDTH, self.HEIGHT))
        except pygame.error:
            self.image = None  # 如果圖片載入失敗，設置為 None

    @classmethod
    def get_tile(cls, tile_type):
        tile_map = {
            "0": cls.EMPTY,
            "1": cls.RIVER,
            "2": cls.GRASS,
            "3": cls.ROCK,
            "4": cls.RIVERSTONE,
            "5": cls.TREE,
        }
        return tile_map.get(tile_type, cls.EMPTY)

# 靜態變數初始化
RPGTile.EMPTY = RPGTile("data/empty.png")  # 對應 0
RPGTile.GRASS = RPGTile("data/grass.png")  # 對應 1
RPGTile.RIVERSTONE = RPGTile("data/riverstone.png")  # 對應 2
RPGTile.RIVER = RPGTile("data/river.png")  # 對應 3
RPGTile.ROCK = RPGTile("data/rock.png")  # 對應 4
RPGTile.TREE = RPGTile("data/tree.jpg")  # 對應 5

class RPGMap:
    def __init__(self, filename):
        try:
            with open(filename, "r") as file:
                self.map = [line.strip() for line in file.readlines()]
        except FileNotFoundError:
            print(f"Error: Map file '{filename}' not found.")
            self.map = ["0" * 10] * 10  # 回退到 10x10 的空白地圖

    def save_to_image(self, output_path):
        # 計算地圖的寬度和高度
        map_width = len(self.map[0]) * RPGTile.WIDTH
        map_height = len(self.map) * RPGTile.HEIGHT

        # 創建一個 Surface 來渲染整個地圖
        map_surface = pygame.Surface((map_width, map_height))

        for y, row in enumerate(self.map):
            for x, tile_type in enumerate(row):
                tile = RPGTile.get_tile(tile_type)
                if tile and tile.image:
                    # 在地圖的 Surface 上繪製對應的圖片
                    map_surface.blit(tile.image, (x * RPGTile.WIDTH, y * RPGTile.HEIGHT))

        # 保存地圖為圖像文件
        pygame.image.save(map_surface, output_path)
        print(f"Map saved to {output_path}")

def Generate(init_map, map_width, map_height):
    # 將地圖行轉為列表列表，以便能直接修改單元格
    new_map = [list(row) for row in init_map]

    # 定義替換比例，這裡假設替換 10% 的單元為 "5"
    replacement_rate = 0.1  # 可以根據需求調整比例
    num_replacements = int(map_width * map_height * replacement_rate)

    # 隨機選擇替換的位置
    for _ in range(num_replacements):
        x = random.randint(0, map_width - 1)
        y = random.randint(0, map_height - 1)
        if new_map[y][x] == "2":
            new_map[y][x] = "5"  # 替換為 "5"

    # 將列表列表轉回字符串列表
    new_map = ["".join(row) for row in new_map]

    
    return new_map

def create_individual(rpg_map, num_population=100):
    # 獲取地圖
    map_width = len(rpg_map.map[0])
    map_height = len(rpg_map.map)

    population = []

    # 生成指定數量的地圖
    for _ in range(num_population):
        new_map = Generate(rpg_map.map, map_width, map_height)
        population.append(new_map)

    return population
def mutate(map_data):
    # 將地圖行轉為列表列表，以便能直接修改單元格
    new_map = [list(row) for row in map_data]

    map_width = len(new_map[0])
    map_height = len(new_map)

    while True:
        x = random.randint(0, map_width - 1)
        y = random.randint(0, map_height - 1)
        # 只能改變草地或石頭
        if new_map[y][x] in ["2", "3"]:
            new_map[y][x] = "5" if new_map[y][x] != "5" else "0"  # 替換為樹或清空
            break

    # 將列表列表轉回字符串列表
    return ["".join(row) for row in new_map]

def evaluate_fitness(map_data):
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 上下左右
    score = 0
    num_trees = 0

    for y, row in enumerate(map_data):
        for x, tile in enumerate(row):
            if tile == "5":  # 如果是樹
                num_trees += 1
                # 檢查是否位於水旁邊
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= ny < len(map_data) and 0 <= nx < len(row):
                        if map_data[ny][nx] == "1":  # 水旁邊
                            score += 5  # 增加適應度分數
                        else:
                            score -= 2

    # 可選：對樹的總數進行適度懲罰或獎勵
    if num_trees < 10:
        score -= 10  # 如果樹太少，減少適應度
    elif num_trees > 50:
        score -= 20  # 如果樹太多，減少適應度
    else:
        score += 10  # 樹數量適中，增加適應度

    return score

def crossover(parent1, parent2):
    # 確保父代地圖大小相同
    if len(parent1) != len(parent2) or len(parent1[0]) != len(parent2[0]):
        raise ValueError("Parent maps must have the same dimensions.")

    # 分割點：將地圖分為上下部分
    split_point = len(parent1) // 2  # 假設地圖高度為 10，分割點為 5

    # 子代1：取父代1的上半部分 + 父代2的下半部分
    child1 = parent1[:split_point] + parent2[split_point:]
    # 子代2：取父代2的上半部分 + 父代1的下半部分
    child2 = parent2[:split_point] + parent1[split_point:]

    return child1, child2

def tournament_selection(population, fitness_scores, tournament_size=3):
    """
    使用錦標賽選擇機制選擇一個父代。
    Args:
        population (list of maps): 種群中的所有地圖。
        fitness_scores (list of float): 每張地圖的適應度分數。
        tournament_size (int): 錦標賽的參與個體數量。
    Returns:
        selected_parent: 選中的父代地圖。
    """
    # 隨機選擇若干個體進行錦標賽
    selected_indices = random.sample(range(len(population)), tournament_size)
    selected = [(population[i], fitness_scores[i]) for i in selected_indices]
    # 按適應度分數排序，返回適應度最高的個體
    selected.sort(key=lambda x: x[1], reverse=True)
    return selected[0][0]  # 返回適應度最高的地圖


def evolve_population(population, generations=100, tournament_size=5):
    for generation in range(generations):
        print(f"Generation {generation + 1}/{generations}")

        # 計算所有個體的適應度
        fitness_scores = [evaluate_fitness(map_data) for map_data in population]

        # 選擇適應度最高的個體（記錄當前最佳）
        best_index = fitness_scores.index(max(fitness_scores))
        best_map = population[best_index]

        # 進行交叉與變異，生成新種群
        new_population = []
        for _ in range(len(population) // 2):  # 每次產生兩個子代
            # 使用錦標賽選擇兩個父代
            parent1 = tournament_selection(population, fitness_scores, tournament_size)
            parent2 = tournament_selection(population, fitness_scores, tournament_size)

            # 確保父代不同
            while parent1 == parent2:
                parent2 = tournament_selection(population, fitness_scores, tournament_size)

            # 交叉生成子代
            child1, child2 = crossover(parent1, parent2)

            # 子代進行變異
            new_population.append(mutate(child1))
            new_population.append(mutate(child2))

        # 更新種群
        population = new_population

    return best_map


def main():
    pygame.init()

    for i in range(10):
        rpg_map = RPGMap("data/default.map")

        population = create_individual(rpg_map, num_population=100)

        best_map = evolve_population(population)
        # besr_map 存進data資料夾
        with open("data/best_map.map", "w") as file:
            file.write("\n".join(best_map))
        
        best_map = RPGMap("data/best_map.map")
        # 確保輸出資料夾存在
        os.makedirs("output", exist_ok=True)

        # 將地圖保存為圖像
        best_map.save_to_image(f"output/map_{i}.png")

    pygame.quit()

if __name__ == "__main__":
    main()
