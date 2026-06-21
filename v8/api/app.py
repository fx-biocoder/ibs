"""
IBS - Índice de Bioactividad del Suelo
Microservicio Flask — Puerto 5000
PHP llama a este servicio vía cURL
"""

from flask import Flask, request, jsonify
import pickle
import numpy as np
import os