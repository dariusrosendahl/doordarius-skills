# GSC & BigQuery Navigation Paths

Browser click-paths for navigating Google Search Console and BigQuery using `claude-in-chrome` tools.

> Replace `<your-domain>` placeholders below with the actual domain you're auditing.

---

## §GSC — Google Search Console

### Property URL

Domain property:
```
https://search.google.com/search-console/performance/search-analytics?resource_id=sc-domain%3A<your-domain>
```

URL-prefix property:
```
https://search.google.com/search-console/performance/search-analytics?resource_id=https%3A%2F%2Fwww.<your-domain>%2F
```

### Prerequisites

- User must be logged into a Google account with GSC access
- Use `claude-in-chrome tabs_context_mcp` to check if GSC is already open
- If not, use `claude-in-chrome navigate` to the property URL above

---

### Performance Report

**Navigation:**
1. Navigate to the property URL above (or click "Performance" → "Search results" in sidebar)
2. The default view shows last 3 months

**Setting date range:**
1. Click the "Date:" filter chip at the top
2. Select preset (7d, 28d, 3m, 6m, 12m, 16m) or "Custom"
3. For custom: set start/end dates, click "Apply"

**Reading data:**
- **Summary cards** at top: Total clicks, Total impressions, Average CTR, Average position
- **Chart** below shows trends over time
- **Table tabs** below chart:
  - **Queries** — search terms driving traffic
  - **Pages** — URLs receiving impressions/clicks
  - **Countries** — geographic distribution
  - **Devices** — mobile/desktop/tablet split
  - **Search Appearance** — rich results, AMP, etc.

**Filtering by URL:**
1. Click "+ New" filter button above the chart
2. Select "Page..."
3. Choose operator: "URLs containing", "Exact URL", or "URLs not containing"
4. Enter the URL or path fragment
5. Click "Apply"

**Filtering by query:**
1. Click "+ New" filter button
2. Select "Query..."
3. Enter keyword or phrase
4. Click "Apply"

**Comparing periods:**
1. Click "Date:" filter chip
2. Select "Compare" tab
3. Choose comparison range
4. Click "Apply"

---

### Coverage / Indexing Report

**Navigation:**
1. Click "Indexing" → "Pages" in the left sidebar
2. Or navigate to: `https://search.google.com/search-console/index?resource_id=sc-domain%3A<your-domain>`

**Reading data:**
- **Summary bar**: count of "Not indexed" and "Indexed" pages
- **Why pages aren't indexed** table — expandable rows:
  - "Crawled - currently not indexed"
  - "Discovered - currently not indexed"
  - "Page with redirect"
  - "Not found (404)"
  - "Excluded by 'noindex' tag"
  - "Duplicate without user-selected canonical"
  - etc.
- Click any row to see the list of affected URLs
- Click "Validate fix" after correcting issues

**Exporting data:**
- Click the export icon (download arrow) top-right of any table
- Choose Google Sheets, CSV, or download

---

### URL Inspection

**Navigation:**
1. Click the search bar at the top of GSC (or use the "URL Inspection" sidebar link)
2. Paste the full URL: `https://www.<your-domain>/path`
3. Press Enter

**Reading results:**
- **URL is on Google** / **URL is not on Google** — primary status
- **Coverage** section:
  - Discovery: "Sitemaps" or "Referral"
  - Crawl: Last crawl date, crawl status
  - Indexing: Allowed?, User-declared canonical, Google-selected canonical
- **Enhancements**: Mobile usability, Breadcrumbs, etc.
- Click "Test live URL" for a fresh crawl (takes ~30 seconds)
- Click "Request indexing" to submit URL for re-crawling

---

### Sitemaps

**Navigation:**
1. Click "Sitemaps" in the left sidebar
2. Or navigate to: `https://search.google.com/search-console/sitemaps?resource_id=sc-domain%3A<your-domain>`

**Actions:**
- View submitted sitemaps, their status, and discovered URL count
- Submit new sitemap: enter URL in "Add a new sitemap" field, click "Submit"
- Click any sitemap to see details and errors

---

## §BigQuery — GA4 & GSC Data

### Console URL

```
https://console.cloud.google.com/bigquery
```

### Prerequisites

- User must be logged into Google Cloud with BigQuery access
- Project must have GA4 BigQuery export or GSC bulk export enabled

### Navigation

**Selecting project:**
1. Click the project dropdown in the top-left nav bar
2. Search for or select the project containing GA4/GSC data
3. Click "Select"

**Finding datasets:**
1. In the Explorer panel (left sidebar), expand the project
2. Look for datasets named like:
   - `analytics_XXXXXXXXX` — GA4 export
   - `searchconsole` — GSC bulk export
3. Expand dataset to see tables:
   - GA4: `events_*` (partitioned by date, e.g., `events_20260218`)
   - GSC: `searchdata_site_impression`, `searchdata_url_impression`

### Example Queries

**GA4 — Landing page performance (last 30 days):**
```sql
SELECT
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS landing_page,
  COUNT(DISTINCT user_pseudo_id) AS users,
  COUNT(*) AS events,
  COUNTIF(event_name = 'session_start') AS sessions,
  COUNTIF(event_name IN ('purchase', 'generate_lead')) AS conversions
FROM `project.analytics_XXXXXXXXX.events_*`
WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY))
  AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
  AND event_name IN ('session_start', 'page_view', 'purchase', 'generate_lead')
GROUP BY landing_page
ORDER BY sessions DESC
LIMIT 50;
```

**GSC — Search query performance:**
```sql
SELECT
  query,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  ROUND(SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100, 2) AS ctr_pct,
  ROUND(AVG(average_position), 1) AS avg_position
FROM `project.searchconsole.searchdata_site_impression`
WHERE data_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE()
GROUP BY query
ORDER BY impressions DESC
LIMIT 50;
```

**GSC — URL performance with indexing status:**
```sql
SELECT
  url,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  ROUND(SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100, 2) AS ctr_pct,
  ROUND(AVG(average_position), 1) AS avg_position
FROM `project.searchconsole.searchdata_url_impression`
WHERE data_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE()
  AND url LIKE '%<your-domain>%'
GROUP BY url
ORDER BY impressions DESC
LIMIT 50;
```

### Running a Query

1. Click "+ Compose new query" (or use the editor tab)
2. Paste the SQL query, replacing `project` and dataset IDs with actual values
3. Click "Run" (or Ctrl+Enter)
4. Results appear in the Results panel below
5. Click "Save Results" → "CSV" or "JSON" to export

### Tips

- GA4 tables are date-sharded (`events_YYYYMMDD`) — always use `_TABLE_SUFFIX` filter to avoid scanning all data
- GSC bulk export updates daily with a ~2-day delay
- Use `SAFE_DIVIDE` to avoid division-by-zero errors on CTR calculations
- BigQuery charges per bytes scanned — always filter by date and `LIMIT` results
