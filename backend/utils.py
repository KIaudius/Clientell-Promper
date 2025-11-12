"""
Utility functions for data conversion and session management
"""

import csv
import json
import uuid
from io import StringIO
from datetime import datetime, timezone
from typing import Dict, List, Any


def utc_now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def generate_session_id() -> str:
    """Generate unique session ID"""
    return str(uuid.uuid4())


def convert_prompts_to_csv(prompts: List[Dict[str, Any]]) -> str:
    """Convert list of test prompts to CSV format"""
    if not prompts:
        return ""

    output = StringIO()

    # Define CSV headers
    fieldnames = [
        'use_case',
        'prompt',
        'expected_object',
        'difficulty',
        'challenges',
        'expected_behavior'
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for prompt in prompts:
        # Convert challenges list to comma-separated string
        row = {
            'use_case': prompt.get('use_case', ''),
            'prompt': prompt.get('prompt', ''),
            'expected_object': prompt.get('expected_object', ''),
            'difficulty': prompt.get('difficulty', ''),
            'challenges': '; '.join(prompt.get('challenges', [])),
            'expected_behavior': prompt.get('expected_behavior', '')
        }
        writer.writerow(row)

    return output.getvalue()


def convert_test_plan_to_csv(plan: Dict[str, Any]) -> str:
    """Convert test preparation plan to CSV format"""
    if not plan or 'tasks' not in plan:
        return ""

    output = StringIO()

    fieldnames = [
        'category',
        'action',
        'purpose',
        'manual_steps',
        'test_prompts',
        'verification'
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for task in plan.get('tasks', []):
        row = {
            'category': task.get('category', ''),
            'action': task.get('action', ''),
            'purpose': task.get('purpose', ''),
            'manual_steps': ' | '.join(task.get('manual_steps', [])),
            'test_prompts': ' | '.join(task.get('test_prompts', [])),
            'verification': ' | '.join(task.get('verification', []))
        }
        writer.writerow(row)

    return output.getvalue()


def convert_metadata_to_csv(metadata: Dict[str, Any]) -> str:
    """Convert metadata summary to CSV format"""
    output = StringIO()

    # Create a summary CSV
    writer = csv.writer(output)
    writer.writerow(['Metric', 'Value'])

    # Org info
    writer.writerow(['Org Name', metadata.get('org_info', {}).get('Name', '')])
    writer.writerow(['Org Type', metadata.get('org_info', {}).get('OrganizationType', '')])
    writer.writerow(['Is Sandbox', metadata.get('org_info', {}).get('IsSandbox', '')])

    # Counts
    writer.writerow(['Total Objects', len(metadata.get('objects', {}))])
    custom_objects = [name for name, obj in metadata.get('objects', {}).items() if obj.get('custom')]
    writer.writerow(['Custom Objects', len(custom_objects)])
    writer.writerow(['Total Flows', len(metadata.get('flows', []))])
    writer.writerow(['Active Flows', sum(1 for f in metadata.get('flows', []) if f.get('IsActive'))])
    writer.writerow(['Total Reports', len(metadata.get('reports', []))])
    writer.writerow(['Validation Rules', len(metadata.get('validation_rules', []))])
    writer.writerow(['Apex Classes', len(metadata.get('apex_classes', []))])
    writer.writerow(['Active Users', len(metadata.get('users', []))])

    return output.getvalue()


# In-memory session storage (use Redis/database in production)
SESSION_STORAGE: Dict[str, Dict[str, Any]] = {}


def store_session_data(session_id: str, data: Dict[str, Any]):
    """Store session data"""
    SESSION_STORAGE[session_id] = data


def get_session_data(session_id: str) -> Dict[str, Any]:
    """Retrieve session data"""
    return SESSION_STORAGE.get(session_id, {})


def delete_session_data(session_id: str):
    """Delete session data (cleanup)"""
    if session_id in SESSION_STORAGE:
        del SESSION_STORAGE[session_id]
