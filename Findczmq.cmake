# see https://github.com/zeromq/czmq/blob/master/Findlibzmq.cmake

if(CONAN_INCLUDE_DIRS_CZMQ AND CONAN_LIB_DIRS_ZMQ AND CONAN_LIBS_CZMQ)
	find_path(CZMQ_INCLUDE_DIR NAMES czmq.h PATHS ${CONAN_INCLUDE_DIRS_ZYRE} NO_CMAKE_FIND_ROOT_PATH)
	find_library(CZMQ_LIBRARY NAMES ${CONAN_LIBS_CZMQ} PATHS ${CONAN_LIB_DIRS_CZMQ} NO_CMAKE_FIND_ROOT_PATH)
else()
	find_path(CZMQ_INCLUDE_DIR NAMES czmq.h )
	find_library(CZMQ_LIBRARY NAMES czmq)
endif()

set(CZMQ_FOUND ON)
set(CZMQ_INCLUDE_DIRS ${CZMQ_INCLUDE_DIR})
set(CZMQ_LIBRARIES ${CZMQ_LIBRARY})

message(STATUS "czmq found by conan!")
message(STATUS "CZMQ_INCLUDE_DIR: ${CZMQ_INCLUDE_DIR}")
message(STATUS "CZMQ_LIBRARY: ${CZMQ_LIBRARY}")
