import React, { useEffect, useRef, useState } from 'react';
import { Amplify, Auth } from 'aws-amplify';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import axios from 'axios';
import './App.css';

const loadConfig = () => {
  if (window.REACT_APP_CONFIG) {
    return {
      apiEndpoint: window.REACT_APP_CONFIG.apiEndpoint,
      userPoolId: window.REACT_APP_CONFIG.userPoolId,
      userPoolClientId: window.REACT_APP_CONFIG.userPoolClientId,
      region: window.REACT_APP_CONFIG.region,
    };
  }

  return {
    apiEndpoint: process.env.REACT_APP_API_ENDPOINT || 'YOUR_API_ENDPOINT',
    userPoolId: process.env.REACT_APP_USER_POOL_ID || 'YOUR_USER_POOL_ID',
    userPoolClientId: process.env.REACT_APP_USER_POOL_CLIENT_ID || 'YOUR_USER_POOL_CLIENT_ID',
    region: process.env.REACT_APP_REGION || 'us-east-1',
  };
};

const config = loadConfig();

Amplify.configure({
  Auth: {
    region: config.region,
    userPoolId: config.userPoolId,
    userPoolWebClientId: config.userPoolClientId,
  },
});

function ChatInterface({ signOut, user }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    setMessages((previous) => [...previous, { role: 'user', content: userMessage }]);
    setLoading(true);
    setError(null);

    try {
      const session = await Auth.currentSession();
      const idToken = session.getIdToken().getJwtToken();

      const response = await axios.post(
        config.apiEndpoint,
        {
          message: userMessage,
          conversationHistory: messages,
        },
        {
          headers: {
            Authorization: idToken,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.data.success) {
        setMessages((previous) => [
          ...previous,
          { role: 'assistant', content: response.data.response },
        ]);
      } else {
        setError('応答の取得に失敗しました。');
      }
    } catch (requestError) {
      console.error('API error:', requestError);
      setError(`エラーが発生しました: ${requestError.message}`);
    } finally {
      setLoading(false);
    }
  };

  const clearConversation = () => {
    setMessages([]);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Bedrock LLM チャットボット</h1>
        <div className="header-buttons">
          <button className="clear-button" onClick={clearConversation}>
            会話をクリア
          </button>
          <button className="logout-button" onClick={signOut}>
            ログアウト ({user.username})
          </button>
        </div>
      </header>

      <main className="chat-container">
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <h2>Bedrock Chatbotへようこそ</h2>
              <p>メッセージを入力して、AIとの会話を始めてください。</p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-content">
                  {message.content.split('\n').map((line, lineIndex) => (
                    <p key={lineIndex}>{line}</p>
                  ))}
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="message assistant loading">
              <div className="typing-indicator">
                <span />
                <span />
                <span />
              </div>
            </div>
          )}

          {error && <div className="error-message">{error}</div>}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="input-form">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="メッセージを入力..."
            disabled={loading}
            aria-label="チャットメッセージ"
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                handleSubmit(event);
              }
            }}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            送信
          </button>
        </form>
      </main>

      <footer>
        <p>Powered by Amazon Bedrock</p>
      </footer>
    </div>
  );
}

function App() {
  return (
    <Authenticator>
      {({ signOut, user }) => <ChatInterface signOut={signOut} user={user} />}
    </Authenticator>
  );
}

export default App;
