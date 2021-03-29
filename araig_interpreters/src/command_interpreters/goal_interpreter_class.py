#!/usr/bin/env python3.6
import move_base_msgs.msg
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal, MoveBaseActionResult
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

        self.ppub_topic_goal = "/goal"
        self.pub_topic_result = "/done"
        self.sub_topic = "/start"
        self.sub_topic_result = "/result"


        self.action_goal = goal
        self.action_name = goal_action
        self.loop_rate_hz = loop_rate_hz
        self.rate = rospy.Rate(loop_rate_hz)

        self.temp_sub = {}

        if self.action_name != "None":
            rospy.loginfo(rospy.get_name() +": will try to action server: {}...".format(self.action_name))
            try_times = 0
            while self.action_init(wait_for_action) == False and try_times < 5:
                rospy.logwarn(rospy.get_name() +": cannot connected to action server: {}, will try again".format(self.action_name))
                try_times += 1
                rospy.sleep(1)
            if try_times == 5:
                rospy.logerr(rospy.get_name() +": cannot connected to action server: {}, shutdown this node".format(self.action_name))
                rospy.signal_shutdown("cannot connected to action server")
        else:
            rospy.logwarn(rospy.get_name() +": will not connect to action server")
        self.pub_init()
        self.sub_init(self.sub_topic, BoolStamped)

        self.flag_send_goal = False

        # init FLAG and LOCK
        GoalInterpreterClass.DATA[self.sub_topic] = False
        GoalInterpreterClass.LOCK[self.sub_topic] = threading.Lock()
        GoalInterpreterClass.DATA[self.sub_topic_result] = ""
        GoalInterpreterClass.LOCK[self.sub_topic_result] = threading.Lock()
        self.temp_sub[self.sub_topic] = False
        
        self.main()
                      
    def action_init(self, wait_time):
        self.action_client = actionlib.SimpleActionClient(self.action_name,MoveBaseAction)
        if self.action_client.wait_for_server(rospy.Duration(wait_time)) == True:
            rospy.loginfo(rospy.get_name() +": connected to action server: {}...".format(self.action_name))
            self.sub_init(self.sub_topic_result, MoveBaseActionResult)
            return True
        else:
            return False

    def callback_start(self, msg, args):
        with GoalInterpreterClass.LOCK[args]:
            GoalInterpreterClass.DATA[args] = msg.data
    
    def callback_result(self, msg, args):
        with GoalInterpreterClass.LOCK[args]:
            GoalInterpreterClass.DATA[args] = msg.status

    def pub_init(self):
        self.pub_diag_goal = rospy.Publisher(
                self.ppub_topic_goal, 
                PoseStamped, 
                queue_size=10,
                latch = True 
            )
        self.goal_msg = PoseStamped()
        self.goal_msg = self.action_goal.target_pose

        self.pub_diag_result = rospy.Publisher(
                self.pub_topic_result, 
                BoolStamped, 
                queue_size=10,
                latch = True 
            )
        self.action_result_msg = BoolStamped()
        self.action_result_msg.header.stamp = rospy.Time.now() 
        self.action_result_msg.data = False
    
    def sub_init(self, topic, datatype):
        self.sub_diag = {}
        self.sub_diag[topic] = rospy.Subscriber(topic, datatype, getattr(self, "callback_" + topic.replace('/', '')), (topic))

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
        self.pub_diag_goal.publish(self.goal_msg)
        rospy.loginfo(rospy.get_name() + ": pub goal")
        return True
    
    def pub_result(self, result):
        self.action_result_msg.header.stamp = rospy.Time.now() 
        self.action_result_msg.data = result
        self.pub_diag_result.publish(self.action_result_msg)
            
    def call_action(self):
        # only call action once
        self.action_client.send_goal(self.action_goal)
        rospy.loginfo(rospy.get_name() + ": send goal to {}".format(self.action_name))

        wait = self.action_client.wait_for_result()
        
        rospy.loginfo(rospy.get_name() + ": finished waiting for result")
        if not wait:
            rospy.logerr(rospy.get_name() + ": didn't get response from {}".format(self.action_name))
            return False
        else:
            result = self.action_client.get_result()
            status = self.action_client.get_state()
            if result:
                #  read result from subscriber
                self.read_action_result()
            if status == 3:
                self.pub_result(True)
            else:
                rospy.logwarn(rospy.get_name() + ": move base failed to move to the goal")
                self.pub_result(False)           
            return True

    def read_action_result(self):
        with GoalInterpreterClass.LOCK[self.sub_topic_result]:
            self.temp_sub[self.sub_topic_result]= GoalInterpreterClass.DATA[self.sub_topic_result]
            rospy.logwarn(rospy.get_name() + ": result: " + str(self.temp_sub[self.sub_topic_result]))   

    def main(self):
        pre_signal = False
        try:
            loop = asyncio.get_event_loop()
            while not rospy.is_shutdown():
                with GoalInterpreterClass.LOCK[self.sub_topic]:
                    self.temp_sub[self.sub_topic]= GoalInterpreterClass.DATA[self.sub_topic]
                
                if pre_signal == False and self.temp_sub[self.sub_topic] == True:
                    self.pub_result(False)
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                        loop.run_until_complete(self.main_pub_and_wait_action(loop, pool))
                pre_signal = self.temp_sub[self.sub_topic]
                self.rate.sleep()
        except rospy.ROSException:
            loop.close()
            pass
