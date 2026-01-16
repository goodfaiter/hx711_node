#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from .hx711 import HX711
import time


class HX711WeightSensor(Node):
    def __init__(self):
        super().__init__("hx711_node")

        # Hardcoded configuration
        self.dout_pin = 17
        self.pd_sck_pin = 21
        self.channel = "A"
        self.gain = 128
        self.sample_rate = 80.0  # Hz
        self.num_samples = 1  # Number of raw readings to average
        self.calibration_factor = 1.0  # Adjust this based on your calibration

        self.prev_raw_data: int = 0
        self.rejection_threshold: int = 1000  # Threshold for rejecting sudden changes

        # Publisher for weight data
        self.weight_publisher = self.create_publisher(Float32, "weight", 10)

        # Initialize HX711
        self.hx711 = None
        self.zero_offset = 0.0

        self.get_logger().info("Initializing HX711 weight sensor...")

        # Create HX711 instance
        self.hx711 = HX711(
            dout_pin=self.dout_pin, pd_sck_pin=self.pd_sck_pin, channel=self.channel, gain=self.gain, logger=self.get_logger()
        )

        # Reset the HX711
        self.hx711.reset()
        time.sleep(0.1)

        # Perform tare/zero calibration at startup
        self.perform_tare()

        self.get_logger().info("HX711 initialized successfully")

        # Start publishing timer
        self.timer = self.create_timer(1.0 / self.sample_rate, self.publish_weight)

    def perform_tare(self):
        """Perform tare operation to zero the scale at startup"""
        self.get_logger().info("Performing tare... Please ensure no weight is on the scale.")

        # Collect tare samples
        tare_values = []
        num_tare_samples = 10

        for i in range(num_tare_samples):
            try:
                raw_data = self.hx711.get_raw_data(times=3)
                if raw_data and raw_data[0] is not None:
                    tare_values.append(raw_data[0])
                    self.get_logger().info(f"Tare sample {i+1}: {raw_data[0]}")
                time.sleep(0.1)
            except Exception as e:
                self.get_logger().warn(f"Error during tare sample {i+1}: {e}")

        if tare_values:
            self.zero_offset = sum(tare_values) / len(tare_values)
            self.prev_raw_data = self.zero_offset
            self.get_logger().info(f"Tare complete. Zero offset: {self.zero_offset}")
        else:
            self.get_logger().warn("Could not collect tare samples, using zero offset = 0")
            self.zero_offset = 0.0

    def get_weight_reading(self):
        """Get current weight reading from HX711"""
        raw_data = self.hx711.get_raw_data(times=1)[0]
        if abs(raw_data - self.prev_raw_data) > self.rejection_threshold:
            raw_data = self.hx711.get_raw_data(times=1)[0]
        self.prev_raw_data = raw_data
        return (raw_data - self.zero_offset) / self.calibration_factor

    def publish_weight(self):
        """Publish current weight reading"""
        weight = self.get_weight_reading()

        # Create and publish message
        weight_msg = Float32()
        weight_msg.data = float(weight)
        self.weight_publisher.publish(weight_msg)

    def destroy_node(self):
        """Cleanup on shutdown"""
        self.get_logger().info("Shutting down HX711 weight sensor")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    try:
        node = HX711WeightSensor()
        rclpy.spin(node)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
