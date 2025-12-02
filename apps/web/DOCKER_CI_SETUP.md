# Docker CI/CD Setup Guide

This guide explains how to set up the automated Docker release pipeline for withoutbg.

## Overview

This project has **TWO** release workflows:

### 1. 🤖 Automated Release (Recommended)
**Triggers:** Automatically on every push to `main`  
**How:** Uses Conventional Commits to determine version  
**See:** [AUTOMATED_RELEASES.md](AUTOMATED_RELEASES.md) for details

### 2. 🎯 Manual Release
**Triggers:** Manually via GitHub Actions UI  
**How:** Uses current version from `pyproject.toml`  
**See:** This guide below

---

## Automated Release System

The system automatically:
- 🔍 Analyzes commit messages
- 📊 Determines version bump (MAJOR/MINOR/PATCH)
- 📝 Updates version files
- 🏷️ Creates git tags
- 🐳 Builds multi-platform Docker images
- 📦 Pushes to Docker Hub
- 🎉 Creates GitHub Release

**For full details, see [AUTOMATED_RELEASES.md](AUTOMATED_RELEASES.md)**

---

## Manual Release Workflow (This Guide)

The manual workflow (`docker-release.yml`) allows you to:
- **Trigger releases on-demand** via GitHub Actions UI
- **Choose version bump type**: auto, major, minor, patch, or none
- **Test builds** with dry run mode (no push)
- **Downloads ONNX model files** from S3
- **Builds multi-platform Docker images** (AMD64 + ARM64)
- **Auto-updates version files** and creates git tags
- **Pushes to Docker Hub** as `withoutbg/app`

### Version Bump Options

| Option | Behavior | Example |
|--------|----------|---------|
| `auto` | Analyzes commits since last tag | feat: → 1.1.0, fix: → 1.0.1 |
| `major` | Breaking changes | 1.2.3 → 2.0.0 |
| `minor` | New features | 1.2.3 → 1.3.0 |
| `patch` | Bug fixes | 1.2.3 → 1.2.4 |
| `none` | No version bump | Uses current tag version |

## Prerequisites

### 1. GitHub Secrets & Variables Configuration

You need to add the following to your GitHub repository (Settings → Secrets and variables → Actions):

#### Required Secrets (Secrets tab):

| Secret Name | Description | Value |
|-------------|-------------|-------|
| `DOCKERHUB_TOKEN` | Docker Hub access token | See instructions below |
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 | Your AWS IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 | Your AWS IAM user secret key |

#### Required Variables (Variables tab):

| Variable Name | Description | Value |
|---------------|-------------|-------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | `withoutbg` |

### 2. Docker Hub Access Token

Create a personal access token for GitHub Actions:

1. Go to [Docker Hub Security Settings](https://hub.docker.com/settings/security)
2. Click **"New Access Token"**
3. Configure:
   - **Description:** `github-actions-withoutbg`
   - **Access permissions:** `Read, Write, Delete`
4. Click **"Generate"**
5. **Copy the token immediately** (you won't see it again)
6. Add to GitHub Secrets as `DOCKERHUB_TOKEN`

### 3. AWS IAM User Setup

Create an IAM user with S3 read permissions for the model files:

#### Option A: Using AWS Console

1. Go to [IAM Users](https://console.aws.amazon.com/iam/home#/users)
2. Click **"Add users"**
3. User name: `github-actions-withoutbg`
4. Select **"Access key - Programmatic access"**
5. Click **"Next: Permissions"**
6. Click **"Attach policies directly"**
7. Click **"Create policy"** → JSON tab
8. Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadModelsFromS3",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::withoutbg-focus",
        "arn:aws:s3:::withoutbg-focus/*"
      ]
    }
  ]
}
```

9. Name the policy: `withoutbg-s3-models-readonly`
10. Complete user creation
11. **Save the Access Key ID and Secret Access Key**
12. Add both to GitHub Secrets

#### Option B: Using AWS CLI

```bash
# Create IAM policy
aws iam create-policy \
  --policy-name withoutbg-s3-models-readonly \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowReadModelsFromS3",
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:ListBucket"],
        "Resource": [
          "arn:aws:s3:::withoutbg-focus",
          "arn:aws:s3:::withoutbg-focus/*"
        ]
      }
    ]
  }'

# Create IAM user
aws iam create-user --user-name github-actions-withoutbg

# Attach policy to user
aws iam attach-user-policy \
  --user-name github-actions-withoutbg \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/withoutbg-s3-models-readonly

# Create access key
aws iam create-access-key --user-name github-actions-withoutbg
```

## S3 Bucket Configuration

The workflow expects model files at the root of the `withoutbg-focus` bucket in `eu-central-1`:

```
s3://withoutbg-focus/
├── depth_anything_v2_vits_slim.onnx
├── focus_matting_1.0.0.onnx
├── focus_refiner_1.0.0.onnx
└── isnet.onnx
```

### Upload Model Files to S3

```bash
cd /path/to/withoutbg

