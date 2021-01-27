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
   scripts/goal_pose_tf_broadcaster
   scripts/goal_interpreter
   scripts/velocity_interpreter
   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
 )

if (CATKIN_ENABLE_TESTING)
  find_package(roslint REQUIRED)
  roslint_python()
  roslint_add_test()

  find_package(rostest REQUIRED)
  include_directories(include ${catkin_INCLUDE_DIRS})

  add_rostest(tests/test_velocity_interpreter.test)
  add_rostest(tests/test_goal_interpreter.test)
  add_rostest(tests/test_goal_interpreter_action.test)

endif()