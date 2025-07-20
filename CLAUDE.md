# Claude Development Guidelines

## Security & Secrets Management

**CRITICAL: Always check for secrets before committing**

1. **Never commit secrets, tokens, or credentials** - Check all files for:
   - API keys, access tokens, passwords
   - Database connection strings with credentials
   - Private keys or certificates
   - Any hardcoded sensitive values

2. **Use environment variables for all secrets:**
   - Create `.env.example` with placeholder values
   - Use `${VARIABLE_NAME}` syntax in config files
   - Ensure `.env` is in `.gitignore`

3. **Before any git commit, scan for:**
   - Files containing `token`, `key`, `password`, `secret`
   - Hardcoded URLs with credentials
   - Any file that should use environment variables

## Project-Specific Guidelines

### Testing Commands
- Test silver layer: Run DLT pipeline in Databricks with updated transformations
- Check for lint/type errors: Determine testing approach from README or ask user

### Pipeline Architecture
- Use parameterized catalogs: `catalog = spark.conf.get("catalog", "cfdb_dev")`
- FBS filtering: `(home_classification = 'fbs' OR away_classification = 'fbs')`
- Time normalization: Convert MM:SS to seconds for game stats, keep seconds for season stats

### Data Processing
- Focus on FBS teams including games against lower divisions
- Use advanced analytics with EPA metrics for sophisticated analysis
- Follow medallion architecture: Bronze → Silver → Gold