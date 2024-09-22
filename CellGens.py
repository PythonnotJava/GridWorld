import random

def generate_grid(column: int, row: int, num_obstacles: int, num_penalty: int, num_endpoints: int) -> tuple:
    """
    生成一个网格，其中包含起点、终点、障碍物、惩罚区域、可行区域。

    :param column: 网格的宽度
    :param row: 网格的高度
    :param num_obstacles: 障碍物数量
    :param num_penalty: 惩罚区域数量
    :param num_endpoints: 终点数量
    :return: 生成的二维网格
    """
    # 初始化网格
    grid = [[0 for _ in range(column)] for _ in range(row)]

    # 选择一个起点
    start_x, start_y = random.randint(0, row - 1), random.randint(0, column - 1)
    grid[start_x][start_y] = 3  # 起点标记为 3

    # 选择多个终点
    endpoints = set()
    while len(endpoints) < num_endpoints:
        ex, ey = random.randint(0, row - 1), random.randint(0, column - 1)
        if grid[ex][ey] == 0 and (ex != start_x or ey != start_y):
            grid[ex][ey] = 4  # 终点标记为 4
            endpoints.add((ex, ey))

    # 选择障碍物
    obstacles = set()
    while len(obstacles) < num_obstacles:
        ox, oy = random.randint(0, row - 1), random.randint(0, column - 1)
        if grid[ox][oy] == 0 and (ox, oy) not in endpoints and (ox, oy) != (start_x, start_y):
            grid[ox][oy] = 1  # 障碍物标记为 1
            obstacles.add((ox, oy))

    # 选择惩罚区域
    penalties = set()
    while len(penalties) < num_penalty:
        px, py = random.randint(0, row - 1), random.randint(0, column - 1)
        if grid[px][py] == 0 and (px, py) not in obstacles and (px, py) not in endpoints and (px, py) != (
        start_x, start_y):
            grid[px][py] = 2  # 惩罚区域标记为 2
            penalties.add((px, py))

    # 确保起点到终点有路径（使用简单的随机路径确保）
    def dfs(x, y, path):
        if (x, y) in endpoints:
            return True
        if not (0 <= x < row and 0 <= y < column) or grid[x][y] in {1, 2} or (x, y) in path:
            return False

        path.add((x, y))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if dfs(x + dx, y + dy, path):
                return True
        path.remove((x, y))
        return False

    path = set()
    dfs(start_x, start_y, path)

    return grid, [start_x, start_y]


# 示例使用
if __name__ == "__main__":
    column = 10
    row = 10
    num_obstacles = 15
    num_penalty = 5
    num_endpoints = 3

    grid = generate_grid(column, row, num_obstacles, num_penalty, num_endpoints)

    for row in grid:
        print(row)
