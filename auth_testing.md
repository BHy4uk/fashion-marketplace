# Auth Testing Playbook

## MongoDB verification
```
mongosh
use fashion_marketplace
db.identity_users.find({role:"admin"}).pretty()
db.identity_users.findOne({role:"admin"}, {password_hash:1})   # bcrypt hash starts with $2b$
db.identity_users.getIndexes()                                  # unique index on email
```

## API (use the external preview URL for e2e; localhost:8001 works locally)
```
# login (sets httpOnly access_token + refresh_token cookies)
curl -c cookies.txt -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"seller@archivemarket.co","password":"Seller12345"}'

# whoami using cookies
curl -b cookies.txt http://localhost:8001/api/auth/me

# my listings (owner-scoped)
curl -b cookies.txt http://localhost:8001/api/listings/mine
```

Accounts: see /app/memory/test_credentials.md
