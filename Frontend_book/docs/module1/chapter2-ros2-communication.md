---
title: Chapter 2 - ROS 2 Communication Patterns
sidebar_position: 2
description: Understanding nodes, topics, services, and actions in ROS 2
---

# Chapter 2: ROS 2 Communication Patterns

## Nodes: The Building Blocks of ROS 2

In ROS 2, a node is the fundamental unit of computation. Each node typically performs a specific task and communicates with other nodes through various communication patterns. Nodes are organized in a peer-to-peer network where each node can potentially communicate with any other node.

### Creating Nodes in Python with rclpy

The `rclpy` library provides the Python API for ROS 2. Here's how to create a basic node:

```python
import rclpy
from rclpy.node import Node

class MyRobotNode(Node):
    def __init__(self):
        super().__init__('my_robot_node')
        self.get_logger().info('MyRobotNode has been started')

def main(args=None):
    rclpy.init(args=args)
    node = MyRobotNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### Node Lifecycle

ROS 2 nodes have a well-defined lifecycle with states like:
- Unconfigured
- Inactive
- Active
- Finalized

This lifecycle management allows for better resource control and system reliability.

## Topics: Publisher-Subscriber Communication

Topics enable asynchronous, one-way communication between nodes using a publish-subscribe pattern. Publishers send messages to topics, and subscribers receive messages from topics they're subscribed to.

### Creating a Publisher

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MinimalPublisher(Node):
    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Hello World: {self.i}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.i += 1

def main(args=None):
    rclpy.init(args=args)
    minimal_publisher = MinimalPublisher()

    try:
        rclpy.spin(minimal_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        minimal_publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### Creating a Subscriber

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MinimalSubscriber(Node):
    def __init__(self):
        super().__init__('minimal_subscriber')
        self.subscription = self.create_subscription(
            String,
            'topic',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info(f'I heard: "{msg.data}"')

def main(args=None):
    rclpy.init(args=args)
    minimal_subscriber = MinimalSubscriber()

    try:
        rclpy.spin(minimal_subscriber)
    except KeyboardInterrupt:
        pass
    finally:
        minimal_subscriber.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Services: Request-Response Communication

Services provide synchronous, bidirectional communication where a client sends a request and waits for a response from a server.

### Creating a Service Server

```python
from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.node import Node

class MinimalService(Node):
    def __init__(self):
        super().__init__('minimal_service')
        self.srv = self.create_service(AddTwoInts, 'add_two_ints', self.add_two_ints_callback)

    def add_two_ints_callback(self, request, response):
        response.sum = request.a + request.b
        self.get_logger().info(f'Incoming request\na: {request.a}, b: {request.b}\n')
        return response

def main(args=None):
    rclpy.init(args=args)
    minimal_service = MinimalService()

    try:
        rclpy.spin(minimal_service)
    except KeyboardInterrupt:
        pass
    finally:
        minimal_service.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### Creating a Service Client

```python
from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.node import Node

class MinimalClient(Node):
    def __init__(self):
        super().__init__('minimal_client')
        self.cli = self.create_client(AddTwoInts, 'add_two_ints')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting again...')
        self.req = AddTwoInts.Request()

    def send_request(self, a, b):
        self.req.a = a
        self.req.b = b
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

def main(args=None):
    rclpy.init(args=args)
    minimal_client = MinimalClient()
    response = minimal_client.send_request(1, 2)
    minimal_client.get_logger().info(f'Result of add_two_ints: {response.sum}')

    minimal_client.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Actions: Long-Running Tasks with Feedback

Actions are used for long-running tasks that provide feedback during execution and return a result upon completion. They're perfect for tasks like navigation or trajectory execution.

### Action Structure

An action has three parts:
- **Goal**: The desired outcome
- **Feedback**: Updates on the progress
- **Result**: The final outcome

### Creating an Action Server

```python
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from example_interfaces.action import Fibonacci

