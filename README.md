# Salesforce Test Prompt Generator

A beautiful, modular web application that generates intelligent, context-aware test prompts for Salesforce organizations using Claude AI.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green)
![React](https://img.shields.io/badge/React-18.2.0-blue)

## ✨ Features

- **Secure Credential Handling**: Salesforce credentials processed in-memory only, never stored
- **Intelligent Use Case Detection**: Automatically identifies test scenarios from your org
- **Customizable Prompt Generation**: Control the number of prompts per use case
- **Multiple Export Formats**: Download results as JSON or CSV
- **Beautiful UI**: Modern, minimal design inspired by premium SaaS applications
- **Real-time Metadata Extraction**: Fetches live data from Salesforce orgs
- **Claude AI Integration**: Leverages Claude for context-aware prompt generation

## 🏗️ Architecture

### Backend (FastAPI)
- **Modular Services**: Separated concerns for metadata extraction, test preparation, and prompt generation
- **RESTful API**: Clean, well-documented endpoints
- **Session Management**: Temporary in-memory storage with automatic cleanup
- **CSV/JSON Export**: Flexible output formats

### Frontend (React + Vite)
- **Three-Step Workflow**:
  1. **Connect**: Enter Salesforce credentials and use case description
  2. **Configure**: Adjust number of prompts for each identified use case
  3. **Download**: Choose format and download results
- **Tailwind CSS**: Beautiful, responsive design
- **Real-time Feedback**: Loading states and error handling

## 📁 Project Structure

```
Clientell-Promper/
├── backend/
│   ├── services/
│   │   ├── metadata_extractor.py    # Salesforce metadata extraction
│   │   ├── test_preparer.py         # Test preparation planning
│   │   └── prompt_generator.py      # Prompt generation logic
│   ├── main.py                       # FastAPI application
│   ├── models.py                     # Pydantic models
│   └── utils.py                      # Utility functions
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Step1Credentials.jsx # Step 1: Credentials
│   │   │   ├── Step2UseCases.jsx    # Step 2: Configure use cases
│   │   │   └── Step3Download.jsx    # Step 3: Download results
│   │   ├── App.jsx                  # Main application
│   │   ├── main.jsx                 # Entry point
│   │   └── index.css                # Tailwind styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Salesforce account (Sandbox or Production)
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Installation

#### 1. Clone the repository

```bash
git clone <repository-url>
cd Clientell-Promper
```

#### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
cd backend
python main.py
```

The backend will run on `http://localhost:8000`

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will run on `http://localhost:3000`

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.env` file in the project root:

```env
# Salesforce (optional - can be entered in UI)
SF_USERNAME=your-username@example.com
SF_PASSWORD=your-password
SF_SECURITY_TOKEN=your-security-token
SF_DOMAIN=test  # or 'login' for production

# Anthropic (optional - can be entered in UI)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

## 📖 Usage

### Step 1: Connect to Salesforce

1. Enter your Salesforce credentials:
   - Username
   - Password
   - Security Token
   - Environment (Sandbox/Production)

2. Enter your Anthropic API key

3. Describe your testing use cases in the text box or upload a file

4. Click "Connect & Extract Metadata"

### Step 2: Configure Use Cases

1. Review the automatically identified use cases
2. Adjust the number of prompts for each use case (1-20)
3. Review the total prompt count
4. Click "Generate Test Prompts"

### Step 3: Download Results

1. Preview the generated prompts
2. Choose your preferred format:
   - **JSON**: Complete metadata, best for automation
   - **CSV**: Spreadsheet format, best for manual review
3. Click "Download" to get your file
4. Session data is automatically cleaned up after download

## 🔐 Security

- **No Credential Storage**: All credentials are processed in-memory only
- **Session Cleanup**: Data is automatically deleted after download
- **HTTPS Recommended**: Use HTTPS in production
- **API Key Protection**: Keys are never logged or stored

## 📊 Output Formats

### JSON Output
```json
{
  "metadata_summary": {
    "org_info": {...},
    "custom_objects": [...],
    "total_flows": 15
  },
  "claude_analysis": {...},
  "test_prompts": [
    {
      "use_case": "uc1",
      "prompt": "Show all insurance policies for Acme Corp",
      "expected_object": "Insurance_Policy__c",
      "difficulty": "medium",
      "challenges": ["disambiguation", "field-selection"],
      "expected_behavior": "Query Insurance_Policy__c WHERE Account.Name = 'Acme Corp'"
    }
  ]
}
```

### CSV Output
```csv
use_case,prompt,expected_object,difficulty,challenges,expected_behavior
uc1,"Show all insurance policies for Acme Corp",Insurance_Policy__c,medium,"disambiguation; field-selection","Query Insurance_Policy__c..."
```

## 🛠️ Development

### Backend Development

```bash
# Run with auto-reload
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Building for Production

```bash
# Backend: Use gunicorn or uvicorn
pip install gunicorn
gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Frontend
cd frontend
npm run build
```

## 📝 API Endpoints

### POST `/api/step1-extract`
Extract Salesforce metadata and identify use cases

**Request:**
```json
{
  "credentials": {
    "username": "user@example.com",
    "password": "password",
    "security_token": "token",
    "domain": "test",
    "anthropic_api_key": "sk-ant-..."
  },
  "use_case_description": "Test insurance policies and commissions"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "use_cases": [...],
  "metadata_summary": {...}
}
```

### POST `/api/step2-generate-prompts`
Generate prompts for configured use cases

**Request:**
```json
{
  "session_id": "uuid",
  "use_cases": [
    {"id": "uc1", "name": "Query Policies", "prompt_count": 5}
  ]
}
```

### GET `/api/download/{session_id}/{format}`
Download results in specified format (json/csv)

### DELETE `/api/cleanup/{session_id}`
Clean up session data

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Claude AI](https://www.anthropic.com/)
- UI inspired by modern SaaS designs
- Salesforce integration via [simple-salesforce](https://github.com/simple-salesforce/simple-salesforce)

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Made with ❤️ for Salesforce testing**
