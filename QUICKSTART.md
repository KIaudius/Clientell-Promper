# Quick Start Guide

Get your Salesforce Test Prompt Generator running in 5 minutes!

## Prerequisites

- Python 3.9+ installed
- Node.js 18+ installed
- Salesforce account credentials
- Anthropic API key

## Installation & Setup

### 1. Install Backend Dependencies

```bash
# From project root
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 3. Start the Backend Server

```bash
cd backend
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Keep this terminal running!

### 4. Start the Frontend (New Terminal)

```bash
cd frontend
npm run dev
```

You should see:
```
  ➜  Local:   http://localhost:3000/
```

### 5. Open Your Browser

Navigate to: **http://localhost:3000**

## Using the Application

### Step 1: Connect
1. Enter your Salesforce credentials
2. Enter your Anthropic API key
3. Describe your testing scenarios
4. Click "Connect & Extract Metadata"

### Step 2: Configure
1. Review the identified use cases
2. Adjust prompt counts (default is 3 per use case)
3. Click "Generate Test Prompts"

### Step 3: Download
1. Preview your generated prompts
2. Choose JSON or CSV format
3. Click "Download"

## Example Use Case Description

```
We need to test the following scenarios:
1. Querying insurance policies by account name
2. Calculating total commission for agents
3. Creating new opportunities with validation
4. Generating monthly sales reports
5. Tracking policy renewals
```

## Troubleshooting

### Port Already in Use
If port 8000 or 3000 is already in use:

**Backend:**
```bash
python main.py --port 8001
```

**Frontend:**
Update `frontend/vite.config.js`:
```js
server: {
  port: 3001,  // Change to any available port
  ...
}
```

### Connection Errors
- Verify Salesforce credentials are correct
- Check security token is up-to-date
- Ensure you selected the correct environment (Sandbox/Production)

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt
cd frontend && npm install
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check the API documentation at `http://localhost:8000/docs`
- Explore the generated prompts and test them with your AI agent

## Need Help?

- Check existing issues on GitHub
- Review the API docs at `/docs`
- Ensure all prerequisites are installed

---

Happy Testing! 🚀
