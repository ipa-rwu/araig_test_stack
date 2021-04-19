#!/usr/bin/env python
import rospy
from base_classes.base_logger import BaseLogger
from base_classes.base import get_sub_folder, check_folder
import os
class RosparamLoggerClass(BaseLogger):
    def __init__(self):
        
        self.node_name = rospy.get_name()
        self.namespace_list = ["calculators"]

        param_list = [
            self.node_name + "/start_offset",
            self.node_name + "/stop_offset",
            self.node_name + "/namespaces",
            ]

        super(RosparamLoggerClass, self).__init__(param_list = param_list)

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

        if start == True and stop == False:
            rospy.sleep(self.config_param[self.node_name + "/start_offset"])
            folder = get_sub_folder()
            
            for ns in self.config_param[self.node_name + "/namespaces"]:
                if check_folder(folder):
                    command = "rosparam dump " + folder +"/param_"+ ns + ".yaml" + " /" + ns
                    self.startCommandProc(command)
                    rospy.loginfo(rospy.get_name() + ": Save rosparam under namespace: " + ns)
                    rospy.sleep(self.config_param[self.node_name + "/stop_offset"])
                    self.killCommandProc()

        # Wait for stop signal
        while stop is False and start is True and not rospy.is_shutdown():
            self._rate.sleep()
            stop = self.getSafeFlag("stop")
            start = self.getSafeFlag("start")