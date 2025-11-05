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

#### Predefined Categories

If you want to use predefined categories instead of letting AI decide:

```bash
cp .categories.example .categories
# Edit .categories to customize your categories
```

If `.categories` doesn't exist, Claude will automatically determine appropriate categories.

### 4. Run

#### Via GitHub Actions (Recommended)

- The workflow runs automatically daily at midnight UTC
- Or manually trigger it: Actions → Update Awesome List → Run workflow

#### Locally

```bash
pip install -r requirements.txt
python scripts/generate_awesome_list.py
```

## How It Works

1. **Fetch Stars**: Retrieves all your GitHub starred repositories
2. **Cache Check**: Compares with `.cache` to find new stars
3. **AI Processing**: For each new star, Claude:
   - Analyzes the repo (description, topics, language, stars)
   - Determines the best category
   - Generates a concise, helpful description
4. **Generate List**: Creates/updates `README.md` with organized list
5. **Commit**: GitHub Actions commits changes automatically

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
