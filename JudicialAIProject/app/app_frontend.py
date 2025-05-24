import streamlit as st
import requests

st.title("Login JudicialAI")

# Inputs del usuario
username = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")

if st.button("Iniciar sesión"):
    # Hacer POST al backend
    data = {
        "username": username,
        "password": password
    }

    response = requests.post(
        "http://127.0.0.1:8000/token",
        data={
            "grant_type": "password",
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code == 200:
        token = response.json().get("access_token")
        st.success("✅ Login exitoso")
        st.write("Token JWT:")
        st.code(token, language="bash")

        # Mostrar información del usuario autenticado
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get("http://127.0.0.1:8000/me", headers=headers)
        if me_response.status_code == 200:
            st.write("Usuario autenticado:", me_response.json())
        else:
            st.warning("Token inválido o expirado")
    else:
        st.error("❌ Credenciales incorrectas")
