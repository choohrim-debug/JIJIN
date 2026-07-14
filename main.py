from vpython import *
import csv
import math
import time as ptime

# 1. 3D 화면 및 시각화 창 설정 (수도여고 디자인)
scene = canvas(title="🏢 수도여고 지진 공명 제어(TMD) 인터랙티브 시뮬레이터", 
               width=800, height=500, center=vector(0, 6, 0), background=color.white)

# 지반(바닥) 생성
ground = box(pos=vector(0, -0.5, 0), size=vector(30, 1, 15), color=color.gray(0.6))

# 실시간 2D 그래프 생성 (B트랙 만족)
vgraph = graph(title="📊 실시간 지진파 및 건물 진폭 그래프", 
               xtitle="시간 (초)", ytitle="세기 / 변위", width=800, height=350)
g_jijin = gcurve(color=color.blue, label="지진 가속도(지반)")
g_building = gcurve(color=color.orange, label="수도여고 건물 흔들림(진폭)")

# 글로벌 제어 변수 초기화
num_floors = 5         
tmd_mass_ratio = 0.02   
reset_flag = False      

building_parts = []
school_text = None
tmd_sphere = None

# 2. 수도여고 본관 3D 객체 생성 함수
def draw_school(floors, tmd_ratio):
    global building_parts, school_text, tmd_sphere
    
    # 기존 객체 지우기 (새로고침용)
    for part in building_parts:
        part.visible = False
        del part
    building_parts = []
    if school_text: school_text.visible = False
    if tmd_sphere: tmd_sphere.visible = False
        
    floor_height = 2.0
    total_height = floors * floor_height
    
    # 수도여고 특유의 넓은 벽돌색 본관 외형
    main_body = box(pos=vector(0, total_height/2, 0), size=vector(18, total_height, 5), color=vector(0.8, 0.45, 0.35))
    building_parts.append(main_body)
    
    # 정면 황금빛 모교 이름
    school_text = text(text="수도여고", pos=vector(-3, total_height - 1.4, 2.6), 
                       height=0.9, depth=0.1, color=color.yellow)
    
    # 창문 배치
    for f in range(floors):
        y_pos = f * floor_height + 1.0
        for x_pos in range(-8, 9, 2):
            if x_pos == 0 and f == floors - 1: continue 
            win = box(pos=vector(x_pos, y_pos, 2.52), size=vector(1.1, 0.9, 0.05), color=color.cyan)
            building_parts.append(win)
            
    # 옥상 빨간색 내진 추 (TMD)
    tmd_radius = 0.3 + (tmd_ratio * 10) * 0.2
    tmd_sphere = sphere(pos=vector(0, total_height + tmd_radius, 0), radius=tmd_radius, color=color.red)

# 3. 마우스 조작용 인터랙티브 UI 슬라이더 배치
scene.append_to_caption("\n📐 **컨트롤 패널** (슬라이더를 조작하면 시뮬레이션이 즉시 재시작됩니다)\n\n")

def set_floors(s):
    global num_floors, reset_flag
    num_floors = int(s.value)
    floor_text.text = f" 🏢 건물 높이: {num_floors}층 "
    reset_flag = True

def set_tmd(s):
    global tmd_mass_ratio, reset_flag
    tmd_mass_ratio = s.value
    tmd_text.text = f" 🔴 내진 추 무게 비율: {tmd_mass_ratio*100:.1f}% "
    reset_flag = True

slider(bind=set_floors, min=3, max=10, value=5, step=1)
floor_text = wtext(text=" 🏢 건물 높이: 5층 ")
scene.append_to_caption("   |   ")

slider(bind=set_tmd, min=0.0, max=0.1, value=0.02, step=0.005)
tmd_text = wtext(text=" 🔴 내진 추 무게 비율: 2.0% ")

# 4. 메인 시뮬레이션 루프
while True:
    draw_school(num_floors, tmd_mass_ratio)
    reset_flag = False
    
    g_jijin.delete()
    g_building.delete()
    
    x_b, v_b = 0.0, 0.0  
    x_t, v_t = 0.0, 0.0  
    x_g, v_g = 0.0, 0.0  
    dt = 0.1             
    
    M_floor = 1000.0              
    M = num_floors * M_floor      
    K = 180000.0 / num_floors     
    C = 2 * 0.04 * math.sqrt(K*M) 
    omega_target = math.sqrt(180000.0 / 5.0 / (5.0 * 1000.0)) 
    
    # 컴퓨터 로컬의 진짜 지진 CSV 파일을 안정적으로 읽어옴!
    try:
        with open('jijin_data.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # 헤더 패스
            
            for row in reader:
                if reset_flag: break 
                
                t = float(row[0])
                a_g = float(row[1]) * 15.0  # 스케일 조정
                
                if tmd_mass_ratio > 0:
                    m = M * tmd_mass_ratio   
                    k_t = m * (omega_target**2) 
                    c_t = 2 * 0.15 * math.sqrt(k_t * m) 
                    
                    a_b = -(K/M)*x_b - (C/M)*v_b + (k_t/M)*x_t + (c_t/M)*v_t - a_g
                    a_t = (K/M)*x_b + (C/M)*v_b - k_t*(1/m + 1/M)*x_t - c_t*(1/m + 1/M)*v_t
                else:
                    a_b = -(K/M)*x_b - (C/M)*v_b - a_g
                    a_t, v_t, x_t = 0.0, 0.0, 0.0
                
                v_b += a_b * dt
                x_b += v_b * dt
                if tmd_mass_ratio > 0:
                    v_t += a_t * dt
                    x_t += v_t * dt
                
                v_g += a_g * dt
                x_g += v_g * dt
                
                rate(10)  # 초당 10프레임 (0.1초 데이터 싱크)
                
                # 객체 움직임 동기화
                ground.pos.x = x_g 
                for part in building_parts:
                    part.pos.x += (a_g*0.05 + v_b*dt)
                school_text.pos.x = building_parts[0].pos.x - 3
                
                if tmd_sphere:
                    tmd_sphere.pos.x = building_parts[0].pos.x + x_t * 2.5
                
                # 실시간 그래프 출력
                g_jijin.plot(t, a_g / 15.0)
                g_building.plot(t, x_b)
                
    except FileNotFoundError:
        print("에러: 'jijin_data.csv' 파일이 코드와 같은 폴더에 있어야 합니다!")
        break
        
    if not reset_flag:
        ptime.sleep(1.0)
