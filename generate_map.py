import pygame
import numpy as np
import random
import os

output_folder = "output"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 地圖參數
MAP_SIZE = (20, 20)  # 地圖尺寸
CELL_SIZE = 30  # 每個格子的像素大小

# 顏色對應
COLORS = {
    0: (30, 144, 255),    # 水：藍色
    1:  (139, 69, 19),  # 山：棕色
    2: (138, 230, 0),    # 草：綠色
    3: (235, 117, 0),  # 沙漠：黃色
    4: (128, 128, 128) # 石頭：灰色
}

# 初始化地圖
def initialize_map():
    map_data = np.full(MAP_SIZE, 2, dtype=int)  # 預設為草地（2）

    # 隨機填入初始水域
    for _ in range(20):  # 水域的總塊數
        x, y = random.randint(0, MAP_SIZE[0] - 1), random.randint(0, MAP_SIZE[1] - 1)
        map_data[x, y] = 0  # 設置為水

    # 隨機生成山脈（兩片不黏在一起）
    mountain_centers = []  # 用來記錄已生成的山脈中心點

    for _ in range(2):  # 生成兩片山
        while True:
            center_x, center_y = random.randint(5, 15), random.randint(5, 15)
            
            # 檢查與已有山脈中心的距離
            if all(np.sqrt((center_x - cx)**2 + (center_y - cy)**2) > 7 for cx, cy in mountain_centers):
                mountain_centers.append((center_x, center_y))
                break  # 距離合適，退出循環
            
        # 生成山脈區域
        for i in range(-2, 3):  # 扩大山的覆盖范围
            for j in range(-2, 3):
                if 0 <= center_x + i < MAP_SIZE[0] and 0 <= center_y + j < MAP_SIZE[1]:
                    if map_data[center_x + i, center_y + j] == 2:  # 確保不覆蓋其他地形
                        map_data[center_x + i, center_y + j] = 1  # 設置為山

    # 隨機生成河流（更長的曲線）
    river_col_start = random.randint(0, MAP_SIZE[1] // 2)  # 河流起始點
    current_col = river_col_start

    for row in range(MAP_SIZE[0]):
        if map_data[row, current_col] == 2:  # 確保河流不覆蓋其他地形
            map_data[row, current_col] = 0  # 設置為水
        if random.random() < 0.4 and current_col + 1 < MAP_SIZE[1]:  # 隨機向右流
            current_col += 1
        elif random.random() < 0.4 and current_col - 1 >= 0:  # 隨機向左流
            current_col -= 1

    # 隨機生成沙漠
    center_x, center_y = random.randint(5, 15), random.randint(5, 15)
    for i in range(-2, 3):  # 沙漠的範圍
        for j in range(-2, 3):
            if 0 <= center_x + i < MAP_SIZE[0] and 0 <= center_y + j < MAP_SIZE[1]:
                if map_data[center_x + i, center_y + j] == 2:  # 確保沙漠不重疊其他地形
                    map_data[center_x + i, center_y + j] = 3  # 設置為沙漠

    # 隨機撒石頭
    for _ in range(30):  # 石頭的數量
        x, y = random.randint(0, MAP_SIZE[0] - 1), random.randint(0, MAP_SIZE[1] - 1)
        if map_data[x, y] == 2:  # 確保石頭只撒在草地上
            map_data[x, y] = 4  # 設置為石頭

    return map_data

def calculate_fitness(map_data):
    fitness = 0

    def find_connected_components(map_data, terrain_value, connectivity="4"):
        """找到指定地形的所有連通分量（4-連通或8-連通）"""
        visited = np.zeros_like(map_data, dtype=bool)
        components = []

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] if connectivity == "4" else \
                     [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        def dfs(x, y, component):
            if x < 0 or x >= map_data.shape[0] or y < 0 or y >= map_data.shape[1]:
                return
            if visited[x, y] or map_data[x, y] != terrain_value:
                return
            visited[x, y] = True
            component.append((x, y))
            for dx, dy in directions:
                dfs(x + dx, y + dy, component)

        for i in range(map_data.shape[0]):
            for j in range(map_data.shape[1]):
                if not visited[i, j] and map_data[i, j] == terrain_value:
                    component = []
                    dfs(i, j, component)
                    if component:
                        components.append(component)

        return components

    # 1. 檢查是否有符合條件的山聚集
    mountain_components = find_connected_components(map_data, 1, connectivity="4")
    valid_mountains = [comp for comp in mountain_components if len(comp) >= 15]
    if len(valid_mountains) == 2:  # 符合山數量限制
        fitness += 10 * len(valid_mountains)  # 每片符合條件的山增加適應度

    # 2. 檢查是否有符合條件的沙漠聚集
    desert_components = find_connected_components(map_data, 3, connectivity="4")
    valid_deserts = [comp for comp in desert_components if len(comp) >= 10]
    fitness += 5 * len(valid_deserts)  # 每片符合條件的沙漠增加適應度

    # 3. 對多餘的山或沙漠扣分
    all_valid_mountain_cells = set(cell for comp in valid_mountains for cell in comp)
    all_valid_desert_cells = set(cell for comp in valid_deserts for cell in comp)

    for x in range(map_data.shape[0]):
        for y in range(map_data.shape[1]):
            if map_data[x, y] == 1 and (x, y) not in all_valid_mountain_cells:
                fitness -= 2  # 多餘的山格子扣分
            if map_data[x, y] == 3 and (x, y) not in all_valid_desert_cells:
                fitness -= 1  # 多餘的沙漠格子扣分

    # 4. 檢查水域是否連通且夠長
    river_components = find_connected_components(map_data, 0, connectivity="8")
    valid_rivers = [comp for comp in river_components if len(comp) >= 20]  # 連通且長度達到 20
    if len(valid_rivers) > 0:  # 至少有一個有效河流
        fitness += 15
    else:
        fitness -= 10  # 如果沒有足夠長的河流，扣分

    # 5. 檢查河流是否在兩片山之間
    if len(valid_mountains) >= 2 and len(valid_rivers) > 0:
        river_cells = set(valid_rivers[0])  # 使用第一條有效河流
        mountain1 = set(valid_mountains[0])
        mountain2 = set(valid_mountains[1])

        # 檢查河流是否同時與兩片山相鄰
        connects_both_mountains = any(
            any((x + dx, y + dy) in mountain1 for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]) and
            any((x + dx, y + dy) in mountain2 for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)])
            for x, y in river_cells
        )

        if connects_both_mountains:
            fitness += 30  # 河流位於兩片山脈之間，大大增加適應度

    return fitness


