---
title: Chapter 3 - URDF for Humanoid Robots
sidebar_position: 3
description: Understanding URDF purpose, structure, and application in humanoid robot modeling
---

# Chapter 3: URDF for Humanoid Robots

## URDF Purpose and Structure

URDF (Unified Robot Description Format) is an XML-based format used in ROS to describe robot models. It defines the physical and visual properties of a robot, including its links, joints, and other components. URDF is essential for:

- **Simulation**: Creating accurate models for robot simulation in tools like Gazebo
- **Visualization**: Displaying robot models in RViz and other visualization tools
- **Kinematics**: Computing forward and inverse kinematics
- **Dynamics**: Performing dynamic simulations and analysis
- **Collision detection**: Determining when parts of a robot collide with each other or the environment

### Basic URDF Structure

A URDF file typically contains:

- **Links**: Rigid bodies that make up the robot
- **Joints**: Connections between links that allow relative motion
- **Visual elements**: How the robot appears in visualization
- **Collision elements**: Shapes used for collision detection
- **Inertial properties**: Mass, center of mass, and inertia tensor for each link

## Links: The Building Blocks

Links represent rigid bodies in the robot. Each link has:

- **Visual properties**: How the link appears (geometry, material, origin)
- **Collision properties**: Shape used for collision detection
- **Inertial properties**: Mass, center of mass, and inertia tensor

### Example Link Definition

```xml
<link name="base_link">
  <visual>
    <geometry>
      <cylinder length="0.6" radius="0.2"/>
    </geometry>
    <material name="blue">
      <color rgba="0 0 0.8 1"/>
    </material>
  </visual>
  <collision>
    <geometry>
      <cylinder length="0.6" radius="0.2"/>
    </geometry>
  </collision>
  <inertial>
    <mass value="10"/>
    <origin xyz="0 0 0"/>
    <inertia ixx="1.0" ixy="0.0" ixz="0.0" iyy="1.0" iyz="0.0" izz="1.0"/>
  </inertial>
</link>
```

### Link Properties

- **Geometry types**: Box, cylinder, sphere, mesh
- **Materials**: Color and texture definitions
- **Inertial parameters**: Essential for physics simulation

## Joints: Connecting the Links

Joints define how links move relative to each other. The main joint types are:

- **Fixed**: No movement (0 DOF)
- **Revolute**: Single axis rotation (1 DOF) - limited by angle
- **Continuous**: Single axis rotation (1 DOF) - unlimited
- **Prismatic**: Single axis translation (1 DOF) - limited by position
- **Floating**: 6 DOF movement in space
- **Planar**: Movement in a plane (3 DOF)

### Example Joint Definition

```xml
<joint name="base_to_wheel" type="continuous">
  <parent link="base_link"/>
  <child link="wheel_link"/>
  <origin xyz="0.1 -0.2 0" rpy="0 0 0"/>
  <axis xyz="0 1 0"/>
</joint>
```

### Joint Properties

- **Parent and child links**: Defines the connection
- **Origin**: Position and orientation of the joint
- **Axis**: Direction of motion for revolute/prismatic joints
- **Limits**: For revolute and prismatic joints (effort, velocity, lower, upper)

## Kinematic Chains in Humanoid Robots

Humanoid robots have complex kinematic structures with multiple chains:

- **Leg chains**: From hip to foot (typically 6+ DOF per leg)
- **Arm chains**: From shoulder to hand (typically 7 DOF per arm)
- **Head chain**: From neck to head
- **Torso**: Connecting upper and lower body

### Forward Kinematics

Forward kinematics calculates the position and orientation of the end-effector given joint angles:

```
T = f(θ₁, θ₂, ..., θₙ)
```

Where T is the transformation matrix and θᵢ are joint angles.

### Inverse Kinematics

Inverse kinematics calculates joint angles needed to achieve a desired end-effector position:

```
θ = f⁻¹(T)
```

## URDF for Humanoid Robot Examples

### Simplified Humanoid Torso

```xml
<?xml version="1.0"?>
<robot name="simple_humanoid">
  <!-- Base link -->
  <link name="base_link">
    <visual>
      <geometry>
        <box size="0.3 0.3 0.3"/>
      </geometry>
      <material name="grey">
        <color rgba="0.5 0.5 0.5 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <box size="0.3 0.3 0.3"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="5"/>
      <origin xyz="0 0 0"/>
      <inertia ixx="0.1" ixy="0" ixz="0" iyy="0.1" iyz="0" izz="0.1"/>
    </inertial>
  </link>

  <!-- Torso -->
  <link name="torso">
    <visual>
      <geometry>
        <box size="0.2 0.2 0.5"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 0.8 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <box size="0.2 0.2 0.5"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="3"/>
      <origin xyz="0 0 0.25"/>
      <inertia ixx="0.05" ixy="0" ixz="0" iyy="0.05" iyz="0" izz="0.02"/>
    </inertial>
  </link>

  <!-- Joint connecting base to torso -->
  <joint name="base_to_torso" type="fixed">
    <parent link="base_link"/>
    <child link="torso"/>
    <origin xyz="0 0 0.15"/>
  </joint>

  <!-- Head -->
  <link name="head">
    <visual>
      <geometry>
        <sphere radius="0.1"/>
      </geometry>
      <material name="white">
        <color rgba="1 1 1 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <sphere radius="0.1"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="1"/>
      <origin xyz="0 0 0"/>
      <inertia ixx="0.004" ixy="0" ixz="0" iyy="0.004" iyz="0" izz="0.004"/>
    </inertial>
  </link>

  <!-- Neck joint -->
  <joint name="neck_joint" type="revolute">
    <parent link="torso"/>
    <child link="head"/>
    <origin xyz="0 0 0.3"/>
    <axis xyz="0 1 0"/>
    <limit lower="-0.5" upper="0.5" effort="10" velocity="1"/>
  </joint>
</robot>
```

