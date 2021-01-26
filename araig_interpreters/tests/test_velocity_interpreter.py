#!/usr/bin/env python
import sys
import unittest
import time
import rostest
import rospy
from  araig_msgs.msg import BoolStamped
from geometry_msgs.msg import Twist

class TestVelocityInterpreter(unittest.TestCase):

    def setUp(self):
        _pub_topic_start = '/test/start'
        _pub_topic_stop = '/test/stop'
        _sub_topic_cmdvel = '/test/cmd_vel'

        rospy.init_node('test_velocity_interpreter', anonymous=True)
        self.pub_start = rospy.Publisher(_pub_topic_start, BoolStamped, latch=True, queue_size=10)
        self.pub_stop = rospy.Publisher(_pub_topic_stop, BoolStamped, latch=True, queue_size=10)

        rospy.Subscriber(_sub_topic_cmdvel, Twist, callback=self.callback_1, queue_size=10)

        while (not rospy.has_param("/interpreters/velocity_interpreter/max_vel")):
            time.sleep(0.1)
        
        self.max_vel = rospy.get_param("/interpreters/velocity_interpreter/max_vel")
        self.vel = None

    def transfer_timestamp(self, timestamp):
        return float(timestamp.secs + float(timestamp.nsecs*(1e-9)))

    def test_expected(self):
        # start true, stop false
        pub_msg_start = BoolStamped()
        pub_msg_start.header.stamp = rospy.Time.now()
        pub_msg_start.data = True
        self.pub_start.publish(pub_msg_start)

        while self.vel is None:
            time.sleep(0.1)
        self.assertEqual(self.vel, self.max_vel, msg='test1: The velocity should be {}, but get {}'.format(self.max_vel, self.vel))
        self.assertAlmostEqual(self.transfer_timestamp(pub_msg_start.header.stamp), self.transfer_timestamp(self.time), \
            msg='test1: Send signal at {}, send velocity at {}'.format(self.transfer_timestamp(pub_msg_start.header.stamp), self.transfer_timestamp(self.time)), \
            delta=0.5)

        # start false, stop true
        pub_msg_start.header.stamp = rospy.Time.now()
        pub_msg_start.data = False
        self.pub_start.publish(pub_msg_start)
        rospy.sleep(0.1)
        pub_msg_stop = BoolStamped()
        pub_msg_stop.header.stamp = rospy.Time.now()
        pub_msg_stop.data = True
        self.pub_stop.publish(pub_msg_stop)
        self.vel = None

        while self.vel is None:
            time.sleep(0.1)
        self.assertEqual(self.vel, 0, msg='test2: The velocity should be {}, but get {}'.format(0, self.vel))
        self.assertAlmostEqual(self.transfer_timestamp(pub_msg_stop.header.stamp), self.transfer_timestamp(self.time), \
            msg='test2: Send signal at {}, send velocity at {}'.format(self.transfer_timestamp(pub_msg_stop.header.stamp), self.transfer_timestamp(self.time)), \
            delta=0.5)

        # reset start false, stop false
        pub_msg_start.header.stamp = rospy.Time.now()
        pub_msg_start.data = False
        self.pub_start.publish(pub_msg_start)
        rospy.sleep(0.1)
        pub_msg_stop = BoolStamped()
        pub_msg_stop.header.stamp = rospy.Time.now()
        pub_msg_stop.data = False
        self.pub_stop.publish(pub_msg_stop)
        rospy.sleep(0.1)

        # start true, stop false
        self.vel = None
        pub_msg_start.header.stamp = rospy.Time.now()
        pub_msg_start.data = True
        self.pub_start.publish(pub_msg_start)
        rospy.sleep(0.1)
        while self.vel is None:
            time.sleep(0.1)
        self.assertEqual(self.vel, self.max_vel, msg='test4: The velocity should be {}, but get {}'.format(self.max_vel, self.vel))
        self.assertAlmostEqual(self.transfer_timestamp(pub_msg_start.header.stamp), self.transfer_timestamp(self.time), \
            msg='test4: Send signal at {}, send velocity at {}'.format(self.transfer_timestamp(pub_msg_start.header.stamp), self.transfer_timestamp(self.time)), \
            delta=0.5)

    def callback_1(self, msg):
        self.vel = msg.linear.x
        self.time = rospy.Time.now()

if __name__ == '__main__':
    pkg = 'araig_interpreter'
    name = 'test_velocity_interpreter'
    rostest.rosrun(pkg, name, TestVelocityInterpreter)