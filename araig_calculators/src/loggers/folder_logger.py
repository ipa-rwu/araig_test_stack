#!/usr/bin/env python
import rospy
from base_classes.base_logger import BaseLogger
import os
from datetime import datetime

class FolderManagerClass(BaseLogger):
    def __init__(self):

        extend_subscribers_dict = {
            "test_failed"          : "/test_failed",
            "test_succeeded"       : "/test_succeeded",
        }

        self.node_name = rospy.get_name()
        param_list = [
            self.node_name + "/start_offset",
            self.node_name + "/stop_offset",
            "/test_type"]

        super(FolderManagerClass, self).__init__(sub_dict= extend_subscribers_dict, param_list = param_list)

        try:
            while not rospy.is_shutdown():
                self.main_loop() 
        except rospy.ROSException:
            pass

    def main_loop(self):
        rospy.loginfo(rospy.get_name() + ": Waiting for start signal...")

        start = False
        stop = False
        while not start and not rospy.is_shutdown():
            self._rate.sleep()
            start = self.getSafeFlag("start")
    
         # get published topic
        if start == True and stop == False:
            now = datetime.now()
            self.dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")

            rospy.sleep(self.config_param[self.node_name + "/start_offset"])

            try: 
                os.listdir(self.pathFolder)
            except OSError as err:
                if err.errno == 2:
                    os.makedirs(self.pathFolder) 

            size = len(os.listdir(self.pathFolder))
            size += 1
            self.folder_name = self.pathFolder + str(size)
            rospy.loginfo(rospy.get_name() + ": Create folder: %s", self.folder_name)
            
            try:
                os.mkdir(self.folder_name)
                rospy.loginfo(rospy.get_name() + ": Successfully created the directory " + self.folder_name)
            except OSError as err:
                rospy.logerr(rospy.get_name() + ": Failed to create " + self.folder_name + ", serror msg: "+ str(err))
    
        # Wait for stop signal
        while not stop and not rospy.is_shutdown():
            self._rate.sleep()
            stop = self.getSafeFlag("stop")
        
        if stop == True and not rospy.is_shutdown():
            rospy.sleep(self.config_param[self.node_name + "/stop_offset"])
            if self.getSafeFlag("test_failed"):
                os.rename(self.folder_name, self.folder_name + "_" + self.dt_string + "_failed")
                rospy.loginfo(rospy.get_name() + ": Test failed, rename folder")
            if self.getSafeFlag("test_succeeded"):
                os.rename(self.folder_name, self.folder_name + "_" + self.dt_string + "_succeeded")
                rospy.loginfo(rospy.get_name() + ": Test succeeded, rename folder")
