#!/usr/bin/env python
from multipledispatch import dispatch as Override
import rospy
import math
from scipy.spatial.transform import Rotation
from geometry_msgs.msg import PoseStamped

from base_classes.base_calculator import BaseCalculator
from araig_msgs.msg import BoolStamped

"""Compare data from two topics, output data_type: bool
    pub_dict = {"/signal": BoolStamped}
    sub_dict = {"topic_1": PoseStamped, "topic_2": PoseStamped}
    inherence Base, only modify compare function"""
class compPoses(BaseCalculator):
    _sub_topic_pose_1 = "/in_pose_1"
    _sub_topic_pose_2 = "/in_pose_2"
    _pub_topic = "/out_bool"
    def __init__(self,
            sub_dict = {_sub_topic_pose_1: PoseStamped,
                        _sub_topic_pose_2: PoseStamped}, 
            pub_dict = {_pub_topic: BoolStamped},
            delta_pos_thresh_meters=0.01, 
            delta_theta_thresh_degrees=5,
            rate = None):
        
            self._delta_pos_thresh_meters = delta_pos_thresh_meters 
            self._delta_theta_thresh_degrees = delta_theta_thresh_degrees
            # checking previous state  
            self.pre_state = None 
            
            super(compPoses, self).__init__(
                sub_dict = sub_dict,
                pub_dict = pub_dict,
                rate = rate)

    def get_yaw_from_quaternion(self, orientation):
        quaternion = [orientation.x,
                        orientation.y,
                        orientation.z,
                        orientation.w]
        rot = Rotation.from_quat(quaternion)
        euler = rot.as_euler('xyz', degrees = True)
        return euler[2]

    @Override()
    def calculate(self):
        temp = {}
        pub_msg = self.PubDict[self._pub_topic]()
        pub_msg.data = False

        for topic in self.SubDict.keys():
            with BaseCalculator.LOCK[topic]:
                temp[topic] = BaseCalculator.MSG[topic]
        
        flag_test_ready = True
        # if subscribered topic not publish yet, test is not ready
        for value in temp.values():
            if value == None:
                flag_test_ready = False
        
        if flag_test_ready == True:
            delta_x = abs(temp[self._sub_topic_pose_1].pose.position.x - temp[self._sub_topic_pose_2].pose.position.x)
            delta_y = abs(temp[self._sub_topic_pose_1].pose.position.y - temp[self._sub_topic_pose_2].pose.position.y)

            delta_theta = abs(self.get_yaw_from_quaternion(temp[self._sub_topic_pose_1].pose.orientation) - \
                                self.get_yaw_from_quaternion(temp[self._sub_topic_pose_2].pose.orientation) )
            delta_pos = math.sqrt((delta_x*delta_x) + (delta_y*delta_y))

            pub_msg.header.stamp = rospy.Time.now()
            if delta_pos <= self._delta_pos_thresh_meters:
                flag_pose = True
            else:
                flag_pose = False

            if self._delta_theta_thresh_degrees == None or delta_theta <= self._delta_theta_thresh_degrees:
                flag_theta = True
            else:
                flag_theta = False

            if flag_theta == True and flag_pose == True:
                pub_msg.data = True
            else:
                pub_msg.data = False

            if self.pub_only_state_change(pre_state = self.pre_state, \
                current_state = pub_msg.data, \
                pub_topic = self._pub_topic, \
                pub_msg = pub_msg, \
                log = "{}: {}".format(rospy.get_name(), pub_msg.data)):
                self.pre_state = pub_msg.data