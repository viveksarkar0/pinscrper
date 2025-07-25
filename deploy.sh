#!/bin/bash
# Pinterest Scraper API Deployment Script

set -e

# Configuration
ENVIRONMENT=${1:-production}
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="pinterest-scraper-api"
IMAGE_TAG=${2:-latest}

echo "🚀 Deploying Pinterest Scraper API"
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo "Account ID: $AWS_ACCOUNT_ID"
echo "Image Tag: $IMAGE_TAG"

# Step 1: Build and push Docker image to ECR
echo "📦 Building and pushing Docker image..."

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION || \
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION

# Get ECR login token
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build image
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .

# Tag image for ECR
docker tag $ECR_REPOSITORY:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# Push image
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

echo "✅ Docker image pushed successfully"

# Step 2: Deploy CloudFormation stack
echo "🏗️  Deploying CloudFormation infrastructure..."

aws cloudformation deploy \
  --template-file aws/cloudformation.yml \
  --stack-name $ENVIRONMENT-pinterest-scraper \
  --parameter-overrides Environment=$ENVIRONMENT \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $AWS_REGION

echo "✅ Infrastructure deployed successfully"

# Step 3: Update ECS task definition
echo "📋 Updating ECS task definition..."

# Replace placeholders in task definition
sed "s/ACCOUNT_ID/$AWS_ACCOUNT_ID/g; s/REGION/$AWS_REGION/g" aws/ecs-task-definition.json > /tmp/task-definition.json

# Register new task definition
TASK_DEFINITION_ARN=$(aws ecs register-task-definition \
  --cli-input-json file:///tmp/task-definition.json \
  --region $AWS_REGION \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

echo "✅ Task definition registered: $TASK_DEFINITION_ARN"

# Step 4: Update ECS service
echo "🔄 Updating ECS service..."

CLUSTER_NAME="$ENVIRONMENT-pinterest-cluster"
SERVICE_NAME="pinterest-scraper-api"

# Check if service exists
if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION --query 'services[0].serviceName' --output text 2>/dev/null | grep -q $SERVICE_NAME; then
  # Update existing service
  aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition $TASK_DEFINITION_ARN \
    --region $AWS_REGION
  
  echo "✅ Service updated successfully"
else
  # Create new service
  TARGET_GROUP_ARN=$(aws cloudformation describe-stacks \
    --stack-name $ENVIRONMENT-pinterest-scraper \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`TargetGroup`].OutputValue' \
    --output text)
  
  PRIVATE_SUBNETS=$(aws cloudformation describe-stacks \
    --stack-name $ENVIRONMENT-pinterest-scraper \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnets`].OutputValue' \
    --output text)
  
  SECURITY_GROUP=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$ENVIRONMENT-pinterest-ecs-sg" \
    --region $AWS_REGION \
    --query 'SecurityGroups[0].GroupId' \
    --output text)
  
  aws ecs create-service \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --task-definition $TASK_DEFINITION_ARN \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNETS],securityGroups=[$SECURITY_GROUP],assignPublicIp=DISABLED}" \
    --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=pinterest-scraper-api,containerPort=8000" \
    --health-check-grace-period-seconds 300 \
    --region $AWS_REGION
  
  echo "✅ Service created successfully"
fi

# Step 5: Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."

aws ecs wait services-stable \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region $AWS_REGION

echo "✅ Deployment completed successfully"

# Step 6: Get service endpoints
echo "🌐 Getting service information..."

LOAD_BALANCER_DNS=$(aws cloudformation describe-stacks \
  --stack-name $ENVIRONMENT-pinterest-scraper \
  --region $AWS_REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
  --output text)

echo ""
echo "🎉 Deployment Complete!"
echo "================================"
echo "API Endpoint: http://$LOAD_BALANCER_DNS"
echo "Health Check: http://$LOAD_BALANCER_DNS/health"
echo "API Documentation: http://$LOAD_BALANCER_DNS/docs"
echo ""
echo "To test the API:"
echo "curl -H 'Authorization: Bearer YOUR_API_KEY' http://$LOAD_BALANCER_DNS/health"
echo ""
echo "Don't forget to update your secrets in AWS Secrets Manager:"
echo "- $ENVIRONMENT-pinterest-credentials"
echo "- $ENVIRONMENT-gemini-api-key"
echo "- $ENVIRONMENT-api-key"

# Cleanup
rm -f /tmp/task-definition.json
