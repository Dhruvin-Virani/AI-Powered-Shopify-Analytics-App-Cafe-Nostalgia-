# AI-Powered Shopify Analytics App

## 🚀 Overview

A mini AI-powered analytics application that connects to Shopify stores, accepts natural language questions about inventory, sales, and customers, and returns business-friendly insights powered by AI.

### Key Features

✅ **Natural Language Processing** - Ask questions in plain English
✅ **AI-Powered Agent** - Intelligent workflow: Intent Classification → ShopifyQL Generation → Execution → Explanation
✅ **ShopifyQL Integration** - Automatically generates and executes analytics queries
✅ **Business-Friendly Answers** - Converts technical data into actionable insights
✅ **Question History** - Track all analytics queries with confidence scores
✅ **Mock Shopify Data** - Realistic sample data for testing (200 orders, 10 products)
✅ **Modern UI** - Clean React interface with Tailwind CSS and shadcn/ui components

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     React Frontend                      │
│  - Question Input Interface                             │
│  - Results Display with Confidence Scores               │
│  - Example Questions & History                          │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend                        │
│  POST /api/v1/questions                                 │
│  ├─ Input Validation                                    │
│  ├─ Request Logging                                     │
│  └─ Response Formatting                                 │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              AI Agent Service                           │
│  Step 1: Intent Classification                          │
│  Step 2: ShopifyQL Generation                          │
│  Step 3: Query Execution                               │
│  Step 4: Result Explanation                            │
└──────┬──────────────────────────────┬──────────────────┘
       │                              │
   ┌───▼───┐                    ┌─────▼──────┐
   │  LLM  │                    │  Shopify   │
   │Service│                    │  Service   │
   │(Gemini│                    │ (Mock Data)│
   │ /GPT) │                    └────────────┘
   └───────┘
```

### Component Breakdown

#### 1. **FastAPI Backend** (`/app/backend`)
- **Main API**: Handles HTTP requests, validation, and response formatting
- **Agent Service**: Orchestrates the complete AI workflow
- **LLM Service**: Manages AI model interactions (Gemini/OpenAI)
- **Shopify Service**: Handles data queries (currently using mock data)

#### 2. **React Frontend** (`/app/frontend`)
- Clean, modern UI for asking questions
- Real-time results with confidence indicators
- Example questions organized by category
- Question history with timestamps

#### 3. **MongoDB Database**
- Stores question logs with metadata
- Tracks confidence scores and timestamps
- Enables conversation history

---

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+ and Yarn
- MongoDB (included in the environment)
- Google Gemini API Key or OpenAI API Key

---

## 🛠️ Setup Instructions

### 1. Backend Setup

```bash
cd /app/backend

# Install Python dependencies
pip install -r requirements.txt
```
Create .env in /backend/
**Add your API key to `/backend/.env`:**

```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"

# Add ONE of the following:
GEMINI_API_KEY=your_gemini_key_here
# OR
OPENAI_API_KEY=your_openai_key_here
```

**Get API Keys:**
- **Gemini**: https://aistudio.google.com/apikey (Free tier available)
- **OPENAI**: https://platform.openai.com/api-keys

### 2. Frontend Setup

```bash
cd /app/frontend

# Install dependencies
yarn install

# Frontend .env is already configured
# No changes needed to /frontend/.env
```
```bash

yarn start
#or
npm start

```


**Services:**
- Backend: http://localhost:8001
- Frontend: http://localhost:3000
- MongoDB: mongodb://localhost:27017

---

## 🎯 Usage Guide

### Example Questions You Can Ask

**Inventory Management:**
- "How many units of Product X will I need next month?"
- "Which products are likely to go out of stock in 7 days?"
- "Show me products with low inventory levels"
- "How much inventory should I reorder based on last 30 days sales?"

**Sales Analytics:**
- "What were my top 5 selling products last week?"
- "What was my total revenue in the last 30 days?"
- "Which products generated the most revenue this month?"
- "Show me sales trends for the past week"

**Customer Insights:**
- "Which customers placed repeat orders in the last 90 days?"
- "Who are my top spending customers?"
- "How many repeat customers do I have?"

---

#### 1. Ask Question (Main Analytics Endpoint)

```http
POST /api/v1/questions
Content-Type: application/json

