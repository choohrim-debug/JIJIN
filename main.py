from vpython import *
import csv
import math

# 1. 화면 및 시각화 창 설정 (수도여고 스킨)
scene = canvas(title="🏢 수도여고 지진 공명 제어(TMD) 인터랙티브 시뮬레이터", 
               width=800, height=500, center=vector(0, 6, 0), background=color.white)

# 지반(바닥) 생성
ground = box(pos=vector(0, -0.5, 0), size=vector(30, 1, 15), color=color.gray(0.6))

# 실시간 2D 그래프 생성 (지진파와 건물의 움직임을 실시간 비교)
vgraph = graph(title="📊 실시간 지진파 및 건물 진폭 그래프", 
               xtitle="시간 (초)", ytitle="세기 / 변위", width=800, height=350)
g_jijin = gcurve(color=color.blue, label="지진 가속도(지반)")
g_building = gcurve(color=color.orange, label="수도여고 건물 흔들림(진폭)")

# 2. 글로벌 변수 초기화 (고2 물리 엔진 피팅)
num_floors = 5         # 초기 건물 높이: 5층
tmd_mass_ratio = 0.02   # 초기 추 무게 비율: 2%
reset_flag = False      # 슬라이더 조작 시 재시작을 위한 플래그

building_parts = []
school_text = None
tmd_sphere = None

# 3. 수도여고 본관 건물 및 내진 추를 그리는 함수
def draw_school(floors, tmd_ratio):
    global building_parts, school_text, tmd_sphere
    
    # 기존에 그려진 건물 잔해들 제거 (새로고침용)
    for part in building_parts:
        part.visible = False
        del part
    building_parts = []
    if school_text: school_text.visible = False
    if tmd_sphere: tmd_sphere.visible = False
        
    floor_height = 2.0
    total_height = floors * floor_height
    
    # 수도여고 본관 특유의 넓고 단단한 직사각형 형태 교사(🧱 따뜻한 벽돌색 느낌)
    main_body = box(pos=vector(0, total_height/2, 0), size=vector(18, total_height, 5), color=vector(0.8, 0.45, 0.35))
    building_parts.append(main_body)
    
    # 본관 정면에 빛나는 황금빛 모교 이름 새기기 ("수도여고")
    school_text = text(text="수도여고", pos=vector(0, total_height - 1.4, 2.6), 
                       align='center', height=0.9, depth=0.1, color=color.yellow)
    
    # 학교 건물답게 층별로 촘촘하고 예쁜 격자형 창문 배치
    for f in range(floors):
        y_pos = f * floor_height + 1.0
        for x_pos in range(-8, 9, 2):
            if x_pos == 0 and f == floors - 1: continue # 교명 자리 비워두기
            win = box(pos=vector(x_pos, y_pos, 2.52), size=vector(1.1, 0.9, 0.05), color=color.cyan)
            building_parts.append(win)
            
    # 옥상에 설치된 붉은색 내진 장치 추 (TMD) - 무게 비율에 따라 크기가 변함
    tmd_radius = 0.3 + (tmd_ratio * 10) * 0.2
    tmd_sphere = sphere(pos=vector(0, total_height + tmd_radius, 0), radius=tmd_radius, color=color.red)

# 4. 인터랙티브 UI 슬라이더 및 설명 텍스트 배치
scene.append_to_caption("\n📐 **컨트롤 패널** (슬라이더를 조작하면 처음부터 다시 실험이 시작됩니다)\n\n")

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

# 건물 높이 슬라이더 (3층 ~ 10층)
slider(bind=set_floors, min=3, max=10, value=5, step=1)
floor_text = wtext(text=" 🏢 건물 높이: 5층 ")
scene.append_to_caption("   |   ")

# 추 무게 슬라이더 (0% = 없음 ~ 10%)
slider(bind=set_tmd, min=0.0, max=0.1, value=0.02, step=0.005)
tmd_text = wtext(text=" 🔴 내진 추 무게 비율: 2.0% ")

