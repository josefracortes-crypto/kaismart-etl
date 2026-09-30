"""Catalogos canonicos de categorias del negocio Kaismart.

Se centralizan aqui para que el generador de datos simulados y la capa
Silver (estandarizacion) usen exactamente los mismos valores y alias.
"""

CIUDADES = ["Bogotá D.C.", "Cali", "Medellín", "Barranquilla", "Bucaramanga", "Pereira"]
CIUDADES_ALIAS = {
    "bogota": "Bogotá D.C.",
    "bogota dc": "Bogotá D.C.",
    "bogota d.c": "Bogotá D.C.",
    "medellin": "Medellín",
    "barranquilla ": "Barranquilla",
}

CANALES = ["Tienda física", "Página web", "Aplicación móvil"]
CANALES_ALIAS = {
    "web": "Página web",
    "pagina web": "Página web",
    "sitio web": "Página web",
    "app": "Aplicación móvil",
    "app movil": "Aplicación móvil",
    "aplicacion movil": "Aplicación móvil",
    "tienda": "Tienda física",
    "tienda fisica": "Tienda física",
}

CATEGORIAS_PRODUCTO = ["Tecnología", "Hogar", "Oficina", "Electrodomésticos", "Deportes"]
CATEGORIAS_PRODUCTO_ALIAS = {
    "tecnologia": "Tecnología",
    "electrodomesticos": "Electrodomésticos",
}

METODOS_PAGO = ["Tarjeta de crédito", "Tarjeta débito", "Efectivo", "PSE", "Pago contraentrega"]

ESTADOS_EVENTO = [
    "Pedido Recibido",
    "En Preparación",
    "Despachado",
    "En Tránsito",
    "Entregado",
    "Devuelto",
    "Cancelado",
]
ESTADOS_EVENTO_ALIAS = {
    "en preparacion": "En Preparación",
    "en transito": "En Tránsito",
    "recibido": "Pedido Recibido",
    "pedido recibido": "Pedido Recibido",
}

TRANSPORTADORAS = ["Servientrega", "Coordinadora", "TCC", "Interrapidísimo", "Envía"]
TRANSPORTADORAS_ALIAS = {
    "interrapidisimo": "Interrapidísimo",
    "envia": "Envía",
}

INCIDENCIAS = [
    "Retraso en entrega",
    "Producto dañado",
    "Dirección errónea",
    "Pérdida de paquete",
    "Cliente ausente",
]
INCIDENCIAS_ALIAS = {
    "producto danado": "Producto dañado",
    "direccion erronea": "Dirección errónea",
    "perdida de paquete": "Pérdida de paquete",
    "retraso": "Retraso en entrega",
}
