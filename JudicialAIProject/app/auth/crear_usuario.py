from sqlalchemy.orm import Session
from oauth2_login_fastapi import SessionLocal, User, pwd_context

# Crear sesión
db: Session = SessionLocal()

# Crear usuario nuevo
nuevo_usuario = User(
    username="user1",
    full_name="Usuario Uno",
    hashed_password=pwd_context.hash("123456")
)

# Guardar en base de datos
db.add(nuevo_usuario)
db.commit()
db.refresh(nuevo_usuario)
print("✅ Usuario creado:", nuevo_usuario.username)
db.close()