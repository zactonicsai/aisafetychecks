cmake_minimum_required(VERSION 3.20)
project(factory_calculator LANGUAGES CXX)
enable_testing()
add_executable(calculator_test calculator_test.cpp)
target_compile_features(calculator_test PRIVATE cxx_std_17)
target_compile_options(calculator_test PRIVATE -Wall -Wextra -Wpedantic)
add_test(NAME calculator_test COMMAND calculator_test)

