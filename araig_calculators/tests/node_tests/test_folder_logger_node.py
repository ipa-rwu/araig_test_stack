#!/usr/bin/env python
import sys
import unittest
import time
import rostest
import rospy
from  araig_msgs.msg import BoolStamped
import os
class TestFolderLogger(unittest.TestCase):

    def setUp(self):
        _pub_topic_start = '/test/start'
        _pub_topic_stop = '/test/stop'

        rospy.init_node('test_folder_logger', anonymous=True)
        self.pub_start = rospy.Publisher(_pub_topic_start, BoolStamped, latch=True, queue_size=10)
        self.pub_stop = rospy.Publisher(_pub_topic_stop, BoolStamped, latch=True, queue_size=10)

        while (not rospy.has_param("/calculators/dest_dir") and \
            not rospy.has_param("/calculators/robot_type") and \
            not rospy.has_param("/calculators/test_type")):
            time.sleep(0.1)
        
        self.dest_dir = rospy.get_param("/calculators/dest_dir")
        self.robot_type = rospy.get_param("/calculators/robot_type")
        self.test_type = rospy.get_param("/calculators/test_type")
        
        self.i = 0

    def test_expected(self):
        print(self.robot_type)
        self.path = self.dest_dir + "/" + self.robot_type + "/" + self.test_type + "/"
        while self.i < 3:
            pub_msg = BoolStamped()
            pub_msg.header.stamp = rospy.Time.now()
            pub_msg.data = True
            self.pub_start.publish(pub_msg)

            rospy.sleep(1)
            if os.listdir(self.path):
                self.result = True
            else:
                self.result = False

            self.assertTrue(self.result, msg='there is no folder')

            for i in os.listdir(self.path):
                print(i)
                os.rmdir(self.path + i)

            rospy.sleep(1)
            pub_msg.header.stamp = rospy.Time.now()
            pub_msg.data = False
            self.pub_start.publish(pub_msg)

            rospy.sleep(1)
            pub_msg.header.stamp = rospy.Time.now()
            pub_msg.data = True
            self.pub_stop.publish(pub_msg)

            rospy.sleep(1)
            pub_msg.header.stamp = rospy.Time.now()
            pub_msg.data = False
            self.pub_stop.publish(pub_msg)

            self.i += 1

if __name__ == '__main__':
    pkg = 'araig_calculators'
    name = 'test_folder_logger'
    rostest.rosrun(pkg, name, TestFolderLogger)