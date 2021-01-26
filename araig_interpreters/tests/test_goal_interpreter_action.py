#!/usr/bin/env python
import time
import unittest
import rostest
import rospy
import actionlib
import move_base_msgs.msg
from geometry_msgs.msg import PoseStamped
from  araig_msgs.msg import BoolStamped
import concurrent.futures

class MockActionServer():
    _feedback = move_base_msgs.msg.MoveBaseFeedback()
    _result = move_base_msgs.msg.MoveBaseResult()

    def __init__(self, name):
        self._action_name = name
        self._as = actionlib.SimpleActionServer(self._action_name, \
            move_base_msgs.msg.MoveBaseAction, \
            execute_cb=self.execute_cb, \
            auto_start = False)
        self._as.start()

    def execute_cb(self, goal):
        success = True
        
        rospy.loginfo('{}: get goal : {}'.format(self._action_name, goal))
        current_position = PoseStamped()
        current_position.header.stamp = rospy.Time.now()
        current_position.pose.orientation.w = 1
        self._feedback.base_position = current_position
        
        self._as.publish_feedback(self._feedback)
        
        if success:
            self._as.set_succeeded(self._result, "Goal reached.")
            rospy.loginfo('%s: Succeeded' % self._action_name)

class TestGoalInterpreter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rospy.init_node('test_goal_interpreter')
        cls.server = MockActionServer('move_base')
    
    def setUp(self):
        _pub_topic_start = '/test/start'
        _sub_topic_goal = '/test/goal'

        self.pub_start = rospy.Publisher(_pub_topic_start, BoolStamped, latch=True, queue_size=10)

        rospy.Subscriber(_sub_topic_goal, PoseStamped, callback=self.callback_1, queue_size=10)

        while (not rospy.has_param("/interpreters/goal_interpreter/goal") and \
            not rospy.has_param("/interpreters/goal_interpreter/goal_action")):
            time.sleep(0.1)
        
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