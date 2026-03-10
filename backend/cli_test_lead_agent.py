#!/usr/bin/env python3
"""
CLI tool for testing lead_agent capabilities
"""

import argparse
import sys
from langchain_core.runnables import RunnableConfig
from src.agents.lead_agent.agent import make_lead_agent
from src.agents.thread_state import ThreadState

def get_message_content(message):
    """Extract content from message object (handles both dict and AIMessage)"""
    if hasattr(message, 'content'):
        return message.content
    elif isinstance(message, dict):
        return message.get("content", "")
    return str(message)

def create_agent():
    """Create a lead_agent instance"""
    config = RunnableConfig()
    return make_lead_agent(config)


def test_basic_interaction(agent):
    """Test basic agent interaction"""
    print("=== Testing Basic Interaction ===")
    
    # Initial state
    state = ThreadState(
        messages=[],
        todos=[],
        title="Test Thread"
    )
    
    # Test message
    test_message = "Hello, what can you do?"
    print(f"User: {test_message}")
    
    # Invoke agent
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": test_message
        }],
        **state
    })
    
    # Print response
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        # Handle both dict and AIMessage objects
        last_message_content = get_message_content(last_message)
        print("Agent:", last_message_content)
    print()


def test_todo_list(agent):
    """Test todo list functionality"""
    print("=== Testing Todo List Functionality ===")
    
    # Initial state with todos
    state = ThreadState(
        messages=[],
        todos=[
            {"content": "Task 1: Test todo list", "status": "pending"},
            {"content": "Task 2: Complete testing", "status": "pending"}
        ],
        title="Test Thread with Todos"
    )
    
    # Test message asking to manage todos
    test_message = "Please help me manage my todo list. Mark the first task as in progress."
    print(f"User: {test_message}")
    
    # Invoke agent
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": test_message
        }],
        **state
    })
    
    # Print response and updated todos
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        last_message_content = get_message_content(last_message)
        print("Agent:", last_message_content)
    print("Updated Todos:", result.get("todos", []))
    print()


def test_summary(agent):
    """Test summary functionality"""
    print("=== Testing Summary Functionality ===")
    
    # Initial state with multiple messages
    state = ThreadState(
        messages=[
            {"role": "user", "content": "Hello, I need help with a project."},
            {"role": "assistant", "content": "Sure, what do you need help with?"},
            {"role": "user", "content": "I need to create a website for my business."},
            {"role": "assistant", "content": "Great, I can help you with that. What kind of business do you have?"},
            {"role": "user", "content": "I run a coffee shop."},
            {"role": "assistant", "content": "Perfect! A coffee shop website would be great. Let's plan it out."},
        ],
        todos=[],
        title="Test Thread for Summary"
    )
    
    # Test message asking for summary
    test_message = "Can you summarize our conversation so far?"
    print(f"User: {test_message}")
    
    # Invoke agent
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": test_message
        }],
        **state
    })
    
    # Print response
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        last_message_content = get_message_content(last_message)
        print("Agent:", last_message_content)
    print()


def test_clarification(agent):
    """Test clarification tool"""
    print("=== Testing Clarification Tool ===")
    
    # Initial state
    state = ThreadState(
        messages=[],
        todos=[],
        title="Test Thread for Clarification"
    )
    
    # Test message that requires clarification
    test_message = "I need help with something."
    print(f"User: {test_message}")
    
    # Invoke agent
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": test_message
        }],
        **state
    })
    
    # Print response
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        last_message_content = get_message_content(last_message)
        print("Agent:", last_message_content)
    print()
#TODO: 完善交互模式
def interactive_mode(agent):
    """Interactive mode for testing"""
    print("=== Interactive Mode ===")
    print("Type 'exit' to quit, 'clear' to clear messages, 'todos' to show todos")
    print()
    
    # Initial state
    state = ThreadState(
        messages=[],
        todos=[],
        title="Interactive Test Thread"
    )
    
    while True:
        try:
            user_input = input("User: ")
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'clear':
                state["messages"] = []
                print("Messages cleared")
                continue
            elif user_input.lower() == 'todos':
                print("Current todos:", state.get("todos", []))
                continue
            
            # 累积消息历史
            state["messages"].append({
                "role": "user",
                "content": user_input
            })
            
            # 传递完整的消息历史
            result = agent.invoke({
                "messages": state["messages"],
                **state
            })
            
            # Update state
            state = result
            
            # Print response
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                last_message_content = get_message_content(last_message)
                # 检查是否是澄清消息
                if hasattr(last_message, 'name') and last_message.name == "ask_clarification":
                    # 这是一个澄清请求，显示问题
                    print("Agent (Clarification):", last_message_content)
                    # 等待用户回答
                    clarification_response = input("Answer: ")
                    # 将回答添加到消息历史
                    state["messages"].append({
                        "role": "user",
                        "content": clarification_response
                    })
                    # 继续执行agent
                    result = agent.invoke({
                        "messages": state["messages"],
                        **state
                    })
                    # 更新状态
                    state = result
                    # 显示agent的回复
                    if result.get("messages"):
                        final_message = result["messages"][-1]
                        final_content = get_message_content(final_message)
                        print("Agent:", final_content)
                else:
                    # 普通回复
                    print("Agent:", last_message_content)
            
            # Show updated todos if any
            if result.get("todos"):
                print("Todos:", result.get("todos"))
            
            print()
            
        except KeyboardInterrupt:
            break



def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test lead_agent capabilities")
    parser.add_argument('--test', choices=['basic', 'todo', 'summary', 'clarification', 'interactive'], 
                      help="Test specific functionality")
    
    args = parser.parse_args()
    
    try:
        print("Creating lead_agent...")
        agent = create_agent()
        print("lead_agent created successfully!")
        print()
        
        if args.test == 'basic':
            test_basic_interaction(agent)
        elif args.test == 'todo':
            test_todo_list(agent)
        elif args.test == 'summary':
            test_summary(agent)
        elif args.test == 'clarification':
            test_clarification(agent)
        elif args.test == 'interactive':
            interactive_mode(agent)
        else:
            # Run all tests
            test_basic_interaction(agent)
            test_todo_list(agent)
            test_summary(agent)
            test_clarification(agent)
            print("=== All tests completed! ===")
            print("Run with --test interactive for interactive mode")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
