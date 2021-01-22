#!/usr/bin/env python
from multipledispatch import dispatch as Override
import rospy
import math
from scipy.spatial.transform import Rotation
from geometry_msgs.msg import PoseStamped

from araig_msgs.msg import BoolStamped, Float64Stamped
from base_classes.base_calculator import BaseCalculator

"""Compare data from one topics, wait for one signal, output 2 topics, data_type: Float64
    pub_list = {"/displacement_angular": Float64, 
                "/displacement_position": Float64}
    sub_list = {"/in_start": BoolStamped, "/in_stop": BoolStamped, "/in_pose": PoseStamped}
    inherence Comparator, only modify compare function"""
class diffPoseTemporal(BaseCalculator):
    _sub_topic_start = "/in_start"
    _sub_topic_stop = "/in_stop"
    _sub_topic_pose = "/in_pose"
    _pub_topic_angular = "/out_disp_angular"
    _pub_topic_position = "/out_disp_position"
    def __init__(self,
                sub_dict = {_sub_topic_start: BoolStamped,
                            _sub_topic_stop: BoolStamped,
                            _sub_topic_pose: PoseStamped},
                pub_dict = {_pub_topic_angular: Float64Stamped,
                    _pub_topic_position: Float64Stamped},
                rate = None):

            self._prestate_start = False
            self._prestate_stop = False

            self._posestamp_start = None
            self._posestamp_stop = None

            self._flag_get_result = False

            super(diffPoseTemporal, self).__init__(
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
        pub_msg_position = self.PubDict[self._pub_topic_position]()
        pub_msg_angular = self.PubDict[self._pub_topic_angular]()

        with BaseCalculator.LOCK[self._sub_topic_start] and BaseCalculator.LOCK[self._sub_topic_pose]:  
            temp[self._sub_topic_start] = BaseCalculator.MSG[self._sub_topic_start]
            temp[self._sub_topic_pose] = BaseCalculator.MSG[self._sub_topic_pose]

        if temp[self._sub_topic_start] != None:
            if self._prestate_start == False and \
                temp[self._sub_topic_start].data == True:
                if temp[self._sub_topic_pose] == None:
                    rospy.logwarn(rospy.get_name() + ": Got Start Signal but didn't get object pose, please resent start signal")
                    temp[self._sub_topic_start].data = False
                else:
                    self._posestamp_start = temp[self._sub_topic_pose]
                    rospy.loginfo(rospy.get_name() + ": Started")

            self._prestate_start = temp[self._sub_topic_start].data
        
        with BaseCalculator.LOCK[self._sub_topic_stop] and BaseCalculator.LOCK[self._sub_topic_pose]:  
            temp[self._sub_topic_stop] = BaseCalculator.MSG[self._sub_topic_stop]
            temp[self._sub_topic_pose] = BaseCalculator.MSG[self._sub_topic_pose]
   
        if temp[self._sub_topic_stop] != None and \
            temp[self._sub_topic_start] != None and \
            temp[self._sub_topic_start].data == True:
            if self._prestate_stop == False and \
                temp[self._sub_topic_stop].data == True:
                self._posestamp_stop = temp[self._sub_topic_pose]
                rospy.loginfo(rospy.get_name() + ": Stopped")

                delta_x = abs(self._posestamp_start.pose.position.x - self._posestamp_stop.pose.position.x)
                delta_y = abs(self._posestamp_start.pose.position.y - self._posestamp_stop.pose.position.y)

                pub_msg_angular.data = abs(self.get_yaw_from_quaternion(self._posestamp_start.pose.orientation) - \
                                    self.get_yaw_from_quaternion(self._posestamp_stop.pose.orientation) )
                pub_msg_angular.header.stamp = rospy.Time.now()

                pub_msg_position.data = math.sqrt((delta_x*delta_x) + (delta_y*delta_y))
                pub_msg_position.header.stamp = rospy.Time.now()

                self.PubDiag[self._pub_topic_angular].publish(pub_msg_angular)
                self.PubDiag[self._pub_topic_position].publish(pub_msg_position)
                rospy.loginfo("{}: Delta angle is {}".format(rospy.get_name(), pub_msg_angular.data))
                rospy.loginfo("{}: Delta position is {}".format(rospy.get_name(), pub_msg_position.data))
            self._prestate_stop = temp[self._sub_topic_stop].data
