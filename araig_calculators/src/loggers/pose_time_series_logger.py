#!/usr/bin/env python
import rospy
import yaml
import csv
from base_classes.base_time_series_logger import TimeSeriesLoggerClass
from geometry_msgs.msg import PoseStamped
import tf
import math

class PoseSeriesLoggerClass(TimeSeriesLoggerClass):
    def __init__(self):
        rospy.Subscriber("/in_pose_stamped", PoseStamped, self.data_subscriber)
        super(PoseSeriesLoggerClass, self).__init__()

    def data_subscriber(self, msg):
        with self.lock_data:
            quaternion = (msg.pose.orientation.x,
                            msg.pose.orientation.y,
                            msg.pose.orientation.z,
                            msg.pose.orientation.w,)
            euler = tf.transformations.euler_from_quaternion(quaternion)
            roll =  math.degrees(euler[0])
            pitch = math.degrees(euler[1])
            yaw =   math.degrees(euler[2])
            self.data_list = [msg.header.stamp, 
                                msg.header.seq,
                                msg.pose.position.x,
                                msg.pose.position.y,
                                msg.pose.position.z,
                                msg.pose.orientation.x,
                                msg.pose.orientation.y,
                                msg.pose.orientation.z,
                                msg.pose.orientation.w,
                                roll, pitch, yaw]
            self.data_available = True
