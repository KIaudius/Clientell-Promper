"""
Salesforce Org Test Preparation with Claude AI
Modular service for web application
"""

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Union
from anthropic import Anthropic


def utc_now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def extract_text_from_blocks(content: Iterable[Union[Dict[str, Any], Any]]) -> str:
    """Normalize Anthropic content blocks into a single text string."""
    text_parts: List[str] = []

    for block in content:
        if isinstance(block, dict):
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            continue

        block_type = getattr(block, "type", None)
        if block_type == "text":
            text_parts.append(getattr(block, "text", ""))

    return "\n".join(part.strip() for part in text_parts if part)


class ClaudeTestPreparer:
    def __init__(self, metadata: dict, anthropic_api_key: str, model_id: str = "claude-3-5-sonnet-20241022"):
        """Initialize with metadata and Claude client"""
        self.metadata = metadata
        self.claude = Anthropic(api_key=anthropic_api_key)
        self.model_id = model_id

    def generate_preparation_plan(self, use_case_context: str = None):
        """Use Claude to generate comprehensive test preparation plan"""
        # Prepare org context
        org_context = {
            'org_type': self.metadata['org_info'].get('OrganizationType'),
            'is_sandbox': self.metadata['org_info'].get('IsSandbox'),
            'custom_objects': [
                name for name, obj in self.metadata['objects'].items()
                if obj.get('custom')
            ][:10],
            'flows': {
                'total': len(self.metadata['flows']),
                'active': [f['ApiName'] for f in self.metadata['flows'] if f.get('IsActive')][:5],
                'inactive': [f['ApiName'] for f in self.metadata['flows'] if not f.get('IsActive')][:5]
            },
            'reports': len(self.metadata['reports']),
            'validation_rules': len(self.metadata['validation_rules'])
        }

        use_case_section = ""
        if use_case_context:
            use_case_section = f"""
**Organization-Specific Use Cases:**
{use_case_context}

Please incorporate these use cases into the test preparation plan.
"""

        prompt = f"""You are a Salesforce testing expert. Create a comprehensive test preparation plan to challenge an AI agent's capabilities.

**Current Org State:**
{json.dumps(org_context, indent=2)}

{use_case_section}

**Your Task:**
Generate a detailed test preparation plan with specific, actionable steps to create challenging test scenarios. Include:

1. **Flow Challenges**: How to deactivate flows, create error flows, and test flow operations
2. **Data Ambiguity**: Creating duplicate/similar records to test disambiguation
3. **Validation Challenges**: Setting up validation rules that will trigger errors
4. **Permission Tests**: Restricting access to test error handling
5. **Performance Tests**: Ensuring sufficient data volume
6. **Custom Object Tests**: Leveraging actual custom objects in the org
7. **Edge Cases**: Unusual scenarios that test robustness

For each challenge category, provide:
- Specific manual steps to execute in Salesforce
- Expected test prompts to use
- What agent behavior to verify
- Why this tests a specific capability

Format as JSON:
{{
  "tasks": [
    {{
      "category": "CATEGORY_NAME",
      "action": "brief description",
      "purpose": "why this is important",
      "manual_steps": ["step 1", "step 2"],
      "test_prompts": ["prompt 1", "prompt 2"],
      "verification": ["what to check"]
    }}
  ]
}}

Return ONLY the JSON, no additional text."""

        try:
            message = self.claude.messages.create(
                model=self.model_id,
                max_tokens=4096,
                temperature=0.4,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = extract_text_from_blocks(message.content)

            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                plan = json.loads(json_match.group())
                plan['generation_timestamp'] = utc_now_iso()
                plan['model'] = message.model
                usage = getattr(message, 'usage', None)
                plan['tokens_used'] = {
                    'input': getattr(usage, 'input_tokens', None),
                    'output': getattr(usage, 'output_tokens', None)
                }

                return plan
            else:
                return {
                    'error': 'JSON parse failed',
                    'raw_response': response_text[:1000]  # First 1000 chars
                }

        except Exception as e:
            return {
                'error': str(e),
                'model': self.model_id,
                'timestamp': utc_now_iso(),
                'suggestions': 'Verify ANTHROPIC_API_KEY / model configuration and consult https://docs.anthropic.com for current models.'
            }
