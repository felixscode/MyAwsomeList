# My Awesome List

> A curated list of my GitHub stars, automatically organized and described by AI

This repository automatically transforms your GitHub stars into a beautifully organized awesome list using Claude AI.

## Features

- **Automatic Categorization**: AI-powered categorization of starred repositories
- **Smart Descriptions**: Claude generates concise, useful descriptions for each repo
- **Daily Updates**: GitHub Actions runs daily to keep your list fresh
- **Caching**: Only processes new stars to save on API costs
- **Customizable**: Optional predefined categories or let AI decide

## Setup

### 1. Fork or Clone This Repository

### 2. Set Up GitHub Secrets

Go to your repository settings → Secrets and variables → Actions, and add:

- `ANTHROPIC_API_KEY`: Your Anthropic API key from [console.anthropic.com](https://console.anthropic.com/settings/keys)
- `GITHUB_TOKEN` is automatically provided by GitHub Actions

### 3. Configure (Optional)

#### Local Development

For local testing, create a `.env` file:

```bash
cp .env.example .env
# Edit .env with your actual tokens
```

#### Categories Configuration (Recommended)

**IMPORTANT**: A `.categories` file is already included with 8 well-organized categories:

- AI & Machine Learning
- Reinforcement Learning
- Developer Tools
- Data Science & Analytics
- Robotics & Autonomous Systems
- Web & Desktop Development
- Finance & Trading
- Productivity & Utilities

The LLM will **only** choose from these predefined categories, preventing category fragmentation.

**To customize categories:**

```bash
# Edit .categories to add/modify/remove categories
nano .categories
```

**Without `.categories`**: Claude will create categories dynamically, which often results in too many similar categories (e.g., "AI Development", "AI Infrastructure", "Artificial Intelligence" as separate categories).

### 4. Run

#### Via GitHub Actions (Recommended)

- The workflow runs automatically daily at midnight UTC
- Or manually trigger it: Actions → Update Awesome List → Run workflow

#### Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Normal run (will modify files)
python scripts/generate_awesome_list.py

# Dry run (test without modifying files)
python scripts/generate_awesome_list.py --dry-run

# Dry run with limit (process only first 3 new repos for quick testing)
python scripts/generate_awesome_list.py --dry-run --limit 3

# Get help
python scripts/generate_awesome_list.py --help
```

**Dry Run Mode:**
- Use `--dry-run` to test the script without modifying `.cache` or `README.md`
- Generates `README.dry-run.md` instead so you can preview the output
- Use `--limit N` to process only N new repositories (saves API costs during testing)
- Perfect for testing before running the full workflow

## How It Works

1. **Fetch Stars**: Retrieves all your GitHub starred repositories
2. **Load Categories**: Loads predefined categories from `.categories` file
3. **Cache Check**: Compares with `.cache` to find new stars
4. **AI Processing**: For each new star, Claude:
   - Analyzes the repo (description, topics, language, stars)
   - Selects the best category from your predefined list
   - Generates a concise, helpful description
5. **Generate List**: Creates/updates `README.md` with organized list
6. **Commit**: GitHub Actions commits changes automatically

## Project Structure

```
MyAwsomeList/
├── .github/
│   └── workflows/
│       └── update-awesome-list.yml   # Automation workflow
├── scripts/
│   └── generate_awesome_list.py      # Main script
├── .cache                             # Processed stars (auto-generated)
├── .categories                        # Optional: predefined categories
├── .categories.example                # Example categories file
├── .env.example                       # Environment variables template
├── .gitignore
├── requirements.txt
├── README.md                          # This file (will be overwritten)
└── LICENSE
```

## Cost Optimization

- Uses **Claude 3.5 Haiku** (cheapest model)
- Caches processed repos to avoid reprocessing
- Only processes new stars
- Estimated cost: ~$0.01-0.10 per run (depending on new stars)

## Customization

### Change Update Frequency

Edit `.github/workflows/update-awesome-list.yml`:

```yaml
schedule:
  - cron: '0 0 * * *'  # Daily at midnight
  # - cron: '0 0 * * 0'  # Weekly on Sunday
  # - cron: '0 0 1 * *'  # Monthly on 1st
```

### Modify README Format

Edit the `generate_readme()` function in `scripts/generate_awesome_list.py`

## Troubleshooting

### Workflow fails with "ANTHROPIC_API_KEY not found"
- Make sure you added the secret in repository settings

### Script processes all repos every time
- Check if `.cache` file exists and is being committed
- Ensure `.cache` is not in `.gitignore`

### Categories seem off
- Create a `.categories` file with your preferred categories
- Or adjust the prompt in `categorize_with_llm()` function

## License

MIT License - See [LICENSE](LICENSE) for details

---

**Note**: This README will be automatically regenerated when the script runs. Any manual changes will be overwritten.
