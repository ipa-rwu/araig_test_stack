#!/usr/bin/env python
import sys
import unittest
import time
import rostest
import rospy
from geometry_msgs.msg import PoseStamped
from  araig_msgs.msg import BoolStamped, Float64Stamped

class TestCalcPoseDelta(unittest.TestCase):

    def setUp(self):
        _pub_topic_1 = '/test/in_obj_1'
        _pub_topic_2 = '/test/in_obj_2'
        _pub_signal = '/test/in_signal'
        _sub_topic_1 = '/test/out_disp_angular'
        _sub_topic_2 = '/test/out_disp_position'

        rospy.init_node('test_calc_pose_delta', anonymous=True)
        self.pub_1 = rospy.Publisher(_pub_topic_1, PoseStamped, latch=True, queue_size=10)
        self.pub_2 = rospy.Publisher(_pub_topic_2, PoseStamped, latch= True, queue_size=10)
        self.pub_signal = rospy.Publisher(_pub_signal, BoolStamped, latch= True, queue_size=10)

        rospy.Subscriber(_sub_topic_1, Float64Stamped, callback=self.callback_1, queue_size=10)
        rospy.Subscriber(_sub_topic_2, Float64Stamped, callback=self.callback_2, queue_size=10)

        self.delta_angle = None
        self.delta_pose = None
        self.msg_seq_angle = 0
        self.msg_seq_pose = 0

    def test_expected(self):
        pub_pose_msg = PoseStamped()
        pub_pose_msg.header.stamp = rospy.Time.now()
        pub_pose_msg.pose.position.x = 1
        pub_pose_msg.pose.position.y = 1
        pub_pose_msg.pose.position.z = 1
        pub_pose_msg.pose.orientation.w = 1
        self.pub_1.publish(pub_pose_msg)

        pub_pose_msg = PoseStamped()
        pub_pose_msg.header.stamp = rospy.Time.now()
        pub_pose_msg.pose.position.x = 4
        pub_pose_msg.pose.position.y = 5
        pub_pose_msg.pose.position.z = 5
        pub_pose_msg.pose.orientation.w = 1
        pub_pose_msg.pose.orientation.z = 1
        self.pub_2.publish(pub_pose_msg)

        pub_signal_msg = BoolStamped()
        pub_signal_msg.header.stamp = rospy.Time.now()
        pub_signal_msg.data = False
        self.pub_signal.publish(pub_signal_msg)

        rospy.sleep(0.5)
        pub_signal_msg.data = True
        self.pub_signal.publish(pub_signal_msg)

        while self.delta_pose is None and self.delta_angle is None:
            time.sleep(0.1)

        self.assertEqual(self.delta_pose, 5.0, 'test1: {} is not equal to 5.0'.format(self.delta_pose))
        self.assertEqual(self.delta_angle, 90.0, 'test1: {} is not equal to 5.0'.format(self.delta_angle))
        self.assertEqual(self.msg_seq_angle, 1, 'test1: msg published {} times'.format(self.msg_seq_angle))
        self.assertEqual(self.msg_seq_pose, 1, 'test1: msg published {} times'.format(self.msg_seq_pose))

        rospy.sleep(0.2)
        pub_signal_msg.data = False
        self.pub_signal.publish(pub_signal_msg)
        self.assertEqual(self.msg_seq_angle, 1, 'test2: msg published {} times'.format(self.msg_seq_angle))
        self.assertEqual(self.msg_seq_pose, 1, 'test2: msg published {} times'.format(self.msg_seq_pose))

        rospy.sleep(0.2)
        pub_signal_msg.data = True
        self.pub_signal.publish(pub_signal_msg)
        rospy.sleep(0.2)
        self.assertEqual(self.msg_seq_angle, 2, 'test3: msg published {} times'.format(self.msg_seq_angle))
        self.assertEqual(self.msg_seq_pose, 2, 'test3: msg published {} times'.format(self.msg_seq_pose))

    def callback_1(self, msg):
        self.delta_angle = msg.data
        self.msg_seq_angle = msg.header.seq

    def callback_2(self, msg):
        self.delta_pose = msg.data
        self.msg_seq_pose = msg.header.seq

if __name__ == '__main__':
    pkg = 'araig_calculators'
    name = 'test_diff_poses_spatial'
    rostest.rosrun(pkg, name, TestCalcPoseDelta)