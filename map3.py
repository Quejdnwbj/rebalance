import random
import time
import sys
import math
import pygame

# 迷宮維度設定 (16*16*16 的路徑空間，加上牆壁後網格大小為 33*33*33)
MAZE_SIZE = 16
GRID_SIZE = MAZE_SIZE * 2 + 1

def generate_3d_maze():
    """使用 3D DFS 演算法生成 16*16*16 的 3D 迷宮，並在終端機展示生成過程"""
    # 初始化 3D 網格：1 代表牆壁，0 代表通道
    grid = [[[1 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    
    random.seed(time.time() + random.randint(1, 9999))
    
    # 起點設定在 (1, 1, 1)
    start_x, start_y, start_z = 1, 1, 1
    grid[start_z][start_y][start_x] = 0
    
    stack = [(start_x, start_y, start_z)]
    
    # 用於終端機動畫的計時與狀態
    last_print_time = 0
    print_interval = 0.03  # 控制終端機刷新率，避免印太慢
    
    while stack:
        cx, cy, cz = stack[-1]
        
        # 尋找 6 個方向上相隔兩格且未走過的鄰居
        neighbors = []
        directions = [
            (0, 0, 2), (0, 0, -2),  # 上下 (Z)
            (0, 2, 0), (0, -2, 0),  # 前後 (Y)
            (2, 0, 0), (-2, 0, 0)   # 左右 (X)
        ]
        
        for dx, dy, dz in directions:
            nx, ny, nz = cx + dx, cy + dy, cz + dz
            if 0 < nx < GRID_SIZE - 1 and 0 < ny < GRID_SIZE - 1 and 0 < nz < GRID_SIZE - 1:
                if grid[nz][ny][nx] == 1:
                    neighbors.append((nx, ny, nz))
                    
        is_backtracking = False
        if neighbors:
            nx, ny, nz = random.choice(neighbors)
            # 打通中間的牆壁
            grid[cz + (nz - cz) // 2][cy + (ny - cy) // 2][cx + (nx - cx) // 2] = 0
            grid[nz][ny][nx] = 0
            stack.append((nx, ny, nz))
            current_x, current_y, current_z = nx, ny, nz
        else:
            current_x, current_y, current_z = stack.pop()
            is_backtracking = True
            
        # 限制終端機刷新頻率，使生成動畫流暢且不卡頓
        curr_time = time.time()
        if curr_time - last_print_time > print_interval or not stack:
            last_print_time = curr_time
            print("\033[H\033[J", end="")  # 清除螢幕
            print("=== 🛠️ 電腦正在製作 3D 迷宮 (16x16x16) ===")
            if is_backtracking:
                print(f"💬 狀態：無路可走！回溯至 ({current_x}, {current_y}, {current_z})")
            else:
                print(f"💬 狀態：正在打通 3D 牆壁至 ({current_x}, {current_y}, {current_z})")
            print(f"⏱️ 剩餘待處理分支節點：{len(stack)}")
            print(f"📍 當前層級 (Z軸): {current_z} / {GRID_SIZE-2}\n")
            
            # 印出當前層級 (Z軸) 的 2D 剖面圖作視覺化
            z_show = current_z
            for y in range(GRID_SIZE):
                row_str = ""
                for x in range(GRID_SIZE):
                    if x == current_x and y == current_y and z_show == current_z:
                        row_str += "↩️ " if is_backtracking else "🛠️ "
                    elif grid[z_show][y][x] == 1:
                        # 牆壁外觀
                        row_str += "█"
                    else:
                        row_str += "  "
                print(row_str)
            print("=========================================")
            
    # 決定出口：在最遠端 (GRID_SIZE-2, GRID_SIZE-2, GRID_SIZE-2) 附近尋找一個通道作為出口
    end_x, end_y, end_z = None, None, None
    for z in range(GRID_SIZE - 2, 0, -1):
        for y in range(GRID_SIZE - 2, 0, -1):
            for x in range(GRID_SIZE - 2, 0, -1):
                if grid[z][y][x] == 0:
                    end_x, end_y, end_z = x, y, z
                    break
            if end_x is not None: break
        if end_x is not None: break
        
    grid[start_z][start_y][start_x] = 'S'
    grid[end_z][end_y][end_x] = 'E'
    
    print("\033[H\033[J", end="")
    print("=== 🎉 3D 迷宮製作完成！ ===")
    print(f"🚪 入口位置：({start_x}, {start_y}, {start_z})")
    print(f"🏁 出口位置：({end_x}, {end_y}, {end_z})")
    print("這張 3D 地圖已經完全連通，且 100% 有解！\n")
    print("即將啟動第一人稱 3D 視窗...")
    time.sleep(1.5)
    
    return grid, (start_x, start_y, start_z), (end_x, end_y, end_z)

def run_3d_maze(grid, start, end):
    """啟動 Pygame 實時 3D 第一人稱迷宮"""
    pygame.init()
    screen_width = 1000
    screen_height = 750
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("3D 立體迷宮探索器 (16x16x16) 🎮")
    clock = pygame.time.Clock()
    
    # 玩家初始位置置中於格子
    px, py, pz = start[0] + 0.5, start[1] + 0.5, start[2] + 0.5
    
    # 視角朝向 (弧度)
    yaw = 0.0      # 水平旋轉
    pitch = 0.0    # 垂直上下看
    
    # 遊戲設定
    fov = math.pi / 3  # 60度視野
    fov_factor = screen_width / (2 * math.tan(fov / 2))
    
    # 控制參數
    move_speed = 4.0
    mouse_sensitivity = 0.003
    
    # 鎖定滑鼠指針以獲得流暢的 3D 視角控制
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)
    
    won = False
    running = True
    
    # 3D 牆壁立方體的相對頂點座標 (以中心點為基準，大小為 1x1x1)
    cube_vertices = [
        (-0.5, -0.5, -0.5), # 0
        ( 0.5, -0.5, -0.5), # 1
        ( 0.5,  0.5, -0.5), # 2
        (-0.5,  0.5, -0.5), # 3
        (-0.5, -0.5,  0.5), # 4
        ( 0.5, -0.5,  0.5), # 5
        ( 0.5,  0.5,  0.5), # 6
        (-0.5,  0.5,  0.5)  # 7
    ]
    
    # 立方體 6 個面的頂點索引與朝向向量
    cube_faces = [
        # (頂點索引, 法向 dx, dy, dz, 面顏色修飾)
        ([0, 1, 2, 3],  0,  0, -1, 0.7), # 底面 (朝 Z-)
        ([4, 5, 6, 7],  0,  0,  1, 1.0), # 頂面 (朝 Z+)
        ([0, 1, 5, 4],  0, -1,  0, 0.8), # 前面 (朝 Y-)
        ([2, 3, 7, 6],  0,  1,  0, 0.8), # 後面 (朝 Y+)
        ([0, 3, 7, 4], -1,  0,  0, 0.9), # 左面 (朝 X-)
        ([1, 2, 6, 5],  1,  0,  0, 0.9)  # 右面 (朝 X+)
    ]
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        # 讀取滑鼠移動量以旋轉視角
        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        if not won:
            yaw += mouse_dx * mouse_sensitivity
            pitch -= mouse_dy * mouse_sensitivity
            # 限制仰角與俯角，避免畫面翻轉
            pitch = max(-math.pi/2.2, min(math.pi/2.2, pitch))
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # 釋放滑鼠控制並退出
                    pygame.event.set_grab(False)
                    pygame.mouse.set_visible(True)
                    running = False
                elif won and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    running = False
                    
        if not won:
            # 鍵盤移動輸入
            keys = pygame.key.get_pressed()
            
            # 計算水平方向向量 (yaw=0 朝向 +Y，順時針旋轉至 +X)
            forward_x = math.sin(yaw)
            forward_y = math.cos(yaw)
            right_x = math.cos(yaw)
            right_y = -math.sin(yaw)
            
            dx, dy, dz = 0.0, 0.0, 0.0
            
            # W/S/A/D 水平移動
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dx += forward_x * move_speed * dt
                dy += forward_y * move_speed * dt
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dx -= forward_x * move_speed * dt
                dy -= forward_y * move_speed * dt
            if keys[pygame.K_a]:
                dx -= right_x * move_speed * dt
                dy -= right_y * move_speed * dt
            if keys[pygame.K_d]:
                dx += right_x * move_speed * dt
                dy += right_y * move_speed * dt
                
            # Space (上升) / Shift (下降) 移動 Z 軸
            if keys[pygame.K_SPACE]:
                dz += move_speed * dt
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                dz -= move_speed * dt
                
            # 3D 碰撞偵測 (每個軸獨立檢查，提供平滑滑行效果)
            margin = 0.25
            
            # 檢查 X 軸
            new_px = px + dx
            check_x = new_px + (margin if dx > 0 else -margin)
            if 0 <= int(check_x) < GRID_SIZE and 0 <= int(py) < GRID_SIZE and 0 <= int(pz) < GRID_SIZE:
                if grid[int(pz)][int(py)][int(check_x)] != 1:
                    px = new_px
                    
            # 檢查 Y 軸
            new_py = py + dy
            check_y = new_py + (margin if dy > 0 else -margin)
            if 0 <= int(px) < GRID_SIZE and 0 <= int(check_y) < GRID_SIZE and 0 <= int(pz) < GRID_SIZE:
                if grid[int(pz)][int(check_y)][int(px)] != 1:
                    py = new_py
                    
            # 檢查 Z 軸
            new_pz = pz + dz
            check_z = new_pz + (margin if dz > 0 else -margin)
            if 0 <= int(px) < GRID_SIZE and 0 <= int(py) < GRID_SIZE and 0 <= int(check_z) < GRID_SIZE:
                if grid[int(check_z)][int(py)][int(px)] != 1:
                    pz = new_pz
                    
            # 檢查是否到達終點 (E)
            if int(px) == end[0] and int(py) == end[1] and int(pz) == end[2]:
                won = True
                pygame.event.set_grab(False)
                pygame.mouse.set_visible(True)

        # ------------------ 3D 投影渲染繪製 ------------------
        # 清除畫面 (背景為星空黑藍色)
        screen.fill((10, 12, 18))
        
        # 收集視野內的所有 3D 面 (Polygons)
        # 渲染半徑設為 8，可兼顧良好效能與視覺距離
        view_radius = 8
        visible_faces = []
        
        start_x_search = max(0, int(px) - view_radius)
        end_x_search = min(GRID_SIZE, int(px) + view_radius + 1)
        start_y_search = max(0, int(py) - view_radius)
        end_y_search = min(GRID_SIZE, int(py) + view_radius + 1)
        start_z_search = max(0, int(pz) - view_radius)
        end_z_search = min(GRID_SIZE, int(pz) + view_radius + 1)
        
        for gz in range(start_z_search, end_z_search):
            for gy in range(start_y_search, end_y_search):
                for gx in range(start_x_search, end_x_search):
                    cell = grid[gz][gy][gx]
                    
                    if cell == 1:
                        # 牆壁立方體
                        for face_idx, (vertices_indices, ndx, ndy, ndz, shade_factor) in enumerate(cube_faces):
                            # 優化：如果相鄰的格子也是牆壁，就不用渲染這個共用面
                            adj_x, adj_y, adj_z = gx + ndx, gy + ndy, gz + ndz
                            if 0 <= adj_x < GRID_SIZE and 0 <= adj_y < GRID_SIZE and 0 <= adj_z < GRID_SIZE:
                                if grid[adj_z][adj_y][adj_x] == 1:
                                    continue
                                    
                            # 計算面中心點到相機的距離
                            face_cx = gx + ndx * 0.5
                            face_cy = gy + ndy * 0.5
                            face_cz = gz + ndz * 0.5
                            
                            dist = math.hypot(face_cx - px, face_cy - py, face_cz - pz)
                            if dist > view_radius:
                                continue
                                
                            # 背面剔除 (Backface Culling)
                            # 當向量 (面中心 - 相機) 與 (面法向) 的內積為正時，面朝向遠離相機，不繪製
                            v_cam_x = face_cx - px
                            v_cam_y = face_cy - py
                            v_cam_z = face_cz - pz
                            dot_product = v_cam_x * ndx + v_cam_y * ndy + v_cam_z * ndz
                            if dot_product > 0:
                                continue
                                
                            # 儲存該面進行後續渲染
                            visible_faces.append({
                                'type': 'wall',
                                'gx': gx, 'gy': gy, 'gz': gz,
                                'face_indices': vertices_indices,
                                'shade_factor': shade_factor,
                                'dist': dist
                            })
                            
                    elif cell == 'E':
                        # 終點傳送門 (Billboard 效果或發光體)
                        dist = math.hypot(gx + 0.5 - px, gy + 0.5 - py, gz + 0.5 - pz)
                        if dist < view_radius:
                            visible_faces.append({
                                'type': 'portal',
                                'gx': gx, 'gy': gy, 'gz': gz,
                                'dist': dist
                            })
                            
        # 依距離從遠到近排序面 (畫家演算法)
        visible_faces.sort(key=lambda f: f['dist'], reverse=True)
        
        # 3D 變換與投影函數
        def project_point(wx, wy, wz):
            # 平移至相機座標系
            tx = wx - px
            ty = wy - py
            tz = wz - pz
            
            # 繞 Z 軸旋轉 (Yaw，轉換為相機座標系需使用 yaw)
            cos_y, sin_y = math.cos(yaw), math.sin(yaw)
            rx = tx * cos_y - ty * sin_y
            ry = tx * sin_y + ty * cos_y
            
            # 繞 X 軸旋轉 (Pitch)
            cos_p, sin_p = math.cos(-pitch), math.sin(-pitch)
            final_y = ry * cos_p - tz * sin_p  # 相機前向深度
            final_z = ry * sin_p + tz * cos_p  # 相機上方高度
            final_x = rx                       # 相機右向寬度
            
            if final_y <= 0.05:  # 位於相機後面或過於貼近
                return None
                
            # 投影到螢幕座標
            sx = int(screen_width / 2 + (final_x / final_y) * fov_factor)
            sy = int(screen_height / 2 - (final_z / final_y) * fov_factor)
            return (sx, sy)
            
        # 繪製排序後的面
        for face in visible_faces:
            dist = face['dist']
            # 計算距離漸變 (越遠越暗的霧化效果)
            fog = max(0.0, 1.0 - (dist / view_radius))
            
            if face['type'] == 'wall':
                gx, gy, gz = face['gx'], face['gy'], face['gz']
                shade = face['shade_factor']
                
                # 計算該牆面的 4 個頂點投影
                projected_points = []
                for idx in face['face_indices']:
                    vx, vy, vz = cube_vertices[idx]
                    pt = project_point(gx + 0.5 + vx, gy + 0.5 + vy, gz + 0.5 + vz)
                    if pt:
                        projected_points.append(pt)
                        
                # 只有當所有頂點都成功投影時才繪製
                if len(projected_points) == 4:
                    # 科幻霓虹主色 (藍色偏青色)
                    base_r = int(0 * shade * fog)
                    base_g = int(140 * shade * fog)
                    base_b = int(255 * shade * fog)
                    
                    # 畫牆面
                    pygame.draw.polygon(screen, (base_r, base_g, base_b), projected_points)
                    # 畫牆面外框 (霓虹邊線)
                    line_color = (int(50 * fog), int(200 * fog), int(255 * fog))
                    pygame.draw.polygon(screen, line_color, projected_points, 1)
                    
            elif face['type'] == 'portal':
                gx, gy, gz = face['gx'], face['gy'], face['gz']
                # 繪製金黃色發光立方體傳送門
                t = time.time()
                glow = int(180 + 75 * math.sin(t * 8))
                r = int(glow * fog)
                g = int(glow * 0.8 * fog)
                b = int(50 * fog)
                
                # 分別繪製傳送門的多個面
                for face_indices in [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [0, 3, 7, 4], [1, 2, 6, 5]]:
                    pts = []
                    for idx in face_indices:
                        vx, vy, vz = cube_vertices[idx]
                        pt = project_point(gx + 0.5 + vx * 0.7, gy + 0.5 + vy * 0.7, gz + 0.5 + vz * 0.7) # 略縮小以成半空懸浮感
                        if pt:
                            pts.append(pt)
                    if len(pts) == 4:
                        pygame.draw.polygon(screen, (r, g, b), pts)
                        pygame.draw.polygon(screen, (255, 255, 200), pts, 2)
                        
        # ------------------ 右上角小地圖 (Minimap) ------------------
        # 顯示玩家所在 Z 軸高度層級的 2D 橫截面
        map_scale = 6
        current_layer = int(pz)
        current_layer = max(0, min(GRID_SIZE - 1, current_layer))
        
        map_w = GRID_SIZE * map_scale
        map_h = GRID_SIZE * map_scale
        map_x = screen_width - map_w - 20
        map_y = 20
        
        # 繪製地圖背景
        pygame.draw.rect(screen, (15, 15, 20), (map_x - 5, map_y - 5, map_w + 10, map_h + 10))
        pygame.draw.rect(screen, (60, 60, 80), (map_x - 5, map_y - 5, map_w + 10, map_h + 10), 2)
        
        for my in range(GRID_SIZE):
            for mx in range(GRID_SIZE):
                cell = grid[current_layer][my][mx]
                rect = (map_x + mx * map_scale, map_y + my * map_scale, map_scale, map_scale)
                if cell == 1:
                    pygame.draw.rect(screen, (50, 50, 70), rect)
                elif cell == 'S':
                    pygame.draw.rect(screen, (0, 120, 255), rect)
                elif cell == 'E':
                    pygame.draw.rect(screen, (255, 180, 0), rect)
                
        # 繪製玩家在小地圖上的投影
        ppx = map_x + px * map_scale
        ppy = map_y + py * map_scale
        pygame.draw.circle(screen, (255, 50, 50), (int(ppx), int(ppy)), 3)
        # 繪製方向視線
        p_dir_x = ppx + math.sin(yaw) * 8
        p_dir_y = ppy + math.cos(yaw) * 8
        pygame.draw.line(screen, (255, 50, 50), (int(ppx), int(ppy)), (int(p_dir_x), int(p_dir_y)), 1)
        
        # ------------------ UI 資訊顯示 ------------------
        font = pygame.font.SysFont("Arial", 16)
        
        # 顯示控制說明與當前高度
        pos_text = font.render(f"位置: ({px:.1f}, {py:.1f}, {pz:.1f}) | 當前層級 (Z軸): {current_layer}", True, (200, 220, 255))
        control_text1 = font.render("移動: W/S/A/D | 轉向: 滑鼠移動", True, (160, 180, 200))
        control_text2 = font.render("垂直移動: 空白鍵 (上升) / Shift (下降)", True, (160, 180, 200))
        esc_text = font.render("按 ESC 鍵釋放滑鼠並退出", True, (160, 180, 200))
        
        screen.blit(pos_text, (20, 20))
        screen.blit(control_text1, (20, 42))
        screen.blit(control_text2, (20, 64))
        screen.blit(esc_text, (20, 86))
        
        # 繪製準星 (Crosshair)
        pygame.draw.line(screen, (255, 255, 255), (screen_width // 2 - 8, screen_height // 2), (screen_width // 2 + 8, screen_height // 2), 1)
        pygame.draw.line(screen, (255, 255, 255), (screen_width // 2, screen_height // 2 - 8), (screen_width // 2, screen_height // 2 + 8), 1)
        
        # 通關畫面
        if won:
            overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            overlay.fill((10, 10, 15, 210))
            screen.blit(overlay, (0, 0))
            
            font_title = pygame.font.SysFont("Arial", 48, bold=True)
            font_sub = pygame.font.SysFont("Arial", 24)
            
            title_surf = font_title.render("🎉 成功逃脫 3D 終極迷宮！ 🎉", True, (255, 215, 0))
            sub_surf = font_sub.render("按 Enter 或 空白鍵 結束並退出", True, (240, 240, 240))
            
            screen.blit(title_surf, (screen_width // 2 - title_surf.get_width() // 2, screen_height // 2 - 50))
            screen.blit(sub_surf, (screen_width // 2 - sub_surf.get_width() // 2, screen_height // 2 + 20))
            
        pygame.display.flip()
        
    pygame.quit()

if __name__ == "__main__":
    grid, start, end = generate_3d_maze()
    run_3d_maze(grid, start, end)