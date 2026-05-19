# JS Extraction Snippets

Browser-executable JavaScript snippets for `claude-in-chrome javascript_tool`. Each returns structured data for SEO analysis.

---

## §1 Meta Tag Extraction

Extracts all SEO-relevant meta tags from the current page.

```javascript
(() => {
  const getMeta = (name) => {
    const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
    return el ? el.getAttribute('content') : null;
  };

  const ogTags = {};
  document.querySelectorAll('meta[property^="og:"]').forEach(el => {
    ogTags[el.getAttribute('property')] = el.getAttribute('content');
  });

  const twitterTags = {};
  document.querySelectorAll('meta[name^="twitter:"], meta[property^="twitter:"]').forEach(el => {
    const key = el.getAttribute('name') || el.getAttribute('property');
    twitterTags[key] = el.getAttribute('content');
  });

  const canonical = document.querySelector('link[rel="canonical"]');

  return JSON.stringify({
    title: document.title,
    titleLength: document.title.length,
    canonical: canonical ? canonical.getAttribute('href') : null,
    description: getMeta('description'),
    descriptionLength: (getMeta('description') || '').length,
    robots: getMeta('robots'),
    viewport: getMeta('viewport'),
    ogTags,
    twitterTags,
    charset: document.characterSet,
    lang: document.documentElement.lang,
    url: window.location.href,
  }, null, 2);
})();
```

---

## §2 JSON-LD Extraction

Parses all `<script type="application/ld+json">` blocks on the page.

```javascript
(() => {
  const scripts = document.querySelectorAll('script[type="application/ld+json"]');
  const schemas = [];

  scripts.forEach((script, i) => {
    try {
      const data = JSON.parse(script.textContent);
      schemas.push({
        index: i,
        type: data['@type'] || (Array.isArray(data['@type']) ? data['@type'].join(', ') : 'unknown'),
        id: data['@id'] || null,
        data,
      });
    } catch (e) {
      schemas.push({
        index: i,
        error: `Parse error: ${e.message}`,
        raw: script.textContent.substring(0, 200),
      });
    }
  });

  return JSON.stringify({
    count: schemas.length,
    schemas,
  }, null, 2);
})();
```

---

## §3 Heading Hierarchy

Extracts all headings (H1-H6) with their level and text content.

```javascript
(() => {
  const headings = [];
  document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(el => {
    headings.push({
      level: parseInt(el.tagName[1]),
      text: el.textContent.trim().substring(0, 120),
      id: el.id || null,
    });
  });

  const h1Count = headings.filter(h => h.level === 1).length;
  const issues = [];

  if (h1Count === 0) issues.push('Missing H1 tag');
  if (h1Count > 1) issues.push(`Multiple H1 tags (${h1Count} found)`);

  // Check for skipped levels
  for (let i = 1; i < headings.length; i++) {
    const gap = headings[i].level - headings[i - 1].level;
    if (gap > 1) {
      issues.push(`Skipped heading level: H${headings[i - 1].level} → H${headings[i].level} ("${headings[i].text.substring(0, 40)}")`);
    }
  }

  return JSON.stringify({
    total: headings.length,
    h1Count,
    issues,
    headings,
  }, null, 2);
})();
```

---

## §4 Internal Link Audit

Finds all internal links, flags trailing-slash issues, and counts totals.

```javascript
(() => {
  const origin = window.location.origin;
  const links = [];
  const issues = [];
  let internalCount = 0;
  let externalCount = 0;
  let trailingSlashCount = 0;

  document.querySelectorAll('a[href]').forEach(el => {
    const href = el.getAttribute('href');
    const text = el.textContent.trim().substring(0, 80);
    let fullUrl;

    try {
      fullUrl = new URL(href, origin);
    } catch {
      issues.push({ type: 'invalid-url', href, text });
      return;
    }

    const isInternal = fullUrl.origin === origin;

    if (isInternal) {
      internalCount++;
      const path = fullUrl.pathname;

      if (path !== '/' && path.endsWith('/')) {
        trailingSlashCount++;
        issues.push({
          type: 'trailing-slash',
          href: path,
          text,
        });
      }

      links.push({
        href: path,
        text,
        hasTrailingSlash: path !== '/' && path.endsWith('/'),
        nofollow: el.getAttribute('rel')?.includes('nofollow') || false,
      });
    } else {
      externalCount++;
    }
  });

  // Check for empty anchor text
  document.querySelectorAll('a[href]').forEach(el => {
    const text = el.textContent.trim();
    const img = el.querySelector('img');
    const ariaLabel = el.getAttribute('aria-label');
    if (!text && !img && !ariaLabel) {
      issues.push({
        type: 'empty-anchor-text',
        href: el.getAttribute('href'),
      });
    }
  });

  return JSON.stringify({
    internalCount,
    externalCount,
    trailingSlashCount,
    issueCount: issues.length,
    issues: issues.slice(0, 50),
    internalLinks: links.slice(0, 100),
  }, null, 2);
})();
```
