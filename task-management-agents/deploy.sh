#!/bin/bash
set -e

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo "Error: Please set PROJECT_ID environment variable first"
    echo "Run: export PROJECT_ID=your-project-id"
    exit 1
fi

REGION="${REGION:-us-central1}"
SERVICE_NAME="task-management-agents"
SA_EMAIL="task-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Deploying to Google Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --service-account=$SA_EMAIL \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
    --allow-unauthenticated \
    --memory=1Gi \
    --timeout=300

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Service URL: $SERVICE_URL"
echo ""
echo "Test endpoints:"
echo "  Health check: curl $SERVICE_URL/health"
echo "  API docs: $SERVICE_URL/docs"
echo ""
echo "To restrict access (recommended for production):"
echo "  gcloud run services update $SERVICE_NAME --region=$REGION --no-allow-unauthenticated"
