"""
LLM Processor for handling model selection, error handling, and LLM calls
"""

import os
import json
import re
import traceback
from typing import Dict, List, Optional, Any
import openai


class LLMProcessor:
    """
    Handles LLM model selection, error handling, and fallback logic for video analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM processor
        
        Args:
            api_key: OpenAI API key (optional, uses environment variable if not provided)
        """
        # Use provided API key or fallback to environment variable
        if api_key:
            self.api_key = api_key
            print(f"🔑 LLMProcessor: Using provided API key")
        else:
            self.api_key = os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                raise ValueError(
                    "No OpenAI API key provided. Either:\n"
                    "1. Pass api_key parameter when creating LLMProcessor\n"
                    "2. Set OPENAI_API_KEY environment variable\n"
                    "3. Create a .env file with OPENAI_API_KEY=your_key_here"
                )
            print(f"🔑 LLMProcessor: Using API key from environment variable")
        
        # Load model configuration from environment variables with defaults
        self.default_model = os.getenv('DEFAULT_MODEL', 'o4-mini')
        self.max_completion_tokens = int(os.getenv('MAX_COMPLETION_TOKENS', '8192'))
        self.reasoning_effort = os.getenv('REASONING_EFFORT', 'high')
        
        # Model configuration with fallback strategy
        self.models_to_try = [
            {
                "name": "o4-mini", 
                "description": "o4-mini (best reasoning model for precise analysis)", 
                "reasoning_model": True,
                "effort": self.reasoning_effort
            },
            {
                "name": self.default_model if self.default_model != "o4-mini" else "gpt-4o", 
                "description": f"{self.default_model if self.default_model != 'o4-mini' else 'gpt-4o'} (fallback from config)", 
                "max_completion_tokens": self.max_completion_tokens,
                "reasoning_model": False
            },
            {
                "name": "gpt-4o", 
                "description": "GPT-4o (high quality, good context understanding)", 
                "max_completion_tokens": self.max_completion_tokens,
                "reasoning_model": False
            },
            {
                "name": "gpt-4o-mini", 
                "description": "GPT-4o Mini (fallback, faster, cost-effective)", 
                "max_completion_tokens": self.max_completion_tokens,
                "reasoning_model": False
            }
        ]
        
        # Remove duplicates while preserving order
        seen_models = set()
        unique_models = []
        for model in self.models_to_try:
            if model["name"] not in seen_models:
                seen_models.add(model["name"])
                unique_models.append(model)
        self.models_to_try = unique_models
        
        print(f"🤖 LLMProcessor: Configured {len(self.models_to_try)} models:")
        for i, model in enumerate(self.models_to_try):
            if model.get("reasoning_model", False):
                print(f"  {i+1}. {model['description']} (reasoning model)")
            else:
                print(f"  {i+1}. {model['description']} ({model['max_completion_tokens']} tokens)")
        
        # Initialize OpenAI client
        self._initialize_client()
        
        # Quality settings
        self.prefer_reasoning_models = os.getenv('PREFER_REASONING_MODELS', 'true').lower() == 'true'
        
        # Sort models to prioritize reasoning models if enabled
        if self.prefer_reasoning_models:
            self.models_to_try.sort(key=lambda x: (not x.get("reasoning_model", False), x["name"]))
            print(f"🧠 LLMProcessor: Prioritizing reasoning models")
    
    def _initialize_client(self):
        """Initialize OpenAI client with error handling"""
        try:
            print(f"🔑 LLMProcessor: Initializing OpenAI client...")
            self.openai_client = openai.OpenAI(api_key=self.api_key)
            print(f"✅ LLMProcessor: OpenAI client initialized successfully")
            
            # Test API key validity
            try:
                print(f"🔑 LLMProcessor: Testing API key validity...")
                models = self.openai_client.models.list()
                print(f"✅ LLMProcessor: API key is valid - found {len(models.data)} models")
            except Exception as test_e:
                print(f"⚠️ LLMProcessor: API key test failed: {str(test_e)}")
                
        except Exception as e:
            print(f"❌ LLMProcessor: Error initializing OpenAI client: {str(e)}")
            # Try alternative initialization
            try:
                if self.api_key:
                    os.environ['OPENAI_API_KEY'] = str(self.api_key)
                self.openai_client = openai.OpenAI()
                print(f"✅ LLMProcessor: OpenAI client initialized with environment variable")
            except Exception as e2:
                print(f"❌ LLMProcessor: Alternative initialization also failed: {str(e2)}")
                raise Exception(f"Failed to initialize OpenAI client: {str(e)}")
    
    def process(self, prompt: str, response_type: str = "json") -> str:
        """
        Process a prompt with LLM using fallback strategy
        
        Args:
            prompt: The prompt to send to the LLM
            response_type: Expected response type ("json" or "text")
            
        Returns:
            LLM response as string
        """
        print(f"🤖 LLMProcessor: Starting LLM processing with {len(self.models_to_try)} models")
        print(f"🤖 LLMProcessor: Prompt length: {len(prompt)} characters")
        
        last_error = None
        response_content = None
        
        for model_info in self.models_to_try:
            model_name = model_info["name"]
            
            try:
                print(f"🤖 LLMProcessor: Trying {model_name}...")
                
                response_content = self._call_model(model_info, prompt, response_type)
                
                if not response_content:
                    raise Exception("Empty response from LLM")
                
                print(f"✅ LLMProcessor: {model_name} response received successfully")
                print(f"🤖 LLMProcessor: Response length: {len(response_content)} characters")
                
                # Validate response format if JSON expected
                if response_type == "json":
                    self._validate_json_response(response_content)
                
                return response_content
                
            except Exception as model_error:
                print(f"❌ LLMProcessor: {model_name} failed: {str(model_error)}")
                last_error = model_error
                continue
        
        # All models failed
        if last_error:
            raise Exception(f"All LLM models failed. Last error: {str(last_error)}")
        else:
            raise Exception("All LLM models failed with unknown errors")
    
    def _call_model(self, model_info: Dict, prompt: str, response_type: str) -> str:
        """
        Call a specific LLM model
        
        Args:
            model_info: Model configuration
            prompt: The prompt to send
            response_type: Expected response type
            
        Returns:
            Model response as string
        """
        model_name = model_info["name"]
        is_reasoning_model = model_info.get("reasoning_model", False)
        
        if model_name == "o4-mini":
            # Special handling for o4-mini
            return self._call_o4_mini(model_info, prompt, response_type)
        elif is_reasoning_model:
            # Other reasoning models
            return self._call_reasoning_model(model_info, prompt, response_type)
        else:
            # Standard models
            return self._call_standard_model(model_info, prompt, response_type)
    
    def _call_o4_mini(self, model_info: Dict, prompt: str, response_type: str) -> str:
        """Call o4-mini with its specific API format"""
        model_effort = model_info.get("effort", "medium")
        
        print(f"📤 LLMProcessor: Sending prompt to o4-mini:")
        print(f"📤 LLMProcessor: Prompt length: {len(prompt)} chars")
        print(f"📤 LLMProcessor: Prompt preview (first 500 chars): {prompt[:500]}...")
        print(f"📤 LLMProcessor: Prompt preview (last 300 chars): {prompt[-300:]}")
        
        # o4-mini API call parameters
        create_params = {
            "model": "o4-mini",
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "reasoning": {
                "effort": model_effort,
                "summary": None 
            },
            "store": False
        }
          # Add text format if needed
        if response_type == "json":
            create_params["text"] = {
                "format": {
                    "type": "json_object"
                }
            }
        
        response = self.openai_client.responses.create(**create_params)
        
        # Extract response content from o4-mini format - need to get text from output message
        print(f"📥 LLMProcessor: Raw o4-mini response received:")
        print(f"📥 LLMProcessor: Response type: {type(response)}")
          # Extract the actual text content from the response
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'content') and item.content:
                    for content_item in item.content:
                        if hasattr(content_item, 'text'):
                            response_content = content_item.text
                            break
                    break
        else:
            # Fallback to string conversion
            response_content = str(response)
        
        print(f"📥 LLMProcessor: Extracted response content length: {len(response_content)} chars")
        print(f"📥 LLMProcessor: ACTUAL CONTENT:")
        print("=" * 80)
        print(response_content)
        print("=" * 80)
        
        # Enhanced JSON extraction for o4-mini responses
        if response_type == "json":
            # Method 1: Find the largest JSON object in the response
            json_objects = []
            brace_count = 0
            start_pos = -1
            
            for i, char in enumerate(response_content):
                if char == '{':
                    if brace_count == 0:
                        start_pos = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_pos != -1:
                        # Found complete JSON object
                        json_candidate = response_content[start_pos:i+1]
                        json_objects.append(json_candidate)
                        print(f"🔍 LLMProcessor: Found JSON candidate ({len(json_candidate)} chars): {json_candidate[:100]}...")
                        start_pos = -1
            
            print(f"🔍 LLMProcessor: Found {len(json_objects)} JSON candidates")            # Try to parse each JSON object and pick the largest valid one
            best_json = None
            for idx, json_candidate in enumerate(json_objects):
                try:
                    # Try to fix common JSON escape issues before parsing
                    cleaned_candidate = self._fix_json_escape_issues(json_candidate)
                    parsed = json.loads(cleaned_candidate)
                    if isinstance(parsed, dict):
                        print(f"✅ LLMProcessor: JSON candidate {idx} is valid ({len(json_candidate)} chars)")
                        print(f"🔍 LLMProcessor: JSON keys: {list(parsed.keys())}")
                        if len(json_candidate) > (len(best_json) if best_json else 0):
                            best_json = cleaned_candidate  # Use the cleaned version
                            print(f"🎯 LLMProcessor: JSON candidate {idx} is now the best one")
                    else:
                        print(f"⚠️ LLMProcessor: JSON candidate {idx} is not a dict: {type(parsed)}")
                except json.JSONDecodeError as e:
                    print(f"❌ LLMProcessor: JSON candidate {idx} is invalid: {e}")
                    # Try with additional escape fixing
                    try:
                        ultra_cleaned = self._aggressive_json_cleanup(json_candidate)
                        parsed = json.loads(ultra_cleaned)
                        if isinstance(parsed, dict) and len(json_candidate) > (len(best_json) if best_json else 0):
                            best_json = ultra_cleaned
                            print(f"🔧 LLMProcessor: JSON candidate {idx} fixed with aggressive cleanup and is now the best one")
                    except:
                        print(f"❌ LLMProcessor: JSON candidate {idx} unfixable")
                    continue
            
            if best_json:
                response_content = best_json
                print(f"🎯 LLMProcessor: Using best JSON ({len(response_content)} chars) from o4-mini response")
            else:
                print(f"❌ LLMProcessor: No valid JSON found in o4-mini response")
                # Method 2: Fallback regex for nested JSON
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    response_content = json_match.group(0)
                    print(f"🎯 LLMProcessor: Extracted JSON using regex fallback ({len(response_content)} chars)")
                else:
                    print(f"❌ LLMProcessor: Could not extract JSON from o4-mini response")
                    print(f"❌ LLMProcessor: Response content: {response_content[:500]}...")
        
        return response_content
    
    def _call_reasoning_model(self, model_info: Dict, prompt: str, response_type: str) -> str:
        """Call reasoning models (o1-preview, o1-mini)"""
        model_name = model_info["name"]
        
        request_params = {
            "model": model_name,
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        }
        
        response = self.openai_client.chat.completions.create(**request_params)
        return response.choices[0].message.content
    
    def _call_standard_model(self, model_info: Dict, prompt: str, response_type: str) -> str:
        """Call standard models (gpt-4o, gpt-4o-mini)"""
        model_name = model_info["name"]
        max_tokens = model_info.get("max_completion_tokens", 8192)
        
        request_params = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "temperature": 0.3,
            "max_completion_tokens": max_tokens,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
        
        if response_type == "json":
            request_params["response_format"] = {"type": "json_object"}
          # Generate debug curl for debugging
        try:
            self._generate_debug_curl(request_params, model_name)
        except Exception as debug_e:
            print(f"⚠️ LLMProcessor: Debug curl generation failed: {debug_e}")
        
        response = self.openai_client.chat.completions.create(**request_params)
        return response.choices[0].message.content
    
    def _validate_json_response(self, response_content: str):
        """Validate that response is valid JSON"""
        response_text = response_content.strip()
        
        print(f"🔍 LLMProcessor: Validating JSON response, length: {len(response_text)} chars")
        print(f"🔍 LLMProcessor: Response preview: {response_text[:200]}...")
        
        # Clean up markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        # Check if response might be truncated
        if not (response_text.strip().endswith(']') or response_text.strip().endswith('}')):
            print(f"⚠️ LLMProcessor: Response appears truncated, attempting fix...")
            response_text = self._fix_truncated_json(response_text)
        
        # Try to parse JSON
        try:
            parsed_json = json.loads(response_text)
            print(f"✅ LLMProcessor: JSON validation successful")
            if isinstance(parsed_json, dict):
                print(f"🔍 LLMProcessor: JSON keys: {list(parsed_json.keys())}")
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"❌ LLMProcessor: JSON decode error: {e}")
            print(f"❌ LLMProcessor: Problematic content: {response_text[:300]}...")
            # Try to fix JSON and validate again
            try:
                fixed_response = self._fix_truncated_json(response_text)
                parsed_json = json.loads(fixed_response)
                print(f"✅ LLMProcessor: JSON validation successful after fix")
                return parsed_json
            except json.JSONDecodeError as e2:
                print(f"❌ LLMProcessor: JSON still invalid after fix: {e2}")
                raise e2
                print(f"❌ LLMProcessor: JSON still invalid after fix: {e2}")
                raise e2
    
    def _fix_truncated_json(self, json_str: str) -> str:
        """Attempt to fix truncated JSON responses"""
        json_str = json_str.strip()
        
        # Count braces and brackets to determine what's missing
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        # Add missing closing characters
        missing_brackets = open_brackets - close_brackets
        missing_braces = open_braces - close_braces
        
        fixed_json = json_str
        fixed_json += ']' * missing_brackets
        fixed_json += '}' * missing_braces
        
        return fixed_json
    
    def _generate_debug_curl(self, request_params: Dict, model_name: str):
        """Generate debug curl command for debugging purposes"""
        try:
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # Create debug directory if it doesn't exist
            debug_dir = os.path.join(os.getcwd(), "debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            # Generate curl command
            curl_cmd = f"""curl -X POST "https://api.openai.com/v1/chat/completions" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer $OPENAI_API_KEY" \\
  -d '{json.dumps(request_params, indent=2)}'"""
            
            # Save to debug file
            debug_file = os.path.join(debug_dir, f"debug_curl_{model_name}_{timestamp}.txt")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"Debug curl for model: {model_name}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Parameters: {json.dumps(request_params, indent=2)}\n\n")
                f.write(f"Curl command:\n{curl_cmd}\n")
            
            print(f"🐛 LLMProcessor: Debug curl saved to {debug_file}")
            
        except Exception as e:
            print(f"⚠️ LLMProcessor: Failed to generate debug curl: {e}")
    
    def _fix_json_escape_issues(self, json_str: str) -> str:
        """Fix common JSON escape issues"""
        # Fix common escape problems
        json_str = json_str.replace('\\n', '\\\\n')  # Fix newlines
        json_str = json_str.replace('\\t', '\\\\t')  # Fix tabs
        json_str = json_str.replace('\\r', '\\\\r')  # Fix carriage returns
        json_str = json_str.replace('\\"', '\\\\"')  # Fix quotes
        
        # Fix invalid escape sequences
        json_str = re.sub(r'\\([^"\\\/bfnrt])', r'\\\\\\1', json_str)
        
        return json_str
    
    def _aggressive_json_cleanup(self, json_str: str) -> str:
        """Aggressive JSON cleanup as last resort"""
        # Remove all problematic escape sequences
        json_str = re.sub(r'\\[^"\\\/bfnrtu]', '', json_str)
        
        # Fix unescaped quotes in strings
        in_string = False
        result = []
        i = 0
        while i < len(json_str):
            char = json_str[i]
            if char == '"' and (i == 0 or json_str[i-1] != '\\'):
                in_string = not in_string
                result.append(char)
            elif char == '"' and in_string and json_str[i-1] != '\\':
                result.append('\\"')
            else:
                result.append(char)
            i += 1
        
        return ''.join(result)
