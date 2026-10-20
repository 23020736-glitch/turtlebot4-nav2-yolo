#!/usr/bin/env python3
"""Node điều hướng tự động: đi tuần tự qua các goal bằng Nav2 Simple Commander."""
import math

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult


def yaw_to_quaternion(yaw):
    return math.sin(yaw / 2.0), math.cos(yaw / 2.0)  # (z, w)


class WaypointNavigator(Node):
    def __init__(self):
        super().__init__('waypoint_navigator')
        # goals: danh sách phẳng [x1, y1, yaw1, x2, y2, yaw2, ...] (m, m, rad)
        self.declare_parameter('goals', [0.0, 0.0, 0.0])
        self.declare_parameter('set_initial_pose', True)
        self.declare_parameter('initial_pose', [0.0, 0.0, 0.0])
        self.declare_parameter('loop', False)
        self.declare_parameter('frame_id', 'map')

        self.nav = BasicNavigator()
        # Nav2 Commander là một node riêng, cần đồng bộ sim time với Gazebo
        if self.get_parameter('use_sim_time').value:
            self.nav.set_parameters(
                [Parameter('use_sim_time', Parameter.Type.BOOL, True)])

    def make_pose(self, x, y, yaw):
        pose = PoseStamped()
        pose.header.frame_id = self.get_parameter('frame_id').value
        pose.header.stamp = self.nav.get_clock().now().to_msg()
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.orientation.z, pose.pose.orientation.w = yaw_to_quaternion(yaw)
        return pose

    def get_goals(self):
        flat = list(self.get_parameter('goals').value)
        if len(flat) % 3 != 0 or len(flat) < 9:
            raise ValueError('Tham số "goals" phải có >= 3 điểm (x, y, yaw).')
        return [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]

    def run(self):
        goals = self.get_goals()

        if self.get_parameter('set_initial_pose').value:
            x, y, yaw = self.get_parameter('initial_pose').value
            self.nav.setInitialPose(self.make_pose(x, y, yaw))
            self.get_logger().info(f'Đã đặt initial pose ({x:.2f}, {y:.2f}, {yaw:.2f})')

        self.get_logger().info('Đang chờ Nav2 active...')
        self.nav.waitUntilNav2Active()
        self.get_logger().info('Nav2 đã sẵn sàng.')

        while rclpy.ok():
            for idx, (x, y, yaw) in enumerate(goals, start=1):
                self.get_logger().info(
                    f'=== Goal {idx}/{len(goals)}: x={x:.2f}, y={y:.2f}, yaw={yaw:.2f} ===')
                self.nav.goToPose(self.make_pose(x, y, yaw))

                last_log = 0
                while not self.nav.isTaskComplete():
                    fb = self.nav.getFeedback()
                    if fb is not None:
                        now = self.nav.get_clock().now().nanoseconds / 1e9
                        if now - last_log > 2.0:
                            self.get_logger().info(
                                f'Goal {idx}: còn {fb.distance_remaining:.2f} m')
                            last_log = now

                result = self.nav.getResult()
                if result == TaskResult.SUCCEEDED:
                    self.get_logger().info(f'Goal {idx}: ĐÃ ĐẾN NƠI.')
                elif result == TaskResult.CANCELED:
                    self.get_logger().warn(f'Goal {idx}: bị hủy.')
                    return
                else:
                    self.get_logger().error(f'Goal {idx}: THẤT BẠI, bỏ qua.')

            if not self.get_parameter('loop').value:
                break

        self.get_logger().info('Hoàn thành tất cả các goal.')


def main(args=None):
    rclpy.init(args=args)
    node = WaypointNavigator()
    try:
        node.run()
    except KeyboardInterrupt:
        node.nav.cancelTask()
    finally:
        node.nav.destroy_node()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