## Using URDF with ROS 2 and Simulators

### URDF in ROS 2

In ROS 2, URDF files are typically stored in the `urdf` directory of a package and can be loaded using the `robot_state_publisher` node:

```xml
<launch>
  <node pkg="robot_state_publisher" exec="robot_state_publisher" name="robot_state_publisher">
    <param name="robot_description" value="$(find-pkg-share my_robot_description)/urdf/my_robot.urdf"/>
  </node>
</launch>
```

### Robot State Publisher

The `robot_state_publisher` node:

- Reads the URDF from a parameter
- Subscribes to joint state information
- Publishes the computed transforms to the `/tf` topic
- Allows visualization of the robot in RViz

### Integration with Gazebo

For simulation in Gazebo, additional tags are needed in URDF:

```xml
<gazebo reference="link_name">
  <material>Gazebo/Blue</material>
  <mu1>0.2</mu1>
  <mu2>0.2</mu2>
</gazebo>
```

## Advanced URDF Concepts

### Transmission Elements

Transmission elements define how actuators connect to joints:

```xml
<transmission name="wheel_trans">
  <type>transmission_interface/SimpleTransmission</type>
  <joint name="wheel_joint">
    <hardwareInterface>hardware_interface/VelocityJointInterface</hardwareInterface>
  </joint>
  <actuator name="wheel_motor">
    <hardwareInterface>hardware_interface/VelocityJointInterface</hardwareInterface>
    <mechanicalReduction>1</mechanicalReduction>
  </actuator>
</transmission>
```

### Gazebo-Specific Tags

For simulation in Gazebo, you can include:

- `<gazebo>` tags for simulation properties
- `<sensor>` tags for sensor definitions
- `<plugin>` tags for Gazebo plugins

### Xacro for Complex Models

Xacro (XML Macros) allows for more maintainable URDF files:

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="humanoid_with_xacro">
  <xacro:property name="M_PI" value="3.14159"/>

  <xacro:macro name="simple_cylinder" params="name radius length color_xyz">
    <link name="${name}">
      <visual>
        <geometry>
          <cylinder radius="${radius}" length="${length}"/>
        </geometry>
        <material name="${name}_material">
          <color rgba="${color_xyz} 1"/>
        </material>
      </visual>
    </link>
  </xacro:macro>

  <xacro:simple_cylinder name="leg" radius="0.05" length="0.5" color_xyz="0.5 0.5 0.5"/>
</robot>
```

## Best Practices for Humanoid Robot URDF

### 1. Proper Mass Distribution

- Accurate inertial properties are crucial for simulation
- Use CAD software to calculate mass properties when possible
- Verify that the total robot mass matches expectations

### 2. Realistic Joint Limits

- Set appropriate joint limits based on mechanical constraints
- Include safety margins in joint limits
- Consider the robot's intended range of motion

### 3. Collision Avoidance

- Design the model to prevent self-collision in normal operation
- Include collision geometry that represents the true collision envelope
- Test the model in simulation for potential collision scenarios

### 4. Visualization vs. Collision

- Use detailed meshes for visualization
- Use simplified shapes for collision detection (for performance)
- Ensure collision geometry completely encompasses the visual geometry

## Common URDF Issues and Troubleshooting

### Invalid URDF

- Check for proper XML syntax
- Ensure all joint parents and children exist
- Verify that there are no loops in the kinematic structure

### Kinematic Issues

- Check that joint axes are properly oriented
- Verify that joint limits are appropriate
- Ensure the robot has a proper base link

### Simulation Problems

- Verify inertial properties are realistic
- Check that collision geometry is properly defined
- Ensure joint friction and damping parameters are set appropriately

## Summary

URDF is a fundamental tool for representing humanoid robots in ROS 2. Understanding its structure and proper usage is essential for simulation, visualization, and control of complex robotic systems. Properly designed URDF models enable accurate simulation and safe robot operation, making them a critical component in humanoid robot development.

## Previous Chapters

Review these previous chapters if you need to refresh your understanding:

- [ROS 2 Fundamentals](./chapter1-ros2-fundamentals.md)
- [ROS 2 Communication Patterns](./chapter2-ros2-communication.md)