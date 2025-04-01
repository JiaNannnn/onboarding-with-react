# Technical Specifications

## 1. API Contracts
```python
class BMSAPIEndpoints:
    @route("/api/v1/points", methods=["POST"])
    def create_point(payload: BMSPointSchema) -> BMSPointResponse:
        """
        Expected Response:
        {
            "point_id": "uuid4",
            "status": "pending|mapped|error"
        }
        """
    
    @route("/api/v1/mappings", methods=["PUT"])
    def update_mapping(source: str, target: str) -> MappingResponse:
        requires: JWT Scope 'mapping:write'
        
    @route("/api/v1/group-points", methods=["POST"])
    def group_points(points: list[str]) -> GroupingResponse:
        """
        AI-based semantic grouping of BMS points
        Implements concurrent processing with timeout handling
        """
        
    @route("/api/v1/map-points", methods=["POST"])
    def map_points(points: list[PointMappingRequest]) -> MappingResponse:
        """
        AI-based semantic mapping to EnOS schema
        Implements parallel point processing with per-point timeouts
        """
```

## 2. Enhanced Data Models
```python
class DeviceGroup(BaseModel):
    device_type: Literal["AHU", "FCU", "CHPL", "BOIL", "VAV", "PUMP"]  # From enos.json keys
    raw_points: list[str]
    normalized_name: str
    instances: list[DeviceInstance]
    ai_confidence: float = 0.0
    ai_reasoning: list[str] = []

class DeviceInstance(BaseModel):
    device_id: str  # e.g. "AHU-1", "FCU-02"
    raw_points: dict[str, str]  # {raw_point: enos_mapping}
    mapping_status: Literal["pending", "partial", "complete"]
    semantic_grouping: dict = {}  # AI-generated semantic grouping
    
class DeviceMapping(BaseModel):
    source_id: str
    enos_path: str  # e.g. "AHU/points/AHU_raw_status"
    mapping_confidence: float
    last_validated: datetime
    point_type: Literal["AI", "AO", "BI", "BO", "MI", "MO"]
    reasoning: list[str] = []  # AI reasoning for mapping
```

## 3. Updated Integration Contracts
```python
class OpenAIClient:
    """Interface to OpenAI GPT-4o model"""
    
    def create_structured_completion(
        self, 
        prompt: str, 
        json_schema: dict, 
        model: str = "gpt-4o",
        temperature: float = 0,
        timeout: int = 30
    ) -> dict:
        """Generate structured JSON outputs using OpenAI with timeout"""

class EnOSAdapter:
    @retry(times=3, delay=1)
    async def fetch_bms_points(self, asset_id: str) -> list[dict]:
        """Implements EnOS Edge API point fetching"""
        
    async def push_mappings(self, mappings: list[DeviceMapping]):
        """Batch push with schema validation against enos.json"""

class BMSProcessor:
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        self.fallback_processor = FallbackProcessor()
        self.cache = {}  # In-memory cache for API responses
    
    def group_by_device_type(self, raw_points: list[str], timeout: int = 60) -> dict[str, DeviceGroup]:
        """AI-based semantic grouping with fallback option and timeout"""
        
    def map_to_enos_schema(self, point_name: str, device_type: str, timeout: int = 5) -> DeviceMapping:
        """AI-based semantic mapping to EnOS schema with confidence scores and timeout"""
        
class FallbackProcessor:
    """Fallback processing using traditional methods when AI is unavailable"""
    
    def group_by_device_type(self, raw_points: list[str]) -> dict[str, DeviceGroup]:
        """Pattern-based grouping using prefixes"""
    
    def map_to_enos_schema(self, point_name: str, device_type: str) -> DeviceMapping:
        """Keyword-based mapping to EnOS schema"""
```

## 4. AI Integration Architecture
```python
class AISchemas:
    """JSON schemas for structured outputs from OpenAI"""
    
    GROUPING_SCHEMA = {
        "type": "object",
        "properties": {
            "grouping": {
                "type": "object",
                "properties": {
                    "deviceTypes": {
                        "type": "object",
                        "description": "Mapping of device type categories to their instances",
                        "additionalProperties": {
                            "type": "object",
                            "description": "Map of device instances to their associated points",
                            "additionalProperties": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "reasoning": {
                "type": "array",
                "description": "Step-by-step reasoning for how the grouping was determined",
                "items": {"type": "string"}
            }
        }
    }
    
    MAPPING_SCHEMA = {
        "type": "object",
        "properties": {
            "mapping": {
                "type": "object",
                "properties": {
                    "pointType": {
                        "type": "string",
                        "description": "The type of point (AI, AO, BI, BO, etc.)"
                    },
                    "enosPath": {
                        "type": "string",
                        "description": "The EnOS standardized path for this point"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence level in the mapping (0-1)"
                    }
                }
            },
            "reasoning": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
```

## 5. Environment Configuration
```python
class AIConfiguration:
    """Required environment variables for AI integration"""
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.4"))  # Lowered from 0.7
    ENABLE_FALLBACK = os.getenv("ENABLE_FALLBACK", "true").lower() == "true"
    
    # Endpoint-specific settings
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))
    POINT_MAPPING_TIMEOUT = int(os.getenv("POINT_MAPPING_TIMEOUT", "5"))
    MAX_POINTS_LIMIT = int(os.getenv("MAX_POINTS_LIMIT", "1000"))
    MAX_CONCURRENT_MAPPINGS = int(os.getenv("MAX_CONCURRENT_MAPPINGS", "5"))
```

## 6. Error Handling and Resilience
```python
class ErrorHandlingStrategy:
    """Enhanced error handling for AI operations"""
    
    # Graceful degradation patterns
    RETRY_WITH_BACKOFF = "Exponential backoff with jitter"
    CIRCUIT_BREAKER = "Fail fast after repeated errors"
    FALLBACK_PROCESSING = "Pattern-based fallback when AI unavailable"
    PARALLEL_PROCESSING = "Concurrent request processing with timeouts"
    
    # Error response categories
    ERROR_TYPES = {
        "TIMEOUT_ERROR": {"status_code": 504, "message": "Operation timed out"},
        "OPENAI_API_ERROR": {"status_code": 502, "message": "Error communicating with AI service"},
        "MEMORY_ERROR": {"status_code": 507, "message": "Memory limit exceeded"},
        "PROCESSING_ERROR": {"status_code": 500, "message": "Error during processing"}
    }
    
    # Resource management
    RESOURCE_LIMITS = {
        "group_points": {"max_points": 1000, "timeout": 60},
        "map_points": {"max_points": 200, "timeout_per_point": 5, "concurrent_mappings": 5}
    }
``` 