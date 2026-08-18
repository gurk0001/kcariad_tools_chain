import React, { useState, useRef, useEffect } from 'react';
import cariadVideo from './assets/20250911_CARIAD_Invisible_Power_small.mp4';
import ReactMarkdown from 'react-markdown';


// --- Custom Inline SVGs matching the CARIAD Icons in your image ---
const SteeringWheelIcon = () => (
  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#3B29E3" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 2a2 2 0 0 1 2 2v8h8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2h8V4a2 2 0 0 1 2-2z" />
    <path d="M12 12m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />
    <path d="M3 5c1-1 2-1 3-1M21 5c-1-1-2-1-3-1" />
  </svg>
);

const UserCentricIcon = () => (
  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#3B29E3" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 21a6 6 0 0 0-12 0" />
    <circle cx="12" cy="10" r="4" />
    <path d="M3 3l3 3M21 3l-3 3M3 21l3-3M21 21l-3-3" />
    <path d="M12 2v2M12 20v2M2 12h2M20 12h2" />
  </svg>
);

const CloudEcosystemIcon = () => (
  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#3B29E3" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17.5 19A3.5 3.5 0 0 0 21 15.5c0-2.79-2.54-4.5-5-4.5-.48 0-.96.06-1.41.17A5.92 5.92 0 0 0 9 8a6 6 0 0 0-6 6c0 3.31 2.69 6 6 6h8.5z" />
    <path d="M19 16a3 3 0 0 1-3 3H8a4 4 0 0 1 0-8h.4a5 5 0 0 1 9.6 2 3 3 0 0 1 1 3z" />
    <path d="M9 16h6M7 13h4M13 13h4" />
  </svg>
);

const VehiclePlatformIcon = () => (
  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#3B29E3" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3C13 6.8 11.8 6 10.5 6H5c-1.1 0-2 .9-2 2v8c0 .6.4 1 1 1h2" />
    <circle cx="7" cy="17" r="2" />
    <path d="M9 17h6" />
    <circle cx="17" cy="17" r="2" />
    <path d="M14 6V4h3v2M15 4h1" />
  </svg>
);

const PremiumChatIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 13.4876 3.36071 14.891 4 16.1247L3 21L7.87532 20C9.10904 20.6393 10.5124 21 12 21Z" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M8 10H16" strokeLinecap="round" />
    <path d="M8 14H13" strokeLinecap="round" />
  </svg>
);

const PremiumCloseIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

const TrashIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'block' }}>
    <polyline points="3 6 5 6 21 6"></polyline>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
    <line x1="10" y1="11" x2="10" y2="17"></line>
    <line x1="14" y1="11" x2="14" y2="17"></line>
  </svg>
);

