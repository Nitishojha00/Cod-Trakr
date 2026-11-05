## Caching Strategy

### Previous Approach: User-Level Dashboard Caching

Initially, the application cached the entire dashboard response per user.

```text
dashboard:data:userId
```

When a dashboard request arrived:

1. Check dashboard cache.
2. Return cached response if available.
3. Refresh data in the background when cache became stale.

While this reduced response time, it introduced a few drawbacks:

* Cached dashboards could become stale even when platform-level data was already updated.
* Additional complexity due to background refresh, timestamps, and locking mechanisms.
* Changing a single platform username required invalidating the entire dashboard cache.
* Multiple cache layers (dashboard cache + platform cache) increased maintenance complexity.

---

### Current Approach: Platform-Level Caching

The application now caches data at the platform level:

```text
leetcode:<username>
codeforces:<username>
codechef:<username>
gfg:<username>
```

Request flow:

```text
User Request
      ↓
Fetch User Platforms
      ↓
Check Platform Cache
      ↓
Cache Hit  → Return Cached Stats
Cache Miss → Fetch Platform Data
           → Store in Redis
           → Return Fresh Stats
      ↓
Aggregate Dashboard Response
      ↓
Send Response
```

---

### Why Platform-Level Caching?

#### 1. More Accurate Data

Caching is applied directly to the expensive operations (scraping and external API calls) rather than the aggregated dashboard response.

This ensures the dashboard is always built using the latest available platform data.

#### 2. Better Username Handling

If a user changes a platform username:

```text
LeetCode: nitish → tourist
```

the system automatically looks for:

```text
leetcode:tourist
```

instead of reusing:

```text
leetcode:nitish
```

This eliminates stale dashboard issues caused by user-level caching.

#### 3. Independent Cache Invalidation

Each platform cache is isolated.

Example:

```text
LeetCode  → Cache Hit
CodeChef  → Cache Hit
Codeforces → Cache Miss
```

Only the missing platform is fetched again.

#### 4. Simpler Architecture

The following components were removed:

* Dashboard cache
* Background refresh jobs
* Cache timestamps
* Distributed locks
* Stale-while-revalidate logic

Resulting in cleaner and easier-to-maintain code.

#### 5. Reduced External Requests

Frequently requested profiles are served directly from Redis, significantly reducing calls to:

* LeetCode APIs
* Codeforces APIs
* CodeChef scraping endpoints
* GeeksforGeeks profile pages

---

### Final Architecture

```text
MongoDB
   ↓
User Platforms
   ↓
Redis Platform Cache
   ↓
Platform Fetchers
   ↓
Dashboard Aggregation
   ↓
API Response
```

This design keeps the caching layer closer to the actual data source, improving freshness, maintainability, and overall system efficiency.
