# prompt_generator_claude.py
"""
Intelligent Test Prompt Generator with Claude AI
Analyzes org metadata and generates context-aware test prompts
"""

import json
import os
from typing import List, Dict, Any
from datetime import datetime, timezone
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def utc_now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()

class ClaudePromptGenerator:
    def __init__(self, metadata_file: str = 'org_metadata_claude.json', 
                 anthropic_api_key: str = None):
        """Load metadata and initialize Claude"""
        with open(metadata_file, 'r') as f:
            self.metadata = json.load(f)
        
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.claude = Anthropic(api_key=api_key)
        
        self.prompts = []
    
    def generate_prompts_with_claude(self):
        """Use Claude to generate context-aware prompts"""
        print("\n🤖 Generating test prompts with Claude AI...")

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
        
        # Create comprehensive prompt for Claude
        prompt = f"""You are a Salesforce testing expert. Generate comprehensive test prompts for an AI agent based on this org metadata.

**Org Metadata Context:**
{json.dumps(context, indent=2)}

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
            # Call Claude with streaming for better UX
            print("   Calling Claude API...")
            
            message = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0.5,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract and parse response
            response_text = message.content[0].text
            
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                prompts_json = json.loads(json_match.group())
                self.prompts = prompts_json
                print(f"   ✅ Generated {len(self.prompts)} test prompts")
            else:
                print("   ⚠️  Could not parse JSON from Claude response")
                print("   Raw response saved to claude_raw_response.txt")
                with open('claude_raw_response.txt', 'w') as f:
                    f.write(response_text)
            
            print(f"   Tokens used: {message.usage.input_tokens} input, {message.usage.output_tokens} output")
            
        except Exception as e:
            print(f"   ❌ Error calling Claude API: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def save_prompts(self, filename: str = 'test_prompts_claude.json'):
        """Save prompts to file"""
        output = {
            'generation_timestamp': utc_now_iso(),
            'total_prompts': len(self.prompts),
            'prompts': self.prompts
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"💾 Prompts saved to {filename}")
    
    def print_prompts(self):
        """Print prompts in readable format"""
        print("\n" + "="*70)
        print("GENERATED TEST PROMPTS")
        print("="*70)
        
        # Group by use case
        by_use_case = {}
        for prompt in self.prompts:
            uc = prompt.get('use_case', 'UNKNOWN')
            if uc not in by_use_case:
                by_use_case[uc] = []
            by_use_case[uc].append(prompt)
        
        for uc, prompts in sorted(by_use_case.items()):
            print(f"\n{'='*70}")
            print(f"{uc}")
            print(f"{'='*70}")
            
            for i, prompt in enumerate(prompts, 1):
                print(f"\n[{i}] {prompt.get('difficulty', 'unknown').upper()}")
                print(f"    Prompt: \"{prompt['prompt']}\"")
                if 'expected_object' in prompt:
                    print(f"    Expected Object: {prompt['expected_object']}")
                if 'challenges' in prompt:
                    print(f"    Challenges: {', '.join(prompt['challenges'])}")
                if 'expected_behavior' in prompt:
                    print(f"    Expected: {prompt['expected_behavior']}")


def main():
    """Main execution"""
    print("="*70)
    print("CLAUDE-POWERED PROMPT GENERATOR")
    print("="*70)
    
    generator = ClaudePromptGenerator('org_metadata_claude.json')
    generator.generate_prompts_with_claude()
    generator.save_prompts('test_prompts_claude.json')
    generator.print_prompts()
    
    print("\n" + "="*70)
    print("✅ PROMPT GENERATION COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()