import streamlit as st
import binascii
import numpy as np
from PIL import Image
import io
import wave
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.fernet import Fernet

# --- Configuración de Página ---
st.set_page_config(page_title="Ultimate Crypto-Stegano Tool", layout="wide")
st.title("🛡️ Herramienta de Encriptación y Esteganografía")

tabs = st.tabs(["Criptografía Moderna", "Esteganografía (Imagen/Audio)", "Codificación Base"])

# --- FUNCIONES DE APOYO ---

def text_to_bin(text):
    return ''.join(format(ord(i), '08b') for i in text)

def bin_to_text(binary):
    str_data = ''
    for i in range(0, len(binary), 8):
        str_data += chr(int(binary[i:i+8], 2))
    return str_data

# --- TAB 1: CRIPTOGRAFÍA MODERNA (RSA & FERNET) ---
with tabs[0]:
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("RSA (Asimétrico)")
        if st.button("Generar Nuevas Llaves RSA"):
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public_key = private_key.public_key()
            
            st.session_state.pri_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()
            
            st.session_state.pub_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()

        pub_input = st.text_area("Llave Pública (PEM)", value=st.session_state.get('pub_key', ''), height=100)
        pri_input = st.text_area("Llave Privada (PEM)", value=st.session_state.get('pri_key', ''), height=100)
        
        msg_rsa = st.text_input("Mensaje para RSA")
        if st.button("Ejecutar RSA"):
            if msg_rsa and pub_input:
                # Encriptar
                pkey = serialization.load_pem_public_key(pub_input.encode())
                encrypted = pkey.encrypt(
                    msg_rsa.encode(),
                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
                )
                st.success(f"Encriptado (Hex): {binascii.hexlify(encrypted).decode()}")

    with col2:
        st.header("AES / Fernet (Simétrico)")
        f_key = st.text_input("Llave Fernet (32 bytes base64)", value=Fernet.generate_key().decode())
        msg_fernet = st.text_area("Mensaje o Hash a procesar")
        f_action = st.radio("Acción", ["Encriptar", "Desencriptar"])
        
        if st.button("Ejecutar Fernet"):
            f = Fernet(f_key.encode())
            if f_action == "Encriptar":
                token = f.encrypt(msg_fernet.encode())
                st.code(token.decode())
            else:
                try:
                    decoded = f.decrypt(msg_fernet.encode())
                    st.success(f"Mensaje original: {decoded.decode()}")
                except:
                    st.error("Llave o mensaje inválido.")

# --- TAB 2: ESTEGANOGRAFÍA ---
with tabs[1]:
    st.header("Ocultar información en Medios (LSB)")
    mode = st.selectbox("Tipo de Medio", ["Imagen (PNG)", "Audio (WAV)"])
    steg_action = st.radio("Acción Estego", ["Esconder", "Extraer"])
    
    file_upload = st.file_uploader(f"Cargar {mode}", type=["png", "wav"])
    
    if steg_action == "Esconder":
        secret_msg = st.text_input("Mensaje Secreto a ocultar")
        
        if file_upload and secret_msg and st.button("Procesar"):
            if mode == "Imagen (PNG)":
                img = Image.open(file_upload).convert('RGB')
                pixels = np.array(img)
                
                # LSB simple logic
                binary_msg = text_to_bin(secret_msg) + '1111111111111110' # EOF marker
                flat_pixels = pixels.flatten()
                
                for i in range(len(binary_msg)):
                    flat_pixels[i] = (flat_pixels[i] & ~1) | int(binary_msg[i])
                
                new_img = flat_pixels.reshape(pixels.shape)
                res_img = Image.fromarray(new_img.astype(np.uint8))
                
                buf = io.BytesIO()
                res_img.save(buf, format="PNG")
                st.image(res_img, caption="Imagen con mensaje oculto")
                st.download_button("Descargar Imagen", buf.getvalue(), "stego_img.png", "image/png")

            elif mode == "Audio (WAV)":
                with wave.open(file_upload, 'rb') as audio:
                    params = audio.getparams()
                    frames = bytearray(list(audio.readframes(audio.getnframes())))
                
                binary_msg = text_to_bin(secret_msg) + '1111111111111110'
                for i in range(len(binary_msg)):
                    frames[i] = (frames[i] & ~1) | int(binary_msg[i])
                
                new_audio = bytes(frames)
                buf = io.BytesIO()
                with wave.open(buf, 'wb') as out_audio:
                    out_audio.setparams(params)
                    out_audio.writeframes(new_audio)
                
                st.audio(buf.getvalue())
                st.download_button("Descargar Audio", buf.getvalue(), "stego_audio.wav", "audio/wav")

    else: # Extraer
        if file_upload and st.button("Extraer Mensaje"):
            if mode == "Imagen (PNG)":
                img = Image.open(file_upload)
                pixels = np.array(img).flatten()
                binary_data = ""
                for p in pixels:
                    binary_data += str(p & 1)
                    if binary_data.endswith('1111111111111110'):
                        break
                st.success(f"Mensaje Extraído: {bin_to_text(binary_data[:-16])}")
            
            elif mode == "Audio (WAV)":
                with wave.open(file_upload, 'rb') as audio:
                    frames = bytearray(list(audio.readframes(audio.getnframes())))
                
                binary_data = ""
                for f in frames:
                    binary_data += str(f & 1)
                    if binary_data.endswith('1111111111111110'):
                        break
                st.success(f"Mensaje Extraído: {bin_to_text(binary_data[:-16])}")

# --- TAB 3: SUSTITUCIÓN Y BASES ---
with tabs[2]:
    st.header("Transformaciones Rápidas")
    raw_input = st.text_area("Input de texto/datos")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button("A Binario"):
            st.code(' '.join(format(ord(x), 'b') for x in raw_input))
    with c2:
        if st.button("A Hexadecimal"):
            st.code(binascii.hexlify(raw_input.encode()).decode())
    with c3:
        shift = st.slider("Cifrado César (Sustitución)", 1, 25, 3)
        if st.button("Aplicar César"):
            res = ""
            for char in raw_input:
                if char.isalpha():
                    start = ord('A') if char.isupper() else ord('a')
                    res += chr((ord(char) - start + shift) % 26 + start)
                else:
                    res += char
            st.success(res)
