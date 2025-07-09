import React from 'react';

// Mock data
const mockFeed = [
  {
    id: '1',
    type: 'email',
    title: 'Superpower Launch Event - April 25th',
    summary: 'Jacob invited you to the superpower launch event in SF next month (April 25, 2025 at 6:00p at Superpower HQ). You offered to co-sponsor and Jacob asked about contribution.',
    tags: ['Email', 'Message'],
    time: '2 hours ago',
  },
  {
    id: '2',
    type: 'document',
    title: 'Q1 Budget Review',
    summary: 'Please find attached the Q1 budget review document that we\'ll be discussing in tomorrow\'s meeting.',
    tags: ['Email', 'Document'],
    time: '5 hours ago',
  },
  {
    id: '3',
    type: 'meeting',
    title: 'Design Team Sync',
    summary: 'We need to finalize the designs for the homepage by the end of the week to meet our timeline.',
    tags: ['Meetings', 'Recording'],
    time: 'Yesterday',
  },
  {
    id: '4',
    type: 'meeting',
    title: 'Engineering Stand-up',
    summary: 'Backend team reported issues with the database performance that need to be addressed.',
    tags: ['Meetings', 'Recording'],
    time: '2 days ago',
  },
  {
    id: '5',
    type: 'spreadsheet',
    title: 'Product Roadmap 2025',
    summary: 'This document outlines our product vision and planned feature releases for the next 12 months.',
    tags: ['Google Drive', 'Spreadsheet'],
    time: '3 days ago',
  },
  {
    id: '6',
    type: 'folder',
    title: 'Marketing Campaign Assets',
    summary: 'Collection of images and copy for our upcoming social media campaign. Please review.',
    tags: ['Google Drive', 'Folder'],
    time: '5 days ago',
  },
  {
    id: '7',
    type: 'email',
    title: 'Client Feedback on Beta Release',
    summary: 'The client has provided some valuable feedback on the beta release which we should incorporate.',
    tags: ['Email', 'Message'],
    time: '1 week ago',
  },
];

interface DataFeedProps {
  onSelect?: (id: string) => void;
}

const DataFeed = ({ onSelect }: DataFeedProps) => (
  <div className="flex-1 flex flex-col overflow-y-auto">
    <div className="p-8 pb-2">
      <h1 className="text-xl font-bold font-mono uppercase tracking-wide mb-1">Data Feed</h1>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 font-mono">Browse and manage your connected information sources</p>
      <div className="flex items-center gap-2 mb-4">
        <input className="w-full border border-[#4a5565] dark:border-zinc-700 rounded px-3 py-2 text-xs bg-white dark:bg-zinc-900 font-mono" placeholder="Search knowledge..." />
        <button className="border border-[#4a5565] dark:border-zinc-700 rounded px-3 py-2 text-xs bg-white dark:bg-zinc-900 flex items-center gap-1 font-mono">
          Date
        </button>
      </div>
      <div className="space-y-4">
        {mockFeed.map(item => (
          <div key={item.id} className="border border-[#4a5565] dark:border-zinc-700 rounded bg-white dark:bg-zinc-900 p-4 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-base font-mono">{item.title}</div>
              <div className="text-xs text-gray-400 font-mono">{item.time}</div>
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 font-mono">{item.summary}</div>
            <div className="flex items-center gap-2 mt-1">
              {item.tags.map(tag => (
                <span key={tag} className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 uppercase font-mono">{tag}</span>
              ))}
            </div>
            <div className="flex justify-end">
              <button className="text-orange-600 text-xs font-semibold flex items-center gap-1 hover:underline font-mono" onClick={() => onSelect && onSelect(item.id)}>
                View <span className="ml-1">→</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default DataFeed; 