#!/usr/bin/env python3
"""Node nhận diện vật thể: subscribe camera RGB -> cv_bridge -> YOLO -> hiển thị/publish."""
import time
from collections import Counter

import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO


class YoloDetector(Node):
    def __init__(self):
        super().__init__('yolo_detector')
        self.declare_parameter('image_topic', '/oakd/rgb/preview/image_raw')
        self.declare_parameter('output_topic', '/yolo/image_annotated')
        self.declare_parameter('model', 'yolov8n.pt')
        self.declare_parameter('conf', 0.4)
        self.declare_parameter('max_fps', 5.0)      # giới hạn tốc độ suy luận
        self.declare_parameter('show_window', True)

        self.conf = self.get_parameter('conf').value
        self.min_dt = 1.0 / max(self.get_parameter('max_fps').value, 0.1)
        self.show = self.get_parameter('show_window').value
        self.last_t = 0.0

        model_name = self.get_parameter('model').value
        self.get_logger().info(f'Đang tải mô hình YOLO: {model_name}')
        self.model = YOLO(model_name)
        self.bridge = CvBridge()

        self.pub = self.create_publisher(
            Image, self.get_parameter('output_topic').value, 10)
        self.create_subscription(
            Image, self.get_parameter('image_topic').value,
            self.on_image, qos_profile_sensor_data)
        self.get_logger().info(
            f'Subscribe: {self.get_parameter("image_topic").value}')

    def on_image(self, msg):
        now = time.time()
        if now - self.last_t < self.min_dt:
            return
        self.last_t = now

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        result = self.model(frame, conf=self.conf, verbose=False)[0]

        # In thông tin vật thể phát hiện được
        if len(result.boxes) > 0:
            names = [self.model.names[int(c)] for c in result.boxes.cls]
            summary = ', '.join(f'{n} x{k}' for n, k in Counter(names).items())
            self.get_logger().info(f'Phát hiện: {summary}')
            for b in result.boxes:
                x1, y1, x2, y2 = (int(v) for v in b.xyxy[0])
                self.get_logger().info(
                    f'  - {self.model.names[int(b.cls)]}: '
                    f'conf={float(b.conf):.2f}, bbox=({x1},{y1},{x2},{y2})')

        # Vẽ bounding box + tên class + độ tự tin
        annotated = result.plot()

        out = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
        out.header = msg.header
        self.pub.publish(out)

        if self.show:
            cv2.imshow('YOLO - TurtleBot 4', annotated)
            cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
