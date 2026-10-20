import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('tb4_nav_yolo')
    goals = os.path.join(share, 'config', 'goals.yaml')
    yolo = os.path.join(share, 'config', 'yolo.yaml')

    return LaunchDescription([
        Node(package='tb4_nav_yolo', executable='yolo_detector',
             name='yolo_detector', output='screen', parameters=[yolo]),
        Node(package='tb4_nav_yolo', executable='waypoint_navigator',
             name='waypoint_navigator', output='screen', parameters=[goals]),
    ])
