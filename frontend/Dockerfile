FROM node:23-alpine

# Crear directorio de trabajo
WORKDIR /app

# Copiar package.json y package-lock.json (si lo tienes)
COPY package*.json ./

# Instalar dependencias
RUN npm cache clean --force && npm install

# Copiar el resto del código
COPY . .

# Exponer el puerto que usa Vite
EXPOSE 3000

# Comando de desarrollo (o reemplaza con `npm run build` y un server si prefieres producción)
CMD ["npm", "run", "dev", "--", "--host"]