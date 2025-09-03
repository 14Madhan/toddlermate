import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Heart, Baby, Stethoscope, MapPin, MessageCircle, Clock, Phone, CheckCircle, AlertTriangle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [milestones, setMilestones] = useState({});
  const [symptoms, setSymptoms] = useState({});
  const [hospitals, setHospitals] = useState([]);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [sessionId, setSessionId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [location, setLocation] = useState('');

  useEffect(() => {
    fetchMilestones();
    fetchSymptoms();
    // Generate session ID
    setSessionId(Date.now().toString());
  }, []);

  const fetchMilestones = async () => {
    try {
      const response = await axios.get(`${API}/milestones`);
      setMilestones(response.data);
    } catch (error) {
      console.error('Failed to fetch milestones:', error);
    }
  };

  const fetchSymptoms = async () => {
    try {
      const response = await axios.get(`${API}/symptoms`);
      setSymptoms(response.data);
    } catch (error) {
      console.error('Failed to fetch symptoms:', error);
    }
  };

  const searchHospitals = async () => {
    if (!location.trim()) return;
    
    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/hospitals`, { location });
      setHospitals(response.data);
    } catch (error) {
      console.error('Failed to search hospitals:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sendChatMessage = async () => {
    if (!chatMessage.trim()) return;
    
    try {
      setIsLoading(true);
      const userMessage = { type: 'user', content: chatMessage };
      setChatHistory(prev => [...prev, userMessage]);
      
      const response = await axios.post(`${API}/chat`, {
        message: chatMessage,
        session_id: sessionId
      });
      
      const aiMessage = { type: 'ai', content: response.data.response };
      setChatHistory(prev => [...prev, aiMessage]);
      setChatMessage('');
    } catch (error) {
      console.error('Failed to send chat message:', error);
      const errorMessage = { type: 'ai', content: 'Sorry, I encountered an error. Please try again.' };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  return (
    <div className="App">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="container mx-auto px-6 py-16">
          <div className="hero-content-wrapper">
            <h1 className="hero-title">Welcome to ToddlerMate</h1>
            
            <div className="hero-image">
              <img 
                src="https://images.unsplash.com/photo-1632052999447-e542d08d4f7d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwxfHxwZWRpYXRyaWN8ZW58MHx8fHwxNzU2OTI0NTA0fDA&ixlib=rb-4.1.0&q=85"
                alt="Pediatrician with child"
                className="rounded-xl shadow-lg"
              />
            </div>
            
            <div className="hero-welcome-message">
              <p>
                Welcome to ToddlerMate! We know parenting a toddler can feel overwhelming – one moment they're your little angel, the next they're testing every boundary. Raising a toddler is one of life's greatest adventures.
              </p>
              <p>
                Whether you're celebrating first words, managing meltdowns, or wondering if that cough needs attention – you'll find answers, support, and peace of mind here.
              </p>
            </div>
            
            <div className="hero-features">
              <div className="feature-item">
                <Baby className="feature-icon" />
                <span>Development Tracking</span>
              </div>
              <div className="feature-item">
                <Stethoscope className="feature-icon" />
                <span>Health Guidance</span>
              </div>
              <div className="feature-item">
                <MessageCircle className="feature-icon" />
                <span>AI Assistant</span>
              </div>
              <div className="feature-item">
                <MapPin className="feature-icon" />
                <span>Hospital Locator</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Development Milestones Section */}
      <section className="milestones-section">
        <div className="container mx-auto px-6 py-16">
          <div className="section-header">
            <h2 className="section-title">
              <Baby className="section-icon" />
              Development Milestones by Age
            </h2>
            <p className="section-subtitle">
              Track your child's expected behaviors and development patterns
            </p>
          </div>
          
          <div className="milestones-grid">
            {Object.entries(milestones).map(([key, milestone]) => (
              <Card key={key} className="milestone-card">
                <CardHeader>
                  <CardTitle className="milestone-title">{milestone.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="milestone-list">
                    {milestone.milestones?.map((item, index) => (
                      <div key={index} className="milestone-item">
                        <CheckCircle className="milestone-check" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Health Symptoms Section */}
      <section className="symptoms-section">
        <div className="container mx-auto px-6 py-16">
          <div className="section-header">
            <h2 className="section-title">
              <Stethoscope className="section-icon" />
              Health Symptoms & Home Remedies
            </h2>
            <p className="section-subtitle">
              Common symptoms and when to seek professional care
            </p>
          </div>

          <div className="symptoms-grid">
            {/* Reorder to put Sleep Problems first */}
            {["sleep", "fever", "cough", "stomach"].map((key) => {
              const symptom = symptoms[key];
              if (!symptom) return null;
              
              return (
                <Card key={key} className="symptom-card">
                  <CardHeader>
                    <CardTitle className="symptom-title">{symptom.title}</CardTitle>
                    <CardDescription>{symptom.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="symptom-content">
                    <div className="remedy-section">
                      <h4 className="remedy-title">Home Remedies:</h4>
                      <ul className="remedy-list">
                        {symptom.home_remedies?.map((remedy, index) => (
                          <li key={index} className="remedy-item">{remedy}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="doctor-section">
                      <AlertTriangle className="doctor-icon" />
                      <div>
                        <h4 className="doctor-title">When to see a doctor:</h4>
                        <p className="doctor-text">{symptom.when_to_see_doctor}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Hospital Locator Section */}
      <section className="hospital-section">
        <div className="container mx-auto px-6 py-16">
          <div className="section-header">
            <h2 className="section-title">
              <MapPin className="section-icon" />
              Find Nearby Pediatric Hospitals
            </h2>
            <p className="section-subtitle">
              Get immediate access to child-friendly healthcare facilities in your area
            </p>
          </div>

          <div className="hospital-search">
            <div className="search-container">
              <Input
                type="text"
                placeholder="Enter your city or location..."
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="search-input"
              />
              <Button 
                onClick={searchHospitals} 
                disabled={isLoading}
                className="search-button"
              >
                {isLoading ? 'Searching...' : 'Find Hospitals'}
              </Button>
            </div>

            {hospitals.length > 0 && (
              <div className="hospitals-grid">
                {hospitals.map((hospital) => (
                  <Card key={hospital.id} className="hospital-card">
                    <CardHeader>
                      <CardTitle className="hospital-name">{hospital.name}</CardTitle>
                      <Badge variant="secondary" className="hospital-type">{hospital.type}</Badge>
                    </CardHeader>
                    <CardContent className="hospital-details">
                      <div className="hospital-info">
                        <MapPin className="info-icon" />
                        <span>{hospital.address}</span>
                      </div>
                      {hospital.phone && (
                        <div className="hospital-info">
                          <Phone className="info-icon" />
                          <span>{hospital.phone}</span>
                        </div>
                      )}
                      {hospital.distance && (
                        <div className="hospital-info">
                          <Clock className="info-icon" />
                          <span>{hospital.distance} away</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* AI Chat Section */}
      <section className="chat-section">
        <div className="container mx-auto px-6 py-16">
          <div className="section-header">
            <h2 className="section-title">
              <MessageCircle className="section-icon" />
              Ask Questions & Get AI Answers
            </h2>
            <p className="section-subtitle">
              Get instant, expert guidance on toddler care and development
            </p>
          </div>

          <Card className="chat-container">
            <CardContent className="chat-content">
              <div className="chat-history">
                {chatHistory.length === 0 ? (
                  <div className="chat-placeholder">
                    <MessageCircle className="placeholder-icon" />
                    <p>Ask me anything about toddler care, development milestones, health concerns, or parenting tips!</p>
                  </div>
                ) : (
                  chatHistory.map((message, index) => (
                    <div key={index} className={`chat-message ${message.type}`}>
                      <div className="message-content">{message.content}</div>
                    </div>
                  ))
                )}
              </div>
              
              <Separator className="chat-separator" />
              
              <div className="chat-input-container">
                <Textarea
                  placeholder="Ask your question here..."
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="chat-input"
                  rows={3}
                />
                <Button 
                  onClick={sendChatMessage} 
                  disabled={isLoading || !chatMessage.trim()}
                  className="chat-send-button"
                >
                  {isLoading ? 'Sending...' : 'Send'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container mx-auto px-6 py-8">
          <div className="footer-content">
            <div className="footer-brand">
              <h3 className="footer-title">ToddlerMate</h3>
              <p className="footer-subtitle">Your parenting companion</p>
            </div>
            <div className="footer-contact">
              <p>Got feedback or suggestions?</p>
              <p>Write to us at: <a href="mailto:madhanit45@gmail.com" className="footer-email">madhanit45@gmail.com</a></p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;