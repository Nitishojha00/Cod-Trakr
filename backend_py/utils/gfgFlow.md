Request
   |
Redis Check
   |
Hit? ---- Yes ---> Return Cached Data
 |
 No
 |
Cheerio
 |
Success? --> saveAndReturn()
 |
 No
 |
Playwright
 |
Success? --> saveAndReturn()
 |
 No
 |
Puppeteer
 |
Success? --> saveAndReturn()
 |
 No
 |
Return Default Result