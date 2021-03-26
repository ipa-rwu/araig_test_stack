#!/usr/bin/env python

import rospy
import subprocess, shlex
from araig_msgs.msg import BoolStamped
from base_classes.base_logger import BaseLogger
import threading
from datetime import datetime
import os

def get_folder_name(root):
    try: 
        os.listdir(root)
    except OSError as err:
        if err.errno == 2:
            os.makedirs(root) 
    
    size = len(os.listdir(root))
    size += 1
    folder_name = root + str(size)
    return folder_name

def create_folder(folder_name):
    try:
        os.mkdir(folder_name)
        rospy.loginfo(rospy.get_name() + ": Successfully created the directory " + folder_name)
    except OSError as err:
        rospy.logerr(rospy.get_name() + ": Failed to create " + folder_name + ", error msg: "+ str(err))

class FolderBagger(BaseLogger):
    def __init__(self):

        self.node_name = rospy.get_name()

        extend_subscribers_dict = {
            "test_failed"          : "/test_failed",
            "test_succeeded"       : "/test_succeeded",
        }

        param_list = [
            self.node_name + "/start_offset",
            self.node_name + "/stop_offset",
            self.node_name + "/blacklist",
            "/test_type"]

        super(FolderBagger, self).__init__(sub_dict= extend_subscribers_dict, param_list = param_list)

        try:
            while not rospy.is_shutdown():
                self.main_loop() 
        except rospy.ROSException:
            pass 

    def prepare_topics(self):
        list_of_topics = rospy.get_published_topics()
        list_of_topics.sort()
        topics_string = ""

        for topic,msg in list_of_topics:
            topic_allowed = True
            for black_string in self.config_param[self.node_name + "/blacklist"]:
                if black_string in topic:
                    rospy.logwarn(rospy.get_name()
                    + " Ignoring topic {} since it is blocked by the entry {} in blacklist"
                    .format(topic, black_string))
                    topic_allowed = False
                    break
            if topic_allowed:
                 topics_string = topics_string + topic + " "

        return topics_string

    def main_loop(self):
        rospy.loginfo(rospy.get_name() + ": Waiting for start signal...")
        # Wait for start signal
        start = False
        stop = False

        while not start and not rospy.is_shutdown():
            self._rate.sleep()
            start = self.getSafeFlag("start")

         # Create folder -> sleep -> start recording
        if start == True and stop == False:
            now = datetime.now()
            dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")

            folder_name = get_folder_name(self.pathFolder)
            create_folder(folder_name)

            rospy.loginfo(rospy.get_name() + ": Start received. Sleep {}s to prepare..."
                .format(self.config_param[self.node_name + "/start_offset"]))
            rospy.sleep(self.config_param[self.node_name + "/start_offset"])

            currentFolder = self.getSubFolder()
            topics_string = self.prepare_topics()
            command = "rosbag record -o " + currentFolder + "/" + self.config_param["/test_type"] + " " + topics_string

            self.startCommandProc(command)

        # Wait for stop signal
        while not stop and not rospy.is_shutdown():
            self._rate.sleep()
            stop = self.getSafeFlag("stop")
        
        # Sleep -> Kill recorder (other loggers finish their tasks) -> rename folder
        if start == True:
            if stop or rospy.is_shutdown():
                rospy.loginfo(rospy.get_name() + ": Stop received. Sleep {}s to settle..."
                    .format(self.config_param[self.node_name + "/stop_offset"]))
                rospy.sleep(self.config_param[self.node_name + "/stop_offset"])
                self.killCommandProc()
                rospy.sleep(0.5) # Sleep again to let process die properly
                if self.getSafeFlag("test_failed"):
                    os.rename(folder_name, folder_name + "_" + dt_string + "_failed")
                    rospy.loginfo(rospy.get_name() + ": Test failed, rename folder")
                elif self.getSafeFlag("test_succeeded"):
                    os.rename(folder_name, folder_name + "_" + dt_string + "_succeeded")
                    rospy.loginfo(rospy.get_name() + ": Test succeeded, rename folder")
