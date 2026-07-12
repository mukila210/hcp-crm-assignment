import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { submitInteraction } from '../api/interactionApi';

const initialState = {
  mode: 'form', // 'form' | 'chat'
  form: {
    hcp_name: '',
    hcp_id: '',
    field_rep_id: '',
    interaction_type: 'in_person_visit',
    interaction_date: new Date().toISOString().slice(0, 16),
    duration_minutes: '',
    topics_discussed: [],
    materials_shared: [],
    samples_dropped: [],
    hcp_sentiment: 'neutral',
    next_best_action: '',
    notes: '',
  },
  submitStatus: 'idle', // idle | loading | succeeded | failed
  error: null,
};

export const submitInteractionForm = createAsyncThunk(
  'interaction/submit',
  async (_, { getState }) => {
    const { form } = getState().interaction;
    return await submitInteraction(form);
  }
);

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    setMode(state, action) {
      state.mode = action.payload;
    },
    updateField(state, action) {
      const { field, value } = action.payload;
      state.form[field] = value;
    },
    addTopic(state, action) {
      if (action.payload && !state.form.topics_discussed.includes(action.payload)) {
        state.form.topics_discussed.push(action.payload);
      }
    },
    removeTopic(state, action) {
      state.form.topics_discussed = state.form.topics_discussed.filter(
        (t) => t !== action.payload
      );
    },
    hydrateFromDraft(state, action) {
      const draft = { ...action.payload };
      if (draft.interaction_date && !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(draft.interaction_date)) {
        delete draft.interaction_date;
      }
      state.form = { ...state.form, ...draft };
    },
    resetForm(state) {
      state.form = initialState.form;
      state.submitStatus = 'idle';
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitInteractionForm.pending, (state) => {
        state.submitStatus = 'loading';
        state.error = null;
      })
      .addCase(submitInteractionForm.fulfilled, (state) => {
        state.submitStatus = 'succeeded';
      })
      .addCase(submitInteractionForm.rejected, (state, action) => {
        state.submitStatus = 'failed';
        state.error = action.error.message;
      });
  },
});

export const {
  setMode,
  updateField,
  addTopic,
  removeTopic,
  hydrateFromDraft,
  resetForm,
} = interactionSlice.actions;

export default interactionSlice.reducer;
