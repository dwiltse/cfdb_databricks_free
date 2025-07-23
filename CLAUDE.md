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

## Databricks Apps Development

### Web Application Framework
- **Cookbook Reference**: https://apps-cookbook.dev/docs/category/streamlit
- **Supported Frameworks**: Streamlit (dashboards), FastAPI (APIs), Dash (advanced analytics)
- **Deployment**: Databricks Apps with serverless compute (scales to zero)

### Integration Patterns
- **Data Access**: Use `databricks.sql.connect()` for Unity Catalog queries
- **Authentication**: Implement OBO (on-behalf-of-user) for user-specific access
- **ML Serving**: Deploy prediction models via Databricks Apps endpoints
- **Cost Optimization**: Leverage auto-scaling serverless compute

### CFDB App Ideas
- Interactive Nebraska prediction dashboard (Streamlit)
- Team comparison analytics (Dash)
- Prediction API service (FastAPI)
- Real-time game analysis tools

### Development Workflow
1. Build locally using cookbook examples
2. Test with sample CFDB data  
3. Deploy to Databricks Apps environment
4. Configure Unity Catalog permissions
5. Enable user authentication