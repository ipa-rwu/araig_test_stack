#!/usr/bin/env python
# license removed for brevity
import rospy
import subprocess, shlex
from araig_msgs.msg import BoolStamped
from base_classes.base_logger import BaseLogger
import threading

class RosbaggerClass(BaseLogger):
    def __init__(self):

        self.node_name = rospy.get_name()
        param_list = [
            self.node_name + "/start_offset",
            self.node_name + "/stop_offset",
            self.node_name + "/blacklist",
            self.node_name + "/whitelist",
            "/test_type"]

        super(RosbaggerClass, self).__init__(param_list = param_list)

        try:
            while not rospy.is_shutdown():
                self.main_loop() 
        except rospy.ROSException:
            pass 
    
    def prepare_topics(self):
        list_of_topics = rospy.get_published_topics()
        list_of_topics.sort()
        topics_string = ""
        for topic, msg in list_of_topics:
            for black_topic in self.config_param[self.node_name + "/blacklist"]:
                if topic == black_topic:
                    topic = ""
            for white_topic in self.config_param[self.node_name + "/whitelist"]:
                if topic == white_topic:
                    topic = ""
            topics_string = topics_string + topic + " "
        
        for white_topic in self.config_param[self.node_name + "/whitelist"]:
            topics_string = topics_string + white_topic + " "
        
        return topics_string

    def main_loop(self):
        rospy.loginfo(rospy.get_name() + ": Waiting for start signal...")
        # Wait for start signal
        start = False
        stop = False
        while not start and not rospy.is_shutdown():
            self._rate.sleep()
            start = self.getSafeFlag("start")
    
         # get published topic
        if start == True and stop == False:
            rospy.sleep(self.config_param[self.node_name + "/start_offset"])
            currentFolder = self.getSubFolder() 

            topics_string = self.prepare_topics()
                
            # Prepare command
            command = "rosbag record -o " + currentFolder + "/" + self.config_param["/test_type"] + " " + topics_string
            rospy.loginfo(rospy.get_name() + ": " + command)
            self.startCommandProc(command)

        # Wait for stop signal
        while not stop and not rospy.is_shutdown():
            self._rate.sleep()
            stop = self.getSafeFlag("stop")
        
        if start == True:
            if stop or rospy.is_shutdown():
                rospy.sleep(self.config_param[self.node_name + "/stop_offset"])
                self.killCommandProc()