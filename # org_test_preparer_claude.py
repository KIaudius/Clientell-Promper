# org_test_preparer_claude.py
"""
Salesforce Org Test Preparation with Claude AI
Creates challenging scenarios for agent testing
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Union
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    def __init__(self, metadata_file: str = 'org_metadata_claude.json',
                 anthropic_api_key: str = None):
        """Load metadata and initialize Claude"""
        with open(metadata_file, 'r') as f:
            self.metadata = json.load(f)
        
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.claude = Anthropic(api_key=api_key)
        self.model_id = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    
    def generate_preparation_plan_with_claude(self):
        """Use Claude to generate comprehensive test preparation plan"""
        print("\n🤖 Generating test preparation plan with Claude AI...")
        
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
        
        prompt = f"""You are a Salesforce testing expert. Create a comprehensive test preparation plan to challenge an AI agent's capabilities.

**Current Org State:**
{json.dumps(org_context, indent=2)}

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
            print("   Calling Claude API...")
            
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
            import re
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

                print(f"   ✅ Generated {len(plan.get('tasks', []))} test preparation tasks")
                if usage:
                    print(f"   Tokens used: {usage.input_tokens} input, {usage.output_tokens} output")

                return plan
            else:
                print("   ⚠️  Could not parse JSON from Claude response")
                with open('claude_prep_raw_response.txt', 'w') as f:
                    f.write(response_text)
                return {'error': 'JSON parse failed', 'raw_response_file': 'claude_prep_raw_response.txt'}

        except Exception as e:
            print(f"   ❌ Error calling Claude API: {str(e)}")
            return {
                'error': str(e),
                'model': self.model_id,
                'timestamp': utc_now_iso(),
                'suggestions': 'Verify ANTHROPIC_API_KEY / ANTHROPIC_MODEL and consult https://docs.anthropic.com for current models.'
            }
    
    def save_preparation_plan(self, plan: dict, filename: str = 'test_preparation_plan_claude.json'):
        """Save preparation plan"""
        with open(filename, 'w') as f:
            json.dump(plan, f, indent=2)
        print(f"💾 Test preparation plan saved to {filename}")
    
    def print_preparation_plan(self, plan: dict):
        """Print preparation plan in readable format"""
        print("\n" + "="*70)
        print("SALESFORCE ORG TEST PREPARATION PLAN (Claude-Generated)")
        print("="*70)
        
        if 'error' in plan:
            print(f"\n❌ Error: {plan['error']}")
            return
        
        print(f"\nGenerated: {plan.get('generation_timestamp')}")
        print(f"Model: {plan.get('model')}")
        print(f"Total Tasks: {len(plan.get('tasks', []))}\n")
        
        for i, task in enumerate(plan.get('tasks', []), 1):
            print(f"\n{'='*70}")
            print(f"TASK {i}: {task.get('category', 'UNKNOWN')}")
            print(f"{'='*70}")
            print(f"Action: {task.get('action', 'N/A')}")
            print(f"Purpose: {task.get('purpose', 'N/A')}")
            
            if 'manual_steps' in task:
                print("\nManual Steps:")
                for step in task['manual_steps']:
                    print(f"  {step}")
            
            if 'test_prompts' in task:
                print("\nTest Prompts:")
                for prompt in task['test_prompts']:
                    print(f"  • \"{prompt}\"")
            
            if 'verification' in task:
                print("\nVerification:")
                for item in task['verification']:
                    print(f"  ✓ {item}")


def main():
    """Main execution"""
    print("="*70)
    print("CLAUDE-POWERED ORG TEST PREPARATION PLANNER")
    print("="*70)
    
    preparer = ClaudeTestPreparer('org_metadata_claude.json')
    plan = preparer.generate_preparation_plan_with_claude()
    preparer.save_preparation_plan(plan)
    preparer.print_preparation_plan(plan)
    
    print("\n" + "="*70)
    print("✅ PREPARATION PLAN GENERATED")
    print("="*70)
    print("\nNext Steps:")
    print("1. Review the plan in test_preparation_plan_claude.json")
    print("2. Execute manual steps in your Salesforce org")
    print("3. Run the test prompts against your agent")
    print("4. Document agent behavior and issues")


if __name__ == "__main__":
    main()