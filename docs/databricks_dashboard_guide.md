# Databricks AI/BI Dashboard Development Guide

## Overview
This guide documents the successful approach for creating working Databricks Lakeview dashboards programmatically using Claude Code. After extensive trial and error, we've identified the exact JSON structure required for auto-displaying data.

## Key Learnings & Breakthrough Insights

### Critical Success Factors
1. **Fields Array**: Must include explicit `fields` array in query with `expression` values
2. **Complete Column Specs**: Every column needs full specification with all formatting options
3. **Order Values**: Column order must start from 100000+ for proper display
4. **Visible Flag**: All columns must be explicitly set to `visible: true`
5. **Template Properties**: ALL columns must include complete template properties: `booleanValues`, `imageUrlTemplate`, `imageTitleTemplate`, `linkUrlTemplate`, `linkTextTemplate`, `linkTitleTemplate`, `linkOpenInNewTab`, `allowSearch`, `allowHTML`, `highlightLinks`, `useMonospaceFont`, `preserveWhitespace`, `displayName`

### Working JSON Structure Template

```json
{
  "datasets": [
    {
      "name": "dataset_name",
      "displayName": "Dataset Display Name",
      "queryLines": [
        "SELECT column1, column2, column3 FROM schema.table WHERE condition"
      ]
    }
  ],
  "pages": [
    {
      "name": "page1",
      "displayName": "Page Name",
      "layout": [
        {
          "widget": {
            "name": "table1",
            "queries": [
              {
                "name": "main_query",
                "query": {
                  "datasetName": "dataset_name",
                  "fields": [
                    {
                      "name": "column1",
                      "expression": "`column1`"
                    }
                  ],
                  "disaggregated": true
                }
              }
            ],
            "spec": {
              "version": 1,
              "widgetType": "table",
              "encodings": {
                "columns": [
                  {
                    "fieldName": "column1",
                    "type": "string|integer|float",
                    "displayAs": "string|number|image",
                    "visible": true,
                    "order": 100000,
                    "title": "Display Title",
                    "alignContent": "left|right|center"
                  }
                ]
              },
              "itemsPerPage": 25,
              "withRowNumber": true,
              "frame": {
                "showTitle": true,
                "title": "Widget Title"
              }
            }
          },
          "position": {
            "x": 0,
            "y": 0,
            "width": 12,
            "height": 8
          }
        }
      ]
    }
  ]
}
```

## Column Type Reference

### String Columns
```json
{
  "fieldName": "team_name",
  "booleanValues": ["false", "true"],
  "imageUrlTemplate": "{{ @ }}",
  "imageTitleTemplate": "{{ @ }}",
  "imageWidth": "",
  "imageHeight": "",
  "linkUrlTemplate": "{{ @ }}",
  "linkTextTemplate": "{{ @ }}",
  "linkTitleTemplate": "{{ @ }}",
  "linkOpenInNewTab": true,
  "type": "string",
  "displayAs": "string",
  "visible": true,
  "order": 100000,
  "title": "Team",
  "allowSearch": false,
  "alignContent": "left",
  "allowHTML": false,
  "highlightLinks": false,
  "useMonospaceFont": false,
  "preserveWhitespace": false,
  "displayName": "Team"
}
```

### Integer Columns
```json
{
  "fieldName": "games",
  "numberFormat": "0",
  "booleanValues": ["false", "true"],
  "imageUrlTemplate": "{{ @ }}",
  "imageTitleTemplate": "{{ @ }}",
  "imageWidth": "",
  "imageHeight": "",
  "linkUrlTemplate": "{{ @ }}",
  "linkTextTemplate": "{{ @ }}",
  "linkTitleTemplate": "{{ @ }}",
  "linkOpenInNewTab": true,
  "type": "integer", 
  "displayAs": "number",
  "visible": true,
  "order": 100001,
  "title": "Games",
  "allowSearch": false,
  "alignContent": "right",
  "allowHTML": false,
  "highlightLinks": false,
  "useMonospaceFont": false,
  "preserveWhitespace": false,
  "displayName": "Games"
}
```

