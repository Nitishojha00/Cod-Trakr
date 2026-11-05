fetchLeetCode(username)
        |
        v
Check Redis Cache
        |
   +----+----+
   |         |
Found      Not Found
   |         |
Return    Call API
Cached       |
Data         v
         Parse Data
              |
         Store in Redis
              |
         Return Result