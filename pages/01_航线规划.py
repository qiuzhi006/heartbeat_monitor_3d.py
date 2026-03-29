import streamlit as st
import pydeck as pdk
import pandas as pd
from utils import convert_coords

st.set_page_config(layout="wide")
st.title("🗺️ 航线规划 - 3D校园地图")

# 初始化session_state
if "coords_a" not in st.session_state:
    st.session_state.coords_a = {"lat": 32.2305, "lon": 118.7485}
if "coords_b" not in st.session_state:
    st.session_state.coords_b = {"lat": 32.2365, "lon": 118.7500}
if "flight_height" not in st.session_state:
    st.session_state.flight_height = 50

# 障碍物（南京科技职业学院校园建筑）
OBSTACLES = [
    {"name": "教学楼1", "lat": 32.2320, "lon": 118.7488, "height": 30},
    {"name": "教学楼2", "lat": 32.2332, "lon": 118.7490, "height": 35},
    {"name": "图书馆", "lat": 32.2340, "lon": 118.7492, "height": 25},
    {"name": "食堂", "lat": 32.2348, "lon": 118.7495, "height": 20},
    {"name": "宿舍楼", "lat": 32.2355, "lon": 118.7498, "height": 28},
]

# 侧边栏控制
with st.sidebar:
    st.header("🎮 坐标系设置")
    
    coord_system = st.selectbox(
        "输入坐标系",
        ["GCJ-02 (高德/腾讯)", "WGS-84 (GPS)"]
    )
    
    is_gcj02 = "GCJ-02" in coord_system
    
    st.divider()
    st.header("📍 起点 A")
    
    lat_a_input = st.number_input("纬度 A", value=32.2305, format="%.6f")
    lon_a_input = st.number_input("经度 A", value=118.7485, format="%.6f")
    
    st.header("📍 终点 B")
    
    lat_b_input = st.number_input("纬度 B", value=32.2365, format="%.6f")
    lon_b_input = st.number_input("经度 B", value=118.7500, format="%.6f")
    
    st.divider()
    st.header("✈️ 飞行参数")
    
    flight_height = st.slider("飞行高度 (m)", 20, 100, 50)
    st.session_state.flight_height = flight_height
    
    st.divider()
    
    st.subheader("📌 系统状态")
    col1, col2 = st.columns(2)
    with col1:
        st.success("A点已设")
    with col2:
        st.success("B点已设")
    st.caption(f"当前坐标系: {coord_system}")

# 坐标转换
if is_gcj02:
    lat_a_display, lon_a_display = lat_a_input, lon_a_input
    lat_b_display, lon_b_display = lat_b_input, lon_b_input
else:
    lon_a_display, lat_a_display = convert_coords(lon_a_input, lat_a_input, "WGS-84", "GCJ-02")
    lon_b_display, lat_b_display = convert_coords(lon_b_input, lat_b_input, "WGS-84", "GCJ-02")

# 保存到session_state
st.session_state.coords_a = {"lat": lat_a_display, "lon": lon_a_display}
st.session_state.coords_b = {"lat": lat_b_display, "lon": lon_b_display}
st.session_state.coord_system = coord_system
st.session_state.is_gcj02 = is_gcj02

# ==================== 3D地图绘制 ====================
st.subheader("🗺️ 校园3D地图")

# 航线数据
path_df = pd.DataFrame({
    "lat": [lat_a_display, lat_b_display],
    "lon": [lon_a_display, lon_b_display],
    "height": [flight_height, flight_height]
})

# 障碍物数据
obstacle_df = pd.DataFrame(OBSTACLES)

# 起点终点标记
points_df = pd.DataFrame([
    {"lat": lat_a_display, "lon": lon_a_display, "type": "起点A", "color": [0, 255, 0]},
    {"lat": lat_b_display, "lon": lon_b_display, "type": "终点B", "color": [255, 0, 0]}
])

# 地图视图
view_state = pdk.ViewState(
    latitude=(lat_a_display + lat_b_display) / 2,
    longitude=(lon_a_display + lon_b_display) / 2,
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
    get_width=5
)

# 障碍物图层
obstacle_layer = pdk.Layer(
    "ColumnLayer",
    data=obstacle_df,
    get_position="[lon, lat]",
    get_elevation="height",
    elevation_scale=1,
    radius=30,
    get_fill_color="[255, 100, 0, 150]"
)

# 点标记图层
point_layer = pdk.Layer(
    "ScatterplotLayer",
    data=points_df,
    get_position="[lon, lat]",
    get_color="color",
    get_radius=20
)

# 渲染
r = pdk.Deck(
    layers=[path_layer, obstacle_layer, point_layer],
    initial_view_state=view_state,
    tooltip={"text": "{name}"},
    map_style="mapbox://styles/mapbox/satellite-streets-v12"
)

st.pydeck_chart(r, use_container_width=True)

# 图例
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("🟢 **绿色** = 起点A")
with col2:
    st.markdown("🔴 **红色** = 终点B")
with col3:
    st.markdown("🟠 **橙色柱** = 障碍物")
with col4:
    st.markdown("🔴 **红线** = 航线")

# 坐标信息显示
st.divider()
st.subheader("📐 坐标信息")

col1, col2 = st.columns(2)
with col1:
    st.info(f"""
    **起点A** (GCJ-02)
    - 纬度: {lat_a_display:.6f}
    - 经度: {lon_a_display:.6f}
    """)
with col2:
    st.info(f"""
    **终点B** (GCJ-02)
    - 纬度: {lat_b_display:.6f}
    - 经度: {lon_b_display:.6f}
    """)

st.caption(f"飞行高度: {flight_height} 米 | 障碍物数量: {len(OBSTACLES)} 个")