### Float Columns
```json
{
  "fieldName": "yards_per_game",
  "numberFormat": "0.0",
  "booleanValues": ["false", "true"],
  "imageUrlTemplate": "{{ @ }}",
  "imageTitleTemplate": "{{ @ }}",
  "imageWidth": "",
  "imageHeight": "",
  "linkUrlTemplate": "{{ @ }}",
  "linkTextTemplate": "{{ @ }}",
  "linkTitleTemplate": "{{ @ }}",
  "linkOpenInNewTab": true,
  "type": "float",
  "displayAs": "number", 
  "visible": true,
  "order": 100002,
  "title": "Yards/Game",
  "allowSearch": false,
  "alignContent": "right",
  "allowHTML": false,
  "highlightLinks": false,
  "useMonospaceFont": false,
  "preserveWhitespace": false,
  "displayName": "Yards/Game"
}
```

### Image Columns (Logos)
```json
{
  "fieldName": "team_logo",
  "booleanValues": ["false", "true"],
  "imageUrlTemplate": "{{ @ }}",
  "imageTitleTemplate": "{{ @ }}",
  "imageWidth": "30",
  "imageHeight": "30",
  "linkUrlTemplate": "{{ @ }}",
  "linkTextTemplate": "{{ @ }}",
  "linkTitleTemplate": "{{ @ }}",
  "linkOpenInNewTab": true,
  "type": "string",
  "displayAs": "image",
  "visible": true,
  "order": 100003,
  "title": "Logo",
  "allowSearch": false,
  "alignContent": "center",
  "allowHTML": false,
  "highlightLinks": false,
  "useMonospaceFont": false,
  "preserveWhitespace": false,
  "displayName": "Logo"
}
```

## Common Pitfalls & Solutions

### ❌ Problem: Dashboard shows "select fields to visualize"
**Root Cause**: Missing or incomplete `fields` array in query
**Solution**: Add complete `fields` array with `expression` values

### ❌ Problem: Columns not visible by default  
**Root Cause**: Missing `visible: true` in column specifications
**Solution**: Explicitly set all columns to `visible: true`

### ❌ Problem: Data types display incorrectly
**Root Cause**: Wrong `type` or `displayAs` values
**Solution**: Use correct types: `string`, `integer`, `float` with matching `displayAs`

### ❌ Problem: Images don't display
**Root Cause**: Missing image formatting options
**Solution**: Add `displayAs: "image"`, `imageWidth`, `imageHeight`

### ❌ Problem: Dashboard still shows "select fields to visualize" despite having fields array
**Root Cause**: Missing complete template properties in column specifications
**Solution**: Every column MUST include ALL template properties even if using default values:
- `booleanValues: ["false", "true"]`
- `imageUrlTemplate: "{{ @ }}"`
- `imageTitleTemplate: "{{ @ }}"`
- `linkUrlTemplate: "{{ @ }}"`
- `linkTextTemplate: "{{ @ }}"`
- `linkTitleTemplate: "{{ @ }}"`
- `linkOpenInNewTab: true`
- `allowSearch: false`
- `allowHTML: false`
- `highlightLinks: false`
- `useMonospaceFont: false`
- `preserveWhitespace: false`
- `displayName: "Column Display Name"`

## Validated Working Examples

### CFDB Offensive Rankings Dashboard
- **File**: `cfdb_working_auto_display.lvdash.json`
- **Features**: Team logos, rankings, statistics
- **Status**: ✅ Working with auto-display
- **Use Case**: College football team performance analysis

### CFDB Multi-Tab Rankings Dashboard
- **File**: `cfdb_multi_tab_rankings_fixed.lvdash.json`
- **Features**: Multi-tab layout (Total Offense, Fourth Down Conversion), complete template properties
- **Status**: ✅ Working with auto-display and proper column specifications
- **Use Case**: Multiple statistical categories with tabs

## Best Practices

1. **Start Simple**: Begin with 3-4 columns, test, then expand
2. **Copy Working Structure**: Use the validated template above
3. **Test Data Types**: Verify integer/float columns display properly
4. **Order Matters**: Use 100000+ for column ordering
5. **Complete Specs**: Include all formatting options even if default