function App() {

  // Track tools used dynamically from the response contract payload
  const [activeTools, setActiveTools] = useState([]);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  const [position, setPosition] = useState({ x: window.innerWidth - 100, y: window.innerHeight - 100 });
  const isDragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const buttonRef = useRef(null);

  const [threadId] = useState(() => {
    const saved = localStorage.getItem('chat_thread_id');
    if (saved) return saved;
    const fresh = 'thread_' + Math.random().toString(36).substring(2, 11);
    localStorage.setItem('chat_thread_id', fresh);
    return fresh;
  });

  const chatEndRef = useRef(null);

  useEffect(() => {
    const handleResize = () => {
      setPosition((prev) => ({
        x: Math.min(prev.x, window.innerWidth - 80),
        y: Math.min(prev.y, window.innerHeight - 80)
      }));
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const res = await fetch(`http://localhost:8000/chat/history/${threadId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.history) setMessages(data.history);
        }
      } catch (err) {
        console.error("Error loading chat history:", err);
      }
    };
    fetchChatHistory();
  }, [threadId]);

  useEffect(() => {
    if (isChatOpen) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isChatOpen]);

  const onMouseDown = (e) => {
    if (e.button !== 0) return;
    isDragging.current = false;
    dragStart.current = { x: e.clientX - position.x, y: e.clientY - position.y };
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  const onMouseMove = (e) => {
    isDragging.current = true;
    const newX = Math.max(20, Math.min(e.clientX - dragStart.current.x, window.innerWidth - 80));
    const newY = Math.max(20, Math.min(e.clientY - dragStart.current.y, window.innerHeight - 80));
    setPosition({ x: newX, y: newY });
  };

  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
  };

  const handleButtonClick = () => {
    if (!isDragging.current) {
      setIsChatOpen(!isChatOpen);
    }
  };

  const clearChatHistory = async () => {
    // Prevent clearing if a chat response is currently streaming
    if (loading) return;

    if (!window.confirm("Are you sure you want to clear your conversation history?")) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/chat/history/${threadId}`, {
        method: 'DELETE', // Matches your FastAPI @app.delete decorator
      });

      if (!response.ok) throw new Error('Failed to delete history on server.');

      // 🚀 Crucial: Wipe out your active React UI message state array immediately
      setMessages([]);
      setActiveTools([]);
      console.log("Database history and local UI states cleared successfully.");
    } catch (error) {
      console.error("Error executing chat deletion:", error);
      alert("Could not clear history. Please check your backend connection.");
    } finally {
      setLoading(false);
    }
  };


  // 🎯 UPDATE: Accept an optional string parameter to receive form commands directly
  // 🎯 UPDATE: Added 'formMessageId' to intercept and filter out the form card bubble instantly
  const sendMessage = async (e, forcedMessage = null, formMessageId = null) => {
    if (e) e.preventDefault();

    const messageToSend = forcedMessage || input;
    if (!messageToSend.trim() || loading) return;

    if (!forcedMessage) setInput('');
    setLoading(true);
    setActiveTools([]);

    // 🚀 THE FIX: If formMessageId exists, remove that bubble from the state list immediately!
    setMessages((prev) => {
      // Filter out the old form card, then append the user's fresh parameters command prompt
      const filteredHistory = formMessageId
        ? prev.filter((msg) => msg.id !== formMessageId)
        : prev;

      return [...filteredHistory, { role: 'user', content: messageToSend }];
    });

    const assistantMessageId = 'ai_' + Date.now();
    setMessages((prev) => [...prev, { id: assistantMessageId, role: 'assistant', content: '' }]);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageToSend, thread_id: threadId }),
      });

      if (!response.ok) throw new Error('Backend server connection dropped.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let accumulatedResponse = '';
      let networkBuffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        networkBuffer += decoder.decode(value, { stream: true });
        const parts = networkBuffer.split('\n\n');
        networkBuffer = parts.pop();

        for (const part of parts) {
          const cleanLine = part.trim();
          if (cleanLine.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(cleanLine.slice(6));

              if (parsed.is_complete === false && parsed.ai_response) {
                accumulatedResponse = parsed.ai_response;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId ? { ...msg, content: accumulatedResponse } : msg
                  )
                );
              }

              if (parsed.is_complete === true) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? {
                        ...msg,
                        content: parsed.ai_response || msg.content,
                        custom_type: parsed.custom_type || 'text'
                      }
                      : msg
                  )
                );
                if (parsed.tools_input) setActiveTools(parsed.tools_input);
              }
            } catch (err) {
              console.error('Fragment chunk parsing exception:', err);
            }
          }
        }
      }
    } catch (error) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: '⚠️ Stream connection dropped. Ensure backend context engines are alive.' }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  };



  // --- View Component 1: Interactive Form ---
  const JiraTicketForm = ({ onFormSubmit, loading }) => {
    const [formData, setFormData] = useState({ tool: '', project: '', usecase: '', details: '' });

    const handleSubmit = (e) => {
      if (e) e.preventDefault();
      if (!formData.tool || !formData.project || !formData.usecase) {
        alert("Please fill in Tool, Project, and Usecase fields.");
        return;
      }

      // 🎯 REVERT TO MARKDOWN: Formulate a clean, structured text block
      const markdownPrompt =
        `COMMAND: EXECUTE_JIRA_CREATION\n\n` +
        `* **Tool Name**: ${formData.tool}\n` +
        `* **Project**: ${formData.project}\n` +
        `* **Usecase**: ${formData.usecase}\n` +
        `* **Details**: ${formData.details || 'None'}`;

      onFormSubmit(markdownPrompt);
    };

    return (
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '250px' }}>
        <div style={{ fontSize: '11px', fontWeight: 'bold', letterSpacing: '0.5px', borderBottom: '1px solid rgba(255,255,255,0.15)', paddingBottom: '4px' }}>📋 JIRA PROFILER DISPATCH</div>
        <input type="text" placeholder="Associated Tool" value={formData.tool} onChange={e => setFormData({ ...formData, tool: e.target.value })} style={{ padding: '6px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#1e1e24', color: '#fff', fontSize: '13px' }} />
        <input type="text" placeholder="Target Project" value={formData.project} onChange={e => setFormData({ ...formData, project: e.target.value })} style={{ padding: '6px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#1e1e24', color: '#fff', fontSize: '13px' }} />
        <input type="text" placeholder="Target Usecase" value={formData.usecase} onChange={e => setFormData({ ...formData, usecase: e.target.value })} style={{ padding: '6px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#1e1e24', color: '#fff', fontSize: '13px' }} />
        <textarea placeholder="Additional Details..." value={formData.details} onChange={e => setFormData({ ...formData, details: e.target.value })} rows={2} style={{ padding: '6px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#1e1e24', color: '#fff', fontSize: '13px', resize: 'none' }} />
        <button
          type="submit"
          onClick={(e) => {
            e.preventDefault();
            handleSubmit(e);
          }}
          disabled={loading}
          style={{ padding: '8px', borderRadius: '4px', border: 'none', backgroundColor: '#3B29E3', color: '#fff', fontWeight: 'bold', cursor: 'pointer' }}
        >
          {loading ? "Processing..." : "Submit Verification Fields"}
        </button>
      </form>
    );
  };

  // --- View Component 2: Ticket Summary Status Badge Card ---
  const JiraTicketCard = ({ dataString, onShowPdf }) => {
    try {
      const data = JSON.parse(dataString);
      return (
        <div style={{ background: '#1e293b', borderRadius: '8px', padding: '15px', borderLeft: '4px solid #07a3db', minWidth: '260px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#eef1f6', letterSpacing: '0.5px' }}>🎫 JIRA TICKET </span>
            <span style={{ fontSize: '11px', background: '#07a3db', padding: '2px 6px', borderRadius: '3px', fontWeight: 'bold' }}>{data.ticket_key}</span>
          </div>
          <div style={{ fontSize: '13px', opacity: 0.9 }}>
            <div style={{ margin: '3px 0' }}><b>Project:</b> {data.project}</div>
            <div style={{ margin: '3px 0' }}><b>Engine Tool:</b> {data.tool_name}</div>
            <div style={{ margin: '3px 0' }}><b>Usecase:</b> {data.usecase}</div>
          </div>
          <button onClick={() => onShowPdf(data)} style={{ marginTop: '5px', padding: '6px', borderRadius: '4px', border: 'none', backgroundColor: '#10b981', color: '#fff', fontWeight: 'bold', fontSize: '12px', cursor: 'pointer' }}>
            show more...
          </button>
        </div>
      );
    } catch (e) {
      return <div style={{ fontSize: '13px', color: '#f87171' }}>Parsing issue displaying active ticket context metrics.</div>;
    }
  };

  // --- View Component 3: Tabular PDF Download Interaction Card ---
  const PdfDownloadCard = ({ ticketData }) => {
    const [downloading, setDownloading] = useState(false);

    const handleDownload = async (e) => {
      e.preventDefault();
      if (downloading) return;

      setDownloading(true);
      try {
        // Target endpoint configuration
        const targetUrl = 'http://localhost:8000/api/download/Jira_Report_CARIAD-7733.pdf';
        const response = await fetch(targetUrl, {
          method: 'GET',
          headers: { 'Accept': 'application/pdf' }
        });

        if (!response.ok) throw new Error('Failed to transfer binary data asset from server.');

        // Convert the response into an accessible browser binary reference
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        
        // Inject a virtual DOM node anchor trigger to execute immediate document saving
        const tempAnchor = document.createElement('a');
        tempAnchor.href = blobUrl;
        tempAnchor.download = `Jira_Report_${ticketData.ticket_key || 'CARIAD-7733'}.pdf`;
        document.body.appendChild(tempAnchor);
        tempAnchor.click();
        
        // Clean up memory structures instantly
        document.body.removeChild(tempAnchor);
        window.URL.revokeObjectURL(blobUrl);
      } catch (error) {
        console.error("PDF Download Operation Aborted:", error);
        alert("Could not process binary download file. Ensure system asset server route is healthy.");
      } finally {
        setDownloading(false);
      }
    };

    return (
      <div style={{ background: '#0f172a', borderRadius: '8px', padding: '15px', border: '1px solid #07a3db', minWidth: '260px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#10b981' }}>📄 GENERATED DATA</div>
        <p style={{ margin: 0, fontSize: '13px', opacity: 0.8 }}>The content table manifest for <b>{ticketData.ticket_key}</b> has been formatted securely into a strict grid structure document alignment layout.</p>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', marginTop: '5px', background: '#1e293b' }}>
          <thead>
            <tr style={{ background: '#334155' }}><th style={{ padding: '6px', textAlign: 'left', border: '1px solid #475569' }}>Items</th><th style={{ padding: '6px', textAlign: 'left', border: '1px solid #475569' }}>Value</th></tr>
          </thead>
          <tbody>
            <tr><td style={{ padding: '6px', border: '1px solid #475569' }}>Key</td><td style={{ padding: '6px', border: '1px solid #475569', color: '#3b82f6', fontWeight: 'bold' }}>{ticketData.ticket_key}</td></tr>
            <tr><td style={{ padding: '6px', border: '1px solid #475569' }}>Tool</td><td style={{ padding: '6px', border: '1px solid #475569' }}>{ticketData.tool_name}</td></tr>
            <tr><td style={{ padding: '6px', border: '1px solid #475569' }}>Project</td><td style={{ padding: '6px', border: '1px solid #475569' }}>{ticketData.project}</td></tr>
          </tbody>
        </table>

        <button 
          onClick={handleDownload}
          disabled={downloading}
          style={{ 
            display: 'block', 
            width: '100%',
            padding: '8px', 
            borderRadius: '4px', 
            backgroundColor: '#10b981', 
            color: '#fff', 
            border: 'none',
            textAlign: 'center', 
            fontWeight: 'bold', 
            fontSize: '13px',
            cursor: downloading ? 'not-allowed' : 'pointer',
            opacity: downloading ? 0.6 : 1,
            transition: 'opacity 0.2s'
          }}
        >
          ⇣ Download PDF File
        </button>
      </div>
    );
  };

  return (
    <div style={styles.pageWrapper}>
      {/* Navigation Header */}
      <nav style={styles.navbar}>
        <div style={styles.brandLogo}>CARIAD</div>
        <div style={styles.navLinks}>
          <span style={styles.activeNavLink}>Home</span>
          <span>Company ▾</span>
          <span>Products ▾</span>
          <span>News ▾</span>
          <span>Careers ▾</span>
        </div>
      </nav>

      {/* Main Container */}
      <main style={styles.mainContainer}>
        {/* Left Side Workspace Panel */}
        <div style={{
          ...styles.leftHeroSection,
          width: isChatOpen ? '50%' : '100%'
        }}>
          <div style={styles.contentAndVideoSplit}>
            {/* Top Video Component */}
            <div style={styles.videoColumn}>
              <div style={styles.videoCard}>
                <video style={styles.videoPlayer} controls autoPlay muted loop>
                  <source src={cariadVideo} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              </div>
            </div>

            {/* Middle Main Text Headers */}
            <div style={styles.textColumn}>
              <h1 style={styles.heroHeading}>Code transforming mobility</h1>
              <p style={styles.heroText}>
                At CARIAD, we are shaping automotive software that supports the Volkswagen Group's path to becoming a global tech driver in automotive.
              </p>
              <p style={styles.heroText}>
                Our products already power mobility experiences in millions of vehicles around the world — making mobility safer, more sustainable, and more comfortable for everyone.
              </p>
            </div>

            {/* Bottom Capabilities Feature Grid from Image */}
            <div style={styles.capabilitiesGrid}>
              <div style={styles.gridCard}>
                <div style={styles.iconContainer}><SteeringWheelIcon /></div>
                <p style={styles.gridText}>Automated Driving for enhanced road safety and driving comfort</p>
              </div>
              <div style={styles.gridCard}>
                <div style={styles.iconContainer}><UserCentricIcon /></div>
                <p style={styles.gridText}>User-centric infotainment solutions for more personalized mobility experiences</p>
              </div>
              <div style={styles.gridCard}>
                <div style={styles.iconContainer}><CloudEcosystemIcon /></div>
                <p style={styles.gridText}>A digital ecosystem in and around the car</p>
              </div>
              <div style={styles.gridCard}>
                <div style={styles.iconContainer}><VehiclePlatformIcon /></div>
                <p style={styles.gridText}>Purpose-build vehicle driving platform for energy, body and motion systems</p>
              </div>
            </div>
          </div>
          <div style={styles.decorativeCurve}></div>
        </div>

        {/* Right Side Chat Drawer Window Panel */}
        {isChatOpen && (
          <div style={styles.rightChatSection}>
            <div style={styles.chatHeader}>
              {/* Left Section containing all textual elements */}
            <div style={styles.headerTitleBlock}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#1E293B' }}>Automotive Assistant</h3>
              <span style={styles.threadBadge}>Session: {threadId.substring(7)}</span>
            </div>

            {/* Right Section containing bundled utility buttons positioned at the right edge */}
            <div style={styles.headerActionControlCluster}>
              {messages.length > 0 && (
                <button
                  onClick={clearChatHistory}
                  disabled={loading}
                  style={styles.inlineTrashButton}
                  title="Clear Conversation History"
                >
                  <TrashIcon />
                </button>
              )}
              
              {/* <button onClick={() => setIsChatOpen(false)} style={styles.closePanelButton}>
                <PremiumCloseIcon />
              </button> */}
            </div>
            </div>

            <div style={styles.chatWindow}>
              {messages.length === 0 ? (
                <div style={styles.emptyState}>
                  <p>Welcome to CARIAD Intelligence Framework. Ask your local development agent anything about the mobility software architecture stack.</p>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div key={msg.id || idx} style={{ ...styles.messageWrapper, justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                    <div style={{
                      ...styles.messageBubble,
                      backgroundColor: msg.role === 'user' ? '#FFFFFF' : '#1e1e24',
                      color: msg.role === 'user' ? '#333333' : '#FFFFFF',
                      border: msg.role === 'user' ? '1px solid #E2E8F0' : 'none',
                      borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                      textAlign: 'left'
                    }}>
                      <div style={styles.bubbleRole}>{msg.role === 'user' ? 'Developer' : 'CARIAD Engine'}</div>
                      <div style={styles.bubbleText}>

                        {/* 🎯 SWITCH CASE 1: Render Interactive Input Form */}
                        {msg.custom_type === 'jira_form' || msg.content === 'JIRA_INPUT_FORM' ? (
                          <JiraTicketForm
                            loading={loading}
                            onFormSubmit={(compiledPrompt) => {
                              // 🚀 Direct Call: Triggers your message stream immediately with zero DOM manipulation hacks!
                              sendMessage(null, compiledPrompt, msg.id);
                            }}
                          />

                          /* 🎯 SWITCH CASE 2: Render Verified Ticket Visual Card */
                        ) : msg.custom_type === 'jira_ticket' ? (
                          <JiraTicketCard
                            dataString={msg.content}
                            onShowPdf={(ticketData) => {
                              // Instantly inject a simulated local message type entry to swap view states cleanly
                              setMessages(prev => [...prev, { role: 'assistant', content: JSON.stringify(ticketData), custom_type: 'pdf_download' }]);
                            }}
                          />

                          /* 🎯 SWITCH CASE 3: Render Tabular PDF Download Component Links */
                        ) : msg.custom_type === 'pdf_download' ? (
                          <PdfDownloadCard ticketData={typeof msg.content === 'string' ? JSON.parse(msg.content) : msg.content} />

                          /* 🎯 SWITCH CASE 4: Fallback to Regular Markdown responses */
                        ) : msg.role === 'assistant' ? (
                          <ReactMarkdown
                            components={{
                              ul: ({ node, ...props }) => <ul style={{ margin: '4px 0 12px 0', paddingLeft: '20px', listStyleType: 'disc' }} {...props} />,
                              ol: ({ node, ...props }) => <ol style={{ margin: '4px 0', paddingLeft: '18px', listStyleType: 'circle' }} {...props} />,
                              li: ({ node, ...props }) => <li style={{ marginBottom: '4px', fontSize: '13.5px', lineHeight: '1.4' }} {...props} />,
                              p: ({ node, ...props }) => <p style={{ margin: '0 0 8px 0', lineHeight: '1.4' }} {...props} />
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        ) : (
                          msg.content
                        )}

                        {loading && idx === messages.length - 1 && !msg.content && '▋'}
                      </div>
                    </div>
                  </div>
                ))
              )}
              <div ref={chatEndRef} />
            </div>


            <form onSubmit={sendMessage} style={styles.inputContainer}>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Query vehicle modules, software layers..."
                disabled={loading}
                style={styles.chatInput}
              />
              <button type="submit" disabled={loading || !input.trim()} style={styles.sendButton}>
                {loading ? '...' : 'Send'}
              </button>
            </form>
          </div>
        )}
      </main>

      {/* Movable Trigger FAB Component */}
      <button
        ref={buttonRef}
        onMouseDown={onMouseDown}
        onClick={handleButtonClick}
        style={{
          ...styles.floatingChatButton,
          left: `${position.x}px`,
          top: `${position.y}px`,
          backgroundColor: isChatOpen ? '#0F172A' : '#3B29E3',
          cursor: isDragging.current ? 'grabbing' : 'grab'
        }}
        title={isChatOpen ? "Close Chat" : "Drag to move / Click to chat"}
      >
        {isChatOpen ? <PremiumCloseIcon /> : <PremiumChatIcon />}
      </button>
    </div>
  );
}

// Complete Layout CSS Styles dictionary mappings
const styles = {
  pageWrapper: { position: 'relative', display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#FFFFFF', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', overflow: 'hidden' },
  navbar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 60px', borderBottom: '1px solid #F1F5F9', backgroundColor: '#FFFFFF', zIndex: 10, userSelect: 'none' },
  brandLogo: { fontSize: '24px', fontWeight: '300', letterSpacing: '6px', color: '#1E293B' },
  navLinks: { display: 'flex', gap: '30px', fontSize: '14px', color: '#64748B', cursor: 'pointer' },
  activeNavLink: { color: '#1E293B', fontWeight: '500' },
  mainContainer: { flex: 1, display: 'flex', flexDirection: 'row', overflow: 'hidden', position: 'relative' },

  // Left Panel Setup
  leftHeroSection: { position: 'relative', backgroundColor: '#3B29E3', padding: '40px 50px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', color: '#FFFFFF', overflowY: 'auto', transition: 'width 0.3s ease-in-out' },
  contentAndVideoSplit: { display: 'flex', flexDirection: 'column', width: '100%', gap: '35px', alignItems: 'stretch', zIndex: 2 },
  videoColumn: { width: '100%', display: 'flex', justifyContent: 'center' },
  videoCard: { width: '100%', maxWidth: '500px', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)', backgroundColor: '#000000', display: 'flex' },
  videoPlayer: { width: '100%', height: 'auto', display: 'block', objectFit: 'cover' },
  textColumn: { width: '100%', display: 'flex', flexDirection: 'column', textAlign: 'left' },
  heroHeading: { fontSize: '36px', fontWeight: '500', lineHeight: '1.2', marginBottom: '15px', letterSpacing: '-0.5px' },
  heroText: { fontSize: '14px', lineHeight: '1.6', marginBottom: '12px', opacity: '0.9', fontWeight: '300', maxWidth: '800px' },

  // 4-Column Feature Grid Layout from Image
  capabilitiesGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '20px', marginTop: '10px', backgroundColor: '#FFFFFF', padding: '30px 25px', borderRadius: '16px', boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' },
  gridCard: { display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '15px', padding: '10px' },
  iconContainer: { display: 'flex', alignItems: 'center', justifyContent: 'center', width: '60px', height: '60px', borderRadius: '50%', backgroundColor: '#F0EEFF' },
  gridText: { fontSize: '12.5px', color: '#334155', lineHeight: '1.5', margin: 0, fontWeight: '400' },
  decorativeCurve: { position: 'absolute', bottom: '-80px', left: '40%', width: '220px', height: '220px', borderRadius: '50%', border: '4px solid #10B981', background: 'transparent', clipPath: 'inset(0px 0px 110px 0px)', zIndex: 1 },

  // Right Chat Panel Setup
  rightChatSection: { width: '50%', display: 'flex', flexDirection: 'column', backgroundColor: '#F8FAFC', borderLeft: '1px solid #E2E8F0', zIndex: 5 },
  chatHeader: { 
    display: 'flex', 
    justifyContent: 'space-between', 
    alignItems: 'center', // Keeps alignment clean with multi-line text
    padding: '20px 30px', 
    borderBottom: '1px solid #E2E8F0', 
    backgroundColor: '#FFFFFF', 
    userSelect: 'none' 
  },
  headerTitleBlock: { display: 'flex', flexDirection: 'column', gap: '6px' },
  closePanelButton: { background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4px', borderRadius: '50%' },
  threadBadge: { alignSelf: 'flex-start', fontSize: '11px', textTransform: 'uppercase', background: '#F1F5F9', color: '#64748B', padding: '2px 8px', borderRadius: '20px', fontWeight: '600' },
  chatWindow: { flex: 1, padding: '30px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' },
  emptyState: { display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: '#94A3B8', textAlign: 'center', padding: '0 40px', fontSize: '14px', lineHeight: '1.5' },
  messageWrapper: { display: 'flex', width: '100%' },
  bubbleRole: { fontSize: '11px', fontWeight: '600', opacity: '0.7', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' },
  inputContainer: { display: 'flex', padding: '20px 30px', backgroundColor: '#FFFFFF', borderTop: '1px solid #E2E8F0', gap: '15px' },
  chatInput: { flex: 1, padding: '14px 20px', border: '1px solid #CBD5E1', borderRadius: '30px', fontSize: '14px', outline: 'none', backgroundColor: '#F8FAFC' },
  sendButton: { padding: '0 28px', backgroundColor: '#3B29E3', color: '#FFFFFF', border: 'none', borderRadius: '30px', cursor: 'pointer', fontWeight: '600', fontSize: '14px' },

  // Movable Floating Action Button Style Layout
  floatingChatButton: { position: 'fixed', width: '64px', height: '64px', borderRadius: '50%', color: '#FFFFFF', border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 12px 30px rgba(59, 41, 227, 0.35)', zIndex: 9999, transition: 'background-color 0.2s ease, transform 0.1s ease', userSelect: 'none' },

  bubbleText: {
    fontSize: '14px',
    lineHeight: '1.5',
    margin: 0,
    whiteSpace: 'pre-wrap',
    textAlign: 'left' // <-- Ensure this matches left configuration tracking rules
  },

  messageBubble: {
    maxWidth: '75%',
    padding: '14px 18px',
    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
    textAlign: 'left' // <-- Ensure this is explicitly set to left
  },

   // New unified sub-row alignment rules for the ID badge and Bin icon
  threadBadgeRow: { 
    display: 'flex', 
    alignItems: 'center', 
    gap: '8px' 
  },

  threadBadge: { 
    alignSelf: 'flex-start',
    fontSize: '11px', 
    textTransform: 'uppercase', 
    background: '#F1F5F9', 
    color: '#64748B', 
    padding: '2px 8px', 
    borderRadius: '20px', 
    fontWeight: '600',
    userSelect: 'none'
  },
  // Cleaned padding configurations to ensure symmetric hover highlights
  inlineTrashButton: {
    background: 'none',
    border: 'none',
    color: '#94A3B8',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '8px',
    borderRadius: '50%',
    transition: 'all 0.2s ease',
  },
  // Added custom flex box container to cluster your action controls nicely on the right margin
  headerActionControlCluster: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    alignSelf: 'center' // Vertically centers both buttons relative to the total header height
  },

};

export default App;