{
  "store_id": "example-store.myshopify.com",
  "question": "What were my top 5 selling products last week?"
}
```

**Response:**
```json
{
  "answer": "Based on the last 7 days, your top 5 selling products are: Wireless Headphones (45 units), Smart Watch (32 units), Phone Case (28 units), Laptop Stand (24 units), and USB-C Cable (22 units). Wireless Headphones are your clear bestseller.",
  "confidence": "high",
  "recommendation": "Consider restocking Wireless Headphones as they're selling quickly.",
  "metadata": {
    "intent": "sales",
    "query_executed": "SELECT product_title, SUM(quantity) AS units_sold FROM line_items WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) GROUP BY product_title ORDER BY units_sold DESC LIMIT 5",
    "data_points": 5,
    "store_id": "example-store.myshopify.com",
    "using_mock_data": true
  }
}
```

#### 2. Get Question History

```http
GET /api/v1/questions/history?store_id=example-store.myshopify.com&limit=50
```

**Response:**
```json
{
  "history": [
    {
      "id": "abc-123",
      "store_id": "example-store.myshopify.com",
      "question": "What were my top 5 selling products last week?",
      "answer": "Based on the last 7 days...",
      "confidence": "high",
      "timestamp": "2025-01-15T10:30:00Z",
      "metadata": {...}
    }
  ],
  "count": 1
}
```

#### 3. Get Example Questions

```http
GET /api/v1/example-questions
```

**Response:**
```json
{
  "examples": [
    {
      "category": "Inventory Management",
      "questions": [
        "How many units of Product X will I need next month?",
        "Which products are likely to go out of stock in 7 days?"
      ]
    }
  ]
}
```

#### 4. Health Check

```http
GET /api/
```

**Response:**
```json
{
  "message": "Shopify AI Analytics API",
  "version": "1.0.0"
}
```

---

## 🤖 AI Agent Workflow

The agent follows a 4-step intelligent workflow:

### Step 1: Intent Classification
```python
Input: "What were my top 5 selling products last week?"

LLM Analyzes:
- Intent: sales
- Time Period: last week (7 days)
- Metrics: [top products, quantity sold]
- Confidence: high
```

### Step 2: ShopifyQL Generation
```python
LLM Generates:
{
  "query": "SELECT product_title, SUM(quantity) AS units_sold 
            FROM line_items 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) 
            GROUP BY product_title 
            ORDER BY units_sold DESC 
            LIMIT 5",
  "explanation": "Query to find top 5 products by quantity sold in last 7 days",
  "data_source": "orders"
}
```

### Step 3: Query Execution
```python
Shopify Service Executes:
- Parses query patterns
- Filters mock data (or queries real Shopify API)
- Returns structured results

Results: [
  {"product_title": "Wireless Headphones", "units_sold": 45},
  {"product_title": "Smart Watch", "units_sold": 32},
  ...
]
```

### Step 4: Business Explanation
```python
LLM Converts to Natural Language:
"Based on the last 7 days, your top 5 selling products are: 
Wireless Headphones (45 units), Smart Watch (32 units)...

Recommendation: Consider restocking Wireless Headphones."
```

---

## 🧪 Testing

### Manual Testing with cURL

```bash
# Test health endpoint
curl http://localhost:8001/api/

# Test analytics question
curl -X POST http://localhost:8001/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "test-store.myshopify.com",
    "question": "What were my top 5 selling products last week?"
  }' | jq

# Get question history
curl http://localhost:8001/api/v1/questions/history?limit=10 | jq

# Get example questions
curl http://localhost:8001/api/v1/example-questions | jq
```

### Frontend Testing

1. Open the application in your browser
2. Enter store ID (default: example-store.myshopify.com)
3. Click on example questions or type your own
4. View results with confidence scores
5. Check history tab for past queries

---

## 📁 Project Structure

```
/app/
├── backend/
│   ├── server.py                 # Main FastAPI application
│   ├── services/
│   │   ├── agent_service.py      # AI Agent orchestration
│   │   ├── llm_service.py        # LLM integration (Gemini/OpenAI)
│   │   └── shopify_service.py    # Shopify data handling (mock)
│   ├── requirements.txt          # Python dependencies
│   └── .env                      # Environment variables
│
├── frontend/
│   ├── src/
│   │   ├── App.js                # Main React component
│   │   ├── index.js              # Entry point
│   │   ├── components/ui/        # UI components (shadcn)
│   │   └── lib/utils.js          # Utility functions
│   ├── package.json              # Node dependencies
│   └── .env                      # Frontend config
│
└── README.md                     # This file
```

---

## 🔧 Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB with Motor (async driver)
- **LLM Integration**: Gemini / GPT-5-mini
- **AI Models**: Google Gemini 2.5 Flash / OpenAI GPT-5-mini

### Frontend
- **Framework**: React 19
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **HTTP Client**: Axios

### Infrastructure
- **Process Manager**: Supervisor
- **Reverse Proxy**: Nginx (handled by platform)

---

## 🔍 Mock Data Details

The application includes realistic mock Shopify data:

**Products (10):**
- Wireless Headphones, Smart Watch, Phone Case, Laptop Stand, USB-C Cable
- Bluetooth Speaker, Portable Charger, Wireless Mouse, Keyboard, Monitor
- Each with inventory levels and prices

**Orders (200):**
- Generated over last 90 days
- 5 mock customers
- Random quantities and products
- Realistic order patterns

**To connect real Shopify store:**
1. Implement OAuth authentication
2. Replace mock data with Shopify API calls
3. Update `shopify_service.py` with real API endpoints

---

