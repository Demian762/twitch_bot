# Configuración del Bot del Estadio

Esta carpeta contiene la configuración externa del bot, separada del código fuente.

## 📁 Archivos

- **`config_template.ini`** - Plantilla con todas las variables de configuración necesarias
- **`config.ini`** - Tu configuración personal (NO se sube a Git, contiene credenciales)

## 🚀 Primera configuración

1. **Copiá el archivo plantilla:**
   ```
   config_template.ini → config.ini
   ```

2. **Editá `config.ini` con tus credenciales:**
   - Tokens de Twitch
   - API keys de YouTube, RAWG, Steam
   - Credenciales de Google Sheets
   - Token de Telegram (opcional)

3. **Guardá y ejecutá el bot**

## 🔒 Seguridad

⚠️ **IMPORTANTE**: El archivo `config.ini` contiene información sensible:
- **NO lo compartas** con nadie
- **NO lo subas** a repositorios públicos
- Está incluido en `.gitignore` automáticamente

## 📝 Notas

- Si algún valor no está configurado, el bot intentará usar variables de entorno
- Para desarrollo local, podés usar los valores hardcodeados en `secretos.py`
- Para distribución, los usuarios DEBEN configurar este archivo

## 🆘 Ayuda

Si tenés problemas:
1. Verificá que todas las secciones estén presentes
2. Asegurate de que no haya espacios extra en los valores
3. Las claves privadas de Google deben mantener el formato con `\n`
4. Revisá los logs en la carpeta `logs/` para ver qué falta
