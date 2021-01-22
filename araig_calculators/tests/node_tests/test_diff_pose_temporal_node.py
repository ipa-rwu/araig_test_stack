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
        _pub_topic_1 = '/test/start'
        _pub_topic_2 = '/test/stop'
        _pub_topic_3 = '/test/pose'
        _sub_topic_1 = '/test/out_disp_angular'
        _sub_topic_2 = '/test/out_disp_position'

        rospy.init_node('test_calc_pose_delta', anonymous=True)
        self.pub_start = rospy.Publisher(_pub_topic_1, BoolStamped, latch=True, queue_size=10)
        self.pub_stop = rospy.Publisher(_pub_topic_2, BoolStamped, latch= True, queue_size=10)
        self.pub_pose = rospy.Publisher(_pub_topic_3, PoseStamped, latch= True, queue_size=10)

        rospy.Subscriber(_sub_topic_1, Float64Stamped, callback=self.callback_1, queue_size=10)
        rospy.Subscriber(_sub_topic_2, Float64Stamped, callback=self.callback_2, queue_size=10)

        self.delta_angle = None
        self.delta_pose = None

        self.msg_seq_angle = 0
        self.msg_seq_pose = 0

    def test_expected(self):
        pub_pose_msg_start = PoseStamped()
        pub_pose_msg_start.header.stamp = rospy.Time.now()
        pub_pose_msg_start.pose.position.x = 1
        pub_pose_msg_start.pose.position.y = 1
        pub_pose_msg_start.pose.position.z = 1
        pub_pose_msg_start.pose.orientation.w = 1
        self.pub_pose.publish(pub_pose_msg_start)
        rospy.sleep(0.5)

        # pub start signal
        pub_signal = BoolStamped()
        pub_signal.header.stamp = rospy.Time.now()
        pub_signal.data = True
        self.pub_start.publish(pub_signal)
        rospy.sleep(0.5)

        pub_pose_msg_stop = PoseStamped()
        pub_pose_msg_stop.header.stamp = rospy.Time.now()
        pub_pose_msg_stop.pose.position.x = 4
        pub_pose_msg_stop.pose.position.y = 5
        pub_pose_msg_stop.pose.position.z = 2
        pub_pose_msg_stop.pose.orientation.w = 1
        pub_pose_msg_stop.pose.orientation.z = 1
        self.pub_pose.publish(pub_pose_msg_stop)

        rospy.sleep(0.5)
        pub_signal.header.stamp = rospy.Time.now()
        pub_signal.data = True
        self.pub_stop.publish(pub_signal)
        
        while self.delta_pose is None and self.delta_angle is None:
            time.sleep(0.1)

        self.assertEqual(self.delta_pose, 5.0, 'test 1:{} is not equal to 5.0'.format(self.delta_pose))
        self.assertEqual(self.delta_angle, 90.0, 'test 1: {} is not equal to 5.0'.format(self.delta_angle))
        self.assertEqual(self.msg_seq_pose, 1, 'test 1: msg_pose published {} times'.format(self.msg_seq_pose))
        self.assertEqual(self.msg_seq_angle, 1, 'test 1: msg_angle published {} times'.format(self.msg_seq_angle))

        # reset signal , test agains
        pub_signal.data = False
        self.pub_start.publish(pub_signal)
        rospy.sleep(0.5)
        self.pub_stop.publish(pub_signal)
        rospy.sleep(0.5)

        self.delta_angle = None
        self.delta_pose = None
        self.pub_pose.publish(pub_pose_msg_start)
        pub_signal.data = True
        self.pub_start.publish(pub_signal)
        rospy.sleep(0.5)
        self.pub_pose.publish(pub_pose_msg_stop)
        self.pub_stop.publish(pub_signal)
        while self.delta_pose is None and self.delta_angle is None:
            time.sleep(0.1)
        self.assertEqual(self.delta_pose, 5.0, 'test 2: {} is not equal to 5.0'.format(self.delta_pose))
        self.assertEqual(self.delta_angle, 90.0, 'test 2: {} is not equal to 5.0'.format(self.delta_angle))
        self.assertEqual(self.msg_seq_angle, 2, 'test 2: msg_angle published {} times'.format(self.msg_seq_angle))
        self.assertEqual(self.msg_seq_pose, 2, 'test 2: msg_pose published {} times'.format(self.msg_seq_pose))


    def callback_1(self, msg):
        self.delta_angle = msg.data
        self.msg_seq_angle = msg.header.seq

    def callback_2(self, msg):
        self.delta_pose = msg.data
        self.msg_seq_pose = msg.header.seq


if __name__ == '__main__':
    pkg = 'araig_calculators'
    name = 'test_calc_pose_delta'
    rostest.rosrun(pkg, name, TestCalcPoseDelta)