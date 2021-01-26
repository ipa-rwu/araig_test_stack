#!/usr/bin/env python3.6
import move_base_msgs.msg
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
import actionlib
import rospy
from geometry_msgs.msg import PoseStamped
import threading
import asyncio
import concurrent.futures
import time

from araig_msgs.msg import BoolStamped

# input: goal =  MoveBaseGoal()
class GoalInterpreterClass():
    LOCK = {}
    DATA = {}
    def __init__(self,
        goal,
        goal_action,
        wait_for_action,
        loop_rate_hz = 1):

        self.pub_topic = "/goal"
        self.sub_topic = "/start"

        self.action_goal = goal
        self.action_name = goal_action
        self.loop_rate_hz = loop_rate_hz
        self.rate = rospy.Rate(loop_rate_hz)

        self.temp_sub = {}

        if self.action_name != "None":
            rospy.loginfo(rospy.get_name() +": will try to action server: {}...".format(self.action_name))
            self.wait_for_action = wait_for_action
            self.action_init()
        else:
            rospy.logwarn(rospy.get_name() +": will not connect to action server")
        self.pub_init()
        self.sub_init()

        self.flag_send_goal = False

        # init FLAG and LOCK
        GoalInterpreterClass.DATA[self.sub_topic] = False
        GoalInterpreterClass.LOCK[self.sub_topic] = threading.Lock()
        self.temp_sub[self.sub_topic] = False
        
        self.main()
                      
    def action_init(self):
        self.action_client = actionlib.SimpleActionClient(self.action_name,MoveBaseAction)
        if self.action_client.wait_for_server(rospy.Duration(self.wait_for_action)) == True:
            rospy.loginfo(rospy.get_name() +": connected to action server: {}...".format(self.action_name))
        else:
            rospy.logerr(rospy.get_name() +": can not connected to action server: {}...".format(self.action_name))
            rospy.signal_shutdown(rospy.get_name() +": Action server not available!")

    def callback_start(self, msg, args):
        with GoalInterpreterClass.LOCK[args]:
            GoalInterpreterClass.DATA[args] = msg.data

    def pub_init(self):
        self.pub_diag = rospy.Publisher(
                self.pub_topic, 
                PoseStamped, 
                queue_size=10,
                latch = True 
            )
        self.goal_msg = PoseStamped()
        self.goal_msg = self.action_goal.target_pose
    
    def sub_init(self):
        self.sub_diag = {}
        topic = self.sub_topic
        self.sub_diag[topic] = rospy.Subscriber(topic, BoolStamped, self.callback_start, (topic))

    #  add two executor, one for pub topic, the other one for action client  
    async def main_pub_and_wait_action(self, loop, pool):
        if self.action_name != "None":
            await asyncio.wait(
                fs={
                    loop.run_in_executor(pool, self.call_action),
                    loop.run_in_executor(pool, self.pub_goal)
                },
                return_when = asyncio.ALL_COMPLETED
            )
        else:
            await asyncio.wait(
                fs={
                    loop.run_in_executor(pool, self.pub_goal)
                },
                return_when = asyncio.ALL_COMPLETED
        )

    def pub_goal(self):
        self.pub_diag.publish(self.goal_msg)
        rospy.loginfo(rospy.get_name() + ": pub ")
        return True
            
    def call_action(self):
        # only call action once
        self.action_client.send_goal(self.action_goal)
        rospy.loginfo(rospy.get_name() + ": send goal to {}".format(self.action_name))

        wait = self.action_client.wait_for_result()
        
        if not wait:
            rospy.logerr(rospy.get_name() + ": didn't get response from {}".format(self.action_name))
            return False
        else:
            result = self.action_client.get_result()
            if result:
                rospy.loginfo(rospy.get_name() + ": get response from {}".format(self.action_name))
                return True
        
    def main(self):
        pre_signal = False
        try:
            loop = asyncio.get_event_loop()
            while not rospy.is_shutdown():
                with GoalInterpreterClass.LOCK[self.sub_topic]:
                    self.temp_sub[self.sub_topic]= GoalInterpreterClass.DATA[self.sub_topic]
                
                if pre_signal == False and self.temp_sub[self.sub_topic] == True:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                        loop.run_until_complete(self.main_pub_and_wait_action(loop, pool))
                pre_signal = self.temp_sub[self.sub_topic]
                self.rate.sleep()
        except rospy.ROSException:
            loop.close()
            pass