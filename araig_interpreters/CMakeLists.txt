cmake_minimum_required(VERSION 3.0.2)
project(araig_interpreters)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  marvelmind_nav
  geometry_msgs
  std_msgs
  tf
  tf2
  tf2_ros
  tf2_geometry_msgs
  araig_msgs
)

find_package(Boost REQUIRED)

catkin_python_setup()

catkin_package(
   CATKIN_DEPENDS
   marvelmind_nav
   rospy
   araig_msgs
   INCLUDE_DIRS
   include
)

include_directories(
  include
  ${catkin_INCLUDE_DIRS}
  ${Boost_INCLUDES}
)


add_executable(marvel_location_interpreter src/location_interpreters/marvel_interpreter.cpp)
target_link_libraries(marvel_location_interpreter ${catkin_LIBRARIES} ${Boost_LIBRARIES})
add_dependencies(marvel_location_interpreter ${catkin_EXPORTED_TARGETS})
install(TARGETS marvel_location_interpreter DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

catkin_install_python(PROGRAMS
   scripts/pose_tf_broadcaster
   scripts/goal_interpreter
   scripts/velocity_interpreter
   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
 )
