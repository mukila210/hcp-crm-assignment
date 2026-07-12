import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendMessage, confirmDraft, pushUserMessage } from '../store/chatSlice';
import { hydrateFromDraft } from '../store/interactionSlice';

export default function ChatInterface() {
  const dispatch = useDispatch();
  const { messages, status, isReadyToConfirm, requiresEscalation, draftInteraction } =
    useSelector((s) => s.chat);
  const [input, setInput] = useState('');
  const [fieldRepId, setFieldRepId] = useState('REP-1029');
  const [hcpId, setHcpId] = useState('');
  const logRef = useRef(null);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || status === 'sending') return;
    const text = input.trim();
    dispatch(pushUserMessage(text));
    setInput('');
    const result = await dispatch(sendMessage({ message: text, fieldRepId }));
    if (result.payload?.draft_interaction) {
      dispatch(hydrateFromDraft(result.payload.draft_interaction));
    }
  };

  const handleConfirm = () => {
    if (!hcpId) return;
    dispatch(confirmDraft({ hcpId, fieldRepId }));
  };

  return (
    <div className="card">
      <div className="field-row" style={{ marginBottom: 16 }}>
        <div className="field">
          <label>HCP ID</label>
          <input
            className="mono"
            placeholder="e.g. HCP-04213"
            value={hcpId}
            onChange={(e) => setHcpId(e.target.value)}
          />
        </div>
        <div className="field">
          <label>Field Rep ID</label>
          <input
            className="mono"
            value={fieldRepId}
            onChange={(e) => setFieldRepId(e.target.value)}
          />
        </div>
      </div>

      <div className="chat-shell">
        <div className="chat-log" ref={logRef}>
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              {m.role === 'assistant' && <div className="badge">AI Assistant</div>}
              {m.content}
            </div>
          ))}
          {status === 'sending' && (
            <div className="msg assistant">
              <div className="badge">AI Assistant</div>
              …
            </div>
          )}
        </div>

        <form className="chat-input-row" onSubmit={handleSend}>
          <input
            placeholder="Describe the interaction…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button className="btn-primary" type="submit">Send</button>
        </form>
      </div>

      {requiresEscalation && (
        <div className="escalation-banner">
          This conversation mentions a potential adverse event. It will be routed to
          Pharmacovigilance/Medical Affairs for review once saved.
        </div>
      )}

      {isReadyToConfirm && draftInteraction && (
        <div className="draft-banner">
          <span>The assistant has enough detail to log this interaction.</span>
          <button
            className="btn-ghost"
            style={{ background: '#fff' }}
            onClick={handleConfirm}
            disabled={!hcpId || status === 'confirming'}
          >
            {status === 'confirming' ? 'Saving…' : 'Confirm & Save'}
          </button>
        </div>
      )}
    </div>
  );
}