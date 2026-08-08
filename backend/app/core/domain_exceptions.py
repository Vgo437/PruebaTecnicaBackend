class DomainException(Exception):
    """Excepcion base para errores de negocio del dominio de solicitudes."""
    pass


class SolicitudNoEncontrada(DomainException):
    """Se lanza cuando no existe una solicitud con el ID solicitado."""
    pass


class IdentificadorDuplicado(DomainException):
    """Se lanza cuando ya existe una solicitud con el mismo identificador_externo."""
    pass


class TransicionInvalida(DomainException):
    """Se lanza cuando se intenta un cambio de estado no permitido."""

    def __init__(self, estado_actual, estado_nuevo):
        self.estado_actual = estado_actual
        self.estado_nuevo = estado_nuevo
        super().__init__(f"No se puede cambiar de '{estado_actual.value}' a '{estado_nuevo.value}'")