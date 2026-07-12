import React from 'react';
import StructuredForm from './StructuredForm';
import ChatInterface from './ChatInterface';

export default function LogInteractionScreen() {
  return (
    <div className="screen screen-wide">
      <div className="screen-header">
        <h1>Log HCP Interaction</h1>
        <p>
          Fill the form directly, or describe the visit to the assistant on the right —
          it fills the form for you as you talk, and you can correct anything before saving.
        </p>
      </div>

      <div className="dual-pane">
        <div className="pane-form">
          <div className="pane-label">Interaction Details</div>
          <StructuredForm />
        </div>
        <div className="pane-chat">
          <div className="pane-label pane-label-accent">AI Assistant</div>
          <ChatInterface />
        </div>
      </div>
    </div>
  );
}