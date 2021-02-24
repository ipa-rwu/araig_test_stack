#!/usr/bin/env python
import rospy
import yaml
from base_classes.base_logger import BaseLogger
from araig_msgs.msg import Float64Stamped
import threading

class ResultsLoggerClass(BaseLogger):
    def __init__(self):

        self.node_name = rospy.get_name()
        self.namespace_list = ["calculators"]

        param_list = [
            self.node_name + "/start_offset",
            self.node_name + "/stop_offset",
            self.node_name + "/logginng_topics",
            ]

        self.config_param = {}
        self.getConfig(param_list)
        self.result_topics_list = self.config_param[self.node_name + "/logginng_topics"]

        extend_subscribers_dict = {
            "test_failed"          : "/test_failed",
            "test_succeeded"       : "/test_succeeded",
        }

        super(ResultsLoggerClass, self).__init__(
            param_list = param_list, \
            result_list = self.result_topics_list, \
            sub_dict = extend_subscribers_dict)

        try:
            while not rospy.is_shutdown():
                self.main_loop() 
        except rospy.ROSException:
            pass 

    def main_loop(self):
        rospy.logwarn_once(rospy.get_name() + ": Waiting for start signal...")

        start = False
        stop = False
        test_succeeded = False
        while not start and not rospy.is_shutdown():
            self._rate.sleep()
            start = self.getSafeFlag("start")
            
        while not stop and not rospy.is_shutdown():
            self._rate.sleep()
            stop = self.getSafeFlag("stop")

        while not test_succeeded and not rospy.is_shutdown():
            self._rate.sleep()
            test_succeeded = self.getSafeFlag("test_succeeded")

        if start == True and stop == True and test_succeeded == True:
            rospy.sleep(self.config_param[self.node_name + "/start_offset"])
            currentFolder = self.getSubFolder()
            filename = currentFolder + "/result.yaml"
            rospy.loginfo(rospy.get_name() + ": Writing into {}...".format(filename))
            result = {}

            for topic in self.result_topics_list:
                result[topic] = self.getSafeFlag(topic)

            with open(filename, 'w+') as yaml_file:
                yaml.dump(result, yaml_file, default_flow_style=False)
        
        rospy.sleep(self.config_param[self.node_name + "/stop_offset"])    
        rospy.loginfo(rospy.get_name() + ": Finished writing into file")