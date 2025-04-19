"""
Gradio Web Interface for Boston School Chatbot

This script creates a web interface for your chatbot using Gradio.
You only need to implement the chat function.

Key Features:
- Creates a web UI for your chatbot
- Handles conversation history
- Provides example questions
- Can be deployed to Hugging Face Spaces

Example Usage:
    # Run locally:
    python app.py
    
    # Access in browser:
    # http://localhost:7860
"""

import gradio as gr
from src.chat import SchoolChatbot
import json

def create_chatbot():
    """
    Creates and configures the chatbot interface.
    """
    chatbot = SchoolChatbot()
    
    def chat(message, history, conversation_state):
        """
        Generate a response for the current message, using conversation history and state.
        
        This function is called by Gradio's ChatInterface every time a user sends a message.
        It maintains conversation state between messages.

        Args:
            message (str): The current message from the user
            history (list): List of previous message pairs, where each pair is
                           [user_message, assistant_message]
            conversation_state (str): JSON string of current conversation state

        Returns:
            tuple: (response, updated_conversation_state)
        """
        try:
            # Load the conversation state if it exists
            if conversation_state:
                try:
                    state_dict = json.loads(conversation_state)
                    chatbot.conversation_state = state_dict
                except:
                    # If there's an error parsing, just use a fresh state
                    chatbot.reset_state()
            
            # Get response from chatbot, passing in the conversation history
            response = chatbot.get_response(message, history)
            
            # Save the updated conversation state
            updated_state = json.dumps(chatbot.conversation_state)
            
            return response, updated_state
        except Exception as e:
            return f"I apologize, but I encountered an error. Please try again. Error: {str(e)}", conversation_state

    # Create blocks for more flexible interface
    with gr.Blocks(title="Boston Public School Selection Assistant") as demo:
        gr.Markdown("# Boston Public School Selection Assistant")
        gr.Markdown("Ask me anything about Boston public schools! I can help you find eligible schools based on your address, child's grade, and language preference.")
        
        # State to preserve conversation context
        conversation_state = gr.State("{}")
        
        # Standard chat interface
        chatbot_interface = gr.ChatInterface(
            fn=chat,
            additional_inputs=[conversation_state],
            additional_outputs=[conversation_state],
            examples=[
                "I live in Jamaica Plain and want to send my child to kindergarten. What schools are available?",
                "Does any school offer a Spanish immersion program?",
                "How do I register my child for BPS?",
                "What documents do I need to apply?",
                "I'm looking for schools for my child who will be in 3rd grade. We live near 123 Commonwealth Ave, Boston, MA 02115.",
                "What phone number or email can I contact to obtain more information?"
            ],
            title="",
        )
        
        # Reset button
        with gr.Row():
            reset_btn = gr.Button("Reset Conversation")
            
            def reset_conversation():
                chatbot.reset_state()
                return json.dumps(chatbot.conversation_state)
            
            reset_btn.click(reset_conversation, outputs=[conversation_state])
        
        # Footer with additional information
        gr.Markdown("""
        ## How to use this assistant:
        
        This chatbot can help you with:
        - Finding eligible schools based on your address, child's grade, and language preference
        - Understanding the school registration process
        - Getting information about required documents 
        - Learning about Welcome Centers and contact information
        
        If you want to find schools, I'll ask for:
        1. Your Boston address or zip code
        2. Your child's grade level
        3. Your language preference
        
        You can also start a new search at any time by clicking the Reset button or typing "start over".
        """)
    
    return demo

if __name__ == "__main__":
    demo = create_chatbot()
    demo.launch()