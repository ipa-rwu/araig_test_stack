#!/usr/bin/env python
import time
import unittest
import rostest
import rospy
from geometry_msgs.msg import PoseStamped
from  araig_msgs.msg import BoolStamped
class TestGoalInterpreter(unittest.TestCase):
    def setUp(self):
        rospy.init_node('test_goal_interpreter')
        _pub_topic_start = '/test/start'
        _sub_topic_goal = '/test/goal'

        self.pub_start = rospy.Publisher(_pub_topic_start, BoolStamped, latch=True, queue_size=10)

        rospy.Subscriber(_sub_topic_goal, PoseStamped, callback=self.callback_1, queue_size=10)

        while (not rospy.has_param("/interpreters/goal_interpreter/goal") and \
            not rospy.has_param("/interpreters/goal_interpreter/goal_action")):
            rospy.sleep(0.1)
        
        self.goal = rospy.get_param("/interpreters/goal_interpreter/goal")
        self.pose = None
    
    def test_connect_to_action(self):
        pub_msg = BoolStamped()
        pub_msg.header.stamp = rospy.Time.now()
        pub_msg.data = True
        self.pub_start.publish(pub_msg)

        while self.pose is None:
            rospy.sleep(0.1)
        self.assertEqual(self.pose.position.x, self.goal["position"]["x"], msg='test1: The goal should be {}, but get {}'.format(self.goal, self.pose))
        self.assertAlmostEqual(self.pose.orientation.w, \
            0.707, \
            msg='test1: The goal should be {}, but get {}'.format(self.goal, self.pose), \
            delta = 0.01)

        rospy.sleep(0.5)
        self.assertEqual(1, self.times, \
            msg='test2: The msg should ony publish {}, but published {}'.format(1, self.times))

    def callback_1(self, msg):
        self.pose = msg.pose
        self.times = msg.header.seq

if __name__ == '__main__':
    pkg = 'araig_interpreter'
    name = 'test_goal_interpreter'
    rostest.rosrun(pkg, name, TestGoalInterpreter)