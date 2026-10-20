# tb4_nav_yolo – TurtleBot 4: Nav2 Autonomous Navigation + YOLO

Package ROS 2 Humble gồm:
- `waypoint_navigator`: gửi tuần tự ≥ 3 goal tới Nav2 bằng `nav2_simple_commander`.
- `yolo_detector`: subscribe camera RGB, nhận diện vật thể bằng YOLO (Ultralytics), vẽ bbox, in kết quả ra terminal và publish ảnh lên `/yolo/image_annotated`.

## 1. Cài đặt
```bash
sudo apt update
sudo apt install ros-humble-turtlebot4-navigation ros-humble-turtlebot4-simulator \
                 ros-humble-nav2-simple-commander ros-humble-cv-bridge
pip install ultralytics "numpy<2"
```
> `numpy<2` cần thiết vì `cv_bridge` của Humble biên dịch với NumPy 1.x.
> Nếu `cv2.imshow` báo lỗi Qt/xcb: `pip uninstall opencv-python && pip install opencv-python-headless`,
> đặt `show_window: false` trong `config/yolo.yaml` và xem ảnh bằng `rqt_image_view` (topic `/yolo/image_annotated`) hoặc RViz2.

## 2. Build
```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone <URL_REPO_CUA_BAN> tb4_nav_yolo
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select tb4_nav_yolo
source install/setup.bash
```

## 3. Chạy (mỗi lệnh một terminal, đều `source` ROS + workspace)

**Terminal 1 – Gazebo (world maze, dùng NVIDIA nếu cần, xem mục 4):**
```bash
ros2 launch turtlebot4_ignition_bringup turtlebot4_ignition.launch.py world:=maze
```
Bấm **Play**. World `maze` chỉ có tường nên cần thêm vật thể (person, chair, fire extinguisher...) bằng Gazebo GUI → **Resource Spawner** (Fuel). Đặt ở góc hoặc ngõ cụt của mê cung, **không chặn hẹp lối đi**, và ở chỗ camera robot nhìn thấy khi đi qua.

**Terminal 2 – Localization (AMCL) với map tuần trước:**
```bash
ros2 launch turtlebot4_navigation localization.launch.py \
    map:=$HOME/ros2_ws/src/tb4_nav_yolo/maps/map.yaml
```

**Terminal 3 – Nav2:**
```bash
ros2 launch turtlebot4_navigation nav2.launch.py
```

**Terminal 4 – RViz2:**
```bash
ros2 launch turtlebot4_viz view_robot.launch.py
```
Đặt **2D Pose Estimate** để scan `/scan` trùng tường trên map (hoặc dùng `initial_pose` trong `config/goals.yaml`).

**Lấy toạ độ goal:** Publish Point + `ros2 topic echo /clicked_point`, hoặc `ros2 topic echo /amcl_pose`.
Điền vào `config/goals.yaml` (x, y, yaw rad), rồi build lại (hoặc `colcon build --symlink-install`).

**Terminal 5 – Điều hướng + YOLO:**
```bash
ros2 launch tb4_nav_yolo nav_yolo.launch.py
```
Hoặc chạy riêng:
```bash
ros2 run tb4_nav_yolo yolo_detector --ros-args --params-file config/yolo.yaml
ros2 run tb4_nav_yolo waypoint_navigator --ros-args --params-file config/goals.yaml
```

## 4. Chạy Gazebo bằng card NVIDIA (PRIME offload)
```bash
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export __VK_LAYER_NV_optimus=NVIDIA_only
```

## 5. Tham số chính
| Node | Tham số | Ý nghĩa |
|---|---|---|
| waypoint_navigator | `goals` | danh sách phẳng `[x,y,yaw,...]` |
| waypoint_navigator | `set_initial_pose`, `initial_pose` | tự đặt pose ban đầu |
| waypoint_navigator | `loop` | lặp lại vòng goal |
| yolo_detector | `model` | `yolov8n.pt`, `yolo11n.pt`... |
| yolo_detector | `conf`, `max_fps`, `show_window` | ngưỡng, tốc độ suy luận, bật cửa sổ OpenCV |

## 6. Cấu trúc
```
tb4_nav_yolo/
├── config/ (goals.yaml, yolo.yaml)
├── launch/nav_yolo.launch.py
├── maps/ (map.yaml, map.pgm)
└── tb4_nav_yolo/ (waypoint_navigator.py, yolo_detector.py)
```
