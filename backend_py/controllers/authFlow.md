```mermaid
flowchart TD

A["User Signup Request<br/>Name, Email, Password"] --> B["Validate Input"]

B --> C{"User Exists?"}

C -->|Yes| D["Return User Already Registered"]

C -->|No| E["Redis INCR otp_limit:email"]

E --> F{"Count > 4?"}

F -->|Yes| G["429 OTP Limit Exceeded"]

F -->|No| H["Generate OTP"]

H --> I["Hash Password & OTP"]

I --> J["Generate signupId (UUID)"]

J --> K["Store in Redis<br/>Key: signup:signupId<br/>TTL: 5 min"]

K --> L["Send OTP Email"]

L --> M{"Email Sent?"}

M -->|No| N["Rollback<br/>DECR otp_limit<br/>Delete Redis Entry"]

M -->|Yes| O["Return signupId"]
``` 