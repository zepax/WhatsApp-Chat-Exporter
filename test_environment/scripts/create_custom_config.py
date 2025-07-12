#!/usr/bin/env python3
"""
Script para crear configuraciones personalizadas del analizador avanzado.
Permite crear configs específicas para diferentes tipos de análisis.
"""

import argparse
import json
from pathlib import Path


def create_work_config():
    """Configuración enfocada en análisis de trabajo."""
    return {
        "keywords": [
            "trabajo",
            "work",
            "oficina",
            "office",
            "proyecto",
            "project",
            "reunion",
            "meeting",
            "cliente",
            "client",
            "jefe",
            "boss",
            "deadline",
            "entrega",
            "presentacion",
            "presentation",
            "email",
            "correo",
            "documento",
            "document",
            "archivo",
            "file",
            "importante",
            "important",
            "urgente",
            "urgent",
            "asap",
            "presupuesto",
            "budget",
            "costo",
            "cost",
            "precio",
            "price",
        ],
        "custom_regex_patterns": {
            "emails_trabajo": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.(com|org|net|edu|gov)\\b",
            "fechas_deadline": "\\b(?:deadline|entrega|fecha[\\s:]*)\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}",
            "horarios_oficina": "\\d{1,2}:\\d{2}(?:\\s*[AP]M)?",
            "montos_trabajo": "\\$\\d+(?:,\\d{3})*(?:\\.\\d{2})?",
            "palabras_urgencia": "(?i)\\b(urgente|importante|asap|ya|ahora|rapido)\\b",
            "reuniones": "(?i)\\b(reunion|meeting|junta|call|videollamada)\\b",
            "proyectos": "(?i)\\b(proyecto|project|task|tarea|entregable)\\b",
        },
        "advanced_config": {
            "max_files": 15000,
            "max_file_size_mb": 300,
            "parallel_workers": 6,
            "save_match_examples": True,
            "max_examples_per_pattern": 30,
        },
        "description": "Configuración especializada para análisis de conversaciones de trabajo",
    }


def create_family_config():
    """Configuración enfocada en análisis familiar."""
    return {
        "keywords": [
            "familia",
            "family",
            "papa",
            "dad",
            "mama",
            "mom",
            "hijo",
            "son",
            "hija",
            "daughter",
            "hermano",
            "brother",
            "hermana",
            "sister",
            "amor",
            "love",
            "te amo",
            "i love you",
            "feliz",
            "happy",
            "cumpleanos",
            "birthday",
            "aniversario",
            "anniversary",
            "vacaciones",
            "vacation",
            "viaje",
            "trip",
            "travel",
            "casa",
            "home",
            "hogar",
            "navidad",
            "christmas",
            "fiesta",
            "party",
            "celebracion",
            "celebration",
        ],
        "custom_regex_patterns": {
            "expresiones_amor": "(?i)\\b(te amo|i love you|te quiero|love you|mi amor|my love)\\b",
            "eventos_familiares": "(?i)\\b(cumpleanos|birthday|aniversario|anniversary|boda|wedding)\\b",
            "familiares": "(?i)\\b(papa|dad|mama|mom|hijo|son|hija|daughter|hermano|brother|hermana|sister|abuelo|grandpa|abuela|grandma)\\b",
            "emociones_positivas": "(?i)\\b(feliz|happy|alegre|contento|emocionado|excited|orgulloso|proud)\\b",
            "fechas_especiales": "\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}",
            "planes_familiares": "(?i)\\b(vacaciones|vacation|viaje|trip|salir|go out|visitar|visit)\\b",
        },
        "advanced_config": {
            "max_files": 20000,
            "max_file_size_mb": 400,
            "parallel_workers": 4,
            "save_match_examples": True,
            "max_examples_per_pattern": 50,
        },
        "description": "Configuración especializada para análisis de conversaciones familiares",
    }


