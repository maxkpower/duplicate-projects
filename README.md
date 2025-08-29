# Bitwarden Project Duplicator

A Python script to duplicate Bitwarden Secrets Manager projects with all their associated secrets. This tool is useful for creating project templates, staging environments, or backup copies of your Bitwarden projects.

## Features

- ✅ **Complete Project Duplication**: Copies all secrets from source project to new project
- ✅ **Secret Naming**: Optional prefix for secret names in the duplicated project
- ✅ **Environment Templates**: Predefined templates for common deployment scenarios
- ✅ **Batch Environment Creation**: Create multiple environment projects at once
- ✅ **Progress Tracking**: Real-time progress bar showing duplication status
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Secure Authentication**: Uses Bitwarden access tokens for secure API access
- ✅ **Cross-Platform**: Works on Windows, macOS, and Linux

## Prerequisites

- Python 3.7 or higher
- Bitwarden account with Secrets Manager access
- Organization ID and Access Token from Bitwarden

## Installation

1. **Clone or download** this repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the project directory with your Bitwarden credentials:

```env
# Required: Your Bitwarden organization ID
ORGANIZATION_ID=your_org_id_here

# Required: Your Bitwarden access token
ACCESS_TOKEN=your_access_token_here

# Optional: Path to store Bitwarden state (default: ./bw_state)
STATE_FILE=./bw_state

# Optional: Custom API URL (default: https://api.bitwarden.com)
API_URL=https://api.bitwarden.com

# Optional: Custom Identity URL (default: https://identity.bitwarden.com)
IDENTITY_URL=https://identity.bitwarden.com

# Optional: Environment Templates (comma-separated, format: env:prefix:description)
# Examples:
# ENVIRONMENT_TEMPLATES=dev:dev:Development,staging:stg:Staging,prod:prod:Production
# ENVIRONMENT_TEMPLATES=dev,staging,prod,qa,uat
ENVIRONMENT_TEMPLATES=dev:dev:Development,staging:stg:Staging,prod:prod:Production,test:test:Testing,qa:qa:Quality Assurance,uat:uat:User Acceptance Testing
```

### Getting Your Credentials

1. **Organization ID**: Found in your Bitwarden organization settings
2. **Access Token**: Generate in Bitwarden → Secrets Manager → Machine Accounts → Access Tokens

## Usage

Run the script:

```bash
python duplicate_project.py
```

The script will present a menu with the following options:

1. **Duplicate single project** - Copy one project with optional secret prefix
2. **Create environment templates** - Create multiple environment projects at once
3. **Show available environment templates** - Display configured templates
4. **Exit** - Quit the script

### Single Project Duplication
1. Authenticate with Bitwarden using your access token
2. Enter the source project UUID
3. Enter the new project name
4. **Optionally** enter a prefix for secret names
5. Show a summary and ask for confirmation
6. Duplicate the project with all its secrets
7. Display real-time progress for each secret

### Example Output

```
=== Bitwarden Project Duplicator ===

2025-08-29 23:18:38,666 - INFO - Successfully authenticated with Bitwarden

Options:
1. Duplicate single project
2. Create environment templates (dev, staging, prod, etc.)
3. Show available environment templates
4. Exit

Select an option (1-4): 2

Enter the source project UUID: eea3936e-4067-4f9a-bb59-b12b0139efbb
Enter the base project name (e.g., 'backend' for 'backend-dev', 'backend-staging'): backend

🌍 Available Environment Templates:
--------------------------------------------------
  dev      → dev_ (prefix)
           Development environment

  staging  → stg_ (prefix)
           Staging environment

  prod     → prod_ (prefix)
           Production environment

Enter the environments to create (comma-separated, e.g., 'dev,staging,prod'):
Available: dev, staging, prod, test, qa, uat
Environments: dev,staging,prod

📋 Ready to create environment projects:
   Source Project ID: eea3936e-4067-4f9a-bb59-b12b0139efbb
   Base Project Name: backend
   Environments: dev, staging, prod
   Projects to create:
     - backend-dev (prefix: dev_)
     - backend-staging (prefix: stg_)
     - backend-prod (prefix: prod_)

Proceed with creation? (y/N): y

🌍 Creating 3 environment projects...

   [1/3] Creating dev environment...
      Project: backend-dev
      Prefix: dev_
      🔄 Duplicating 10 secrets...
         [1/10] 'DB_PORT' → 'dev_DB_PORT'... ✅
         [2/10] 'DB_USER' → 'dev_DB_USER'... ✅
         ...

   [2/3] Creating staging environment...
      Project: backend-staging
      Prefix: stg_
      🔄 Duplicating 10 secrets...
         [1/10] 'DB_PORT' → 'stg_DB_PORT'... ✅
         [2/10] 'DB_USER' → 'stg_DB_USER'... ✅
         ...

   [3/3] Creating prod environment...
      Project: backend-prod
      Prefix: prod_
      🔄 Duplicating 10 secrets...
         [1/10] 'DB_PORT' → 'prod_DB_PORT'... ✅
         [2/10] 'DB_USER' → 'prod_DB_USER'... ✅
         ...

🎉 Environment creation completed!
   Created 3 environment projects:
   ✅ dev: backend-dev (10/10 secrets)
   ✅ staging: backend-staging (10/10 secrets)
   ✅ prod: backend-prod (10/10 secrets)
```