# 錦標賽選擇
def tournament_selection(population, fitness_scores, tournament_size):
    selected = random.sample(list(zip(population, fitness_scores)), tournament_size)
    selected.sort(key=lambda x: x[1], reverse=True)
    return selected[0][0]

# 交叉
def crossover(map1, map2):
    cut = random.randint(0, MAP_SIZE[0])
    new_map = np.vstack((map1[:cut, :], map2[cut:, :]))
    return new_map

# 突變
def mutate(map_data, mutation_rate):
    new_map = map_data.copy()
    for _ in range(int(MAP_SIZE[0] * MAP_SIZE[1] * mutation_rate)):  # 10% 突變率
        x, y = random.randint(0, MAP_SIZE[0] - 1), random.randint(0, MAP_SIZE[1] - 1)
        new_map[x, y] = random.randint(0, 3)
    return new_map

# 在 pygame 中繪製地圖
def draw_map(screen, map_data):
    for x in range(MAP_SIZE[0]):
        for y in range(MAP_SIZE[1]):
            rect = pygame.Rect(y * CELL_SIZE, x * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, COLORS[map_data[x, y]], rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)  # 格子邊界

# 主演化流程
def evolutionary_algorithm():
    population = [initialize_map() for _ in range(50)]
    best_fitness = float('-inf')  # 跟蹤最佳適應度
    best_map = None
    mutation_rate = 0.05

    # 初始化 Pygame
    # pygame.init()
    # screen = pygame.display.set_mode((MAP_SIZE[1] * CELL_SIZE, MAP_SIZE[0] * CELL_SIZE))
    # pygame.display.set_caption("Evolutionary Map Generation")
    # clock = pygame.time.Clock()

    for generation in range(100):  # 演化 100 代
        fitness_scores = [calculate_fitness(map_data) for map_data in population]

        # 更新最佳個體
        max_fitness = max(fitness_scores)
        if max_fitness > best_fitness:
            best_fitness = max_fitness
            best_map = population[fitness_scores.index(max_fitness)]

        # 處理事件，避免窗口卡住
        # for event in pygame.event.get():
        #     if event.type == pygame.QUIT:
        #         pygame.quit()
        #         return best_map  # 提前結束程序

        # 顯示當前最佳地圖
        # screen.fill((255, 255, 255))  # 清空屏幕
        # draw_map(screen, best_map)
        # pygame.display.flip()
        # clock.tick(1)  # 每秒顯示一張地圖

        # 選擇與交叉
        sorted_population = [map_data for _, map_data in sorted(zip(fitness_scores, population), key=lambda x: x[0], reverse=True)]
        elite = sorted_population[:5]  # 精英策略，保留前兩個最優個體
        new_population = elite  # 將精英直接加入新族群

        while len(new_population) < 100:  # 確保新族群數量足夠
            parent1 = tournament_selection(population, fitness_scores, tournament_size=3)
            parent2 = tournament_selection(population, fitness_scores, tournament_size=3)
            child = crossover(parent1, parent2)
            child = mutate(child, mutation_rate)  # 動態調整突變率
            new_population.append(child)

        population = new_population

        # 動態調整突變率
        if generation > 20:  # 中後期降低突變率
            mutation_rate = 0.02
        else:
            mutation_rate = 0.05

        # 打印進度
        print(f"Generation {generation}, Best Fitness: {best_fitness:.2f}")

    # pygame.quit()
    return best_map

# 運行
# 跑 10 次，把每張圖都保存下來
for i in range(11):
    pygame.init()  # 確保 Pygame 被初始化
    screen = pygame.display.set_mode((MAP_SIZE[1] * CELL_SIZE, MAP_SIZE[0] * CELL_SIZE))
    best_map = evolutionary_algorithm()

    # 顯示並保存地圖
    screen.fill((255, 255, 255))  # 清空屏幕
    draw_map(screen, best_map)
    pygame.display.flip()

    # 保存地圖到 output 資料夾
    filename = os.path.join(output_folder, f"map_{i}.png")
    pygame.image.save(screen, filename)
    print(f"Map {i} saved as {filename}.")
    pygame.quit()

