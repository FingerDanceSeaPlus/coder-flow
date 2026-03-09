#!/usr/bin/env python3
"""
Simple CLI tool for testing lead_agent structure and capabilities
"""

import argparse
import sys
from langchain_core.runnables import RunnableConfig
from src.agents.lead_agent.agent import make_lead_agent
from src.agents.thread_state import ThreadState
from src.agents.middlewares.middleware_manager import MiddlewareManager


def test_agent_creation():
    """Test that the lead_agent can be created"""
    print("=== Testing Agent Creation ===")
    try:
        config = RunnableConfig()
        agent = make_lead_agent(config)
        print("✓ lead_agent created successfully")
        print(f"  Agent type: {type(agent).__name__}")
        print()
        return agent
    except Exception as e:
        print(f"✗ Failed to create lead_agent: {e}")
        return None


def test_middleware_manager():
    """Test the middleware manager"""
    print("=== Testing Middleware Manager ===")
    try:
        config = RunnableConfig()
        manager = MiddlewareManager(config)
        middlewares = manager.build_middlewares()
        print(f"✓ Middleware manager created successfully")
        print(f"  Number of middlewares: {len(middlewares)}")
        for i, middleware in enumerate(middlewares):
            print(f"  Middleware {i+1}: {type(middleware).__name__}")
        print()
        return True
    except Exception as e:
        print(f"✗ Failed to test middleware manager: {e}")
        return False


def test_thread_state():
    """Test ThreadState functionality"""
    print("=== Testing ThreadState ===")
    try:
        # Test basic creation
        state = ThreadState(
            messages=[],
            todos=[],
            title="Test Thread"
        )
        print("✓ ThreadState created successfully")
        print(f"  Initial state: {state}")
        
        # Test with todos
        state_with_todos = ThreadState(
            messages=[],
            todos=[
                {"content": "Task 1", "status": "pending"},
                {"content": "Task 2", "status": "in_progress"}
            ],
            title="Test Thread with Todos"
        )
        print("✓ ThreadState with todos created successfully")
        print(f"  Todos: {state_with_todos['todos']}")
        print()
        return True
    except Exception as e:
        print(f"✗ Failed to test ThreadState: {e}")
        return False


def test_agent_structure(agent):
    """Test the agent structure"""
    print("=== Testing Agent Structure ===")
    try:
        if agent:
            print("✓ Agent structure verification")
            print(f"  Has invoke method: {hasattr(agent, 'invoke')}")
            print(f"  Has stream method: {hasattr(agent, 'stream')}")
            print()
            return True
        else:
            print("✗ Agent not available for structure testing")
            print()
            return False
    except Exception as e:
        print(f"✗ Failed to test agent structure: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test lead_agent structure and capabilities")
    parser.add_argument('--test', choices=['agent', 'middleware', 'thread', 'structure'], 
                      help="Test specific functionality")
    
    args = parser.parse_args()
    
    try:
        if args.test == 'agent':
            test_agent_creation()
        elif args.test == 'middleware':
            test_middleware_manager()
        elif args.test == 'thread':
            test_thread_state()
        elif args.test == 'structure':
            agent = test_agent_creation()
            test_agent_structure(agent)
        else:
            # Run all tests
            print("Running all tests...")
            print("=" * 50)
            
            agent = test_agent_creation()
            test_middleware_manager()
            test_thread_state()
            test_agent_structure(agent)
            
            print("=" * 50)
            print("All tests completed!")
            print()
            print("Note: Full functionality testing requires API keys and network access.")
            print("This test only verifies the structure and setup of the lead_agent.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
