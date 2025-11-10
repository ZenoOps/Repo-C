FROM node:22-alpine
WORKDIR /app
COPY . .
COPY package.json .
EXPOSE 4137
RUN npm install --force
RUN npm run build
CMD npm run preview