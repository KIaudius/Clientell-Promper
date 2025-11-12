"""
Pydantic models for FastAPI request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class SalesforceCredentials(BaseModel):
    """Salesforce connection credentials"""
    username: str = Field(..., description="Salesforce username")
    password: str = Field(..., description="Salesforce password")
    security_token: str = Field(..., description="Salesforce security token")
    domain: str = Field(default="login", description="Domain: 'login' for production, 'test' for sandbox")
    anthropic_api_key: str = Field(..., description="Anthropic API key for Claude")


class ExtractMetadataRequest(BaseModel):
    """Request to extract Salesforce metadata"""
    credentials: SalesforceCredentials
    use_case_description: str = Field(..., description="Description of organization's use cases")


class UseCaseItem(BaseModel):
    """Individual use case with customizable prompt count"""
    id: str = Field(..., description="Unique identifier for the use case")
    name: str = Field(..., description="Name of the use case")
    description: str = Field(..., description="Description of what the use case tests")
    default_prompt_count: int = Field(default=3, description="Default number of prompts to generate")
    prompt_count: int = Field(default=3, description="User-specified number of prompts")


class UseCaseListResponse(BaseModel):
    """Response containing list of identified use cases"""
    session_id: str = Field(..., description="Unique session identifier")
    use_cases: List[UseCaseItem] = Field(..., description="List of identified use cases")
    metadata_summary: Dict[str, Any] = Field(..., description="Summary of extracted metadata")


class GeneratePromptsRequest(BaseModel):
    """Request to generate prompts for specific use cases"""
    session_id: str = Field(..., description="Session ID from metadata extraction")
    use_cases: List[UseCaseItem] = Field(..., description="Use cases with desired prompt counts")


class TestPrompt(BaseModel):
    """Individual test prompt"""
    use_case: str
    prompt: str
    expected_object: Optional[str] = None
    difficulty: str
    challenges: List[str]
    expected_behavior: str


class GeneratePromptsResponse(BaseModel):
    """Response containing generated prompts"""
    session_id: str
    total_prompts: int
    prompts: List[TestPrompt]
    generation_timestamp: str
    model: str
    tokens_used: Dict[str, int]


class DownloadFormat(BaseModel):
    """Request format for download"""
    format: str = Field(..., description="Output format: 'json' or 'csv'")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    details: Optional[str] = None
    timestamp: str
