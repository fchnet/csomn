# utils/validadores.py
import re

def validar_telefone(telefone: str) -> bool:
    # Aceita DDD + número com ou sem hífen, espaços ou parênteses
    return bool(re.fullmatch(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}", telefone))

def validar_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))
