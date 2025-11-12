"""
Salesforce Org Metadata Extraction with Claude AI Analysis
Modular service for web application
"""

import json
from datetime import datetime, timezone
from simple_salesforce import Salesforce
from typing import Dict, List, Any, Iterable, Union
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

    return "\n\n".join(part.strip() for part in text_parts if part)


class SalesforceMetadataExtractor:
    def __init__(self, username: str, password: str, security_token: str,
                 anthropic_api_key: str, domain: str = 'login', model_id: str = "claude-3-5-sonnet-20241022"):
        """Initialize Salesforce connection and Claude client"""
        self.sf = None
        self.username = username
        self.password = password
        self.security_token = security_token
        self.domain = domain

        # Initialize Claude client
        self.claude = Anthropic(api_key=anthropic_api_key)
        self.model_id = model_id

        self.metadata = {
            "extraction_timestamp": utc_now_iso(),
            "org_info": {},
            "objects": {},
            "flows": [],
            "reports": [],
            "validation_rules": [],
            "apex_classes": [],
            "profiles": [],
            "users": [],
            "sample_data": {},
            "claude_analysis": {},
            "warnings": []
        }

    def connect(self):
        """Establish connection to Salesforce"""
        try:
            self.sf = Salesforce(
                username=self.username,
                password=self.password,
                security_token=self.security_token,
                domain=self.domain
            )
            return {"success": True, "message": "Connected to Salesforce"}
        except Exception as e:
            raise Exception(f"Failed to connect to Salesforce: {str(e)}")

    def fetch_org_info(self):
        """Get basic org information"""
        org_query = """
            SELECT Id, Name, OrganizationType, InstanceName, IsSandbox,
                   TrialExpirationDate, NamespacePrefix
            FROM Organization
        """
        result = self.sf.query_all(org_query)
        if result['records']:
            self.metadata['org_info'] = result['records'][0]

    def fetch_all_objects(self):
        """Get all standard and custom objects"""
        describe = self.sf.describe()

        for sobject in describe['sobjects']:
            obj_name = sobject['name']

            if sobject['queryable'] and sobject['retrieveable']:
                self.metadata['objects'][obj_name] = {
                    'label': sobject['label'],
                    'custom': sobject['custom'],
                    'keyPrefix': sobject['keyPrefix'],
                    'fields': []
                }

    def fetch_object_fields(self, object_name: str):
        """Get all fields for a specific object"""
        try:
            describe = getattr(self.sf, object_name).describe()
            fields = []

            for field in describe['fields']:
                field_data = {
                    'name': field['name'],
                    'label': field['label'],
                    'type': field['type'],
                    'custom': field.get('custom', False),
                    'length': field.get('length'),
                    'unique': field.get('unique'),
                    'nillable': field.get('nillable'),
                    'updateable': field.get('updateable'),
                    'createable': field.get('createable'),
                }

                if field['type'] in ('picklist', 'multipicklist'):
                    field_data['picklistValues'] = [
                        pv['value'] for pv in field.get('picklistValues', [])
                    ]

                if field.get('referenceTo'):
                    field_data['referenceTo'] = field['referenceTo']
                    field_data['relationshipName'] = field.get('relationshipName')

                fields.append(field_data)

            return fields
        except Exception as e:
            self.metadata['warnings'].append(f"Error fetching fields for {object_name}: {str(e)}")
            return []

    def fetch_key_object_fields(self):
        """Fetch fields for key business objects"""
        priority_objects = [
            'Account', 'Contact', 'Lead', 'Opportunity',
            'User', 'Profile', 'RecordType'
        ]

        custom_objects = [name for name, obj in self.metadata['objects'].items()
                         if obj['custom']]

        all_objects = priority_objects + custom_objects[:20]

        for obj_name in all_objects:
            if obj_name in self.metadata['objects']:
                fields = self.fetch_object_fields(obj_name)
                self.metadata['objects'][obj_name]['fields'] = fields

    def fetch_flows(self):
        """Get all flows with metadata"""
        flow_query = """
            SELECT Id, ApiName, Label, ProcessType, TriggerType, RecordTriggerType,
                   IsActive, VersionNumber, Description, TriggerObjectOrEventLabel,
                   LastModifiedDate
            FROM FlowDefinitionView
            ORDER BY LastModifiedDate DESC
        """

        result = self.sf.query_all(flow_query)
        self.metadata['flows'] = result['records']

    def fetch_reports(self):
        """Get all reports"""
        report_query = """
            SELECT Id, Name, Description, FolderName, Format,
                   CreatedDate, LastModifiedDate, LastRunDate,
                   CreatedBy.Name, LastModifiedBy.Name, Owner.Name
            FROM Report
            ORDER BY LastViewedDate DESC NULLS LAST
            LIMIT 500
        """

        result = self.sf.query_all(report_query)
        self.metadata['reports'] = result['records']

    def fetch_validation_rules(self):
        """Get validation rules via Tooling API"""
        vr_query = """
            SELECT Id, ValidationName, EntityDefinition.QualifiedApiName,
                   Active, Description
            FROM ValidationRule
            ORDER BY EntityDefinition.QualifiedApiName, ValidationName
            LIMIT 200
        """

        try:
            result = self.sf.toolingexecute(
                method='GET',
                action='query',
                params={'q': vr_query}
            )
            self.metadata['validation_rules'] = result.get('records', [])
        except Exception as e:
            self.metadata['validation_rules'] = []
            self.metadata['warnings'].append(
                f"ValidationRule query failed: {str(e)}. Try the query in Developer Console or confirm Tooling API access."
            )

    def fetch_apex_classes(self):
        """Get Apex classes"""
        apex_query = """
            SELECT Id, Name, ApiVersion, Status, IsValid, LengthWithoutComments
            FROM ApexClass
            ORDER BY Name
            LIMIT 200
        """

        try:
            result = self.sf.toolingexecute(
                method='GET',
                action='query',
                params={'q': apex_query}
            )
            self.metadata['apex_classes'] = result.get('records', [])
        except Exception as e:
            self.metadata['warnings'].append(f"Error fetching Apex classes: {str(e)}")

    def fetch_users(self):
        """Get active users"""
        user_query = """
            SELECT Id, Name, Username, Email, Profile.Name, IsActive, UserRole.Name
            FROM User
            WHERE IsActive = true
            ORDER BY Name
            LIMIT 50
        """

        result = self.sf.query_all(user_query)
        self.metadata['users'] = result['records']

    def fetch_sample_data(self):
        """Fetch sample records for test prompt generation"""
        sample_data = {}

        # Fetch sample Accounts
        try:
            account_query = "SELECT Id, Name FROM Account ORDER BY LastModifiedDate DESC LIMIT 10"
            result = self.sf.query_all(account_query)
            sample_data['accounts'] = [{'Id': r['Id'], 'Name': r['Name']} for r in result['records']]
        except Exception as e:
            sample_data['accounts'] = []

        # Fetch sample Opportunities
        try:
            opp_query = "SELECT Id, Name, Amount, StageName FROM Opportunity ORDER BY LastModifiedDate DESC LIMIT 10"
            result = self.sf.query_all(opp_query)
            sample_data['opportunities'] = [
                {'Id': r['Id'], 'Name': r['Name'], 'Amount': r.get('Amount'), 'StageName': r.get('StageName')}
                for r in result['records']
            ]
        except Exception as e:
            sample_data['opportunities'] = []

        # Fetch sample records from custom objects
        custom_objects = [name for name, obj in self.metadata['objects'].items() if obj['custom']]

        for obj_name in custom_objects[:5]:  # Limit to first 5 custom objects
            try:
                query = f"SELECT Id, Name FROM {obj_name} ORDER BY LastModifiedDate DESC LIMIT 5"
                result = self.sf.query_all(query)
                sample_data[obj_name] = [{'Id': r['Id'], 'Name': r.get('Name', 'N/A')} for r in result['records']]
            except Exception as e:
                # Skip if object has no Name field or other errors
                pass

        self.metadata['sample_data'] = sample_data

    def analyze_with_claude(self, use_case_context: str = None):
        """Use Claude to analyze metadata and generate insights"""
        # Prepare metadata summary for Claude
        metadata_summary = {
            'org_type': self.metadata['org_info'].get('OrganizationType'),
            'is_sandbox': self.metadata['org_info'].get('IsSandbox'),
            'custom_objects': [
                {'name': name, 'label': obj['label']}
                for name, obj in self.metadata['objects'].items()
                if obj['custom']
            ],
            'total_flows': len(self.metadata['flows']),
            'active_flows': sum(1 for f in self.metadata['flows'] if f.get('IsActive')),
            'inactive_flows': sum(1 for f in self.metadata['flows'] if not f.get('IsActive')),
            'total_reports': len(self.metadata['reports']),
            'validation_rules': len(self.metadata['validation_rules']),
        }

        # Find commission/financial fields
        commission_objects = {}
        for obj_name, obj_data in self.metadata['objects'].items():
            commission_fields = [
                f['name'] for f in obj_data.get('fields', [])
                if any(kw in f['name'].lower() or kw in f['label'].lower()
                      for kw in ['commission', 'premium', 'amount', 'value', 'policy'])
            ]
            if commission_fields:
                commission_objects[obj_name] = commission_fields[:5]  # Limit to 5

        metadata_summary['objects_with_financial_fields'] = commission_objects

        # Create prompt for Claude
        use_case_section = ""
        if use_case_context:
            use_case_section = f"""
**Organization-Specific Use Cases:**
{use_case_context}

Please incorporate these use cases into your analysis and recommendations.
"""

        prompt = f"""You are a Salesforce testing expert. Analyze this Salesforce org metadata and provide:

1. **Org Overview**: Brief summary of the org type and key characteristics
2. **Custom Objects Analysis**: What custom objects exist and what they might be used for
3. **Testing Opportunities**: Specific test scenarios based on the metadata
4. **Prompt Recommendations**: Suggest 5-10 context-aware test prompts that leverage the actual metadata
5. **Challenge Scenarios**: Recommend specific changes to create challenging test conditions

{use_case_section}

Metadata Summary:
{json.dumps(metadata_summary, indent=2)}

Provide your analysis in a structured format."""

        try:
            message = self.claude.messages.create(
                model=self.model_id,
                max_tokens=4096,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = extract_text_from_blocks(message.content)

            self.metadata['claude_analysis'] = {
                'timestamp': utc_now_iso(),
                'model': message.model,
                'analysis': analysis or 'No analysis text returned by Claude.',
                'usage': {
                    'input_tokens': getattr(message.usage, 'input_tokens', None),
                    'output_tokens': getattr(message.usage, 'output_tokens', None)
                }
            }

        except Exception as e:
            suggestions = (
                "Verify ANTHROPIC_API_KEY and model configuration. "
                "Visit https://docs.anthropic.com for the latest model IDs."
            )
            self.metadata['claude_analysis'] = {
                'error': str(e),
                'timestamp': utc_now_iso(),
                'model': self.model_id,
                'suggestions': suggestions
            }
            self.metadata['warnings'].append(
                f"Claude analysis failed: {str(e)}. {suggestions}"
            )

    def extract_all(self, use_case_context: str = None):
        """Main extraction workflow"""
        self.connect()
        self.fetch_org_info()
        self.fetch_all_objects()
        self.fetch_key_object_fields()
        self.fetch_flows()
        self.fetch_reports()
        self.fetch_validation_rules()
        self.fetch_apex_classes()
        self.fetch_users()
        self.fetch_sample_data()

        # Use Claude for analysis
        self.analyze_with_claude(use_case_context)

        return self.metadata

    def close(self):
        """Close connection"""
        # Salesforce connection doesn't need explicit closing
        pass
