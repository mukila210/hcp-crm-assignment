import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  updateField,
  addTopic,
  removeTopic,
  submitInteractionForm,
  resetForm,
} from '../store/interactionSlice';

const INTERACTION_TYPES = [
  ['in_person_visit', 'In-Person Visit'],
  ['virtual_call', 'Virtual Call'],
  ['phone_call', 'Phone Call'],
  ['email', 'Email'],
  ['conference', 'Conference'],
  ['sample_drop', 'Sample Drop'],
];

export default function StructuredForm() {
  const dispatch = useDispatch();
  const form = useSelector((s) => s.interaction.form);
  const submitStatus = useSelector((s) => s.interaction.submitStatus);
  const [topicDraft, setTopicDraft] = useState('');

  const onChange = (field) => (e) =>
    dispatch(updateField({ field, value: e.target.value }));

  const handleAddTopic = (e) => {
    e.preventDefault();
    if (topicDraft.trim()) {
      dispatch(addTopic(topicDraft.trim()));
      setTopicDraft('');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(submitInteractionForm());
  };

  return (
    <form className="card" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="hcp_name">HCP Name</label>
        <input
          id="hcp_name"
          placeholder="e.g. Dr. Ananya Rao"
          value={form.hcp_name}
          onChange={onChange('hcp_name')}
        />
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor="hcp_id">HCP ID</label>
          <input
            id="hcp_id"
            className="mono"
            placeholder="e.g. HCP-04213"
            value={form.hcp_id}
            onChange={onChange('hcp_id')}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="field_rep_id">Field Rep ID</label>
          <input
            id="field_rep_id"
            className="mono"
            placeholder="e.g. REP-1029"
            value={form.field_rep_id}
            onChange={onChange('field_rep_id')}
            required
          />
        </div>
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor="interaction_type">Interaction Type</label>
          <select
            id="interaction_type"
            value={form.interaction_type}
            onChange={onChange('interaction_type')}
          >
            {INTERACTION_TYPES.map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="interaction_date">Date &amp; Time</label>
          <input
            id="interaction_date"
            type="datetime-local"
            value={form.interaction_date}
            onChange={onChange('interaction_date')}
          />
        </div>
      </div>

      <div className="field">
        <label htmlFor="topics">Topics Discussed</label>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            id="topics"
            placeholder="e.g. Drug X Phase III efficacy data"
            value={topicDraft}
            onChange={(e) => setTopicDraft(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddTopic(e)}
          />
          <button className="btn-ghost" onClick={handleAddTopic} type="button">Add</button>
        </div>
        <div className="tag-input-chips">
          {form.topics_discussed.map((t) => (
            <span className="chip" key={t}>
              {t}
              <button type="button" onClick={() => dispatch(removeTopic(t))}>×</button>
            </span>
          ))}
        </div>
      </div>

      <div className="field">
        <label htmlFor="sentiment">HCP Sentiment</label>
        <select id="sentiment" value={form.hcp_sentiment} onChange={onChange('hcp_sentiment')}>
          <option value="positive">Positive</option>
          <option value="neutral">Neutral</option>
          <option value="negative">Negative</option>
        </select>
      </div>

      <div className="field">
        <label htmlFor="next_action">Next Best Action</label>
        <input
          id="next_action"
          placeholder="e.g. Send updated dosing chart by Friday"
          value={form.next_best_action}
          onChange={onChange('next_best_action')}
        />
      </div>

      <div className="field">
        <label htmlFor="notes">Additional Notes</label>
        <textarea
          id="notes"
          rows={3}
          value={form.notes}
          onChange={onChange('notes')}
        />
      </div>

      <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
        <button className="btn-primary" type="submit" disabled={submitStatus === 'loading'}>
          {submitStatus === 'loading' ? 'Saving…' : 'Save Interaction'}
        </button>
        <button className="btn-ghost" type="button" onClick={() => dispatch(resetForm())}>
          Clear
        </button>
      </div>

      {submitStatus === 'succeeded' && (
        <div className="draft-banner" style={{ marginTop: 16 }}>
          Interaction logged successfully.
        </div>
      )}
    </form>
  );
}
