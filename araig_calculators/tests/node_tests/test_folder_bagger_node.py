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
        _pub_topic_success = '/test/test_succeeded'
        _pub_topic_fail = '/test/test_failed'      

        rospy.init_node('test_folder_logger', anonymous=True)
        self.pub_start = rospy.Publisher(_pub_topic_start, BoolStamped, latch=True, queue_size=10)
        self.pub_stop = rospy.Publisher(_pub_topic_stop, BoolStamped, latch=True, queue_size=10)
        self.pub_success = rospy.Publisher(_pub_topic_success, BoolStamped, latch=True, queue_size=10)
        self.pub_fail = rospy.Publisher(_pub_topic_fail, BoolStamped, latch=True, queue_size=10)

        module = "/calculators"

        while (not rospy.has_param(module + "/robot_type") and \
            not rospy.has_param(module + "/test_type")):
            time.sleep(0.1)
                
        if (not rospy.has_param(module + "/dest_dir") or rospy.get_param(module + "/dest_dir") == "") :
            self.dest_dir = os.path.expanduser("~")
        else:
            self.dest_dir = rospy.get_param(module + "/dest_dir")

        self.robot_type = rospy.get_param(module + "/robot_type")
        self.test_type = rospy.get_param(module + "/test_type")
        
        self.i = 0

    def test_expected(self):
        print(self.robot_type)
        self.path = self.dest_dir + "/" + self.robot_type + "/" + self.test_type + "/"
        while self.i < 3:
            pub_msg = BoolStamped()
            pub_msg.header.stamp = rospy.Time.now()
            pub_msg.data = True
            self.pub_start.publish(pub_msg)

            rospy.sleep(3)
            if os.listdir(self.path):
                self.result = True
            else:
                self.result = False

            self.assertTrue(self.result, msg='there is no folder')

            rospy.sleep(2)
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
            
            rospy.sleep(1)
            pub_msg.header.stamp = rospy.Time.now()
            pub_msg.data = True
            self.pub_success.publish(pub_msg)

            rospy.sleep(3)
            for i in os.listdir(self.path):
                try:
                    os.rmdir(self.path + i)
                except:
                    files = os.listdir(self.path + i)
                    for f in files:
                        os.remove(os.path.join(self.path + i, f))
                        os.rmdir(self.path + i)
            self.i += 1


if __name__ == '__main__':
    pkg = 'araig_calculators'
    name = 'test_folder_bagger'
    rostest.rosrun(pkg, name, TestFolderLogger)