## How It Works

1. **Authentication**: Uses your access token to authenticate with Bitwarden's API
2. **Project Discovery**: Retrieves the source project details
3. **Secret Retrieval**: Gets all secrets in your organization and filters by project association
4. **Project Creation**: Creates a new project with the specified name
5. **Secret Duplication**: Copies each secret to the new project, preserving:
   - Secret value
   - Notes
   - Project association
   - **Secret key** (with optional prefix if specified)

### Secret Naming with Prefixes

When duplicating a project, you can optionally add a prefix to all secret names. This is useful for:

- **Environment separation**: `prod_`, `staging_`, `dev_`
- **Project identification**: `backend_`, `frontend_`, `api_`
- **Version control**: `v2_`, `legacy_`, `new_`

**Example**: If you prefix with `staging_`, a secret named `DB_PASSWORD` becomes `staging_DB_PASSWORD` in the new project.

## Environment Templates

The script includes predefined environment templates for common deployment scenarios. You can customize these templates in your `.env` file.

### Default Templates

- **dev** → `dev_` prefix (Development environment)
- **staging** → `staging_` prefix (Staging/QA environment)
- **prod** → `prod_` prefix (Production environment)
- **test** → `test_` prefix (Testing environment)
- **qa** → `qa_` prefix (Quality Assurance environment)
- **uat** → `uat_` prefix (User Acceptance Testing environment)

### Customizing Templates

Add `ENVIRONMENT_TEMPLATES` to your `.env` file to customize the available templates:

```env
# Format: environment:prefix:description
ENVIRONMENT_TEMPLATES=dev:dev:Development,staging:stg:Staging,prod:prod:Production

# Or just environment names (uses environment name as prefix)
ENVIRONMENT_TEMPLATES=dev,staging,prod,qa,uat
```

### Batch Environment Creation

Use the "Create environment templates" option to create multiple environment projects at once:

1. Choose option 2 from the main menu
2. Enter your source project UUID
3. Enter a base project name (e.g., "backend")
4. Select environments to create (e.g., "dev,staging,prod")
5. The script will create:
   - `backend-dev` with `dev_` prefixed secrets
   - `backend-staging` with `stg_` prefixed secrets
   - `backend-prod` with `prod_` prefixed secrets

## Troubleshooting

### Common Issues

- **Authentication Failed**: Check your `ACCESS_TOKEN` and `ORGANIZATION_ID` in the `.env` file
- **No Secrets Found**: Verify the source project UUID is correct and contains secrets
- **Permission Denied**: Ensure your access token has the necessary permissions

### Debug Mode

The script includes comprehensive logging. Check the console output for detailed information about each step.

## Security Notes

- **Never commit** your `.env` file to version control
- **Keep your access token secure** - it provides access to your Bitwarden organization
- **Use environment variables** in production environments
- **Rotate access tokens** regularly for security

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify your Bitwarden credentials
3. Ensure you have the necessary permissions in your Bitwarden organization
4. Check the [Bitwarden SDK documentation](https://github.com/bitwarden/sdk-sm) for API details