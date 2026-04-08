---
title: Chapter 1 - ROS 2 Fundamentals
sidebar_position: 1
description: Introduction to ROS 2 as the middleware for humanoid robots
---

# Chapter 1: ROS 2 Fundamentals

## What is Robot Middleware?

Robot middleware serves as the communication backbone that allows different components of a robotic system to interact with each other. Think of it as the "nervous system" of a robot, enabling sensors, actuators, controllers, and other modules to exchange information seamlessly.

In traditional robotics, each component might use its own communication protocol, making it difficult to integrate new components or modify existing ones. Robot middleware solves this problem by providing:

- **Standardized communication protocols** that all components can use
- **Abstraction layers** that hide the complexity of direct hardware interaction
- **Message passing mechanisms** that allow asynchronous communication
- **Service discovery** to locate and connect to available services

## Introduction to ROS 2

ROS 2 (Robot Operating System 2) is the latest generation of the Robot Operating System, designed to address the limitations of the original ROS framework. Unlike its predecessor, ROS 2 is built from the ground up to be production-ready, with features like:

- **Real-time capabilities** for time-critical applications
- **Multi-robot systems** support for coordinating multiple robots
- **Security features** including authentication and encryption
- **Distributed computing** across multiple machines
- **Quality of Service (QoS)** policies for reliable communication

ROS 2 uses the Data Distribution Service (DDS) as its underlying communication middleware, which provides a rich set of communication patterns and policies.

## ROS 2 Architecture and DDS

The Data Distribution Service (DDS) is a middleware specification that provides a publisher-subscriber communication model. In ROS 2, DDS handles:

- **Discovery**: Automatically finding other nodes on the network
- **Transport**: Moving messages between nodes using various protocols (TCP, UDP, shared memory)
- **Quality of Service**: Configuring how messages are delivered (reliability, durability, etc.)

The ROS 2 architecture consists of several layers:

1. **Application Layer**: Your robot applications and algorithms
2. **Client Library Layer**: rclcpp (C++) and rclpy (Python) provide language-specific APIs
3. **ROS Client Library (rcl)**: Common interface for all client libraries
4. **DDS Abstraction Layer**: Abstracts different DDS implementations
5. **DDS Implementation**: Specific DDS vendor implementation (Fast DDS, Cyclone DDS, etc.)

## Role of ROS 2 in Humanoid Robots

Humanoid robots present unique challenges that make ROS 2 particularly valuable:

- **Complex sensor integration**: Humanoid robots have numerous sensors (cameras, IMUs, force sensors, joint encoders) that need to communicate in real-time
- **Distributed processing**: Different parts of the robot (head, arms, legs) may have separate computing units that need to coordinate
- **Safety-critical communication**: Fall prevention and safe interaction require reliable, low-latency communication
- **Modular development**: Different teams can work on perception, locomotion, manipulation, and control independently

ROS 2's distributed architecture allows humanoid robots to scale from simple research platforms to complex commercial systems with hundreds of nodes communicating simultaneously.

## Key Concepts in ROS 2

### Nodes
A node is a process that performs computation. In a humanoid robot, you might have nodes for:
- Perception (vision, audio, tactile sensing)
- Planning (motion planning, path planning)
- Control (joint control, balance control)
- Communication (networking, user interfaces)

### Topics and Messages
Topics are named buses over which nodes exchange messages. For example:
- `/joint_states` for sharing the current position of robot joints
- `/camera/image_raw` for raw camera images
- `/cmd_vel` for sending velocity commands

### Services
Services provide a request-response communication pattern. Examples include:
- `/set_parameters` to configure robot parameters
- `/get_map` to retrieve a map from a mapping node

### Actions
Actions are for long-running tasks with feedback. Common actions in humanoid robots:
- `/move_base` for navigation tasks
- `/joint_trajectory` for coordinated movement of multiple joints

## Summary

ROS 2 serves as the essential communication framework for humanoid robots, enabling complex systems to work together cohesively. Its architecture based on DDS provides the reliability and flexibility needed for real-world robotic applications. Understanding these fundamentals is crucial for developing sophisticated humanoid robot systems.

## Next Steps

Continue to the next chapter to learn about [ROS 2 Communication Patterns](./chapter2-ros2-communication.md).