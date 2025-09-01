import React from 'react';

// Mock data removed - will use real data from API
const mockFeedDetails: Record<string, unknown> = {};

interface FeedItemDetailProps {
  id: string;
  onBack: () => void;
}

const FeedItemDetail = ({ id, onBack }: FeedItemDetailProps) => {
  const detail = mockFeedDetails[id as keyof typeof mockFeedDetails];
  if (!detail) return <div className="p-8">Not found.</div>;
  
  if (detail.type === 'email') {
    const msg = detail.messages[0];
    return (
      <div className="flex-1 flex flex-col overflow-y-auto scrollbar-hide">
        <div className="p-8 pb-2">
          <button onClick={onBack} className="mb-4 text-xs text-gray-500 hover:underline">&lt; Feed</button>
          <h1 className="text-xl font-bold mb-1">{detail.title}</h1>
          <div className="text-xs text-gray-500 mb-2">Feed &gt; Email &gt; {detail.title}</div>
          <div className="border border-[#4a5565] dark:border-zinc-700 rounded bg-white dark:bg-zinc-900 p-6 mb-4">
            <div className="font-semibold mb-2">Thread Summary</div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">{detail.summary}</div>
            <div className="text-xs mb-2"><b>Next Step:</b> {detail.nextStep}</div>
            <div className="mb-2">
              <input className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-1 text-xs mb-1" value={detail.participants[0]} readOnly />
            </div>
            <div className="text-xs mb-2"><b>Message Summary:</b> {detail.messageSummary}</div>
            <div className="border-t border-[#4a5565] dark:border-zinc-700 my-4"></div>
            <div className="mb-2 text-xs text-gray-500">{msg.date}</div>
            <div className="mb-2 text-xs"><b>From:</b> {msg.from} ({msg.email})</div>
            <div className="mb-2 text-xs"><b>To:</b> {msg.to} <b>CC:</b> {msg.cc}</div>
            <div className="bg-stone-50 dark:bg-zinc-800 rounded p-4 text-xs whitespace-pre-wrap mb-2">{msg.body}</div>
            <div className="mb-2">
              <div className="font-semibold text-xs mb-1">Attachments ({msg.attachments.length})</div>
              <div className="flex gap-2">
                {msg.attachments.map(a => (
                  <div key={a.name} className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-1 text-xs flex items-center gap-2">
                    <span>{a.name}</span>
                    <span className="text-gray-400">{a.size}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-1 text-xs">Extract tasks</button>
              <button className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-1 text-xs">Draft reply</button>
              <button className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-1 text-xs">Summarize follow-ups</button>
            </div>
            <div className="mt-4">
              <input className="w-full border border-[#4a5565] dark:border-zinc-700 rounded px-3 py-2 text-xs bg-white dark:bg-zinc-900" placeholder="Type your question..." />
            </div>
          </div>
        </div>
      </div>
    );
  }
  // Add more types (document, meeting, etc.) as needed
  return <div className="p-8">Detail view for type: {detail.type}</div>;
};

export default FeedItemDetail; 