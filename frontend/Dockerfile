FROM node:23-alpine

# Crear directorio de trabajo
WORKDIR /app

# Copiar package.json y package-lock.json (si lo tienes)
COPY package*.json ./

# Instalar dependencias
RUN npm install && npm install -D vite@^5.0.0 @vitejs/plugin-vue
# Copiar el resto del código
COPY . .

# Exponer el puerto que usa Vite
EXPOSE 3000

# Comando de desarrollo (o reemplaza con `npm run build` y un server si prefieres producción)
CMD ["npm", "run", "dev", "--", "--host"]