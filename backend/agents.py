"""
Mock implementation of the agents module for testing purposes.
This is a simplified version that allows the server to start without the full agent functionality.
"""

class Agent:
    """Mock Agent class."""
    
    def __init__(self, name="MockAgent", instructions="", model="gpt-4", temperature=0.0, response_format=None):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.temperature = temperature
        self.response_format = response_format
        print(f"Mock Agent '{name}' initialized")
    
    def run(self, prompt, **kwargs):
        """Mock run method that returns a simple response."""
        # Extract device type and point name from prompt if possible for better mock mapping
        device_type = 'UNKNOWN'
        point_name = 'unknown_point'
        
        try:
            if 'Device Type:' in prompt:
                device_parts = prompt.split('Device Type:', 1)[1].strip().split('\n', 1)[0]
                device_type = device_parts.strip().upper()
            
            if 'BMS Point Name:' in prompt:
                point_parts = prompt.split('BMS Point Name:', 1)[1].strip().split('\n', 1)[0]
                point_name = point_parts.strip()
                
            # For temperature points, provide a more specific mapping
            if 'temp' in point_name.lower() or 'temperature' in point_name.lower():
                if 'supply' in point_name.lower() or 'discharge' in point_name.lower():
                    return {"content": '{"enosPoint": "' + device_type + '_raw_supply_temp"}'}
                elif 'return' in point_name.lower():
                    return {"content": '{"enosPoint": "' + device_type + '_raw_return_temp"}'}
                else:
                    return {"content": '{"enosPoint": "' + device_type + '_raw_temp"}'}
            
            # For status points
            elif 'status' in point_name.lower() or 'st' in point_name.lower():
                return {"content": '{"enosPoint": "' + device_type + '_stat_device_on_off"}'}
                
            # For setpoints
            elif 'setpoint' in point_name.lower() or 'sp' in point_name.lower():
                return {"content": '{"enosPoint": "' + device_type + '_sp_temp"}'}
                
            # Default response with device type prefix if available
            return {"content": '{"enosPoint": "' + device_type + '_raw_value"}'}
            
        except Exception:
            # Fallback to completely generic response
            return {"content": '{"enosPoint": "unknown"}'}


class Runner:
    """Mock Runner class."""
    
    def __init__(self, agents=None):
        self.agents = agents or []
        print("Mock Runner initialized")
    
    def run(self, inputs=None):
        """Mock run method."""
        return {"result": "mock_result"}
        
    @classmethod
    def run_sync(cls, agent, prompt, **kwargs):
        """Mock synchronous run method for compatibility with existing code.
        
        Returns a response object with final_output containing mock JSON for mapping.
        """
        if isinstance(agent, Agent):
            # If it's an actual agent instance, use its run method
            response = agent.run(prompt, **kwargs)
            if isinstance(response, dict) and "content" in response:
                return type('Response', (), {'final_output': response['content']})
            # Return a dummy response if the agent's run method doesn't return expected format
            return type('Response', (), {'final_output': '{"enosPoint": "unknown"}'})
        else:
            # Create a simple response object with a callable final_output
            return type('Response', (), {'final_output': '{"enosPoint": "unknown"}'})


# Print a warning to make it clear this is a mock implementation
print("WARNING: Using mock agents implementation. Limited functionality available.") 