from django.core.exceptions import ValidationError

# ============================================================
# VALIDADORES PERSONALIZADOS
# ============================================================
# Son funciones que reciben un valor y lanzan ValidationError
# si no cumple la regla de negocio.
# Se aplican en el parámetro 'validators' de los campos del modelo.
# ============================================================

# Valida que el peso sea mayor a 0
def validar_peso_positivo(value):
    if value <= 0:
        raise ValidationError(
            f'El peso debe ser mayor a 0. Recibió: {value} kg'
        )

# Valida que el código de encomienda empiece con "ENC-"
def validar_codigo_encomienda(value):
    """El código debe empezar con ENC-"""
    if not value.startswith('ENC-'):
        raise ValidationError(
            'El código de encomienda debe comenzar con ENC-'
        )

# Valida que el DNI tenga exactamente 8 dígitos numéricos
def validar_nro_doc_dni(value):
    """El DNI debe tener exactamente 8 dígitos numéricos"""
    if not value.isdigit() or len(value) != 8:
        raise ValidationError(
            'El DNI debe contener exactamente 8 dígitos numéricos'
        )