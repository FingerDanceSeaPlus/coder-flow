#!/usr/bin/env python3
"""
Command-line chat program with memory and streaming output using DeerFlowClient.

Usage:
    python chat.py

Features:
    - Real-time streaming output
    - Conversation memory (persistent context)
    - Command support: exit, clear, help
    - Thread isolation for multiple conversations
"""

import argparse
import sys
from langgraph.checkpoint.memory import MemorySaver
from src.client import DeerFlowClient
from dotenv import load_dotenv
import os
def create_client():
    """Create a DeerFlowClient with memory capability."""
    # Create a memory saver for conversation persistence
    load_dotenv()
    checkpointer = MemorySaver()
    
    # Initialize client with memory
    client = DeerFlowClient(
        checkpointer=checkpointer,
        thinking_enabled=True,
        plan_mode=True
    )
    return client

def print_help():
    """Print help information."""
    print("=== Help ===")
    print("Commands:")
    print("  exit       - Exit the chat")
    print("  clear      - Clear the current conversation")
    print("  help       - Show this help message")
    print("  thread     - Show current thread ID")
    print("  new thread - Start a new conversation thread")
    print()

def main():
    load_dotenv()
    """Main chat function."""
    parser = argparse.ArgumentParser(description="Command-line chat with DeerFlowClient")
    parser.add_argument('--thread-id', type=str, help="Thread ID for conversation context")
    args = parser.parse_args()
    
    print("=== DeerFlow Chat ===")
    print("Type 'help' for commands, 'exit' to quit")
    print()
    
    # Create client with memory
    client = create_client()
    
    # Use provided thread ID or generate a new one
    thread_id = args.thread_id or "default-chat-thread"
    print(f"Current thread: {thread_id}")
    print()
    
    while True:
        try:
            user_input = input("You: ")
            
            if not user_input.strip():
                continue
            
            # Handle commands
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            elif user_input.lower() == 'clear':
                # Clear conversation by creating a new thread
                thread_id = f"new-thread-{hash(user_input)}"
                print(f"Starting new conversation thread: {thread_id}")
                print()
                continue
            elif user_input.lower() == 'help':
                print_help()
                continue
            elif user_input.lower() == 'thread':
                print(f"Current thread ID: {thread_id}")
                print()
                continue
            elif user_input.lower() == 'new thread':
                import uuid
                thread_id = str(uuid.uuid4())
                print(f"Starting new conversation thread: {thread_id}")
                print()
                continue
            
            # Process chat with streaming
            print("Assistant: ", end="", flush=True)
            # 用于跟踪已处理的消息
            processed_messages = set()
            # Stream response
            for event in client.stream(user_input, thread_id=thread_id):
                if event.type == "messages-tuple" and event.data.get("type") == "ai":
                    content = event.data.get("content", "")
                    msg_id = event.data.get("id")
                    
                    # 确保只处理新消息
                    if msg_id not in processed_messages:
                        processed_messages.add(msg_id)
                        if content:
                            # 逐字打印，模拟真实的打字效果
                            for char in content:
                                print(char, end="", flush=True)
                                # 可选：添加微小延迟，增强打字效果
                                # import time
                                # time.sleep(0.01)
                elif event.type == "messages-tuple" and event.data.get("type") == "tool":
                    # Show tool messages if needed
                    content = event.data.get("content", "")
                    if content:
                        print(f"[Tool] {content}", end="", flush=True)
            
            print()
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            print()

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    print(api_key)
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
    sys.exit(main())
