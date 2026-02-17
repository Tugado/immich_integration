# Integración Immich para Home Assistant

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Quality Scale](https://img.shields.io/badge/Quality%20Scale-Platinum-brightgreen)](quality_scale.yaml)

Esta integración permite agregar tu cuenta de usuario de [Immich](https://immich.app/) a Home Assistant, integrando completamente tu servidor de fotos sin depender de la nube.

## 🎯 Características Principales

- **Media Source**: Accede a tus álbumes, personas y etiquetas desde Home Assistant
- **Sensores de Almacenamiento**: Monitoriza el espacio en disco, cantidad de fotos y videos
- **Control de Jobs**: Pausa y reanuda trabajos del servidor Immich (respaldos, análisis, etc.)
- **Upload de Archivos**: Carga fotos y videos directamente a Immich desde Home Assistant
- **Notificaciones de Actualizaciones**: Recibe alertas cuando hay nuevas versiones disponibles
- **Integración Local**: Funciona completamente en tu red local sin conexión a Internet

## 📋 Requisitos Previos

### Obtener la clave API

Necesitas obtener una [clave API](https://immich.app/docs/features/command-line-interface#obtain-the-api-key) para tu cuenta de usuario en tu instancia de Immich.

### Permisos Requeridos

Al crear tu clave API, habilita los siguientes permisos. Sin estos datos, la integración puede no funcionar correctamente:

- `album.read` - Lectura de álbumes
- `albumAsset.create` - Agregar recursos a álbumes
- `asset.download` - Descargar recursos
- `asset.upload` - Cargar recursos
- `asset.view` - Ver recursos
- `person.read` - Lectura de personas
- `server.about` - Información del servidor
- `server.statistics` - Estadísticas (solo administrador)
- `server.storage` - almacenamiento
- `server.versionCheck` - Verificación de versión
- `tag.read` - Lectura de etiquetas
- `user.read` - Lectura de usuarios

> **Nota Importante**: Para versiones de Immich anteriores a 1.138.0, es necesario usar el permiso `all`.

## ⚙️ Configuración

### Instalación Automática (Recomendado)

1. Ve a **Configuración > Dispositivos e integraciones**
2. Haz clic en **Crear automatización** (esquina inferior derecha)
3. Busca "Immich"
4. Completa la información:
   - **URL**: La dirección de tu instancia Immich (ej: `https://immich.example.com`)
   - **Clave API**: Tu clave API obtenida anteriormente
   - **Verificar certificado SSL**: Activa según tu configuración

### Configuración Manual

Agregar a tu `configuration.yaml`:

```yaml
immich:
  url: https://immich.example.com
  api_key: your_api_key_here
  verify_ssl: true
```

## 📊 Actualizaciones de Datos

La integración realiza una búsqueda de datos cada **60 segundos** para mantener sincronizada la información de tu servidor Immich.

## 🖼️ Fuente de Medios

Se proporciona una fuente de medios para acceder a tus álbumes de Immich. Muestra solo los recursos que posees o que se comparten contigo.

Los recursos están organizados en:
- **Álbumes**: Tus colecciones de fotos y videos
- **Personas**: Recursos agrupados por personas detectadas
- **Etiquetas**: Recursos etiquetados

Si tienes múltiples instancias de Immich configuradas en Home Assistant (una por cada usuario), la fuente de medios mostrará solo los recursos de ese usuario específico.

**Uso en Media Player**: Puedes usar la fuente de medios con cualquier media player en Home Assistant:

```yaml
service: media_player.play_media
target:
  entity_id: media_player.living_room
data:
  media_content_type: image
  media_content_id: >
    media-source://media_source/immich/albums/[album_id]/[asset_id]
```

## 📈 Sensores

Se crean automáticamente los siguientes sensores de monitoreo:

| Sensor | Descripción | Requiere Admin |
|--------|-------------|---|
| Tamaño Total del Disco | Tamaño total disponible en el disco | ✅ |
| Espacio Disponible | Espacio libre en el disco | ✅ |
| Espacio Utilizado | Espacio usado en el disco | ❌ |
| Porcentaje de Uso | Porcentaje de uso del disco | ❌ |
| Cantidad de Fotos | Número total de fotos almacenadas (solo admin) | ✅ |
| Cantidad de Videos | Número total de videos almacenados (solo admin) | ✅ |
| Espacio por Fotos | Espacio en disco ocupado por fotos (solo admin) | ❌ |
| Espacio por Videos | Espacio en disco ocupado por videos (solo admin) | ❌ |

### Ejemplo de Automatización

Crear una notificación cuando el disco está casi lleno:

```yaml
automation:
  - alias: "Alertar - Disco Immich Casi Lleno"
    trigger:
      platform: numeric_state
      entity_id: sensor.immich_disk_usage
      above: 85
    action:
      service: notify.mobile_app
      data:
        message: "El disco de Immich está al {{ states('sensor.immich_disk_usage') }}% de capacidad"
        title: "⚠️ Espacio en Disco Bajo"
```

## 🔄 Control de Jobs (FUNCIONALIDAD EXTENDIDA)

Esta integración incluye control completo sobre los jobs del servidor Immich, permitiendo pausar y reanudar operaciones del servidor como:

- **Face Detection** - Análisis de rostros
- **Clip Encoding** - Codificación CLIP
- **Generate Thumbnails** - Generación de miniaturas
- **Smart Search** - Búsqueda inteligente
- **Tag Dedupe** - Deduplicación de etiquetas
- **Classify Objects** - Clasificación de objetos
- **Recognize Faces** - Reconocimiento facial
- **Transcode Video** - Transcodificación de video

### Interruptores de Jobs

Se crean automáticamente interruptores para cada job disponible en tu servidor. El estado del interruptor indica si el job está pausado:

- **Interruptor ENCENDIDO** = Job pausado
- **Interruptor APAGADO** = Job ejecutándose

Puedes controlar estos interruptores desde la interfaz de usuario o mediante automatizaciones.

### Acciones de Control de Jobs

#### 1. Pausar un Job

```yaml
action: immich.pause_job
data:
  config_entry_id: "entrada_de_configuracion_id"
  job_id: "face_detection"
```

#### 2. Reanudar un Job

```yaml
action: immich.resume_job
data:
  config_entry_id: "entrada_de_configuracion_id"
  job_id: "face_detection"
```

### Ejemplos de Automatización

**Pausar análisis de caras durante horas de trabajo**:

```yaml
automation:
  - alias: "Pausar Face Detection - Horas de Trabajo"
    trigger:
      platform: time
      at: "08:00:00"
    action:
      action: immich.pause_job
      data:
        config_entry_id: "01JVJ0RA387MWA938VE8HGXBMJ"
        job_id: "face_detection"
    condition:
      platform: time
      weekday:
        - mon
        - tue
        - wed
        - thu
        - fri

  - alias: "Reanudar Face Detection - Después del Trabajo"
    trigger:
      platform: time
      at: "18:00:00"
    action:
      action: immich.resume_job
      data:
        config_entry_id: "01JVJ0RA387MWA938VE8HGXBMJ"
        job_id: "face_detection"
```

**Pausar jobs cuando el sistema está cargado**:

```yaml
automation:
  - alias: "Pausar Jobs - Sistema Cargado"
    trigger:
      platform: numeric_state
      entity_id: sensor.cpu_usage
      above: 80
    action:
      - action: immich.pause_job
        data:
          config_entry_id: "01JVJ0RA387MWA938VE8HGXBMJ"
          job_id: "face_detection"
      - action: immich.pause_job
        data:
          config_entry_id: "01JVJ0RA387MWA938VE8HGXBMJ"
          job_id: "clip_encoding"
```

## 📤 Acciones (Services)

### Cargar Archivo

Permite cargar un archivo de medios (foto o video) directamente a tu instancia de Immich.

**Parámetros**:
- `config_entry_id` (requerido): ID de la instancia Immich destino
- `file` (requerido): El archivo a cargar (foto o video)
- `album_id` (opcional): ID del álbum donde colocar el archivo

**Obtener el ID del Álbum**: Abre tu instancia de Immich en el navegador, ve al álbum deseado y copia el ID de la URL: `https://tu-instancia/albums/<ALBUM-ID>`

#### Ejemplo: Captura de Cámara a Immich

Tomar una foto de tu cámara y cargarla automáticamente a Immich:

```yaml
automation:
  - alias: "Capturar foto de Cámara a Immich"
    trigger:
      platform: time
      at: "08:00:00"
    action:
      - variables:
          file_name: cámara_{{ now().strftime("%Y%m%d-%H%M%S") }}.jpg
      - action: camera.snapshot
        data:
          filename: "/media/{{ file_name }}"
        target:
          entity_id: camera.puerta_entrada
      - action: immich.upload_file
        data:
          config_entry_id: "01JVJ0RA387MWA938VE8HGXBMJ"
          file:
            media_content_id: "media-source://media_source/local/{{ file_name }}"
            media_content_type: "image/jpeg"
          album_id: "f2de0ede-d7d4-4db3-afe3-7288f4e65bb1"
```

## 🔄 Entidad de Actualización

Se crea automáticamente una entidad de actualización que te informa sobre nuevas versiones disponibles de tu servidor Immich.

> **Requisito**: Immich server v1.134.0 o superior

Puedes usar esta entidad en automatizaciones para notificarte de actualizaciones:

```yaml
automation:
  - alias: "Notificar - Nueva versión de Immich"
    trigger:
      platform: state
      entity_id: update.immich_server_version
      to: "on"
    action:
      service: notify.mobile_app
      data:
        title: "Actualización de Immich Disponible"
        message: >
          Nueva versión disponible: 
          {{ state_attr('update.immich_server_version', 'latest_version') }}
```

## 🐛 Solución de Problemas

### Problema: "La clave API no tiene permisos suficientes"

**Solución**: Verifica que tu clave API tenga todos los permisos necesarios listados en la sección de requisitos.

### Problema: "No se pueden conectar a Immich"

1. Verifica que la URL sea correcta y accesible desde tu red local
2. Si usas HTTPS, intenta desactivar "Verificar certificado SSL" (solo para testing)
3. Revisa los logs de Home Assistant para más detalles

### Problema: Los sensores no muestran datos

- Algunos sensores requieren permisos de administrador en Immich
- Espera 60 segundos (intervalo de polling) para que se actualicen los datos
- Intenta recargar la integración desde Settings > Devices & Services

### Habilitar Logs de Debug

Para obtener información detallada de depuración:

```yaml
logger:
  logs:
    aioimmich: debug
    homeassistant.components.immich: debug
```

### Descargar Datos de Diagnóstico

1. Ve a **Settings > Devices & Services**
2. Selecciona tu instancia de Immich
3. Haz clic en los tres puntos y selecciona **Descargar diagnósticos**

Esta información puede ser útil al reportar problemas.

## 📋 Limitaciones Conocidas

- Los jobs disponibles dependen de la versión de tu servidor Immich
- El control de jobs está disponible solo para administradores del servidor
- La carga de archivos solo soporta medios locales (no URLs remotas)

## ❌ Remover la Integración

### Para remover una instancia de Immich

1. Ve a **Settings > Devices & Services** (Configuración > Dispositivos e integraciones)
2. Busca tu instancia de Immich en la lista
3. Haz clic en ella
4. Selecciona los tres puntos ⋮ en la esquina superior derecha
5. Haz clic en **Delete** (Eliminar)

Si la clave API ya no se usa, elimínala también de tu instancia de Immich en Settings > API Keys.

## 📝 Información Adicional

- **Tipo de Integración**: Servicio
- **Clase IoT**: Local Polling
- **Escala de Calidad**: Platinum
- **Última Actualización**: 2026

## 🔗 Enlaces Útiles

- [Documentación oficial de Immich](https://immich.app/docs/)
- [API de Immich](https://immich.app/docs/api/)
- [Home Assistant Immich Integration](https://www.home-assistant.io/integrations/immich/)
- [Repositorio en GitHub](https://github.com/home-assistant/core/tree/dev/homeassistant/components/immich)

## 👨‍💻 Contribuyentes

Esta integración fue creada y es mantenida por los siguientes colaboradores:
- [@mib1185](https://github.com/mib1185)
- [@Tugado](https://github.com/Tugado)

## 📄 Licencia

Esta integración está bajo licencia Apache 2.0. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

**¿Necesitas ayuda?** Reporta problemas o solicita nuevas características en [GitHub Issues](https://github.com/home-assistant/core/issues?q=is%3Aissue+label%3A%22integration%3A+immich%22)
