# Green Campus Alert Map – API Documentation
## ENREDD Batna, Algeria | Version 1.0

Base URL: `http://localhost:5000/api`

---

## Authentication

### POST /auth/register
Register a new user.
**Body:**
```json
{
  "username":   "student1",
  "email":      "student1@enredd.dz",
  "password":   "securepass",
  "full_name":  "Ahmed Boudiaf",
  "student_id": "20210001",
  "department": "Renewable Energy"
}