import { useState, useEffect } from "react";
import "@/App.css";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, TrendingUp, Package, Users, MessageSquare, Sparkles, Clock, AlertCircle } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [storeId, setStoreId] = useState("example-store.myshopify.com");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [exampleQuestions, setExampleQuestions] = useState([]);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchExampleQuestions();
    fetchHistory();
  }, []);

  const fetchExampleQuestions = async () => {
    try {
      const res = await axios.get(`${API}/v1/example-questions`);
      setExampleQuestions(res.data.examples || []);
    } catch (e) {
      console.error("Error fetching examples:", e);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API}/v1/questions/history?limit=10`);
      setHistory(res.data.history || []);
    } catch (e) {
      console.error("Error fetching history:", e);
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim() || !storeId.trim()) {
      setError("Please enter both store ID and question");
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await axios.post(`${API}/v1/questions`, {
        store_id: storeId,
        question: question.trim()
      });
      
      setResponse(res.data);
      fetchHistory(); // Refresh history
    } catch (e) {
      console.error("Error asking question:", e);
      setError(e.response?.data?.detail || "Failed to process question. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (exampleQuestion) => {
    setQuestion(exampleQuestion);
    setResponse(null);
    setError(null);
  };

  const getConfidenceBadgeColor = (confidence) => {
    switch (confidence?.toLowerCase()) {
      case 'high': return 'bg-green-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getCategoryIcon = (category) => {
    if (category.includes('Inventory')) return <Package className="w-4 h-4" />;
    if (category.includes('Sales')) return <TrendingUp className="w-4 h-4" />;
    if (category.includes('Customer')) return <Users className="w-4 h-4" />;
    return <MessageSquare className="w-4 h-4" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Sparkles className="w-10 h-10 text-indigo-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">Shopify AI Analytics</h1>
          </div>
          <p className="text-gray-600 text-lg">
            Ask questions about your store in plain English and get instant insights
          </p>
          <Badge className="mt-2 bg-indigo-100 text-indigo-700 hover:bg-indigo-200" data-testid="mock-data-badge">
            Using Mock Data - Connect your store for real analytics
          </Badge>
        </div>

        <Tabs defaultValue="ask" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 max-w-md mx-auto">
            <TabsTrigger value="ask" data-testid="ask-tab">Ask Question</TabsTrigger>
            <TabsTrigger value="examples" data-testid="examples-tab">Examples</TabsTrigger>
            <TabsTrigger value="history" data-testid="history-tab">History</TabsTrigger>
          </TabsList>

          {/* Ask Question Tab */}
          <TabsContent value="ask" className="space-y-6">
            <Card data-testid="question-input-card">
              <CardHeader>
                <CardTitle>Store Configuration</CardTitle>
                <CardDescription>Enter your Shopify store ID</CardDescription>
              </CardHeader>
              <CardContent>
                <Input
                  data-testid="store-id-input"
                  placeholder="example-store.myshopify.com"
                  value={storeId}
                  onChange={(e) => setStoreId(e.target.value)}
                  className="text-lg"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MessageSquare className="w-5 h-5 mr-2" />
                  Ask Your Question
                </CardTitle>
                <CardDescription>
                  Ask anything about inventory, sales, or customers
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  data-testid="question-input"
                  placeholder="e.g., What were my top 5 selling products last week?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="min-h-[100px] text-lg"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.ctrlKey) {
                      handleAskQuestion();
                    }
                  }}
                />
                <Button
                  data-testid="ask-button"
                  onClick={handleAskQuestion}
                  disabled={loading}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-lg py-6"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5 mr-2" />
                      Get Answer
                    </>
                  )}
                </Button>
                <p className="text-xs text-gray-500 text-center">
                  Tip: Press Ctrl+Enter to submit
                </p>
              </CardContent>
            </Card>

            {/* Error Display */}
            {error && (
              <Alert variant="destructive" data-testid="error-alert">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Response Display */}
            {response && (
              <Card className="border-2 border-indigo-200 bg-indigo-50/50" data-testid="response-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-indigo-900">Analysis Result</CardTitle>
                    <Badge 
                      className={getConfidenceBadgeColor(response.confidence)}
                      data-testid="confidence-badge"
                    >
                      {response.confidence} confidence
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="bg-white p-6 rounded-lg">
                    <p className="text-lg text-gray-800 leading-relaxed" data-testid="answer-text">
                      {response.answer}
                    </p>
                  </div>

                  {response.recommendation && (
                    <Alert className="bg-green-50 border-green-200">
                      <TrendingUp className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-800">
                        <strong>Recommendation:</strong> {response.recommendation}
                      </AlertDescription>
                    </Alert>
                  )}

                  {response.metadata && (
                    <details className="text-xs text-gray-600">
                      <summary className="cursor-pointer font-medium hover:text-gray-900">
                        View Technical Details
                      </summary>
                      <div className="mt-2 bg-gray-100 p-3 rounded space-y-1">
                        <p><strong>Intent:</strong> {response.metadata.intent}</p>
                        <p><strong>Data Points:</strong> {response.metadata.data_points}</p>
                        <p><strong>Query:</strong> {response.metadata.query_executed}</p>
                      </div>
                    </details>
                  )}
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Examples Tab */}
          <TabsContent value="examples" className="space-y-4">
            {exampleQuestions.map((category, idx) => (
              <Card key={idx}>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    {getCategoryIcon(category.category)}
                    <span className="ml-2">{category.category}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {category.questions.map((q, qIdx) => (
                    <Button
                      key={qIdx}
                      variant="outline"
                      className="w-full justify-start text-left h-auto py-3 px-4 hover:bg-indigo-50"
                      onClick={() => handleExampleClick(q)}
                      data-testid={`example-question-${idx}-${qIdx}`}
                    >
                      <MessageSquare className="w-4 h-4 mr-2 flex-shrink-0" />
                      <span className="text-sm">{q}</span>
                    </Button>
                  ))}
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Clock className="w-5 h-5 mr-2" />
                  Recent Questions
                </CardTitle>
                <CardDescription>
                  Your last 10 analytics queries
                </CardDescription>
              </CardHeader>
              <CardContent>
                {history.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No questions asked yet</p>
                ) : (
                  <div className="space-y-3">
                    {history.map((item, idx) => (
                      <div
                        key={idx}
                        className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                        onClick={() => handleExampleClick(item.question)}
                        data-testid={`history-item-${idx}`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <p className="font-medium text-gray-900 flex-1">{item.question}</p>
                          <Badge className={getConfidenceBadgeColor(item.confidence)} variant="secondary">
                            {item.confidence}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 line-clamp-2">{item.answer}</p>
                        <p className="text-xs text-gray-400 mt-2">
                          {new Date(item.timestamp).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Footer */}
        <div className="mt-12 text-center text-sm text-gray-600">
          <p>Powered by AI • ShopifyQL • Real-time Analytics</p>
        </div>
      </div>
    </div>
  );
}

export default App;
