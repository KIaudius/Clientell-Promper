"""
Intelligent Test Prompt Generator with Claude AI
Modular service for web application
"""

import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any
from anthropic import Anthropic


def utc_now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


class ClaudePromptGenerator:
    def __init__(self, metadata: dict, anthropic_api_key: str, model_id: str = "claude-3-5-sonnet-20241022"):
        """Initialize with metadata and Claude client"""
        self.metadata = metadata
        self.claude = Anthropic(api_key=anthropic_api_key)
        self.model_id = model_id

    def generate_prompts(self, use_case_context: str = None):
        """Use Claude to generate context-aware prompts"""
        # Prepare context for Claude
        custom_objects = [
            {'name': name, 'label': obj['label']}
            for name, obj in self.metadata['objects'].items()
            if obj.get('custom')
        ]

        # Find financial fields
        financial_fields = {}
        for obj_name, obj_data in self.metadata['objects'].items():
            fields = [
                f['name'] for f in obj_data.get('fields', [])
                if any(kw in f['name'].lower() or kw in f['label'].lower()
                      for kw in ['commission', 'premium', 'amount', 'policy'])
            ]
            if fields:
                financial_fields[obj_name] = fields[:3]

        # Get actual sample data from org
        sample_data = self.metadata.get('sample_data', {})
        sample_accounts = [acc['Name'] for acc in sample_data.get('accounts', [])]
        sample_opportunities = [opp['Name'] for opp in sample_data.get('opportunities', [])]

        # Get custom object sample data
        custom_object_samples = {}
        for obj_name in [name for name, obj in self.metadata['objects'].items() if obj.get('custom')][:5]:
            if obj_name in sample_data:
                custom_object_samples[obj_name] = [rec.get('Name') for rec in sample_data[obj_name] if rec.get('Name')]

        context = {
            'custom_objects': custom_objects[:10],
            'financial_fields': financial_fields,
            'sample_accounts': sample_accounts[:10] if sample_accounts else ["[No accounts found in org]"],
            'sample_opportunities': sample_opportunities[:10] if sample_opportunities else ["[No opportunities found]"],
            'custom_object_samples': custom_object_samples,
            'total_flows': len(self.metadata['flows']),
            'inactive_flows': [
                f['ApiName'] for f in self.metadata['flows']
                if not f.get('IsActive')
            ][:5],
            'reports': [
                {'name': r['Name'], 'folder': r.get('FolderName')}
                for r in self.metadata['reports'][:10]
            ]
        }

        use_case_section = ""
        if use_case_context:
            use_case_section = f"""
**Organization-Specific Use Cases:**
{use_case_context}

Please generate prompts that specifically test these use cases.
"""

        # Create comprehensive prompt for Claude
        prompt = f"""You are a Salesforce testing expert. Generate comprehensive test prompts for an AI agent based on this org metadata.

**Org Metadata Context:**
{json.dumps(context, indent=2)}

{use_case_section}

**Use Cases to Cover:**
1. Show insurance policies for an account (query custom objects)
2. Calculate total commission for an account (aggregation)
3. Find open opportunities closing this month (date filtering + user context)
4. Create a lead (record creation with validation)
5. Create an opportunity (record creation with account lookup)
6. Build custom commission report (report generation with grouping)
7. Sales goal progress tracking (data analysis)

**CRITICAL Requirements:**
- Generate 2-3 prompt variations per use case (15-20 total)
- **USE ACTUAL ACCOUNT NAMES from sample_accounts** - DO NOT make up fake account names
- **USE ACTUAL OPPORTUNITY NAMES from sample_opportunities** - DO NOT use placeholder names
- **USE ACTUAL CUSTOM OBJECT NAMES and sample data** from custom_object_samples
- Use actual field names from financial_fields when referencing commissions/amounts
- Include varying difficulty levels: easy, medium, hard
- Add edge cases that test disambiguation (ambiguous account names, etc.)
- Include prompts that will challenge error handling
- Format as JSON array with this structure:
  [
    {{
      "use_case": "UC1",
      "prompt": "actual prompt text with real data",
      "expected_object": "ObjectName",
      "difficulty": "easy|medium|hard",
      "challenges": ["list", "of", "challenges"],
      "expected_behavior": "what agent should do"
    }}
  ]

Return ONLY the JSON array, no additional text."""

        try:
            message = self.claude.messages.create(
                model=self.model_id,
                max_tokens=4096,
                temperature=0.5,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract and parse response
            response_text = message.content[0].text

            # Try to extract JSON from response
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                prompts_json = json.loads(json_match.group())
                return {
                    'generation_timestamp': utc_now_iso(),
                    'total_prompts': len(prompts_json),
                    'model': message.model,
                    'tokens_used': {
                        'input': message.usage.input_tokens,
                        'output': message.usage.output_tokens
                    },
                    'prompts': prompts_json
                }
            else:
                return {
                    'error': 'JSON parse failed',
                    'raw_response': response_text[:1000]  # First 1000 chars
                }

        except Exception as e:
            return {
                'error': str(e),
                'model': self.model_id,
                'timestamp': utc_now_iso()
            }
