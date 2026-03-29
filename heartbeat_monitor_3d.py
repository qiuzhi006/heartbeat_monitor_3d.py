# heartbeat_monitor_3d.py
import time
import pandas as pd
import streamlit as st
import pydeck as pdk
import numpy as np
from datetime import datetime

# 页面配置
st.set_page_config(layout="wide", page_title="无人机心跳监测 + 3D地图")

# 初始化数据
if "heartbeats" not in st.session_state:
    st.session_state.heartbeats = []
    st.session_state.last_time = time.time()
    st.session_state.running = False

# 南京科技职业学院校园内坐标 (GCJ-02)
# A点: 南门附近, B点: 北门附近, 中间有教学楼等障碍物
SCHOOL_COORDS = {
    "南门(A点)": {"lat": 32.2305, "lon": 118.7485},
    "教学楼1": {"lat": 32.2320, "lon": 118.7488},
    "教学楼2": {"lat": 32.2332, "lon": 118.7490},
    "图书馆": {"lat": 32.2340, "lon": 118.7492},
    "食堂": {"lat": 32.2348, "lon": 118.7495},
    "宿舍楼": {"lat": 32.2355, "lon": 118.7498},
    "北门(B点)": {"lat": 32.2365, "lon": 118.7500},
}

# 障碍物列表（建筑）
OBSTACLES = [
    {"name": "教学楼1", "lat": 32.2320, "lon": 118.7488, "height": 30},
    {"name": "教学楼2", "lat": 32.2332, "lon": 118.7490, "height": 35},
    {"name": "图书馆", "lat": 32.2340, "lon": 118.7492, "height": 25},
    {"name": "食堂", "lat": 32.2348, "lon": 118.7495, "height": 20},
    {"name": "宿舍楼", "lat": 32.2355, "lon": 118.7498, "height": 28},
]

st.title("🚁 无人机心跳监测 + 3D地图可视化")
st.caption("南京科技职业学院校园无人机模拟系统 | GCJ-02坐标系")

# ==================== 侧边栏：控制面板 ====================
with st.sidebar:
    st.header("🎮 控制面板")
    
    # 心跳模拟控制
    st.subheader("心跳模拟")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ 开始模拟", use_container_width=True):
            st.session_state.running = True
    with col2:
        if st.button("⏹️ 停止模拟", use_container_width=True):
            st.session_state.running = False
    
    if st.button("🗑️ 清空数据", use_container_width=True):
        st.session_state.heartbeats = []
        st.session_state.last_time = time.time()
        st.session_state.running = False
    
    st.divider()
    
    # A/B点坐标设置
    st.subheader("📍 航线规划 (GCJ-02)")
    
    # 起点A
    lat_a = st.number_input("起点A - 纬度", value=32.2305, format="%.6f")
    lon_a = st.number_input("起点A - 经度", value=118.7485, format="%.6f")
    
    # 终点B
    lat_b = st.number_input("终点B - 纬度", value=32.2365, format="%.6f")
    lon_b = st.number_input("终点B - 经度", value=118.7500, format="%.6f")
    
    # 飞行高度
    flight_height = st.slider("✈️ 飞行高度 (m)", min_value=20, max_value=100, value=50)
    
    st.divider()
    
    # 状态显示
    st.subheader("📡 飞行状态")
    if len(st.session_state.heartbeats) > 0:
        latest = st.session_state.heartbeats[-1]
        st.metric("最新心跳序号", latest["序号"])
        st.metric("最后心跳间隔", f"{latest['延迟(秒)']}秒")
        
        last_beat_time = st.session_state.heartbeats[-1]["时间"].timestamp()
        seconds_since = time.time() - last_beat_time
        if seconds_since > 3:
            st.error(f"⚠️ 掉线！{seconds_since:.1f}秒无心跳")
        else:
            st.success(f"✅ 在线中 | {seconds_since:.1f}秒前")
    else:
        st.info("等待心跳数据...")

# ==================== 心跳生成逻辑 ====================
def generate_heartbeat():
    seq = len(st.session_state.heartbeats) + 1
    now = datetime.now()
    st.session_state.heartbeats.append({
        "序号": seq,
        "时间": now,
        "延迟(秒)": round(time.time() - st.session_state.last_time, 3)
    })
    st.session_state.last_time = time.time()

if st.session_state.running:
    current_time = time.time()
    if current_time - st.session_state.last_time >= 1:
        generate_heartbeat()
        st.rerun()

# ==================== 3D地图绘制 ====================
st.subheader("🗺️ 3D校园地图 - 航线与障碍物")

# 准备航线数据（A点到B点）
flight_path = {
    "path": [
        [lon_a, lat_a, flight_height],
        [lon_b, lat_b, flight_height]
    ]
}

# 准备障碍物数据（3D立方体）
obstacle_data = []
for obs in OBSTACLES:
    obstacle_data.append({
        "name": obs["name"],
        "lat": obs["lat"],
        "lon": obs["lon"],
        "height": obs["height"],
        "width": 0.0005  # 约50米
    })

# 创建DataFrame用于pydeck
path_df = pd.DataFrame({
    "lat": [lat_a, lat_b],
    "lon": [lon_a, lon_b],
    "height": [flight_height, flight_height]
})

obstacle_df = pd.DataFrame(obstacle_data)

# 设置地图视图
view_state = pdk.ViewState(
    latitude=(lat_a + lat_b) / 2,
    longitude=(lon_a + lon_b) / 2,
    zoom=15,
    pitch=60,
    bearing=0
)

# 航线图层
path_layer = pdk.Layer(
    "LineLayer",
    data=path_df,
    get_source_position="[lon, lat]",
    get_target_position="[lon, lat]",
    get_color="[255, 0, 0, 200]",
    get_width=5,
    pickable=True,
)

# 障碍物图层（用柱状图表示）
obstacle_layer = pdk.Layer(
 
