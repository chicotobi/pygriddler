cmake_minimum_required(VERSION 3.15)
project(nonogram_solver)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optimization flags
if(MSVC)
    add_compile_options(/O2 /arch:AVX2)
else()
    add_compile_options(-O3 -march=native)
endif()

# Find Python
find_package(Python COMPONENTS Interpreter Development REQUIRED)

# Add pybind11
add_subdirectory(pybind11)

# Create the Python module
pybind11_add_module(nonogram_cpp 
    python_bindings.cpp
    nonogram_solver.cpp
)

# Link libraries if needed
target_include_directories(nonogram_cpp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
