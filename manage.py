#!/usr/bin/env python
"""Point d'entrée principal pour les commandes Django du projet Dynamic."""
from __future__ import annotations

import os
import sys


def main() -> None:
    """Initialise les paramètres Django et exécute la commande demandée."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dynamic_shop.dynamic_shop.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
