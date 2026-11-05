Request
   |
Redis Check
   |
Hit? ------ Yes ---> Return Cached Data
 |
 No
 |
Axios
 |
Success? ---> saveAndReturn()
 |
 No
 |
Playwright
 |
Success? ---> saveAndReturn()
 |
 No
 |
Puppeteer
 |
Success? ---> saveAndReturn()
 |
 No
 |
Return { solved: 0, rating: 0 }