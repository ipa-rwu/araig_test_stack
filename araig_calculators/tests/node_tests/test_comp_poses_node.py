#!/usr/bin/env python
import sys
import unittest
import time
import rostest
import rospy
import rostopic
from  araig_msgs.msg import BoolStamped
from std_msgs.msg import Float64
from geometry_msgs.msg import PoseStamped


class TestCompParam(unittest.TestCase):

    def setUp(self):
        _pub_topic_1 = "/test/in_pose_1"
        _pub_topic_2 = "/test/in_pose_2"
        _sub_topic = "/test/out_bool"

        rospy.init_node('test_comp_param', anonymous=True)
        self.pub_1 = rospy.Publisher(_pub_topic_1, PoseStamped, latch=True, queue_size=10)
        self.pub_2 = rospy.Publisher(_pub_topic_2, PoseStamped, latch=True, queue_size=10)

        rospy.Subscriber(_sub_topic, BoolStamped, callback=self.callback_1, queue_size=10)
        self._sub_topic = _sub_topic

        while (not rospy.has_param("/calculators/comp_poses_node/pose_tolerance") and \
            not rospy.has_param("/calculators/comp_poses_node/orientation_tolerance")):
            time.sleep(0.1)
        
        self.pose_tolerance = rospy.get_param("/calculators/comp_poses_node/pose_tolerance")
        self.orientation_tolerance = rospy.get_param("/calculators/comp_poses_node/orientation_tolerance")
        self.result = None

    def test_expected(self):
        pub_pose_msg_1 = PoseStamped()
        pub_pose_msg_1.header.stamp = rospy.Time.now()
        pub_pose_msg_1.pose.position.x = 1
        pub_pose_msg_1.pose.position.y = 1
        pub_pose_msg_1.pose.position.z = 1
        pub_pose_msg_1.pose.orientation.w = 1
        pub_pose_msg_1.pose.orientation.z = 0
        
        pub_pose_msg_2 = PoseStamped()
        pub_pose_msg_2.header.stamp = rospy.Time.now()
        pub_pose_msg_2.pose.position.x = 1
        pub_pose_msg_2.pose.position.y = 1
        pub_pose_msg_2.pose.position.z = 5
        pub_pose_msg_2.pose.orientation.w = 1
        pub_pose_msg_2.pose.orientation.z = 0
        
        while self.result is None:
            self.pub_1.publish(pub_pose_msg_1)
            self.pub_2.publish(pub_pose_msg_2)
        self.assertTrue(self.result, msg='Compare with Tolerance Failed')
        self.assertEqual(self.msg_seq, 1, 'msg published {} times'.format(self.msg_seq))

        self.pub_1.publish(pub_pose_msg_1)
        self.pub_2.publish(pub_pose_msg_2)

        self.assertTrue(self.result, msg='Compare with Tolerance Failed')
        self.assertEqual(self.msg_seq, 1, 'msg published {} times'.format(self.msg_seq))

        self.result = None
        pub_pose_msg_2.pose.position.y = 2
        while self.result is None:
            self.pub_1.publish(pub_pose_msg_1)
            self.pub_2.publish(pub_pose_msg_2)

        self.assertFalse(self.result, msg='Compare with Tolerance Failed')
        self.assertEqual(self.msg_seq, 2, 'msg published {} times'.format(self.msg_seq))

    def callback_1(self, msg):
        self.result = msg.data
        self.msg_seq = msg.header.seq

if __name__ == '__main__':
    pkg = 'araig_calculators'
    name = 'test_comp_poses'
    rostest.rosrun(pkg, name, TestCompParam)