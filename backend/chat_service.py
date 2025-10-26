"""
Chat Service for AI-guided setup verification
"""

import os
import json
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
import google.generativeai as genai

from .prompts import CHAT_SYSTEM_INSTRUCTION
from .mcp_client import get_mcp_client
from .gemini_service import GeminiService


class ChatSession:
    """Represents a single chat session with a user"""
    
    def __init__(self, session_id: str, protocol_content: str, protocol_path: str):
        self.session_id = session_id
        self.protocol_content = protocol_content
        self.protocol_path = protocol_path
        self.messages: List[Dict[str, Any]] = []
        self.captured_images: List[str] = []
        self.checkpoints: Optional[List[Dict[str, Any]]] = None
        self.verification_results: Optional[Dict[str, Any]] = None
        self.protocol_executed = False
        
        # Initialize Gemini chat
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",
            system_instruction=CHAT_SYSTEM_INSTRUCTION
        )
        self.chat = self.model.start_chat(history=[])
        
        # Initialize services
        self.mcp_client = get_mcp_client()
        self.gemini_service = GeminiService()


class ChatService:
    """Service for managing chat sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
    
    def create_session(self, protocol_content: str, protocol_path: str) -> str:
        """
        Create a new chat session
        
        Args:
            protocol_content: Content of the protocol file
            protocol_path: Path to the protocol file
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        session = ChatSession(session_id, protocol_content, protocol_path)
        self.sessions[session_id] = session
        
        # Generate initial checkpoints from protocol
        try:
            checkpoints_data = session.gemini_service.generate_checkpoints(protocol_content)
            session.checkpoints = checkpoints_data.get("checkpoints", [])
        except Exception as e:
            print(f"Warning: Failed to generate initial checkpoints: {e}")
            session.checkpoints = []
        
        # Send initial message to AI
        initial_prompt = f"""A user has uploaded their Opentrons protocol file. Here is the protocol content:

```python
{protocol_content}
```

Please analyze this protocol and guide the user to set up their experiment. Start by greeting them and explaining what they need to set up."""
        
        try:
            response = session.chat.send_message(initial_prompt)
            ai_message = response.text
            
            # Store the exchange
            session.messages.append({
                "role": "user",
                "content": initial_prompt,
                "timestamp": self._get_timestamp()
            })
            session.messages.append({
                "role": "assistant",
                "content": ai_message,
                "timestamp": self._get_timestamp()
            })
            
        except Exception as e:
            print(f"Error getting initial AI response: {e}")
            ai_message = "Hello! I'm ready to help you verify your Opentrons setup. Please let me know when you have completed the physical setup of your experiment."
            session.messages.append({
                "role": "assistant",
                "content": ai_message,
                "timestamp": self._get_timestamp()
            })
        
        return session_id
    
    async def send_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Send a message and get AI response
        
        Args:
            session_id: Session ID
            user_message: User's message
            
        Returns:
            Response containing AI message and any actions taken
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"ChatService.send_message called - session_id: {session_id}, message: {user_message[:50]}...")
        
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        logger.info(f"Session found. Message count: {len(session.messages)}")
        
        # Store user message
        session.messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": self._get_timestamp()
        })
        
        # Analyze user message to determine if we need to take action
        action_taken = None
        image_url = None
        checkpoints_result = None
        
        # Check if user indicates setup is complete
        setup_keywords = ["完了", "完成", "done", "ready", "finished", "set up", "setup"]
        user_message_lower = user_message.lower()
        
        logger.info(f"Checking for setup keywords in: '{user_message_lower}'")
        
        if any(keyword in user_message_lower for keyword in setup_keywords):
            logger.info("Setup completion detected! Starting verification process...")
            # User indicates setup is complete - take photo and verify
            try:
                # 1. Take photo
                print("Taking photo...")
                image_path = await session.mcp_client.take_photo()
                session.captured_images.append(image_path)
                action_taken = "photo_taken"
                image_url = f"/api/chat/image/{session_id}/{len(session.captured_images) - 1}"
                
                # 2. Verify setup
                print("Verifying setup...")
                validation_result = session.gemini_service.full_validation(
                    protocol_content=session.protocol_content,
                    image_path=image_path
                )
                
                session.verification_results = validation_result
                checkpoints_result = validation_result
                
                # 3. Build context for AI
                verification_summary = f"""I have taken a photo and verified the setup. Here are the results:

Overall Result: {validation_result['overall_result'].upper()}

Checkpoints:
"""
                for cp in validation_result.get('checkpoints', []):
                    status = "✅ PASS" if cp['result'] == 'pass' else "❌ FAIL"
                    verification_summary += f"\n{status} - {cp['description']}"
                    if cp.get('details'):
                        verification_summary += f"\n  Details: {cp['details']}"
                
                # 4. Determine next action
                if validation_result['overall_result'] == 'pass':
                    # Verification passed - execute protocol
                    if not session.protocol_executed:
                        try:
                            print("Executing protocol...")
                            execution_result = await session.mcp_client.upload_and_run_protocol(
                                protocol_path=session.protocol_path,
                                start=True,
                                wait=False
                            )
                            session.protocol_executed = True
                            verification_summary += f"\n\n✅ Protocol execution started successfully!"
                            verification_summary += f"\nRun ID: {execution_result.get('run_id', 'N/A')}"
                            action_taken = "protocol_executed"
                        except Exception as e:
                            verification_summary += f"\n\n❌ Failed to execute protocol: {str(e)}"
                else:
                    verification_summary += "\n\n⚠️ Please correct the issues and let me know when ready."
                
                # Send verification summary to AI for natural response
                ai_prompt = f"{user_message}\n\n[SYSTEM: {verification_summary}]"
                
            except Exception as e:
                logger.error(f"Error during photo/verification: {str(e)}", exc_info=True)
                print(f"Error during photo/verification: {e}")
                ai_prompt = f"{user_message}\n\n[SYSTEM ERROR: Failed to take photo or verify setup: {str(e)}]"
        else:
            logger.info("No setup keywords detected, passing message to AI")
            ai_prompt = user_message
        
        # Get AI response
        try:
            logger.info("Sending message to AI...")
            response = session.chat.send_message(ai_prompt)
            ai_message = response.text
            logger.info(f"AI response received: {ai_message[:100]}...")
        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}", exc_info=True)
            print(f"Error getting AI response: {e}")
            ai_message = "I apologize, but I encountered an error processing your message. Please try again."
        
        # Store AI message
        session.messages.append({
            "role": "assistant",
            "content": ai_message,
            "timestamp": self._get_timestamp(),
            "image_url": image_url,
            "checkpoints": checkpoints_result,
            "action": action_taken
        })
        
        response_data = {
            "session_id": session_id,
            "message": ai_message,
            "image_url": image_url,
            "checkpoints": checkpoints_result,
            "action": action_taken,
            "protocol_executed": session.protocol_executed
        }
        
        logger.info(f"Returning response - action: {action_taken}, protocol_executed: {session.protocol_executed}")
        
        return response_data
    
    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get chat history for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of messages
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        return self.sessions[session_id].messages
    
    def get_image(self, session_id: str, image_index: int) -> str:
        """
        Get captured image path
        
        Args:
            session_id: Session ID
            image_index: Index of the image
            
        Returns:
            Image file path
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        if image_index < 0 or image_index >= len(session.captured_images):
            raise ValueError(f"Image index {image_index} out of range")
        
        return session.captured_images[image_index]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Global singleton
_chat_service = None


def get_chat_service() -> ChatService:
    """Get or create chat service singleton"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service

