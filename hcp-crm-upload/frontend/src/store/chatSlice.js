import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { sendChatTurn, confirmChatInteraction } from '../api/interactionApi';

const initialState = {
  sessionId: crypto.randomUUID(),
  messages: [
    {
      role: 'assistant',
      content:
        "Tell me about the interaction — who you met, what you discussed, and anything you left behind or should follow up on.",
    },
  ],
  draftInteraction: null,
  isReadyToConfirm: false,
  requiresEscalation: false,
  status: 'idle', // idle | sending | confirming
};

export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ message, fieldRepId }, { getState }) => {
    const { sessionId, messages } = getState().chat;
    return await sendChatTurn({
      session_id: sessionId,
      field_rep_id: fieldRepId,
      message,
      history: messages,
    });
  }
);

export const confirmDraft = createAsyncThunk(
  'chat/confirmDraft',
  async ({ hcpId, fieldRepId }, { getState }) => {
    const { sessionId } = getState().chat;
    return await confirmChatInteraction(sessionId, hcpId, fieldRepId);
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    pushUserMessage(state, action) {
      state.messages.push({ role: 'user', content: action.payload });
    },
    resetChat(state) {
      Object.assign(state, { ...initialState, sessionId: crypto.randomUUID() });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.status = 'sending';
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.status = 'idle';
        state.messages.push({ role: 'assistant', content: action.payload.assistant_message });
        state.draftInteraction = action.payload.draft_interaction;
        state.isReadyToConfirm = action.payload.is_ready_to_confirm;
        state.requiresEscalation = action.payload.requires_escalation;
      })
      .addCase(sendMessage.rejected, (state) => {
        state.status = 'idle';
        state.messages.push({
          role: 'assistant',
          content: "Sorry, I couldn't process that — please try again.",
        });
      })
      .addCase(confirmDraft.pending, (state) => {
        state.status = 'confirming';
      })
      .addCase(confirmDraft.fulfilled, (state) => {
        state.status = 'idle';
      });
  },
});

export const { pushUserMessage, resetChat } = chatSlice.actions;
export default chatSlice.reducer;
