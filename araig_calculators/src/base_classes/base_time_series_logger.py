#!/usr/bin/env python
import rospy
import yaml
import csv
from base_classes.base_logger import BaseLogger
from base_classes.base import get_sub_folder, check_folder
import os
import threading

class TimeSeriesLoggerClass(BaseLogger):
    def __init__(self):

        self.node_name = rospy.get_name()
        self.namespace_list = ["calculators"]

        param_list = [
            self.node_name + "/start_offset",
            self.node_name + "/stop_offset",
            self.node_name + "/logged_data_title",
            self.node_name + "/column_headers"
            ]

        self.config_param = {}
        self.getConfig(param_list)

        self.data_list = []
        self.data_available = False
        self.lock_data = threading.Lock()

        extend_subscribers_dict = {
        }

        super(TimeSeriesLoggerClass, self).__init__(
            param_list = param_list, \
            sub_dict = extend_subscribers_dict)

        try:
            while not rospy.is_shutdown():
                self.main_loop() 
        except rospy.ROSException:
            pass 

    # Must be overridden to populate self.data_row based on subscribed type, and self.data_available.
    def data_subscriber(self, msg):
        pass

    def main_loop(self):
        rospy.loginfo(rospy.get_name() + ": Waiting for start signal...")

        start = False
        stop = False

        while not start and not rospy.is_shutdown():
            self._rate.sleep()
            start = self.getSafeFlag("start")

        rospy.loginfo(rospy.get_name() + ": Start recevied. Sleep {}s to prepare"
                        .format(self.config_param[self.node_name + "/start_offset"]))
        rospy.sleep(self.config_param[self.node_name + "/start_offset"])
        folder = get_sub_folder()
        if check_folder(folder):
            filename = folder + "/" + self.config_param[self.node_name + "/logged_data_title"] + ".csv"
            rospy.loginfo(rospy.get_name() + ": Starting logging into {} "
                            .format(filename))

            with open(filename, mode='a') as target:
                writer = csv.writer(target)
                writer.writerow(self.config_param[self.node_name + "/column_headers"])
                while not stop and not rospy.is_shutdown():
                    self._rate.sleep()
                    with self.lock_data:
                        if self.data_available:
                            writer.writerow(self.data_list)
                            self.data_available = False
                            self.data_list = []
                    stop = self.getSafeFlag("stop")

            rospy.loginfo(rospy.get_name() + ": Stop recevied. Waiting for trigger signals to reset.")

        # Wait for stop and start to go low
        while (stop or start) and not rospy.is_shutdown():
                self._rate.sleep()
                stop = self.getSafeFlag("stop")
                start = self.getSafeFlag("start")
        rospy.loginfo(rospy.get_name() + ": Resetting.")
