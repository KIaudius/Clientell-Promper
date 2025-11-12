"""
FastAPI Backend for Salesforce Test Prompt Generator
Modular web application with multi-step workflow
"""

import json
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import io

from models import (
    ExtractMetadataRequest,
    UseCaseListResponse,
    UseCaseItem,
    GeneratePromptsRequest,
    GeneratePromptsResponse,
    ErrorResponse,
    TestPrompt
)
from services.metadata_extractor import SalesforceMetadataExtractor
from services.test_preparer import ClaudeTestPreparer
from services.prompt_generator import ClaudePromptGenerator
from utils import (
    generate_session_id,
    store_session_data,
    get_session_data,
    delete_session_data,
    convert_prompts_to_csv,
    convert_test_plan_to_csv,
    convert_metadata_to_csv,
    utc_now_iso
)

app = FastAPI(
    title="Salesforce Test Prompt Generator",
    description="Generate context-aware test prompts for Salesforce organizations",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Salesforce Test Prompt Generator",
        "version": "1.0.0"
    }


@app.post("/api/step1-extract", response_model=UseCaseListResponse)
async def step1_extract_metadata(request: ExtractMetadataRequest):
    """
    Step 1: Extract Salesforce metadata and identify use cases
    Returns list of use cases for user to customize
    """
    try:
        # Generate session ID
        session_id = generate_session_id()

        # Extract metadata
        extractor = SalesforceMetadataExtractor(
            username=request.credentials.username,
            password=request.credentials.password,
            security_token=request.credentials.security_token,
            anthropic_api_key=request.credentials.anthropic_api_key,
            domain=request.credentials.domain
        )

        metadata = extractor.extract_all(use_case_context=request.use_case_description)
        extractor.close()

        # Use Claude to identify and categorize use cases
        # Parse the use case description and create structured use cases
        use_cases = await identify_use_cases(
            metadata,
            request.use_case_description,
            request.credentials.anthropic_api_key
        )

        # Store metadata and use cases in session
        store_session_data(session_id, {
            'metadata': metadata,
            'use_case_description': request.use_case_description,
            'use_cases': [uc.dict() for uc in use_cases],
            'anthropic_api_key': request.credentials.anthropic_api_key,
            'timestamp': utc_now_iso()
        })

        # Create metadata summary
        metadata_summary = {
            'org_name': metadata.get('org_info', {}).get('Name', ''),
            'org_type': metadata.get('org_info', {}).get('OrganizationType', ''),
            'is_sandbox': metadata.get('org_info', {}).get('IsSandbox', False),
            'custom_objects': len([o for o in metadata.get('objects', {}).values() if o.get('custom')]),
            'total_flows': len(metadata.get('flows', [])),
            'total_reports': len(metadata.get('reports', []))
        }

        return UseCaseListResponse(
            session_id=session_id,
            use_cases=use_cases,
            metadata_summary=metadata_summary
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/step2-generate-prompts", response_model=GeneratePromptsResponse)
async def step2_generate_prompts(request: GeneratePromptsRequest):
    """
    Step 2: Generate prompts based on user-specified counts for each use case
    """
    try:
        # Retrieve session data
        session_data = get_session_data(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        metadata = session_data['metadata']
        use_case_description = session_data['use_case_description']
        anthropic_api_key = session_data['anthropic_api_key']

        # Generate prompts for each use case with specified count
        all_prompts = []
        total_tokens = {'input': 0, 'output': 0}

        for use_case in request.use_cases:
            # Generate prompts for this specific use case
            prompts = await generate_prompts_for_use_case(
                metadata=metadata,
                use_case=use_case,
                anthropic_api_key=anthropic_api_key,
                use_case_description=use_case_description
            )

            # Add to total
            all_prompts.extend(prompts['prompts'])
            if 'tokens_used' in prompts:
                total_tokens['input'] += prompts['tokens_used'].get('input', 0)
                total_tokens['output'] += prompts['tokens_used'].get('output', 0)

        # Store generated prompts in session
        session_data['generated_prompts'] = all_prompts
        session_data['generation_timestamp'] = utc_now_iso()
        store_session_data(request.session_id, session_data)

        # Convert to TestPrompt models
        test_prompts = [TestPrompt(**prompt) for prompt in all_prompts]

        return GeneratePromptsResponse(
            session_id=request.session_id,
            total_prompts=len(test_prompts),
            prompts=test_prompts,
            generation_timestamp=utc_now_iso(),
            model="claude-3-5-sonnet-20241022",
            tokens_used=total_tokens
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{session_id}/{format}")
async def download_results(session_id: str, format: str):
    """
    Step 3: Download results in specified format (json or csv)
    """
    try:
        # Validate format
        if format not in ['json', 'csv']:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")

        # Retrieve session data
        session_data = get_session_data(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        prompts = session_data.get('generated_prompts', [])
        metadata = session_data.get('metadata', {})

        if format == 'json':
            # Return JSON with all data
            output = {
                'metadata_summary': {
                    'org_info': metadata.get('org_info', {}),
                    'extraction_timestamp': metadata.get('extraction_timestamp'),
                    'custom_objects': [name for name, obj in metadata.get('objects', {}).items() if obj.get('custom')],
                    'total_flows': len(metadata.get('flows', [])),
                    'total_reports': len(metadata.get('reports', []))
                },
                'claude_analysis': metadata.get('claude_analysis', {}),
                'test_prompts': prompts,
                'generation_timestamp': session_data.get('generation_timestamp'),
                'total_prompts': len(prompts)
            }

            return Response(
                content=json.dumps(output, indent=2, default=str),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=test_prompts_{session_id[:8]}.json"
                }
            )

        else:  # CSV format
            csv_content = convert_prompts_to_csv(prompts)

            return StreamingResponse(
                io.StringIO(csv_content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=test_prompts_{session_id[:8]}.csv"
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download-metadata/{session_id}/{format}")
async def download_metadata(session_id: str, format: str):
    """
    Download full metadata in specified format
    """
    try:
        if format not in ['json', 'csv']:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")

        session_data = get_session_data(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        metadata = session_data.get('metadata', {})

        if format == 'json':
            return Response(
                content=json.dumps(metadata, indent=2, default=str),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=metadata_{session_id[:8]}.json"
                }
            )
        else:  # CSV
            csv_content = convert_metadata_to_csv(metadata)
            return StreamingResponse(
                io.StringIO(csv_content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=metadata_{session_id[:8]}.csv"
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """
    Cleanup session data (call this after download to free memory)
    """
    try:
        delete_session_data(session_id)
        return {"status": "success", "message": "Session cleaned up"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

async def identify_use_cases(
    metadata: Dict[str, Any],
    use_case_description: str,
    anthropic_api_key: str
) -> list[UseCaseItem]:
    """
    Use Claude to identify and structure use cases from description
    """
    from anthropic import Anthropic
    import re

    claude = Anthropic(api_key=anthropic_api_key)

    # Get custom objects for context
    custom_objects = [
        {'name': name, 'label': obj['label']}
        for name, obj in metadata['objects'].items()
        if obj.get('custom')
    ]

    prompt = f"""You are a Salesforce testing expert. Based on the user's description and the org metadata, identify distinct use cases that should be tested.

**User's Use Case Description:**
{use_case_description}

**Org Context:**
- Custom Objects: {json.dumps(custom_objects[:10], indent=2)}
- Total Flows: {len(metadata.get('flows', []))}
- Total Reports: {len(metadata.get('reports', []))}

**Your Task:**
Identify 5-10 distinct, testable use cases. Each use case should be specific and actionable.

Return ONLY a JSON array with this structure:
[
  {{
    "id": "uc1",
    "name": "Query Insurance Policies",
    "description": "Test querying custom insurance policy objects for specific accounts",
    "default_prompt_count": 3
  }},
  ...
]

Return ONLY the JSON array, no additional text."""

    try:
        message = claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        # Extract JSON
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            use_cases_data = json.loads(json_match.group())
            return [UseCaseItem(**uc) for uc in use_cases_data]
        else:
            # Fallback to default use cases
            return get_default_use_cases()

    except Exception as e:
        # Fallback to default use cases
        return get_default_use_cases()


async def generate_prompts_for_use_case(
    metadata: Dict[str, Any],
    use_case: UseCaseItem,
    anthropic_api_key: str,
    use_case_description: str
) -> Dict[str, Any]:
    """
    Generate specific number of prompts for a single use case
    """
    from anthropic import Anthropic
    import re

    claude = Anthropic(api_key=anthropic_api_key)

    # Get sample data
    sample_data = metadata.get('sample_data', {})
    sample_accounts = [acc['Name'] for acc in sample_data.get('accounts', [])]
    sample_opportunities = [opp['Name'] for opp in sample_data.get('opportunities', [])]

    # Get custom objects
    custom_objects = [name for name, obj in metadata['objects'].items() if obj.get('custom')]

    context = {
        'use_case': use_case.dict(),
        'sample_accounts': sample_accounts[:5],
        'sample_opportunities': sample_opportunities[:5],
        'custom_objects': custom_objects[:5]
    }

    prompt = f"""Generate exactly {use_case.prompt_count} test prompts for this specific use case:

**Use Case:**
- Name: {use_case.name}
- Description: {use_case.description}

**Context:**
{json.dumps(context, indent=2)}

**Requirements:**
- Generate EXACTLY {use_case.prompt_count} prompts
- Use ACTUAL data from sample_accounts and sample_opportunities
- Vary difficulty: easy, medium, hard
- Include edge cases

Return ONLY a JSON array:
[
  {{
    "use_case": "{use_case.id}",
    "prompt": "actual prompt text with real data",
    "expected_object": "ObjectName",
    "difficulty": "easy|medium|hard",
    "challenges": ["challenge1", "challenge2"],
    "expected_behavior": "what should happen"
  }}
]

Return ONLY the JSON array, no additional text."""

    try:
        message = claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        # Extract JSON
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            prompts = json.loads(json_match.group())
            return {
                'prompts': prompts,
                'tokens_used': {
                    'input': message.usage.input_tokens,
                    'output': message.usage.output_tokens
                }
            }
        else:
            return {'prompts': [], 'tokens_used': {'input': 0, 'output': 0}}

    except Exception as e:
        return {'prompts': [], 'tokens_used': {'input': 0, 'output': 0}, 'error': str(e)}


def get_default_use_cases() -> list[UseCaseItem]:
    """
    Fallback default use cases
    """
    return [
        UseCaseItem(
            id="uc1",
            name="Query Records",
            description="Test querying records from custom objects",
            default_prompt_count=3,
            prompt_count=3
        ),
        UseCaseItem(
            id="uc2",
            name="Create Records",
            description="Test creating new records with validation",
            default_prompt_count=3,
            prompt_count=3
        ),
        UseCaseItem(
            id="uc3",
            name="Update Records",
            description="Test updating existing records",
            default_prompt_count=3,
            prompt_count=3
        ),
        UseCaseItem(
            id="uc4",
            name="Calculate Aggregations",
            description="Test calculating sums, averages, and aggregations",
            default_prompt_count=3,
            prompt_count=3
        ),
        UseCaseItem(
            id="uc5",
            name="Generate Reports",
            description="Test generating custom reports",
            default_prompt_count=3,
            prompt_count=3
        )
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