def create_business_config():
    """Configuración enfocada en análisis de negocios."""
    return {
        "keywords": [
            "negocio",
            "business",
            "venta",
            "sale",
            "compra",
            "buy",
            "cliente",
            "client",
            "customer",
            "proveedor",
            "supplier",
            "dinero",
            "money",
            "precio",
            "price",
            "costo",
            "cost",
            "factura",
            "invoice",
            "pago",
            "payment",
            "cobro",
            "collection",
            "producto",
            "product",
            "servicio",
            "service",
            "mercado",
            "market",
            "competencia",
            "competition",
            "estrategia",
            "strategy",
        ],
        "custom_regex_patterns": {
            "montos_negocio": "\\$\\d+(?:,\\d{3})*(?:\\.\\d{2})?",
            "porcentajes": "\\d+(?:\\.\\d+)?%",
            "numeros_factura": "(?i)\\b(?:factura|invoice)[\\s#:]*\\d+",
            "fechas_pago": "(?i)\\b(?:pago|payment|fecha)[\\s:]*)\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}",
            "terminos_negocio": "(?i)\\b(venta|sale|compra|buy|precio|price|descuento|discount|oferta|offer)\\b",
            "contactos_negocio": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.(com|net|org)\\b",
        },
        "advanced_config": {
            "max_files": 30000,
            "max_file_size_mb": 600,
            "parallel_workers": 8,
            "save_match_examples": True,
            "max_examples_per_pattern": 40,
        },
        "description": "Configuración especializada para análisis de conversaciones de negocios",
    }


def create_social_config():
    """Configuración enfocada en análisis social."""
    return {
        "keywords": [
            "amigo",
            "friend",
            "amigos",
            "friends",
            "fiesta",
            "party",
            "salir",
            "go out",
            "diversion",
            "fun",
            "risa",
            "laugh",
            "broma",
            "joke",
            "gracioso",
            "funny",
            "jaja",
            "haha",
            "lol",
            "plan",
            "plans",
            "evento",
            "event",
            "concierto",
            "concert",
            "restaurante",
            "restaurant",
            "comida",
            "food",
            "bebida",
            "drink",
        ],
        "custom_regex_patterns": {
            "risas": "(?i)\\b(jaja|haha|lol|jeje|hehe|xd)\\b",
            "planes_sociales": "(?i)\\b(salir|go out|plan|plans|evento|event|fiesta|party)\\b",
            "lugares_sociales": "(?i)\\b(restaurante|restaurant|bar|club|cafe|cinema|parque|park)\\b",
            "emociones_sociales": "(?i)\\b(divertido|fun|gracioso|funny|genial|awesome|increible|amazing)\\b",
            "invitaciones": "(?i)\\b(vamos|let's go|quieres|want to|te invito|invite you)\\b",
        },
        "advanced_config": {
            "max_files": 25000,
            "max_file_size_mb": 500,
            "parallel_workers": 6,
            "save_match_examples": True,
            "max_examples_per_pattern": 35,
        },
        "description": "Configuración especializada para análisis de conversaciones sociales",
    }


def main():
    parser = argparse.ArgumentParser(description="Crear configuraciones personalizadas")
    parser.add_argument(
        "type",
        choices=["work", "family", "business", "social", "all"],
        help="Tipo de configuración a crear",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=".",
        help="Directorio donde guardar las configuraciones",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    configs = {
        "work": create_work_config,
        "family": create_family_config,
        "business": create_business_config,
        "social": create_social_config,
    }

    if args.type == "all":
        for config_type, config_func in configs.items():
            config_data = config_func()
            output_file = output_dir / f"{config_type}_config.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            print(f"✅ Configuración '{config_type}' creada: {output_file}")
    else:
        config_data = configs[args.type]()
        output_file = output_dir / f"{args.type}_config.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Configuración '{args.type}' creada: {output_file}")

    print("\n📋 Uso:")
    if args.type == "all":
        for config_type in configs.keys():
            print(
                f"  python3 advanced_content_analyzer.py /ruta/chats --config {config_type}_config.json"
            )
    else:
        print(
            f"  python3 advanced_content_analyzer.py /ruta/chats --config {args.type}_config.json"
        )


if __name__ == "__main__":
    main()
