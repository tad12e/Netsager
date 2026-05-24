import React from 'react';
import { Search } from 'lucide-react';

export default function SearchBar({ value, onChange }) {
  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <div style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }}>
        <Search size={18} />
      </div>
      <input
        type="text"
        placeholder="Type to search..."
        value={value}
        onChange={onChange}
        style={{
          width: '100%',
          padding: '0.8rem 1rem 0.8rem 2.8rem',
          borderRadius: '12px',
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid var(--border-glass)',
          color: 'var(--text-primary)',
          outline: 'none'
        }}
      />
    </div>
  );
}
