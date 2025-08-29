#!/usr/bin/env python3
"""
Bitwarden Project Duplicator

This script duplicates a Bitwarden project with all its secrets.
It prompts the user for the source project UUID and new project name.
"""

import logging
import os
import sys
from typing import List, Optional
from dotenv import load_dotenv
from bitwarden_sdk import BitwardenClient, DeviceType, client_settings_from_dict

class BitwardenProjectDuplicator:
    def __init__(self):
        """Initialize the Bitwarden client and load environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Validate required environment variables
        self.organization_id = os.getenv("ORGANIZATION_ID")
        self.access_token = os.getenv("ACCESS_TOKEN")
        self.state_path = os.getenv("STATE_FILE", "./bw_state")
        
        if not self.organization_id:
            raise ValueError("ORGANIZATION_ID environment variable is required")
        if not self.access_token:
            raise ValueError("ACCESS_TOKEN environment variable is required")
        
        # Create the BitwardenClient
        self.client = BitwardenClient(
            client_settings_from_dict(
                {
                    "apiUrl": os.getenv("API_URL", "https://api.bitwarden.com"),
                    "deviceType": DeviceType.SDK,
                    "identityUrl": os.getenv("IDENTITY_URL", "https://identity.bitwarden.com"),
                    "userAgent": "Python Project Duplicator",
                }
            )
        )
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Load environment templates from .env or use defaults
        self.environment_templates = self._load_environment_templates()

    def _load_environment_templates(self) -> dict:
        """Load environment templates from .env file or return defaults."""
        templates = {}
        
        # Try to load from environment variables
        env_templates = os.getenv("ENVIRONMENT_TEMPLATES")
        if env_templates:
            try:
                # Parse comma-separated environment:prefix:description format
                for template in env_templates.split(","):
                    parts = template.strip().split(":")
                    if len(parts) >= 2:
                        env_name = parts[0].strip()
                        prefix = parts[1].strip()
                        description = parts[2].strip() if len(parts) > 2 else f"{env_name.title()} environment"
                        templates[env_name] = {"prefix": prefix, "description": description}
                    elif len(parts) == 1:
                        # Just environment name, use default prefix
                        env_name = parts[0].strip()
                        templates[env_name] = {"prefix": env_name, "description": f"{env_name.title()} environment"}
                
                if templates:
                    self.logger.info(f"Loaded {len(templates)} environment templates from .env")
                    return templates
            except Exception as e:
                self.logger.warning(f"Failed to parse ENVIRONMENT_TEMPLATES from .env: {e}")
        
        # Fallback to default templates
        default_templates = {
            "dev": {"prefix": "dev", "description": "Development environment"},
            "staging": {"prefix": "staging", "description": "Staging/QA environment"},
            "prod": {"prefix": "prod", "description": "Production environment"},
            "test": {"prefix": "test", "description": "Testing environment"},
            "qa": {"prefix": "qa", "description": "Quality Assurance environment"},
            "uat": {"prefix": "uat", "description": "User Acceptance Testing environment"}
        }
        
        self.logger.info("Using default environment templates")
        return default_templates

    def authenticate(self) -> bool:
        """Authenticate with Bitwarden using the access token."""
        try:
            self.client.auth().login_access_token(self.access_token, self.state_path)
            self.logger.info("Successfully authenticated with Bitwarden")
            return True
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False

    def get_project(self, project_id: str) -> Optional[dict]:
        """Retrieve a project by its ID."""
        try:
            response = self.client.projects().get(project_id)
            if response.success:
                return response.data
            else:
                self.logger.error(f"Failed to retrieve project: {response.error_message}")
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving project {project_id}: {e}")
            return None

    def get_project_secrets(self, project_id: str) -> List[dict]:
        """Retrieve all secrets associated with a project."""
        try:
            all_secrets_response = self.client.secrets().list(self.organization_id)
            
            if not all_secrets_response.success:
                self.logger.error(f"Failed to retrieve secrets: {all_secrets_response.error_message}")
                return []
            
            # Filter secrets that belong to the specified project
            project_secrets = []
            for secret in all_secrets_response.data.data:
                secret_detail_response = self.client.secrets().get(secret.id)
                if secret_detail_response.success:
                    secret_detail = secret_detail_response.data
                    if hasattr(secret_detail, 'project_ids') and project_id in secret_detail.project_ids:
                        project_secrets.append(secret_detail)
                    elif hasattr(secret_detail, 'project_id') and str(secret_detail.project_id) == str(project_id):
                        project_secrets.append(secret_detail)
                
            return project_secrets
        except Exception as e:
            self.logger.error(f"Error retrieving secrets for project {project_id}: {e}")
            return []

    def create_project(self, project_name: str) -> Optional[dict]:
        """Create a new project."""
        try:
            response = self.client.projects().create(self.organization_id, project_name)
            if response.success:
                self.logger.info(f"Created new project: {project_name} (ID: {response.data.id})")
                return response.data
            else:
                self.logger.error(f"Failed to create project: {response.error_message}")
                return None
        except Exception as e:
            self.logger.error(f"Error creating project {project_name}: {e}")
            return None

    def duplicate_secret(self, secret: dict, new_project_id: str, secret_prefix: str = None) -> bool:
        """Duplicate a secret to the new project."""
        try:
            # Apply prefix to secret key if provided
            new_secret_key = f"{secret_prefix}_{secret.key}" if secret_prefix else secret.key
            
            response = self.client.secrets().create(
                self.organization_id,
                new_secret_key,
                secret.value,
                secret.note,
                [new_project_id]
            )
            
            if response.success:
                return True
            else:
                self.logger.error(f"Failed to duplicate secret {secret.key}: {response.error_message}")
                return False
        except Exception as e:
            self.logger.error(f"Error duplicating secret {secret.key}: {e}")
            return False

    def duplicate_project(self, source_project_id: str, new_project_name: str, secret_prefix: str = None) -> bool:
        """Duplicate a project with all its secrets."""
        self.logger.info(f"Starting duplication of project {source_project_id}")
        
        # Get source project
        source_project = self.get_project(source_project_id)
        if not source_project:
            self.logger.error("Source project not found or inaccessible")
            return False
        
        self.logger.info(f"Found source project: {source_project.name}")
        
        # Get project secrets
        secrets = self.get_project_secrets(source_project_id)
        self.logger.info(f"Found {len(secrets)} secrets in source project")
        
        # Create new project
        new_project = self.create_project(new_project_name)
        if not new_project:
            return False
        
        # Duplicate all secrets with progress bar
        success_count = 0
        total_secrets = len(secrets)
        
        if total_secrets > 0:
            print(f"\n🔄 Duplicating {total_secrets} secrets...")
            for i, secret in enumerate(secrets, 1):
                new_key = f"{secret_prefix}_{secret.key}" if secret_prefix else secret.key
                print(f"   [{i}/{total_secrets}] Duplicating '{secret.key}' → '{new_key}'...", end=" ")
                if self.duplicate_secret(secret, new_project.id, secret_prefix):
                    success_count += 1
                    print("✅")
                else:
                    print("❌")
        else:
            print("\nℹ️  No secrets to duplicate")
        
        self.logger.info(f"Successfully duplicated {success_count}/{len(secrets)} secrets")
        self.logger.info(f"Project duplication completed. New project ID: {new_project.id}")
        
        return True

    def create_environment_templates(self, source_project_id: str, base_project_name: str, environments: List[str]) -> bool:
        """Create multiple environment projects from a source project using predefined templates."""
        self.logger.info(f"Starting batch environment creation for project {source_project_id}")
        
        # Get source project
        source_project = self.get_project(source_project_id)
        if not source_project:
            self.logger.error("Source project not found or inaccessible")
            return False
        
        self.logger.info(f"Found source project: {source_project.name}")
        
        # Get project secrets
        secrets = self.get_project_secrets(source_project_id)
        self.logger.info(f"Found {len(secrets)} secrets in source project")
        
        if not secrets:
            self.logger.warning("No secrets found in source project")
            return False
        
        # Create environments
        created_projects = []
        total_environments = len(environments)
        
        print(f"\n🌍 Creating {total_environments} environment projects...")
        
        for i, env in enumerate(environments, 1):
            if env not in self.environment_templates:
                self.logger.warning(f"Unknown environment template: {env}")
                continue
            
            template = self.environment_templates[env]
            project_name = f"{base_project_name}-{env}"
            prefix = template["prefix"]
            
            print(f"\n   [{i}/{total_environments}] Creating {env} environment...")
            print(f"      Project: {project_name}")
            print(f"      Prefix: {prefix}_")
            
            # Create new project
            new_project = self.create_project(project_name)
            if not new_project:
                self.logger.error(f"Failed to create project for {env} environment")
                continue
            
            # Duplicate secrets with prefix
            success_count = 0
            total_secrets = len(secrets)
            
            print(f"      🔄 Duplicating {total_secrets} secrets...")
            for j, secret in enumerate(secrets, 1):
                new_key = f"{prefix}_{secret.key}"
                print(f"         [{j}/{total_secrets}] '{secret.key}' → '{new_key}'...", end=" ")
                if self.duplicate_secret(secret, new_project.id, prefix):
                    success_count += 1
                    print("✅")
                else:
                    print("❌")
            
            created_projects.append({
                "environment": env,
                "project_name": project_name,
                "project_id": new_project.id,
                "secrets_duplicated": success_count,
                "total_secrets": total_secrets
            })
            
            self.logger.info(f"Created {env} environment: {project_name} (ID: {new_project.id})")
            self.logger.info(f"Successfully duplicated {success_count}/{total_secrets} secrets")
        
        # Summary
        print(f"\n🎉 Environment creation completed!")
        print(f"   Created {len(created_projects)} environment projects:")
        for project in created_projects:
            print(f"   ✅ {project['environment']}: {project['project_name']} ({project['secrets_duplicated']}/{project['total_secrets']} secrets)")
        
        return True

    def show_environment_templates(self):
        """Display available environment templates."""
        print("\n🌍 Available Environment Templates:")
        print("-" * 50)
        for env, template in self.environment_templates.items():
            print(f"  {env:8} → {template['prefix']}_ (prefix)")
            print(f"           {template['description']}")
            print()

    def run(self):
        """Main execution method."""
        print("=== Bitwarden Project Duplicator ===\n")
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Please check your ACCESS_TOKEN in the .env file.")
            sys.exit(1)
        
        # Show menu options
        while True:
            print("\nOptions:")
            print("1. Duplicate single project")
            print("2. Create environment templates (dev, staging, prod, etc.)")
            print("3. Show available environment templates")
            print("4. Exit")
            
            choice = input("\nSelect an option (1-4): ").strip()
            
            if choice == "1":
                self._duplicate_single_project()
                break
            elif choice == "2":
                self._create_environment_templates()
                break
            elif choice == "3":
                self._show_environment_templates()
            elif choice == "4":
                print("Goodbye!")
                sys.exit(0)
            else:
                print("Invalid choice. Please select 1-4.")

    def _duplicate_single_project(self):
        """Handle single project duplication."""
        # Get source project UUID
        while True:
            source_project_id = input("Enter the source project UUID: ").strip()
            if source_project_id:
                break
            print("Project UUID cannot be empty. Please try again.")
        
        # Get new project name
        while True:
            new_project_name = input("Enter the new project name: ").strip()
            if new_project_name:
                break
            print("Project name cannot be empty. Please try again.")
        
        # Get secret prefix (optional)
        secret_prefix = input("Enter a prefix for secret names (optional, press Enter to skip): ").strip()
        if secret_prefix:
            print(f"   Secret names will be prefixed with: '{secret_prefix}_'")
        
        # Confirm duplication
        print(f"\n📋 Ready to duplicate:")
        print(f"   Source Project ID: {source_project_id}")
        print(f"   New Project Name: {new_project_name}")
        if secret_prefix:
            print(f"   Secret Prefix: {secret_prefix}_")
        
        confirm = input("\nProceed with duplication? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Operation cancelled.")
            sys.exit(0)
        
        # Perform duplication
        try:
            if self.duplicate_project(source_project_id, new_project_name, secret_prefix):
                print("\n✅ Project duplication completed successfully!")
            else:
                print("\n❌ Project duplication failed. Check the logs above for details.")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n\n⚠️  Operation cancelled by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            sys.exit(1)

    def _create_environment_templates(self):
        """Handle environment template creation."""
        # Get source project UUID
        while True:
            source_project_id = input("Enter the source project UUID: ").strip()
            if source_project_id:
                break
            print("Project UUID cannot be empty. Please try again.")
        
        # Get base project name
        while True:
            base_project_name = input("Enter the base project name (e.g., 'backend' for 'backend-dev', 'backend-staging'): ").strip()
            if base_project_name:
                break
            print("Base project name cannot be empty. Please try again.")
        
        # Show available templates
        self.show_environment_templates()
        
        # Get environments to create
        print("Enter the environments to create (comma-separated, e.g., 'dev,staging,prod'):")
        print("Available: " + ", ".join(self.environment_templates.keys()))
        
        while True:
            env_input = input("Environments: ").strip()
            if env_input:
                environments = [env.strip().lower() for env in env_input.split(",")]
                # Validate environments
                invalid_envs = [env for env in environments if env not in self.environment_templates]
                if invalid_envs:
                    print(f"Invalid environments: {', '.join(invalid_envs)}")
                    print(f"Available: {', '.join(self.environment_templates.keys())}")
                    continue
                break
            print("Environments cannot be empty. Please try again.")
        
        # Confirm creation
        print(f"\n📋 Ready to create environment projects:")
        print(f"   Source Project ID: {source_project_id}")
        print(f"   Base Project Name: {base_project_name}")
        print(f"   Environments: {', '.join(environments)}")
        print(f"   Projects to create:")
        for env in environments:
            template = self.environment_templates[env]
            print(f"     - {base_project_name}-{env} (prefix: {template['prefix']}_)")
        
        confirm = input("\nProceed with creation? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Operation cancelled.")
            sys.exit(0)
        
        # Perform creation
        try:
            if self.create_environment_templates(source_project_id, base_project_name, environments):
                print("\n✅ Environment template creation completed successfully!")
            else:
                print("\n❌ Environment template creation failed. Check the logs above for details.")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n\n⚠️  Operation cancelled by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            sys.exit(1)

    def _show_environment_templates(self):
        """Display environment templates and return to main menu."""
        self.show_environment_templates()
        input("Press Enter to return to main menu...")


def main():
    """Entry point for the script."""
    try:
        duplicator = BitwardenProjectDuplicator()
        duplicator.run()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease ensure your .env file contains:")
        print("  - ORGANIZATION_ID=your_org_id")
        print("  - ACCESS_TOKEN=your_access_token")
        print("  - STATE_FILE=./bw_state (optional)")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()