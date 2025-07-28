#!/bin/bash

# Deploy the project-onboarding-ai edge function to Supabase
echo "🚀 Deploying project-onboarding-ai edge function..."

# Check if supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI is not installed. Please install it first:"
    echo "npm install -g supabase"
    exit 1
fi

# Deploy the function
supabase functions deploy project-onboarding-ai

echo "✅ Edge function deployed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Add your OpenAI API key to Supabase secrets:"
echo "   supabase secrets set OPENAI_API_KEY=your_openai_api_key_here"
echo ""
echo "2. Test the function by creating a new project in your app"
echo ""
echo "3. Check the function logs if needed:"
echo "   supabase functions logs project-onboarding-ai" 