# 5. 메인 물리 연산 및 지진 구동 루프
while True:
    # 슬라이더 값에 맞춰 건물 새로 그리기
    draw_school(num_floors, tmd_mass_ratio)
    reset_flag = False
    
    # 그래프 초기화
    g_jijin.delete()
    g_building.delete()
    
    # 물리 공식용 변수 초기화
    x_b, v_b = 0.0, 0.0  # 건물의 상대 변위 및 속도
    x_t, v_t = 0.0, 0.0  # 추(TMD)의 상대 변위 및 속도
    x_g, v_g = 0.0, 0.0  # 지반(땅)의 절대 변위 및 속도
    dt = 0.1             # 데이터 간격 (0.1초)
    
    # 고2 수준 물리 상수 설정 (층수에 따라 질량과 강성이 변함)
    M_floor = 1000.0              # 한 층당 질량
    M = num_floors * M_floor      # 건물 총 질량
    K = 180000.0 / num_floors     # 건물 강성 (높아질수록 유연해짐 -> stiffness 감소)
    C = 2 * 0.04 * math.sqrt(K*M) # 건물의 자체 구조 감쇠 (4%)
    
    # 💡 첨단기술 탐구의 핵심: 내진 추가 '5층 건물' 기준(모교의 평균 높이)으로 튜닝되어 있다고 가정!
    # 이로 인해 5층일 때는 공명을 기가 막히게 막지만, 3층이나 9층으로 바꾸면 튜닝이 어긋나 흔들리게 됨!
    omega_target = math.sqrt(180000.0 / 5.0 / (5.0 * 1000.0)) # 5층 건물의 고유 진동수
    
    # CSV 파일 읽기 프로세스
    try:
        with open('jijin_data.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader) # 제목 행 패스
            
            for row in reader:
                if reset_flag: break # 사용자가 슬라이더 만지면 즉시 루프 탈출 후 재시작
                
                t = float(row[0])
                a_g = float(row[1]) * 15.0 # 시각적 효과를 위해 지진 가속도 스케일 업
                
                # 6. 뉴턴 운동 제2법칙($F=ma$) 기반 수치해석 물리 엔진
                if tmd_mass_ratio > 0:
                    m = M * tmd_mass_ratio   # 추의 진짜 질량
                    k_t = m * (omega_target**2) # 추의 용수철 강성
                    c_t = 2 * 0.15 * math.sqrt(k_t * m) # 추의 자체 감쇠 (15%)
                    
                    # 운동방정식 가속도 도출
                    a_b = -(K/M)*x_b - (C/M)*v_b + (k_t/M)*x_t + (c_t/M)*v_t - a_g
                    a_t = (K/M)*x_b + (C/M)*v_b - k_t*(1/m + 1/M)*x_t - c_t*(1/m + 1/M)*v_t
                else:
                    # 추가 없을 때 (0% 일 때)
                    a_b = -(K/M)*x_b - (C/M)*v_b - a_g
                    a_t, v_t, x_t = 0.0, 0.0, 0.0
                
                # 속도 및 변위 업데이트 (오일러-크롬 방법)
                v_b += a_b * dt
                x_b += v_b * dt
                if tmd_mass_ratio > 0:
                    v_t += a_t * dt
                    x_t += v_t * dt
                
                # 지반의 움직임 계산 (가속도를 적분하여 시각화)
                v_g += a_g * dt
                x_g += v_g * dt
                
                # 7. 3D 그래픽 객체 위치 실시간 연동 (화면 렌더링)
                rate(10) # 0.1초 데이터 간격에 맞추어 초당 10번 프레임 실행
                
                # 지반은 지진 변위대로 움직임
                ground.pos.x = x_g 
                # 건물은 [지반 위치 + 건물의 상대 흔들림] 만큼 움직임
                for part in building_parts:
                    part.pos.x += (a_g*0.05 + v_b*dt) # 부드러운 흔들림 연출
                school_text.pos.x = building_parts[0].pos.x - 3 # 교명 텍스트 동기화
                
                # 추는 [건물 위치 + 추의 상대 움직임] 만큼 반대로 움직이며 중심을 잡음
                if tmd_sphere:
                    tmd_sphere.pos.x = building_parts[0].pos.x + x_t * 2.5
                
                # 8. 실시간 그래프 플로팅 (B트랙 시각화 완성)
                g_jijin.plot(t, a_g / 15.0)
                g_building.plot(t, x_b)
                
    except FileNotFoundError:
        print("에러: 'jijin_data.csv' 파일이 코드와 같은 폴더에 있는지 확인하세여!")
        break
        
    # 데이터가 한 바퀴 다 돌면 1초 쉬었다가 자동 무한 반복
    if not reset_flag:
        ptime.sleep(1.0)
