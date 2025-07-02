import React from 'react';

// Mock data for feed item details
const mockFeedDetails = {
  '1': {
    type: 'email',
    title: 'Superpower Launch Event - April 25th',
    summary: 'This is an email thread between Jacob Peters, Sarah Johnson, and others regarding the Superpower Launch Event on April 25, 2025. The discussion covers event details, sponsorship options (Gold: $5,000; Silver: $2,500; Bronze: $1,000), and next steps. The team decides to go with the Gold tier ($5,000) for maximum brand visibility. The latest email requests feedback on project documents by Friday.',
    nextStep: 'No action detected',
    participants: ['Jacob Peters (jacob@superpower.com)'],
    messageSummary: 'Sarah Johnson follows up on a meeting about the Superpower Launch Event, confirms selection of the Gold sponsorship tier ($5,000), and requests feedback on attached documents by Friday.',
    messages: [
      {
        from: 'Sarah Johnson',
        email: 'sarah.johnson@example.com',
        date: 'Mar 18, 2025, 4:27 PM',
        to: 'Jacob Peters',
        cc: 'Marketing Team',
        body: `Hi everyone,\n\nI wanted to follow up on our meeting about the Superpower Launch Event from last week.\nAs discussed, we need to finalize the project scope by the end of this month. We\'re planning to go with the Gold sponsorship tier ($5,000) as it offers the best visibility for our brand.\nPlease review the attached documents and provide your feedback by Friday. Let me know if you have any questions or concerns.\n\nBest regards,\nSarah`,
        attachments: [
          { name: 'marketing_assets.pdf', size: '8.7 MB' },
          { name: 'event_timeline.xlsx', size: '1.2 MB' },
        ],
      },
    ],
  },
  // Add more mock details for other items as needed
};

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
      <div className="flex-1 flex flex-col overflow-y-auto">
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