aws s3 cp models/checkpoints/depth_anything_v2_vits_slim.onnx s3://withoutbg-focus/ --region eu-central-1
aws s3 cp models/checkpoints/focus_matting_1.0.0.onnx s3://withoutbg-focus/ --region eu-central-1
aws s3 cp models/checkpoints/focus_refiner_1.0.0.onnx s3://withoutbg-focus/ --region eu-central-1
aws s3 cp models/checkpoints/isnet.onnx s3://withoutbg-focus/ --region eu-central-1
```

Verify files are uploaded:

```bash
aws s3 ls s3://withoutbg-focus/ --region eu-central-1
```

## Usage

### Manual Release Options

#### Option 1: Auto Version Bump (Recommended)

Analyzes commits since last release and auto-detects version bump:

1. **Trigger the workflow**:
   - Go to [GitHub Actions](https://github.com/YOUR_ORG/withoutbg/actions)
   - Select **"Docker Release (Manual)"** workflow
   - Click **"Run workflow"**
   - **Version bump type**: `auto`
   - **Dry run**: `false`
   - Click **"Run workflow"**

2. **What happens**:
   - Checks commits since last tag
   - `feat:` commits → MINOR bump (1.0.0 → 1.1.0)
   - `fix:` commits → PATCH bump (1.0.0 → 1.0.1)
   - `feat!:` commits → MAJOR bump (1.0.0 → 2.0.0)
   - Updates version files, creates tag, builds & pushes Docker images

#### Option 2: Specific Version Bump

Force a specific version bump type:

1. Go to GitHub Actions → "Docker Release (Manual)" workflow
2. Click "Run workflow"
3. Choose **Version bump type**:
   - `major` - Breaking changes (1.2.3 → 2.0.0)
   - `minor` - New features (1.2.3 → 1.3.0)
   - `patch` - Bug fixes (1.2.3 → 1.2.4)
4. Click "Run workflow"

#### Option 3: Rebuild Current Version

Rebuild Docker images without changing version:

1. Go to GitHub Actions → "Docker Release (Manual)" workflow
2. Click "Run workflow"
3. **Version bump type**: `none`
4. Click "Run workflow"

This rebuilds and pushes the current tagged version.

### Testing Before Release (Dry Run)

To test the build without pushing to Docker Hub:

1. Go to GitHub Actions → "Docker Release (Manual)" workflow
2. Click "Run workflow"
3. **Version bump type**: Choose any
4. **Dry run**: `true` ✓
5. Click "Run workflow"

This will:
- Calculate what version would be released
- Download models from S3
- Build the Docker image for both platforms
- Test the image locally
- **NOT** update version files
- **NOT** create git tags
- **NOT** push to Docker Hub

## What the Workflow Does

1. **Extract Version**: Reads version from `apps/web/backend/pyproject.toml`
2. **Download Models**: Fetches ONNX files from S3 bucket
3. **Setup Buildx**: Configures multi-platform Docker builds
4. **Local Test**: Builds and tests image on AMD64
5. **Multi-platform Build**: Builds for AMD64 and ARM64
6. **Tag & Push**: Creates semantic version tags and pushes to Docker Hub

## Expected Build Times

- **First build**: 10-20 minutes (no cache)
- **Subsequent builds**: 3-5 minutes (with cache)
- **Dry run**: 5-10 minutes (faster, no push)

## Available Tags After Release

After releasing version `1.2.3`, users can pull:

| Tag | Command | Purpose |
|-----|---------|---------|
| `latest` | `docker run -p 80:80 withoutbg/app:latest` | Always newest |
| `1.2.3` | `docker run -p 80:80 withoutbg/app:1.2.3` | Exact version |
| `1.2` | `docker run -p 80:80 withoutbg/app:1.2` | Latest patch |
| `1` | `docker run -p 80:80 withoutbg/app:1` | Latest minor |

## Troubleshooting

### "AWS S3 Access Denied"

Check:
- AWS credentials are correctly set in GitHub Secrets
- IAM user has `s3:GetObject` and `s3:ListBucket` permissions
- Bucket name is `withoutbg-focus`
- Region is `eu-central-1`

### "Docker Hub Authentication Failed"

Check:
- `DOCKERHUB_USERNAME` variable is set to `withoutbg` (in Variables tab)
- `DOCKERHUB_TOKEN` secret is a valid access token (not password)
- Token has `Read, Write, Delete` permissions

### "Health Check Failed"

The workflow tests the built image before pushing. If this fails:
- Check backend application logs in the workflow
- Ensure all model files downloaded successfully
- Verify Dockerfile is correct

### "Build Takes Too Long"

First builds take longer. To speed up:
- Ensure GitHub Actions cache is enabled (it is by default)
- Subsequent builds will use cached layers
- Consider using dry run for testing

## Monitoring

### View Workflow Status

- Go to [GitHub Actions](https://github.com/YOUR_ORG/withoutbg/actions)
- Click on the workflow run
- Monitor each step's progress

### View Published Images

- Docker Hub: https://hub.docker.com/r/withoutbg/app
- Check platforms: `docker manifest inspect withoutbg/app:latest`

## Security Best Practices

1. **Rotate Access Tokens**: Rotate Docker Hub and AWS tokens periodically
2. **Least Privilege**: AWS IAM user has read-only S3 access
3. **Secret Management**: Never commit secrets to the repository
4. **Audit**: Review GitHub Actions logs regularly

## Additional Resources

- [AUTOMATED_RELEASES.md](AUTOMATED_RELEASES.md) - Automated release system guide
- [Commit Convention Guide](../.github/COMMIT_CONVENTION.md) - How to write commit messages
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Buildx Documentation](https://docs.docker.com/build/buildx/)

