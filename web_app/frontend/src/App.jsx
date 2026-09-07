import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Stepper } from './components/Stepper';
import { VideoWorkspace } from './components/VideoWorkspace';
import { VoiceStudio } from './components/VoiceStudio';
import { TranslationEditor } from './components/TranslationEditor';
import { TerminalConsole } from './components/TerminalConsole';
import { MediaCenter } from './components/MediaCenter';

import { usePipelineStatus } from './hooks/usePipelineStatus';
import { runStep, cancelPipeline, getTranscription, getSessions, selectSession } from './services/api';

export default function App() {
  const statusState = usePipelineStatus(3000);
  const [transcriptionData, setTranscriptionData] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState('default');

  const loadSessionsData = async () => {
    try {
      const sData = await getSessions();
      setSessions(sData.sessions || []);
      if (sData.active_session) {
        setActiveSession(sData.active_session);
      }
    } catch (e) {
      console.error('Failed to load sessions', e);
    }
  };

  const loadData = async () => {
    try {
      const data = await getTranscription();
      setTranscriptionData(data);
    } catch (e) {
      console.error('Failed to load transcription data', e);
    }
  };

  useEffect(() => {
    loadSessionsData();
    loadData();
  }, [statusState.status]);

  const handleSelectSession = async (sessionName) => {
    try {
      await selectSession(sessionName);
      setActiveSession(sessionName);
      await loadSessionsData();
      await loadData();
    } catch (e) {
      alert('Failed to switch session: ' + e.message);
    }
  };

  const handleRunAll = async () => {
    try {
      await runStep('all');
    } catch (e) {
      alert('Failed to start pipeline: ' + e.message);
    }
  };

  const handleRunStep = async (stepId) => {
    try {
      await runStep(stepId);
    } catch (e) {
      alert('Failed to start step: ' + e.message);
    }
  };

  const handleCancel = async () => {
    try {
      await cancelPipeline();
    } catch (e) {
      alert('Failed to cancel: ' + e.message);
    }
  };

  return (
    <div className="app-container">
      {/* Navbar */}
      <Navbar
        statusState={statusState}
        sessions={sessions}
        activeSession={activeSession}
        onSelectSession={handleSelectSession}
        onRunAll={handleRunAll}
        onCancel={handleCancel}
      />

      {/* Stepper */}
      <Stepper
        currentStep={statusState.current_step}
        onRunStep={handleRunStep}
        isRunning={statusState.is_running}
      />

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Left Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <VideoWorkspace
            videoUrl={statusState.video_url}
            onUploadSuccess={async () => { await loadSessionsData(); await loadData(); }}
          />
          <VoiceStudio profiles={transcriptionData?.profiles} />
          <TranslationEditor
            translations={transcriptionData?.translations}
            onSaveSuccess={loadData}
          />
        </div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <TerminalConsole />
          <MediaCenter />
        </div>
      </div>
    </div>
  );
}
