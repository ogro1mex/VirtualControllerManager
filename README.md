# Virtual Controller Manager

Programa profesional similar a DS4Windows con interfaz gráfica, detección de mandos físicos, creación de mandos Xbox360 virtuales, tracking visual con IA (ONNX), y sistema de macros avanzado.

## Características

- ✅ Detección de todos los tipos de mandos (PS4, PS5, Xbox, Switch, genéricos)
- ✅ Creación de mandos Xbox360 virtuales
- ✅ Replicación en tiempo real de inputs
- ✅ Tracking visual con detección de objetivos (modelos ONNX 320x320)
- ✅ Sistema de macros enlazadas al mando virtual
- ✅ Interfaz gráfica similar a DS4Windows
- ✅ Múltiples pestañas de control
- ✅ Persistencia de tracking

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

## Estructura del Proyecto

```
VirtualControllerManager/
├── main.py                 # Aplicación principal
├── requirements.txt        # Dependencias
├── config/
│   ├── __init__.py
│   └── settings.json      # Configuración persistente
├── controllers/
│   ├── __init__.py
│   ├── input_detector.py  # Detección de mandos físicos
│   └── virtual_xbox.py    # Control de Xbox360 virtual
├── tracking/
│   ├── __init__.py
│   ├── object_tracker.py  # Tracking de objetivos
│   └── visual_capture.py  # Captura y procesamiento visual
├── macros/
│   ├── __init__.py
│   └── macro_engine.py    # Sistema de macros
├── ui/
│   ├── __init__.py
│   ├── main_window.py     # Ventana principal
│   ├── tabs/
│   │   ├── __init__.py
│   │   ├── controller_tab.py
│   │   ├── tracking_tab.py
│   │   ├── macros_tab.py
│   │   └── settings_tab.py
│   └── styles.qss        # Estilos personalizados
└── models/
    └── yolov8_320x320.onnx  # Modelo ONNX para tracking
```

## Requisitos del Sistema

- Python 3.10+
- Windows 10/11
- Driver ViGEmBus instalado
- Webcam o cámara para tracking visual

## Instalación de ViGEmBus

Descargar desde: https://github.com/ViGEm/ViGEmBus/releases

## Licencia

MIT