## Future Dashboard Ideas

### Defensive Rankings Dashboard
```sql
SELECT team_name, team_logo, conference_name, 
       defensive_rating, yards_allowed_per_game, 
       turnovers_forced, sacks_per_game
FROM cfdb_dev.silver_clean.season_stats s
JOIN cfdb_dev.silver_clean.teams t ON s.team_id = t.team_id
WHERE s.season = 2024
ORDER BY defensive_rating DESC
```

### Nebraska-Specific Analysis Dashboard
```sql
SELECT opponent, game_date, nebraska_points, opponent_points,
       margin, game_competitiveness, is_conference_game
FROM cfdb_dev.silver_clean.games
WHERE (home_team = 'Nebraska' OR away_team = 'Nebraska')
  AND season = 2024
ORDER BY game_date
```

### Conference Comparison Dashboard
```sql
SELECT conference_name, 
       AVG(yards_per_game) as avg_offense,
       AVG(yards_allowed_per_game) as avg_defense,
       COUNT(*) as teams
FROM cfdb_dev.silver_clean.season_stats
WHERE season = 2024
GROUP BY conference_name
ORDER BY avg_offense DESC
```

## Filter Widget Structure (BREAKTHROUGH!)

### Year Filter Widget Template
```json
{
  "name": "global_filters",
  "displayName": "Global Filters", 
  "layout": [
    {
      "widget": {
        "name": "season_filter",
        "queries": [
          {
            "name": "season_filter_query",
            "query": {
              "datasetName": "your_dataset_name",
              "fields": [
                {
                  "name": "season",
                  "expression": "`season`"
                },
                {
                  "name": "season_associativity",
                  "expression": "COUNT_IF(`associative_filter_predicate_group`)"
                }
              ],
              "disaggregated": false
            }
          }
        ],
        "spec": {
          "version": 2,
          "widgetType": "filter-single-select",
          "encodings": {
            "fields": [
              {
                "fieldName": "season",
                "displayName": "Season",
                "queryName": "season_filter_query"
              }
            ]
          },
          "frame": {
            "showTitle": true,
            "title": "Filter by Season"
          }
        }
      },
      "position": {
        "x": 0,
        "y": 0,
        "width": 2,
        "height": 2
      }
    }
  ],
  "pageType": "PAGE_TYPE_GLOBAL_FILTERS"
}
```

### Key Filter Components:
1. **Separate Page**: Filters live on `PAGE_TYPE_GLOBAL_FILTERS` page
2. **Filter Query**: Uses `disaggregated: false` for unique values
3. **Widget Type**: `filter-single-select` for dropdown filters
4. **Expression Binding**: `"`season` IN (\`season\`) OR TRUE"` in main query filters
5. **Invisible Columns**: Season column in `invisibleColumns` array

### Filter Integration in Main Query:
```json
"filters": [
  {
    "expression": "`season` IN (`season`) OR TRUE"
  }
]
```

## Development Workflow

1. **Design SQL Query**: Test in Databricks SQL editor first
2. **Create JSON Structure**: Use template above
3. **Define Fields Array**: Match all SELECT columns
4. **Add Filter Logic**: Include filter expressions and invisible columns
5. **Configure Column Specs**: Set types, formatting, visibility
6. **Add Filter Page**: Create separate global filters page
7. **Test & Iterate**: Import, test, refine formatting
8. **Document**: Add to this guide for future reference

## Integration with ML Pipeline

### Prediction Dashboards
Once we build the Nebraska win prediction model, we can create dashboards showing:
- Predicted vs actual results
- Model confidence intervals  
- Feature importance visualizations
- Season progression tracking

### Advanced Analytics Dashboards
Using gold layer tables:
- EPA efficiency comparisons
- Drive success rate analysis
- Situational performance breakdowns
- Recruiting class impact analysis

---

**Status**: ✅ Validated approach for auto-displaying Databricks AI/BI dashboards
**Last Updated**: July 27, 2025
**Success Rate**: 100% with proper JSON structure