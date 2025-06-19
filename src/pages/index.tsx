import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function IndexPage() {
  const navigate = useNavigate();

  return (
    <div style={{ 
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '2rem',
      background: 'linear-gradient(to bottom right, #EEF2FF, #E0E7FF)'
    }}>
      <h1 style={{
        fontSize: '4rem',
        fontWeight: 'bold',
        color: '#111827'
      }}>
        askUNO
      </h1>
      <button
        onClick={() => navigate('/dashboard')}
        style={{
          padding: '0.75rem 2rem',
          backgroundColor: '#2563EB',
          color: 'white',
          fontWeight: '500',
          borderRadius: '0.5rem',
          cursor: 'pointer',
          border: 'none',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
        }}
      >
        Login
      </button>
    </div>
  );
} 