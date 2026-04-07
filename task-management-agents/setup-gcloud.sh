#!/bin/bash
set -e

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo "Error: Please set PROJECT_ID environment variable first"
    echo "Run: export PROJECT_ID=your-project-id"
    exit 1
fi

echo "Setting up Google Cloud project: $PROJECT_ID"
gcloud config set project $PROJECT_ID

echo ""
echo "=== Step 1: Enabling APIs ==="
gcloud services enable \
    firestore.googleapis.com \
    run.googleapis.com \
    aiplatform.googleapis.com \
    calendar-json.googleapis.com \
    gmail.googleapis.com \
    iam.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com

echo ""
echo "=== Step 2: Creating Firestore Database ==="
# Check if database exists
if gcloud firestore databases describe --database="(default)" 2>/dev/null; then
    echo "Firestore database already exists"
else
    gcloud firestore databases create --location=us-central1
fi

echo ""
echo "=== Step 3: Creating Service Account ==="
SA_NAME="task-agent-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Create service account if it doesn't exist
if gcloud iam service-accounts describe $SA_EMAIL 2>/dev/null; then
    echo "Service account already exists: $SA_EMAIL"
else
    gcloud iam service-accounts create $SA_NAME \
        --display-name="Task Management Agent"
fi

echo ""
echo "=== Step 4: Granting Permissions ==="
# Firestore access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/datastore.user" \
    --quiet

# Vertex AI access (for Gemini)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/aiplatform.user" \
    --quiet

# Secret Manager access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Service Account: $SA_EMAIL"
echo ""
echo "Next steps:"
echo "1. Create OAuth credentials at: https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
echo "2. Run: ./deploy.sh to deploy to Cloud Run"
