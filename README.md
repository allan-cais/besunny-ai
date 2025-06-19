# Kirit Askuno

An AI-powered document assistant built with React, TypeScript, and Supabase.

## Features

- **Document Management**: Upload, organize, and search through documents
- **AI Chat Assistant**: Interactive chat interface powered by AI
- **Knowledge Spaces**: Organize documents into logical spaces
- **Receipt Processing**: OCR-powered receipt parsing and analysis
- **Daily Digests**: Automated summaries of your documents
- **Multi-Project Support**: Manage multiple projects with separate document collections

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS
- **Authentication**: Supabase Auth
- **Database**: Supabase (PostgreSQL)
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Icons**: Lucide React

## Project Structure

```
kirit-askuno/
├── public/                       # Static files, index.html
├── src/
│   ├── assets/                   # Logos, icons, etc.
│   │   ├── ui/                   # Inputs, buttons, loaders, modals
│   │   ├── chat/                 # Chat-specific display components
│   │   ├── layout/               # Header, sidebar, nav, shell
│   │   └── tags/                 # Tag selector, chip list, filters
│   ├── features/                 # Feature-level concerns
│   │   ├── auth/                 # Supabase auth hooks and views
│   │   ├── chat/                 # Chat assistant UX
│   │   ├── dashboard/           # Project summary, quick access
│   │   ├── digests/             # Digest history & daily summaries
│   │   ├── documents/           # Document feed / timeline
│   │   ├── spaces/              # Knowledge space browsing
│   │   ├── receipts/            # OCR parsed receipts log
│   │   ├── settings/            # Admin project & user management
│   │   └── upload/              # Manual file ingestion UI
│   ├── lib/                     # Utility functions
│   │   ├── apiClient.ts         # Axios/fetch with baseURL, auth
│   │   ├── supabaseClient.ts    # Supabase client + auth helpers
│   │   ├── embedUtils.ts        # Embed chunk/text helpers
│   │   └── constants.ts         # Enumerations, fixed tag lists
│   ├── pages/                   # Route endpoints
│   ├── providers/               # Global context providers
│   ├── routes/                  # Navigation structure, guards
│   ├── styles/
│   │   └── globals.css
│   ├── types/                   # Shared type definitions
│   └── main.tsx                 # App root
├── docs/                        # UI, UX and project scope documentation
├── package.json
├── tsconfig.json
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Supabase account

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd kirit-askuno
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```env
# Supabase Configuration
VITE_SUPABASE_URL=your_supabase_url_here
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# API Configuration
VITE_API_BASE_URL=http://localhost:3001/api

# N8N Webhook URLs (optional)
VITE_N8N_WEBHOOK_URL=your_n8n_webhook_url_here
```

4. Start the development server:
```bash
npm run dev
```

5. Open your browser and navigate to `http://localhost:5173`

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

### Code Style

This project uses:
- TypeScript for type safety
- ESLint for code linting
- Prettier for code formatting
- Tailwind CSS for styling

### Project Structure Guidelines

- **Components**: Reusable UI components in `src/components/`
- **Features**: Feature-specific logic in `src/features/`
- **Pages**: Route components in `src/pages/`
- **Providers**: Global state management in `src/providers/`
- **Types**: Shared TypeScript interfaces in `src/types/`
- **Utils**: Helper functions in `src/lib/`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@kiritaskuno.com or create an issue in the repository.
