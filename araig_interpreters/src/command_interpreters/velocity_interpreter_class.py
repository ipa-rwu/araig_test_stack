#!/usr/bin/env python
import rospy
import threading
from araig_msgs.msg import BoolStamped
from geometry_msgs.msg import Twist

class VelocityInterpreterClass():
    LOCK = {}
    DATA = {}
    def __init__(self,
        max_linear_x,
        loop_rate_hz = 1):

        self.pub_topic = "/velocity"
        self.sub_topic_start = "/start"
        self.sub_topic_stop = "/stop"

        self.max_linear_x = max_linear_x
        self.rate = rospy.Rate(loop_rate_hz)

        self.pub_init()
        self.sub_init()

        # init FLAG and LOCK
        for topic in [self.sub_topic_start, self.sub_topic_stop]:
            self.DATA[topic] = False
            self.LOCK[topic] = threading.Lock()
        
        self.main()
        
    def pub_init(self):
        self.pub_diag = rospy.Publisher(
                self.pub_topic, 
                Twist, 
                queue_size=10,
                latch = True
            )

    def callback_start(self, msg, args):
        with self.LOCK[args]:
            self.DATA[args] = msg.data

    def callback_stop(self, msg, args):
        with self.LOCK[args]:
            self.DATA[args] = msg.data

    def sub_init(self):
        sub_diag = {}
        sub_diag[self.sub_topic_start] = rospy.Subscriber(self.sub_topic_start, BoolStamped, self.callback_start, (self.sub_topic_start))
        sub_diag[self.sub_topic_stop] = rospy.Subscriber(self.sub_topic_stop, BoolStamped, self.callback_start, (self.sub_topic_stop))

      
    def main(self):
        flag_both_high = False
        pre_start = False 
        pre_stop = False
        msg = Twist()
        try:
            while not rospy.is_shutdown():
                temp = {}

                for topic in [self.sub_topic_start, self.sub_topic_stop]:
                    with self.LOCK[topic]:
                        temp[topic]= self.DATA[topic]

                if temp[self.sub_topic_start] == 1 and temp[self.sub_topic_stop] == 0:
                    msg.linear.x = self.max_linear_x
                    self.pub_diag.publish(msg)
                    if pre_start == False:
                        rospy.loginfo(rospy.get_name() +": send velocity({}) to robot...".format(msg.linear.x)) 
                        pre_start = True       
                    
                if temp[self.sub_topic_start] == 0 and temp[self.sub_topic_stop] == 1:
                    msg.linear.x = 0
                    self.pub_diag.publish(msg)
                    if pre_stop == False:
                        rospy.loginfo(rospy.get_name() +": stop robot...") 
                        pre_stop = True       

                if temp[self.sub_topic_start] == 1 and temp[self.sub_topic_stop] == 1 and flag_both_high == False:
                    rospy.logwarn(rospy.get_name() +": Both  START and STOP signals are high")
                    flag_both_high = True

                if pre_stop == True and pre_stop == True and temp[self.sub_topic_start] == 0 and temp[self.sub_topic_stop] == 0:
                    rospy.logwarn(rospy.get_name() +": reset velocity interpreter")
                    pre_start = False 
                    pre_stop = False
                
            self.rate.sleep()   
        except rospy.ROSException:
            pass