import streamlit as st
import binascii
import numpy as np
from PIL import Image
import io
import wave
import base64

# --- LÓGICA DEL NÚCLEO (OFUSCADA) ---
# Esta sección contiene las funciones de esteganografía y cifrado César
_core_logic = """
def t_b(t): return ''.join(format(ord(i), '08b') for i in t)
def b_t(b):
    d = ''
    for i in range(0, len(b), 8): d += chr(int(b[i:i+8], 2))
    return d

def s_i(f, m):
    img = Image.open(f).convert('RGB')
    p = np.array(img)
    b_m = t_b(m) + '1111111111111110'
    f_p = p.flatten()
    for i in range(len(b_m)): f_p[i] = (f_p[i] & ~1) | int(b_m[i])
    return Image.fromarray(f_p.reshape(p.shape).astype(np.uint8))

def x_i(f):
    img = Image.open(f)
    p = np.array(img).flatten()
    b_d = ""
    for x in p:
        b_d += str(x & 1)
        if b_d.endswith('1111111111111110'): break
    return b_t(b_d[:-16])

def s_a(f, m):
    with wave.open(f, 'rb') as a:
        pa = a.getparams()
        fr = bytearray(list(a.readframes(a.getnframes())))
    b_m = t_b(m) + '1111111111111110'
    for i in range(len(b_m)): fr[i] = (fr[i] & ~1) | int(b_m[i])
    o = io.BytesIO()
    with wave.open(o, 'wb') as oa:
        oa.setparams(pa)
        oa.writeframes(bytes(fr))
    return o.getvalue()

def x_a(f):
    with wave.open(f, 'rb') as a:
        fr = bytearray(list(a.readframes(a.getnframes())))
    b_d = ""
    for x in fr:
        b_d += str(x & 1)
        if b_d.endswith('1111111111111110'): break
    return b_t(b_d[:-16])
"""
exec(_core_logic)

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Stegano & Basic Crypto", layout="centered")
st.title("🥷 Herramienta de Ocultación")

tab1, tab2 = st.tabs(["Esteganografía", "Criptografía Básica"])

with tab1:
    st.header("Esteganografía LSB")
    m_type = st.radio("Tipo de medio", ["Imagen (PNG)", "Audio (WAV)"])
    act = st.radio("Operación", ["Esconder", "Extraer"])
    u_file = st.file_uploader(f"Cargar {m_type}")

    if act == "Esconder":
        msg = st.text_area("Mensaje Secreto")
        if u_file and msg and st.button("Ejecutar"):
            if "Imagen" in m_type:
                res = s_i(u_file, msg)
                buf = io.BytesIO()
                res.save(buf, format="PNG")
                st.image(res, caption="Procesado")
                st.download_button("Descargar PNG", buf.getvalue(), "secret.png")
            else:
                res_a = s_a(u_file, msg)
                st.audio(res_a)
                st.download_button("Descargar WAV", res_a, "secret.wav")
    else:
        if u_file and st.button("Revelar"):
            try:
                res = x_i(u_file) if "Imagen" in m_type else x_a(u_file)
                st.success(f"Contenido: {res}")
            except: st.error("No se encontró mensaje oculto.")

with tab2:
    st.header("Transformaciones y Sustitución")
    txt = st.text_area("Texto a procesar")
    c1, c2, c3 = st.columns(3)
    
    if c1.button("Binario"):
        st.code(' '.join(format(ord(x), 'b') for x in txt))
    if c2.button("Hex"):
        st.code(binascii.hexlify(txt.encode()).decode())
    if c3.button("César (ROT3)"):
        r = "".join([chr((ord(c)-97+3)%26+97) if c.islower() else (chr((ord(c)-65+3)%26+65) if c.isupper() else c) for c in txt])
        st.success(r)
