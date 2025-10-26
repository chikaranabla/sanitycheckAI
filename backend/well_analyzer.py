"""
Well Analyzer - Dual AI Analysis (Random Forest + Gemini Vision)
"""

import os
import tempfile
import numpy as np
import google.generativeai as genai
from PIL import Image
from typing import Dict
from pathlib import Path

from backend.contamination_model import ContaminationDetector


class WellAnalyzer:
    """Analyze well images using dual AI approach"""
    
    def __init__(self):
        """Initialize analyzer"""
        # Initialize Random Forest detector
        self.rf_detector = ContaminationDetector()
        
        # Try to load existing model, will train on first use if not found
        if not self.rf_detector.load_model():
            print("WARNING: RF model not loaded. Will need to train first.")
        
        # Initialize Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    
    def analyze_well(self, image: np.ndarray, image_path: str = None) -> Dict:
        """
        Perform dual AI analysis on well image
        
        Args:
            image: Well image as numpy array
            image_path: Optional path to image file (for Gemini)
            
        Returns:
            Dictionary with both RF and LLM predictions
        """
        # 1. Random Forest Analysis
        rf_result = self._analyze_with_rf(image)
        
        # 2. Gemini Vision Analysis
        llm_result = self._analyze_with_gemini(image, image_path)
        
        return {
            'rf_prediction': rf_result,
            'llm_prediction': llm_result
        }
    
    def _analyze_with_rf(self, image: np.ndarray) -> Dict:
        """Analyze image with Random Forest"""
        try:
            result = self.rf_detector.predict(image)
            return result
        except Exception as e:
            print(f"RF analysis error: {e}")
            return {
                'label': 'error',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _analyze_with_gemini(self, image: np.ndarray, image_path: str = None) -> Dict:
        """Analyze image with Gemini Vision API"""
        import time
        from google.api_core import exceptions as google_exceptions
        
        try:
            # Save image to temporary file if not provided
            if image_path is None or not os.path.exists(image_path):
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    # Convert to uint8 and ensure RGB format
                    img_uint8 = (image * 255).astype(np.uint8)
                    img_pil = Image.fromarray(img_uint8)
                    
                    # Convert to RGB if grayscale
                    if img_pil.mode != 'RGB':
                        img_pil = img_pil.convert('RGB')
                    
                    # Save as JPEG (better compatibility)
                    img_pil.save(tmp.name, format='JPEG', quality=95)
                    image_path = tmp.name
                    temp_file_created = True
            else:
                temp_file_created = False
            
            # Upload image to Gemini with retry logic
            max_retries = 3
            retry_delay = 2
            uploaded_file = None
            
            for attempt in range(max_retries):
                try:
                    uploaded_file = genai.upload_file(image_path)
                    break
                except google_exceptions.ResourceExhausted as e:
                    if attempt < max_retries - 1:
                        print(f"Rate limit hit, waiting {retry_delay}s before retry...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise
            
            if uploaded_file is None:
                raise ValueError("Failed to upload file after retries")
            
            # Wait for file to be processed
            max_wait = 30
            wait_time = 0
            while uploaded_file.state.name == "PROCESSING" and wait_time < max_wait:
                time.sleep(1)
                wait_time += 1
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise ValueError(f"File upload failed: {uploaded_file.state.name}")
            
            if uploaded_file.state.name == "PROCESSING":
                raise ValueError(f"File processing timeout after {max_wait}s")
            
            # Create prompt - simple text prompt
            prompt = """Analyze this bacterial culture well image from a microscope.

Determine if the culture is:
- CLEAN: Pure, healthy bacterial culture with uniform morphology
- CONTAMINATED: Mixed species, abnormal morphology, or contamination visible

Respond in this format:
Judgment: [clean or contaminated]
Reasoning: [1-2 sentences explaining why]"""
            
            # Get response with retry logic
            response = None
            for attempt in range(max_retries):
                try:
                    # Use the uploaded file directly in generate_content
                    response = self.gemini_model.generate_content(
                        [prompt, uploaded_file],
                        request_options={"timeout": 60}
                    )
                    break
                except google_exceptions.ResourceExhausted as e:
                    if attempt < max_retries - 1:
                        # Extract retry delay from error message
                        import re
                        match = re.search(r'retry in (\d+(?:\.\d+)?)', str(e))
                        if match:
                            delay = float(match.group(1)) + 1
                        else:
                            delay = retry_delay
                        print(f"Rate limit hit, waiting {delay}s before retry...")
                        time.sleep(delay)
                    else:
                        raise
                except google_exceptions.InvalidArgument as e:
                    print(f"Invalid argument error: {e}")
                    # Try with just the file, no prompt in array
                    try:
                        response = self.gemini_model.generate_content(
                            prompt + "\n\n[Image uploaded]",
                            request_options={"timeout": 60}
                        )
                        break
                    except:
                        raise
            
            if response is None:
                raise ValueError("Failed to get response after retries")
            
            response_text = response.text.strip()
            
            # Parse response
            label, reasoning = self._parse_gemini_response(response_text)
            
            # Cleanup
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass  # Ignore cleanup errors
            
            if temp_file_created and os.path.exists(image_path):
                try:
                    os.unlink(image_path)
                except:
                    pass  # Ignore cleanup errors
            
            return {
                'label': label,
                'reasoning': reasoning,
                'raw_response': response_text
            }
            
        except google_exceptions.ResourceExhausted as e:
            print(f"Gemini analysis error (rate limit): {e}")
            return {
                'label': 'error',
                'reasoning': 'Rate limit exceeded. Please wait and try again.',
                'error': 'rate_limit'
            }
        except Exception as e:
            print(f"Gemini analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'label': 'error',
                'reasoning': f'Analysis failed: {str(e)}',
                'error': str(e)
            }
    
    def _parse_gemini_response(self, response_text: str) -> tuple:
        """
        Parse Gemini response to extract label and reasoning
        
        Returns:
            Tuple of (label, reasoning)
        """
        response_lower = response_text.lower()
        
        # Determine label
        if 'contaminat' in response_lower:
            label = 'contaminated'
        elif 'clean' in response_lower or 'pure' in response_lower or 'healthy' in response_lower:
            label = 'clean'
        else:
            label = 'uncertain'
        
        # Extract reasoning (use full response for now)
        reasoning = response_text[:200]  # Limit length
        
        return label, reasoning
    
    def train_rf_model(self, clean_dir: str = "1_Clean_Samples",
                      contaminated_dir: str = "2_Contaminated_Samples") -> Dict:
        """
        Train the Random Forest model
        
        Args:
            clean_dir: Directory with clean images
            contaminated_dir: Directory with contaminated images
            
        Returns:
            Training results
        """
        return self.rf_detector.train(clean_dir, contaminated_dir)

