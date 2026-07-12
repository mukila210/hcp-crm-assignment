import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setMode } from '../store/interactionSlice';

export default function ModeToggle() {
  const dispatch = useDispatch();
  const mode = useSelector((s) => s.interaction.mode);
  const isChatActive = mode === 'chat';

  return (
    <div className={`mode-switch ${isChatActive ? 'chat-active' : ''}`}>
      <div className="thumb" />
      <button
        className={!isChatActive ? 'active' : ''}
        onClick={() => dispatch(setMode('form'))}
      >
        Structured Form
      </button>
      <button
        className={isChatActive ? 'active' : ''}
        onClick={() => dispatch(setMode('chat'))}
      >
        Chat with Assistant
      </button>
    </div>
  );
}