class FibonacciActionServer(Node):
    def __init__(self):
        super().__init__('fibonacci_action_server')
        self._action_server = ActionServer(
            self,
            Fibonacci,
            'fibonacci',
            self.execute_callback)

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')

        feedback_msg = Fibonacci.Feedback()
        feedback_msg.sequence = [0, 1]

        for i in range(1, goal_handle.request.order):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info('Goal canceled')
                return Fibonacci.Result()

            feedback_msg.sequence.append(
                feedback_msg.sequence[i] + feedback_msg.sequence[i-1])

            goal_handle.publish_feedback(feedback_msg)
            self.get_logger().info(f'Feedback: {feedback_msg.sequence}')

        goal_handle.succeed()
        result = Fibonacci.Result()
        result.sequence = feedback_msg.sequence
        return result

def main(args=None):
    rclpy.init(args=args)
    fibonacci_action_server = FibonacciActionServer()

    try:
        rclpy.spin(fibonacci_action_server)
    except KeyboardInterrupt:
        pass
    finally:
        fibonacci_action_server.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## rclpy and Python-Based Control

The `rclpy` package provides the Python client library for ROS 2, allowing Python developers to create ROS 2 nodes, publish and subscribe to topics, provide and use services, and work with actions.

### Key Features of rclpy

- **Asynchronous execution**: Supports both single-threaded and multi-threaded execution
- **Timer support**: Built-in timer functionality for periodic tasks
- **Parameter system**: Dynamic parameter configuration
- **Logging**: Integrated logging system
- **Lifecycle management**: Node lifecycle support

### Best Practices with rclpy

1. **Use context managers** when possible to ensure proper cleanup
2. **Handle exceptions gracefully** to prevent node crashes
3. **Use appropriate Quality of Service (QoS) settings** for your application
4. **Implement proper shutdown procedures** to clean up resources

## Connecting AI Agents to ROS Controllers

One of the most important applications in modern robotics is connecting AI agents to ROS controllers. This allows AI systems to interact with and control physical robots.

### Architecture Pattern

```
AI Agent (Python) → ROS 2 Bridge → Robot Hardware
```

### Example: AI Agent Controlling a Robot Arm

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from control_msgs.msg import JointTrajectoryControllerState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import numpy as np

class AIAgentController(Node):
    def __init__(self):
        super().__init__('ai_agent_controller')

        # Publishers for sending commands to the robot
        self.trajectory_publisher = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10)

        # Subscribers for receiving robot state
        self.joint_state_subscriber = self.create_subscription(
            JointState, '/joint_states', self.joint_state_callback, 10)

        # Timer for AI decision making
        self.ai_timer = self.create_timer(0.1, self.ai_decision_callback)

        self.current_joint_states = None

    def joint_state_callback(self, msg):
        self.current_joint_states = msg

    def ai_decision_callback(self):
        if self.current_joint_states is not None:
            # Simple AI logic to determine next action
            target_positions = self.calculate_next_action()
            self.send_trajectory_command(target_positions)

    def calculate_next_action(self):
        # AI algorithm would go here
        # This is a simplified example
        return [0.0, 0.5, -0.3, 0.2, 0.1, 0.0]  # Example joint positions

    def send_trajectory_command(self, positions):
        trajectory_msg = JointTrajectory()
        trajectory_msg.joint_names = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']

        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start.sec = 1  # Execute in 1 second
        trajectory_msg.points = [point]

        self.trajectory_publisher.publish(trajectory_msg)

def main(args=None):
    rclpy.init(args=args)
    ai_controller = AIAgentController()

    try:
        rclpy.spin(ai_controller)
    except KeyboardInterrupt:
        pass
    finally:
        ai_controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Quality of Service (QoS) in ROS 2

QoS policies allow you to configure how messages are delivered, which is crucial for real-time and safety-critical applications:

- **Reliability**: Best effort or reliable delivery
- **Durability**: Volatile or transient local
- **History**: Keep last N messages or keep all
- **Deadline**: Maximum time between messages
- **Liveliness**: How to detect if a publisher is alive

## Summary

ROS 2 communication patterns provide a robust foundation for building complex robotic systems. The combination of topics, services, and actions allows for flexible and reliable communication between different components. Understanding these patterns is essential for developing sophisticated robotic applications, especially when connecting AI agents to physical robot controllers.

## Next Steps

Continue to the next chapter to learn about [URDF for Humanoid Robots](./chapter3-urdf-humanoids.md).

## Previous Chapter

Review the [ROS 2 Fundamentals](./chapter1-ros2-fundamentals.md) if you need to refresh your understanding of the basics.