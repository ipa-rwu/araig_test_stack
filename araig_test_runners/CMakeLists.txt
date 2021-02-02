cmake_minimum_required(VERSION 3.0.2)
project(araig_test_runners)

find_package(catkin REQUIRED COMPONENTS
  rospy
)

catkin_python_setup()

catkin_package(
   CATKIN_DEPENDS rospy
)

catkin_install_python(PROGRAMS
   scripts/test_1_braking
   scripts/test_4_static_obstacle
   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch
   DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)