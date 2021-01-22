#!/usr/bin/env python
import sys
import unittest
import time
import rostest
import rospy
import rostopic
from  araig_msgs.msg import BoolStamped


class TestCompParam(unittest.TestCase):

    def setUp(self):
        _pub_topic_1 = "/test/in_bool_1"
        _pub_topic_2 = "/test/in_bool_2"
        _sub_topic = "/test/out_bool"

        rospy.init_node('test_comp_param', anonymous=True)
        self.pub_1 = rospy.Publisher(_pub_topic_1, BoolStamped, latch=True, queue_size=10)
        self.pub_2 = rospy.Publisher(_pub_topic_2, BoolStamped, latch=True, queue_size=10)

        rospy.Subscriber(_sub_topic, BoolStamped, callback=self.callback_1, queue_size=10)

        while (not rospy.has_param("/calculators/comp_topics_node/tolerance")):
            time.sleep(0.1)
        
        self.tolerance = rospy.get_param("/calculators/comp_topics_node/tolerance")
        self.result = None
        self.msg_seq = 0

    def test_expected(self):
        pub_msg_1 = BoolStamped()
        pub_msg_1.header.stamp = rospy.Time.now()
        pub_msg_1.data = False
        self.pub_1.publish(pub_msg_1)

        pub_msg_2 = BoolStamped()
        pub_msg_2.header.stamp = rospy.Time.now()
        pub_msg_2.data = False
        self.pub_2.publish(pub_msg_2)

        while self.result is None:
            time.sleep(0.1)

        self.assertFalse(self.result, msg='Compare with Tolerance Failed')
        self.assertEqual(self.msg_seq, 1, 'msg published {} times'.format(self.msg_seq))

        pub_msg_1.data = True
        pub_msg_2.data = True
        self.result = None
        self.pub_1.publish(pub_msg_1)
        self.pub_2.publish(pub_msg_2)
        while self.result is None:
            time.sleep(0.1)
        self.assertTrue(self.result, msg='Compare with Tolerance Failed')
        self.assertEqual(self.msg_seq, 2, 'msg published {} times'.format(self.msg_seq))

        pub_msg_1.data = False
        pub_msg_2.data = True
        self.result = None
        self.pub_1.publish(pub_msg_1)
        self.pub_2.publish(pub_msg_2)
        while self.result is None:
            time.sleep(0.1)
        self.assertFalse(self.result, msg='Compare with Tolerance Failed')
        self.assertEqual(self.msg_seq, 3, 'msg published {} times'.format(self.msg_seq))

        pub_msg_1.data = True
        pub_msg_2.data = True
        self.result = None
        self.pub_1.publish(pub_msg_1)
        self.pub_2.publish(pub_msg_2)
        while self.result is None:
            time.sleep(0.1)
        self.assertTrue(self.result, msg='Compare with Tolerance Failed')
        self.assertEqual(self.msg_seq, 4, 'msg published {} times'.format(self.msg_seq))

        pub_msg_1.data = True
        pub_msg_2.data = False
        self.result = None
        self.pub_1.publish(pub_msg_1)
        self.pub_2.publish(pub_msg_2)
        while self.result is None:
            time.sleep(0.1)
        self.assertFalse(self.result, msg='Compare with Tolerance Failed')
        self.assertEqual(self.msg_seq, 5, 'msg published {} times'.format(self.msg_seq))

    def callback_1(self, msg):
        self.result = msg.data
        self.msg_seq = msg.header.seq

if __name__ == '__main__':
    pkg = 'araig_calculators'
    name = 'test_comp_topics'
    rostest.rosrun(pkg, name, TestCompParam)