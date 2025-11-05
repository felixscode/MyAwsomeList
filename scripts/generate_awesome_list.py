#!/usr/bin/env python3
"""
GitHub Stars to Awesome List Generator
Uses Anthropic's Claude API to automatically categorize and describe starred repositories.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional


class AwesomeListGenerator:
    def __init__(self, dry_run: bool = False, limit: Optional[int] = None):
        # Import dependencies here so --help works without them installed
        try:
            import requests
            import yaml
            from anthropic import Anthropic
            from dotenv import load_dotenv
            self.requests = requests
            self.yaml = yaml
            self.Anthropic = Anthropic
            # Load .env file if it exists
            if os.path.exists("./.env"):
                load_dotenv(".env")
        except ImportError as e:
            print(f"❌ Missing required dependency: {e}")
            print("Install dependencies with: pip install -r requirements.txt")
            sys.exit(1)
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.github_username = os.environ.get("GITHUB_USERNAME")
        self.dry_run = dry_run
        self.limit = limit
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.anthropic = Anthropic(api_key=self.anthropic_api_key)
        self.cache_file = ".cache"
        self.categories_file = ".categories"
        self.readme_file = "README.md" if not dry_run else "README.dry-run.md"

        if self.dry_run:
            print("🧪 DRY RUN MODE - No files will be modified")
            if self.limit:
                print(f"   Limiting processing to {self.limit} new repos")
            print()

    def fetch_github_stars(self) -> List[Dict]:
        """Fetch all starred repositories from GitHub."""
        print("Fetching GitHub stars...")

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        stars = []
        page = 1

        # If username is provided, use it; otherwise fetch authenticated user
        if self.github_username:
            url = f"https://api.github.com/users/{self.github_username}/starred"
        else:
            # Get authenticated user's starred repos
            url = "https://api.github.com/user/starred"

        while True:
            response = self.requests.get(
                url,
                headers=headers,
                params={"page": page, "per_page": 100}
            )

            if response.status_code != 200:
                print(f"Error fetching stars: {response.status_code}")
                print(f"Response: {response.text}")
                sys.exit(1)

            page_stars = response.json()
            if not page_stars:
                break

            stars.extend(page_stars)
            print(f"Fetched page {page} ({len(page_stars)} repos)")
            page += 1

        print(f"Total stars fetched: {len(stars)}")
        return stars

    def load_cache(self) -> Dict:
        """Load the cache of already processed stars."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}

    def save_cache(self, cache: Dict):
        """Save the cache to disk."""
        if self.dry_run:
            print(f"[DRY RUN] Would save cache with {len(cache)} entries to {self.cache_file}")
            return

        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=2)

    def load_categories(self) -> Optional[Dict]:
        """Load predefined categories if available."""
        if os.path.exists(self.categories_file):
            with open(self.categories_file, 'r') as f:
                return self.yaml.safe_load(f)
        return None

    def categorize_with_llm(self, repo: Dict, predefined_categories: Optional[Dict] = None) -> Dict:
        """Use Claude API to categorize and describe a repository."""
        repo_name = repo["full_name"]
        description = repo.get("description", "No description provided")
        topics = ", ".join(repo.get("topics", []))
        language = repo.get("language", "Unknown")
        stars = repo.get("stargazers_count", 0)

        # Build the prompt with strict category enforcement
        if predefined_categories and "categories" in predefined_categories:
            # Build detailed category list with descriptions
            category_details = []
            for cat in predefined_categories["categories"]:
                cat_name = cat["name"]
                cat_desc = cat.get("description", "")
                category_details.append(f"- {cat_name}: {cat_desc}")

            categories_text = "\n".join(category_details)

            prompt = f"""Analyze this GitHub repository and categorize it.

Repository Information:
- Name: {repo_name}
- Description: {description}
- Topics: {topics}
- Language: {language}
- Stars: {stars}

IMPORTANT: You MUST choose EXACTLY ONE category from this list. Do NOT create new categories.

Available Categories:
{categories_text}

Your tasks:
1. Select the MOST appropriate category from the list above (use exact category name)
2. Write a concise 1-2 sentence description explaining what the repository does and why it's useful

Respond ONLY with valid JSON in this exact format:
{{"category": "Category Name", "description": "Your concise description here."}}

Remember: Use the EXACT category name from the list above."""
        else:
            # Fallback if no categories file exists
            prompt = f"""Analyze this GitHub repository and provide:
1. A category name (e.g., "Web Development", "Machine Learning", "DevOps", etc.)
2. A concise 1-2 sentence description that explains what the repository does and why it's useful

Repository: {repo_name}
Description: {description}
Topics: {topics}
Language: {language}
Stars: {stars}

Respond ONLY with valid JSON in this exact format:
{{"category": "Category Name", "description": "Your concise description here."}}"""

        try:
            message = self.anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text.strip()

            # Parse JSON response
            result = json.loads(response_text)

            return {
                "category": result["category"],
                "description": result["description"],
                "url": repo["html_url"],
                "stars": stars,
                "language": language,
                "processed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"Error processing {repo_name}: {e}")
            # Fallback to basic categorization
            return {
                "category": language if language else "Other",
                "description": description or "Interesting repository",
                "url": repo["html_url"],
                "stars": stars,
                "language": language,
                "processed_at": datetime.utcnow().isoformat()
            }

    def process_new_stars(self, stars: List[Dict], cache: Dict, predefined_categories: Optional[Dict] = None) -> Dict:
        """Process only new stars that aren't in the cache."""
        new_count = 0
        updated_count = 0
        processed_new = 0

        for repo in stars:
            repo_full_name = repo["full_name"]

            # Check if repo is already in cache
            if repo_full_name in cache:
                # Update star count if changed
                if cache[repo_full_name]["stars"] != repo["stargazers_count"]:
                    cache[repo_full_name]["stars"] = repo["stargazers_count"]
                    updated_count += 1
                continue

            # Check if we've hit the limit in dry run mode
            if self.dry_run and self.limit and processed_new >= self.limit:
                new_count += 1  # Count it but don't process
                continue

            # New star - process it
            print(f"Processing new star: {repo_full_name}")
            result = self.categorize_with_llm(repo, predefined_categories)
            cache[repo_full_name] = result
            new_count += 1
            processed_new += 1

        if self.dry_run and self.limit and new_count > processed_new:
            print(f"\n[DRY RUN] Processed {processed_new} of {new_count} new stars (limit: {self.limit})")
            print(f"[DRY RUN] {new_count - processed_new} new stars were skipped due to limit")
        else:
            print(f"\nProcessed {new_count} new stars, updated {updated_count} existing stars")

        return cache

    def generate_readme(self, cache: Dict):
        """Generate the README.md awesome list."""
        if self.dry_run:
            print(f"\n[DRY RUN] Generating {self.readme_file}...")
        else:
            print("\nGenerating README.md...")

        # Organize by category
        categories = {}
        for repo_name, data in cache.items():
            category = data["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append({
                "name": repo_name,
                "url": data["url"],
                "description": data["description"],
                "stars": data["stars"],
                "language": data.get("language", "")
            })

        # Sort categories alphabetically and repos by stars within each category
        sorted_categories = sorted(categories.keys())
        for category in sorted_categories:
            categories[category].sort(key=lambda x: x["stars"], reverse=True)

        # Build README content
        readme_content = "# My Awesome List\n\n"
        readme_content += "> A curated list of my GitHub stars, automatically organized and described by AI 🤖\n\n"
        readme_content += f"*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | Total repos: {len(cache)}*\n\n"

        # Table of contents
        readme_content += "## Contents\n\n"
        for category in sorted_categories:
            anchor = category.lower().replace(" ", "-").replace("/", "").replace("&", "")
            readme_content += f"- [{category}](#user-content-{anchor}) ({len(categories[category])})\n"
        readme_content += "\n---\n\n"

        # Generate category sections
        for category in sorted_categories:
            readme_content += f"## {category}\n\n"
            for repo in categories[category]:
                repo_name = repo["name"].split("/")[1]  # Get just the repo name, not owner/repo
                language = f" `{repo['language']}`" if repo['language'] else ""
                stars = f"⭐ {repo['stars']}" if repo['stars'] > 0 else ""
                readme_content += f"- **[{repo_name}]({repo['url']})** - {repo['description']}{language} {stars}\n"
            readme_content += "\n"

        readme_content += "---\n\n"
        readme_content += "*Generated automatically by [MyAwsomeList](https://github.com/felixscode/MyAwsomeList) using Claude API*\n"

        # Write to file
        with open(self.readme_file, 'w') as f:
            f.write(readme_content)

        if self.dry_run:
            print(f"[DRY RUN] {self.readme_file} generated with {len(sorted_categories)} categories")
            print(f"[DRY RUN] Preview the generated file: cat {self.readme_file}")
        else:
            print(f"README.md generated with {len(sorted_categories)} categories")

    def run(self):
        """Main execution flow."""
        print("=" * 60)
        print("GitHub Stars to Awesome List Generator")
        print("=" * 60)

        # Load existing cache
        cache = self.load_cache()
        print(f"Loaded cache with {len(cache)} existing entries")

        # Load predefined categories (REQUIRED for consistent categorization)
        predefined_categories = self.load_categories()
        if predefined_categories:
            num_cats = len(predefined_categories.get('categories', []))
            print(f"✓ Loaded {num_cats} predefined categories from {self.categories_file}")
            # Show category names
            cat_names = [cat["name"] for cat in predefined_categories.get('categories', [])]
            print(f"  Categories: {', '.join(cat_names)}")
        else:
            print(f"⚠ WARNING: No .categories file found!")
            print(f"  The LLM will create categories dynamically (may result in many categories)")
            print(f"  Recommended: Copy .categories.example to .categories and customize it")

        # Fetch all stars from GitHub
        stars = self.fetch_github_stars()

        # Process new stars
        cache = self.process_new_stars(stars, cache, predefined_categories)

        # Save updated cache
        self.save_cache(cache)
        print(f"Cache saved with {len(cache)} total entries")

        # Generate README
        self.generate_readme(cache)

        print("\n" + "=" * 60)
        if self.dry_run:
            print("✅ Dry run complete! No actual files were modified.")
            print(f"   Cache would be saved to: {self.cache_file}")
            print(f"   README preview saved to: {self.readme_file}")
        else:
            print("✅ Awesome list generation complete!")
        print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate an awesome list from your GitHub stars using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal run (will modify files)
  python generate_awesome_list.py

  # Dry run (no files modified, generates README.dry-run.md)
  python generate_awesome_list.py --dry-run

  # Dry run with limit (process only first 3 new repos)
  python generate_awesome_list.py --dry-run --limit 3

  # Verbose dry run
  python generate_awesome_list.py --dry-run --verbose
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without modifying cache or README.md (generates README.dry-run.md instead)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="Limit processing to N new repositories (useful with --dry-run for testing)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    try:
        generator = AwesomeListGenerator(dry_run=args.dry_run, limit=args.limit)
        generator.run()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
