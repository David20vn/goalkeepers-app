from app.core.security import verify_password, hash_password
hashed = hash_password ("YaammyamP192025&")

print (hashed)

print(verify_password("admin", "$argon2id$v=19$m=65536,t=3,p=4$WRKENmOGgO2hYDmo6fBlEQ$Z66hucTHaX8uSgOQmYQQ/YR3vQSZOGD6IEJTkCTUDcw"))